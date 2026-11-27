#!/usr/bin/env python3
"""Reconstruct Indonesian household loads from the four original research exports.

No household demand, PV or battery trajectory is invented. The optional short-gap
file is a separately labelled modelling sensitivity and is never the primary data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

CALCULATED = "Calculated total household load (grid ± PV ± battery)"
INVERTER = "Inverter-side AC consumption"
GRID = "Grid-side meter (net import/export at the PLN connection)"
HOUSE_B = "H05"
STEP_HOURS = 0.25


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inputs", type=Path, default=Path(__file__).parent / "input")
    ap.add_argument("--output", type=Path, default=Path(__file__).parent / "data")
    args = ap.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    frames, manifest = [], []
    for source in sorted(args.inputs.glob("research_15min_*.xlsx")):
        frame = pd.read_excel(source, sheet_name="Data")
        frame["source_file"] = source.name
        frame["source_excel_row"] = np.arange(len(frame)) + 2
        frames.append(frame)
        manifest.append({"filename": source.name, "sheet": "Data", "rows": len(frame),
                         "size_bytes": source.stat().st_size,
                         "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
    if len(frames) != 4:
        raise ValueError("Expected four original research_15min Excel exports")
    raw = pd.concat(frames, ignore_index=True)
    raw["ts"] = pd.to_datetime(raw.timestamp_local)
    if raw.duplicated(["household_id", "ts"]).any():
        raise ValueError("Duplicate household/timestamp rows require source resolution")
    if not raw.interval_minutes.eq(15).all():
        raise ValueError("Unexpected interval definition")
    if raw.ts.dt.second.ne(0).any() or raw.ts.dt.minute.mod(15).ne(0).any():
        raise ValueError("Off-grid timestamp")
    raw = raw.sort_values(["household_id", "ts"]).reset_index(drop=True)
    raw["gross_load_candidate_kw"] = np.nan
    raw["load_basis"] = "not_identifiable"
    raw["measurement_status"] = "unresolved"
    raw["limitation"] = ""
    calc = raw.p_source.eq(CALCULATED) & raw.demand_p_kw.notna()
    inv = raw.p_source.eq(INVERTER) & raw.demand_p_kw.notna()
    b = (raw.household_id.eq(HOUSE_B) & raw.p_source.eq(GRID)
         & raw.battery_kwh.eq(0) & raw.demand_p_kw.notna() & raw.pv_output_kw.notna())
    raw.loc[calc | inv, "gross_load_candidate_kw"] = raw.loc[calc | inv, "demand_p_kw"]
    raw.loc[calc, "load_basis"] = "export_calculated_total_load"
    raw.loc[calc, "measurement_status"] = "export_identifies_household_total"
    raw.loc[calc, "limitation"] = "Upstream calculation cannot be independently balanced without component channels"
    raw.loc[inv, "load_basis"] = "inverter_ac_consumption"
    raw.loc[inv, "measurement_status"] = "whole_house_boundary_unconfirmed"
    raw.loc[inv, "limitation"] = "Confirm whether inverter consumption covers every household circuit"
    raw.loc[b, "gross_load_candidate_kw"] = raw.loc[b, "demand_p_kw"] + raw.loc[b, "pv_output_kw"]
    raw.loc[b, "load_basis"] = "net_grid_plus_pv_no_battery"
    raw.loc[b, "measurement_status"] = "pv_channel_metadata_inconsistent"
    raw.loc[b, "limitation"] = "PV reaches 8.172 kW against 3.2 kWp metadata; verify channel mapping, scaling and capacity"
    raw.loc[raw.household_id.eq("H02"), "limitation"] = "Net grid plus PV is insufficient without battery charge/discharge"
    raw.loc[raw.household_id.eq("H06"), "limitation"] = "PV channel absent and main-meter boundary unconfirmed"
    raw.loc[raw.household_id.eq("H03"), "limitation"] = "PV and battery-power channels absent and main-meter boundary unconfirmed"
    early_alex = raw.household_id.eq("H01") & ~calc
    raw.loc[early_alex, "limitation"] = "Before calculated-load channel: main-meter boundary or demand channel unresolved"
    missing_b = raw.household_id.eq(HOUSE_B) & ~b
    raw.loc[missing_b, "limitation"] = "PV channel missing, so gross demand cannot be reconstructed"
    raw["pv_negative_raw"] = raw.pv_output_kw.lt(0)
    raw["pv_above_listed_kwp"] = raw.pv_output_kw.gt(raw.pv_kwp)
    raw["gross_load_negative"] = raw.gross_load_candidate_kw.lt(0)
    # A separate physical-zero sensitivity preserves the exact raw sum in the main column.
    raw["gross_load_zero_floor_pv_sensitivity_kw"] = np.nan
    raw.loc[b, "gross_load_zero_floor_pv_sensitivity_kw"] = (
        raw.loc[b, "demand_p_kw"] + raw.loc[b, "pv_output_kw"].clip(lower=0))
    raw["observed_bin_approx_energy_kwh"] = raw.gross_load_candidate_kw * STEP_HOURS
    raw["eligible_for_primary_household_analysis"] = calc & ~raw.gross_load_negative
    raw["local_date"] = raw.ts.dt.strftime("%Y-%m-%d")
    observed = raw[raw.gross_load_candidate_kw.notna()].copy()
    valid = observed[~observed.gross_load_negative].copy()

    daily_rows, complete_frames, filled_frames, summary = [], [], [], []
    for hh, source_rows in raw.groupby("household_id", sort=True):
        z = valid[valid.household_id.eq(hh)].copy()
        counts = z.groupby("local_date").size()
        full_dates = set(counts[counts.eq(96)].index)
        full = z[z.local_date.isin(full_dates)].copy()
        if len(full):
            complete_frames.append(full)
        all_days = pd.date_range(source_rows.ts.min().normalize(), source_rows.ts.max().normalize(), freq="D")
        for day in all_days:
            date = day.strftime("%Y-%m-%d")
            r = source_rows[source_rows.local_date.eq(date)]
            q = z[z.local_date.eq(date)]
            daily_rows.append({
                "household_id": hh, "class_va": int(source_rows.class_va.iloc[0]), "local_date": date,
                "raw_rows": len(r), "demand_channel_bins": int(r.demand_p_kw.count()),
                "pv_channel_bins": int(r.pv_output_kw.count()), "load_candidate_bins": len(q),
                "expected_bins": 96, "coverage_fraction": len(q) / 96,
                "complete_observed_day": len(q) == 96,
                "observed_bins_approx_energy_kwh": float(q.gross_load_candidate_kw.sum() * STEP_HOURS),
                "full_day_approx_energy_kwh": float(q.gross_load_candidate_kw.sum() * STEP_HOURS) if len(q) == 96 else np.nan,
                "measurement_status": q.measurement_status.iloc[0] if len(q) else "no_identifiable_load_bins",
            })
        n_filled = 0
        optional_full_dates = set()
        if len(z):
            # Limit to the candidate-load period; never extrapolate beyond observations.
            idx = pd.date_range(z.ts.min(), z.ts.max(), freq="15min")
            s = z.set_index("ts").gross_load_candidate_kw.reindex(idx)
            miss = s.isna()
            run = miss.ne(miss.shift()).cumsum()
            run_size = miss.groupby(run).transform("sum")
            interpolated = s.interpolate(method="time", limit_area="inside")
            fill_ok = miss & run_size.le(2) & interpolated.notna()
            result = s.copy()
            result.loc[fill_ok] = interpolated.loc[fill_ok]
            opt = pd.DataFrame({"household_id": hh, "class_va": int(z.class_va.iloc[0]),
                                "timestamp_local": idx.astype(str),
                                "load_candidate_kw": result.to_numpy(),
                                "is_interpolated": fill_ok.to_numpy(),
                                "is_observed": s.notna().to_numpy(),
                                "measurement_status": z.measurement_status.iloc[0],
                                "gap_rule": "linear interpolation only for 1-2 missing 15-minute bins; bounded at both ends"})
            opt["local_date"] = idx.strftime("%Y-%m-%d")
            opt_counts = opt.groupby("local_date").load_candidate_kw.count()
            optional_full_dates = set(opt_counts[opt_counts.eq(96)].index)
            selected = opt[opt.local_date.isin(optional_full_dates)].copy()
            if len(selected):
                selected["approx_interval_energy_kwh"] = selected.load_candidate_kw * STEP_HOURS
                filled_frames.append(selected)
                n_filled = int(selected.is_interpolated.sum())
        energies = full.groupby("local_date").gross_load_candidate_kw.sum() * STEP_HOURS
        summary.append({
            "household_id": hh, "class_va": int(source_rows.class_va.iloc[0]),
            "raw_rows": len(source_rows), "load_candidate_intervals": len(z),
            "candidate_start_local": str(z.ts.min()) if len(z) else "",
            "candidate_end_local": str(z.ts.max()) if len(z) else "",
            "complete_observed_days": len(full_dates),
            "mean_complete_day_kwh": float(energies.mean()) if len(energies) else np.nan,
            "observed_candidate_peak_kw": float(z.gross_load_candidate_kw.max()) if len(z) else np.nan,
            "complete_days_with_optional_short_gap_fill": len(optional_full_dates),
            "additional_days_from_short_gap_fill": len(optional_full_dates - full_dates),
            "filled_bins_in_optional_complete_days": n_filled,
            "pv_negative_bins": int(source_rows.pv_negative_raw.sum()),
            "pv_above_listed_capacity_bins": int(source_rows.pv_above_listed_kwp.sum()),
            "negative_candidate_load_bins": int(source_rows.gross_load_negative.sum()),
            "measurement_status": z.measurement_status.iloc[0] if len(z) else "not_identifiable",
            "primary_complete_observed_days": len(full_dates) if len(z) and z.eligible_for_primary_household_analysis.all() else 0,
        })
    summary = pd.DataFrame(summary)
    daily = pd.DataFrame(daily_rows)
    complete = pd.concat(complete_frames, ignore_index=True)
    optional = pd.concat(filled_frames, ignore_index=True)
    # Mathematical, provenance and coverage checks directly relevant to reconstruction.
    np.testing.assert_allclose(raw.loc[calc | inv, "gross_load_candidate_kw"], raw.loc[calc | inv, "demand_p_kw"], atol=0, rtol=0)
    np.testing.assert_allclose(raw.loc[b, "gross_load_candidate_kw"], raw.loc[b, "demand_p_kw"] + raw.loc[b, "pv_output_kw"], atol=0, rtol=0)
    assert complete.groupby(["household_id", "local_date"]).size().eq(96).all()
    assert not complete.duplicated(["household_id", "timestamp_local"]).any()
    assert complete.gross_load_candidate_kw.notna().all()
    assert optional.groupby(["household_id", "local_date"]).size().eq(96).all()
    assert not optional.load_candidate_kw.isna().any()
    assert not raw.loc[raw.household_id.isin(["H02", "H06", "H03"]), "gross_load_candidate_kw"].notna().any()
    for frame, name in [(raw.drop(columns="ts"), "interval_audit_all_households.csv"),
                        (observed.drop(columns="ts"), "observed_load_candidates.csv"),
                        (complete.drop(columns="ts"), "complete_observed_day_profiles.csv"),
                        (complete[complete.eligible_for_primary_household_analysis].drop(columns="ts"), "primary_complete_day_profiles.csv"),
                        (optional, "optional_short_gap_complete_day_profiles.csv"),
                        (daily, "daily_coverage.csv"), (summary, "household_summary.csv")]:
        frame.to_csv(out / name, index=False, float_format="%.10g")
    (out / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    validation = {"input_rows": len(raw), "duplicate_household_timestamps": 0,
                  "observed_candidate_rows": len(observed),
                  "complete_observed_household_days": len(complete) // 96,
                  "primary_complete_observed_household_days": int(summary.primary_complete_observed_days.sum()),
                  "optional_complete_household_days": len(optional) // 96,
                  "checks": "passed: source copy, grid+PV identity, no double PV addition, 96-bin complete days, no fabricated battery channels",
                  "caution": "Algebra checks are not independent physical validation of upstream calculated load or PV channels."}
    (out / "validation.json").write_text(json.dumps(validation, indent=2) + "\n")
    print(summary[["household_id", "complete_observed_days", "mean_complete_day_kwh", "additional_days_from_short_gap_fill", "measurement_status"]].to_string(index=False))
    print(json.dumps(validation, indent=2))


if __name__ == "__main__":
    main()
