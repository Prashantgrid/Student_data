"""Build auditable 15-minute profiles from Zenodo 7955410.

Usage: python build_15min.py [input_root] [output_root]
Input root contains record_metadata.json and raw/ with the original 13 files.
Dependencies: numpy, pandas, openpyxl, pycdlib, matplotlib, pillow.
"""
from pathlib import Path
from datetime import datetime
import io
import json
import re
import sys
import hashlib
import shutil

import numpy as np
import pandas as pd
import openpyxl
import pycdlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "processed"
OUT.mkdir(parents=True, exist_ok=True)
EXTRACTED = OUT / "extracted_original_files"
EXTRACTED.mkdir(exist_ok=True)
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
metadata = json.loads((ROOT / "record_metadata.json").read_text())
verification = []
for entry in metadata["files"]:
    p = ROOT / "raw" / entry["key"]
    md5 = hashlib.md5(p.read_bytes()).hexdigest()
    assert "md5:" + md5 == entry["checksum"], p.name
    verification.append({"file": p.name, "bytes": p.stat().st_size, "md5_verified": True})


def aggregate_curve(x, y, edges, max_gap=5 / 60, edge_limit=15 / 60):
    """Time-weighted means of the piecewise-linear source curve.

    x is in hours. No interpolation across internal gaps exceeding max_gap.
    Strict means require full source-domain coverage. A separate estimate may
    extend the first/last source value by at most edge_limit hours.
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    assert np.isfinite(x).all() and np.isfinite(y).all()
    assert np.all(np.diff(x) > 0)
    gaps = [(a, b) for a, b in zip(x[:-1], x[1:]) if b - a > max_gap + 1e-8]
    rows = []
    for a, b in zip(edges[:-1], edges[1:]):
        support = max(0.0, min(b, x[-1]) - max(a, x[0]))
        missing_inside = sum(max(0.0, min(b, v) - max(a, u)) for u, v in gaps)
        support = max(0.0, support - missing_inside)
        coverage = min(1.0, support / (b - a))
        nodes = np.r_[a, x[(x > a) & (x < b)], b]
        mean = float(np.trapezoid(np.interp(nodes, x, y), nodes) / (b - a))
        valid_edges = (x[0] - a <= edge_limit + 1e-9) and (b - x[-1] <= edge_limit + 1e-9)
        estimate = mean if valid_edges and missing_inside < 1e-9 and coverage > 0 else np.nan
        strict = mean if coverage >= 1 - 1e-8 else np.nan
        rows.append((strict, estimate, coverage, missing_inside > 1e-9))
    return np.asarray(rows)


weekly = []
audits = []
edges = np.arange(97, dtype=float) / 4
for iso_file in sorted((ROOT / "raw").glob("*.iso"), key=lambda p: int(re.search(r"\d+", p.stem).group())):
    profile_number = int(re.search(r"\d+", iso_file.stem).group())
    profile_id = f"Z7955410_Type{profile_number:02d}"
    iso = pycdlib.PyCdlib()
    iso.open(str(iso_file))
    use_joliet = iso.has_joliet()
    walk_kw = {"joliet_path": "/"} if use_joliet else {"iso_path": "/"}
    for parent, _, filenames in iso.walk(**walk_kw):
        for filename in filenames:
            member = parent.rstrip("/") + "/" + filename
            buffer = io.BytesIO()
            iso.get_file_from_iso_fp(buffer, **({"joliet_path": member} if use_joliet else {"iso_path": member}))
            destination = EXTRACTED / profile_id / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(buffer.getvalue())
    iso.close()
    for path in sorted((EXTRACTED / profile_id).glob("*.csv")):
        day = path.stem.replace("Tueday", "Tuesday")
        assert day in WEEKDAYS, day
        data = pd.read_csv(path, header=None, names=["source_time", "apparent_power_kva"], skipinitialspace=True)
        data = data.sort_values("source_time")
        x, y = data.source_time.to_numpy(), data.apparent_power_kva.to_numpy()
        # Values span approximately 0..24 with ~0.0166 spacing. Accompanying
        # plots label the x axis "Jam" (hours). Do not interpret x as minutes.
        assert 23 < x.max() <= 24 and 0.015 < np.median(np.diff(x)) < 0.018
        values = aggregate_curve(x, y, edges)
        # Independently check integration over the padded 24-hour source curve.
        nodes = np.r_[0.0, x[(x > 0) & (x < 24)], 24.0]
        source_integral = float(np.trapezoid(np.interp(nodes, x, y), nodes))
        target_integral = float(values[:, 1].sum() * 0.25)
        assert np.isfinite(values[:, 1]).all(), (profile_id, day)
        assert abs(source_integral - target_integral) < 1e-8
        for k, (strict, filled, coverage, internal_gap) in enumerate(values):
            weekly.append({
                "profile_id": profile_id, "profile_type": profile_number,
                "weekday": day, "weekday_index": WEEKDAYS.index(day),
                "interval_index": k, "interval_start_minute": k * 15,
                "interval_start_local_clock": f"{k // 4:02d}:{(k % 4) * 15:02d}",
                "interval_end_minute": (k + 1) * 15,
                "apparent_power_kva_strict": strict,
                "apparent_power_kva_edgefilled_estimate": filled,
                "source_domain_coverage_fraction": coverage,
                "edge_extension_used": bool(coverage < 1 - 1e-8),
                "internal_gap_exceeds_5min": bool(internal_gap),
                "contract_va": np.nan, "calendar_date": "",
                "source_file": iso_file.name, "source_member": path.name,
                "source_series_preinterpolated": True,
                "time_axis_hours_inferred_from_values_and_plot": True,
            })
        audits.append({
            "profile_id": profile_id, "weekday": day, "source_rows": len(data),
            "source_start_hour": float(x[0]), "source_end_hour": float(x[-1]),
            "median_step_seconds": float(np.median(np.diff(x)) * 3600),
            "max_step_seconds": float(np.max(np.diff(x)) * 3600),
            "complete_15min_bins": int(np.isfinite(values[:, 0]).sum()),
            "edgefilled_15min_bins": int((values[:, 2] < 1 - 1e-8).sum()),
            "edge_extension_minutes_total": float((1 - values[:, 2]).sum() * 15),
            "integration_error_kvah": target_integral - source_integral,
        })

weekly_df = pd.DataFrame(weekly).sort_values(["profile_type", "weekday_index", "interval_index"])
weekly_df["apparent_power_shape_daily_mean1"] = weekly_df.apparent_power_kva_edgefilled_estimate / weekly_df.groupby(["profile_id", "weekday"]).apparent_power_kva_edgefilled_estimate.transform("mean")
weekly_df.to_csv(OUT / "weekly_apparent_power_15min.csv", index=False, float_format="%.10g")
wide = weekly_df.assign(curve=weekly_df.profile_id + "_" + weekly_df.weekday).pivot(index="interval_start_minute", columns="curve", values="apparent_power_kva_edgefilled_estimate")
wide.to_csv(OUT / "weekly_apparent_power_15min_wide.csv", float_format="%.10g")
pd.DataFrame(audits).to_csv(OUT / "weekly_profile_quality.csv", index=False)
assert len(weekly_df) == 12 * 7 * 96
assert weekly_df.groupby(["profile_id", "weekday"]).size().eq(96).all()

# Parse the original meter workbook, retaining signed PF as recorded.
# Its TIME cell's date component is an elapsed Excel day and is discarded;
# use the DATE column plus the time-of-day component.
workbook_path = next((ROOT / "raw").glob("*.xlsx"))
workbook = openpyxl.load_workbook(workbook_path, data_only=True, read_only=True)
meter_rows = []
for row in workbook.active.iter_rows(min_row=16, values_only=True):
    if not isinstance(row[0], datetime) or not isinstance(row[6], (float, int)):
        continue
    tod = row[1].time() if isinstance(row[1], datetime) else row[1]
    stamp = datetime.combine(row[0].date(), tod)
    meter_rows.append({"timestamp_source_local": stamp, "status": row[3],
                       "voltage_v": row[4], "current_a": row[5],
                       "active_power_kw": row[6] / 1000,
                       "reactive_power_kvar": row[7] / 1000,
                       "apparent_power_kva": row[8] / 1000,
                       "pf_signed_source": row[9], "frequency_hz": row[10]})
meter = pd.DataFrame(meter_rows).sort_values("timestamp_source_local")
assert not meter.timestamp_source_local.duplicated().any()
assert meter.status.eq(0).all()
assert (meter.timestamp_source_local.diff().dropna() == pd.Timedelta(minutes=5)).all()
meter.to_csv(OUT / "home1_4400va_original_5min_clean.csv", index=False)
start = meter.timestamp_source_local.min().normalize()
# Stop at the midnight supported by the final observation. The trailing
# isolated observation on 6 July is retained in the cleaned original file.
end = meter.timestamp_source_local.max().normalize()
time_hours = (meter.timestamp_source_local - start).dt.total_seconds().to_numpy() / 3600
meter_edges = np.arange(int((end - start).total_seconds() / 900) + 1) / 4
meter_15 = pd.DataFrame({"timestamp_source_local": pd.date_range(start, end, freq="15min", inclusive="left")})
meter_15["profile_id"] = "Z7955410_Home1_4400VA"
meter_15["contract_va"] = 4400
meter_15["timezone_verified"] = False
for column in ["active_power_kw", "reactive_power_kvar", "apparent_power_kva", "voltage_v", "current_a", "frequency_hz"]:
    vals = aggregate_curve(time_hours, meter[column].to_numpy(), meter_edges, max_gap=10 / 60, edge_limit=5 / 60)
    meter_15[column + "_strict"] = vals[:, 0]
    meter_15[column + "_edgefilled_estimate"] = vals[:, 1]
meter_15["source_domain_coverage_fraction"] = vals[:, 2]
meter_15["edge_extension_used"] = vals[:, 2] < 1 - 1e-8
meter_15["active_energy_kwh_estimate"] = meter_15.active_power_kw_edgefilled_estimate * .25
meter_15["pf_ratio_mean_p_over_mean_s"] = meter_15.active_power_kw_edgefilled_estimate / meter_15.apparent_power_kva_edgefilled_estimate
meter_15["timestamp_interpretation"] = "source_local_clock_timezone_unverified"
meter_15["aggregation"] = "piecewise_linear_time_weighted_mean_of_meter_readings"
meter_15["source_file"] = workbook_path.name
meter_15.to_csv(OUT / "home1_4400va_15min.csv", index=False, float_format="%.10g")
assert len(meter_15) == 13 * 96
assert np.isfinite(meter_15.active_power_kw_edgefilled_estimate).all()
assert meter_15.groupby(meter_15.timestamp_source_local.dt.date).size().eq(96).all()
nodes = np.r_[meter_edges[0], time_hours[(time_hours > meter_edges[0]) & (time_hours < meter_edges[-1])], meter_edges[-1]]
source_energy = float(np.trapezoid(np.interp(nodes, time_hours, meter.active_power_kw.to_numpy()), nodes))
target_energy = float(meter_15.active_energy_kwh_estimate.sum())
assert abs(source_energy - target_energy) < 1e-8

# A common long table combines rows without blending different households,
# quantities or undated weekday templates into an invented chronology.
combined = weekly_df.rename(columns={"apparent_power_kva_edgefilled_estimate": "apparent_power_kva_estimate"}).copy()
combined["series_kind"] = "undated_weekday_template_apparent_power"
combined["active_power_kw_estimate"] = np.nan
combined["timestamp_source_local"] = ""
dated = pd.DataFrame({
    "profile_id": meter_15.profile_id, "profile_type": np.nan,
    "weekday": meter_15.timestamp_source_local.dt.day_name(),
    "weekday_index": meter_15.timestamp_source_local.dt.dayofweek,
    "interval_index": meter_15.timestamp_source_local.dt.hour * 4 + meter_15.timestamp_source_local.dt.minute // 15,
    "interval_start_minute": meter_15.timestamp_source_local.dt.hour * 60 + meter_15.timestamp_source_local.dt.minute,
    "interval_start_local_clock": meter_15.timestamp_source_local.dt.strftime("%H:%M"),
    "calendar_date": meter_15.timestamp_source_local.dt.strftime("%Y-%m-%d"),
    "timestamp_source_local": meter_15.timestamp_source_local,
    "contract_va": 4400, "apparent_power_kva_estimate": meter_15.apparent_power_kva_edgefilled_estimate,
    "apparent_power_kva_strict": meter_15.apparent_power_kva_strict,
    "active_power_kw_estimate": meter_15.active_power_kw_edgefilled_estimate,
    "active_power_kw_strict": meter_15.active_power_kw_strict,
    "reactive_power_kvar_estimate": meter_15.reactive_power_kvar_edgefilled_estimate,
    "source_domain_coverage_fraction": meter_15.source_domain_coverage_fraction,
    "edge_extension_used": meter_15.edge_extension_used,
    "series_kind": "dated_household_meter_active_reactive_apparent",
    "source_file": workbook_path.name,
})
pd.concat([combined, dated], ignore_index=True).to_csv(OUT / "combined_profiles_15min_long.csv", index=False, float_format="%.10g")

# Direct comparisons keep the physical units distinct.
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
fig, axes = plt.subplots(4, 3, figsize=(11, 10), sharex=True, sharey=True)
for number, ax in enumerate(axes.flat, 1):
    block = weekly_df[weekly_df.profile_type == number]
    for idx, part in block.groupby("weekday_index"):
        ax.plot(part.interval_start_minute / 60 + .125, part.apparent_power_kva_edgefilled_estimate,
                color="#b9c4ce" if idx < 5 else "#d48b46", alpha=.65, linewidth=.7)
    mean = block.groupby("interval_index").apparent_power_kva_edgefilled_estimate.mean()
    ax.plot(np.arange(96) / 4 + .125, mean, color="#155c83", linewidth=1.7)
    ax.set_title(f"Type {number}", loc="left", fontsize=10)
    ax.grid(axis="y", color="#e8e8e8", linewidth=.5)
    ax.set_xticks([0, 6, 12, 18, 24]);ax.set_xlim(0, 24)
fig.suptitle("Indonesian residential apparent-power profiles", fontsize=15, x=.08, ha="left")
fig.text(.08, .945, "Grey: Monday-Friday | Orange: weekend | Blue: seven-day mean. Type-to-connection mapping is unavailable.", fontsize=9)
fig.supxlabel("Local clock hour as represented by source curves")
fig.supylabel("Apparent power (kVA)")
fig.tight_layout(rect=[.02, .025, 1, .925])
fig.savefig(OUT / "weekly_profiles_overview.png", dpi=180)
plt.close(fig)

blocks = meter_15.assign(clock=meter_15.timestamp_source_local.dt.hour * 4 + meter_15.timestamp_source_local.dt.minute // 15)
group = blocks.groupby("clock").active_power_kw_edgefilled_estimate
fig, ax = plt.subplots(figsize=(9, 4))
x = np.arange(96) / 4 + .125
ax.fill_between(x, group.quantile(.1), group.quantile(.9), color="#dcebf2", label="10th-90th percentile across 13 days")
ax.plot(x, group.mean(), color="#155c83", linewidth=2, label="Mean measured active power, aggregated to 15 minutes")
ax.set(xlabel="Source local clock hour", ylabel="Active power (kW)", xlim=(0, 24), title="Home 1: measured demand on a 4,400 VA connection")
ax.set_xticks([0, 6, 12, 18, 24]);ax.grid(axis="y", color="#e8e8e8", linewidth=.5)
ax.legend(frameon=False, loc="upper left", fontsize=8)
fig.tight_layout();fig.savefig(OUT / "home1_active_power_overview.png", dpi=180);plt.close(fig)

summary = {
    "source_doi": "10.5281/zenodo.7955410", "source_license": "CC BY 4.0",
    "raw_files_verified": len(verification), "weekly_profile_types": 12,
    "weekly_day_curves": 84, "weekly_15min_rows": len(weekly_df),
    "weekly_strict_complete_bins": int(weekly_df.apparent_power_kva_strict.notna().sum()),
    "weekly_edgefilled_bins": int(weekly_df.edge_extension_used.sum()),
    "weekly_contract_mapping_available": False,
    "home1_contract_va": 4400, "home1_original_5min_records": len(meter),
    "home1_15min_rows": len(meter_15), "home1_full_calendar_days_with_small_edge_estimate": 13,
    "home1_start": str(start), "home1_end_exclusive": str(end),
    "home1_edgefilled_bins": int(meter_15.edge_extension_used.sum()),
    "home1_active_energy_kwh_over_13days_estimate": target_energy,
    "home1_integration_error_kwh": target_energy - source_energy,
    "home1_power_factor_signed_source_min": float(meter.pf_signed_source.min()),
    "home1_power_factor_signed_source_max": float(meter.pf_signed_source.max()),
    "calendar_timezone_verified": False,
    "aggregation": "exact integration of piecewise-linear published curves; separately flagged endpoint extension",
    "important": "No appliance-level observations and no validated mapping from Type 1-12 to contract VA are supplied. No extra households or seasons have been fabricated.",
}
(OUT / "quality_summary.json").write_text(json.dumps(summary, indent=2))
(OUT / "download_checksums.json").write_text(json.dumps(verification, indent=2))
print(json.dumps(summary, indent=2))
