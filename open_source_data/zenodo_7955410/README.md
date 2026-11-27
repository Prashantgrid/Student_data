# Indonesian residential profiles at 15-minute intervals

Source: Abdul Wachid Syamroni and Abduh Aziz Basharah, *Time Series Measurement Data of Residentials | Jabodetabek Regions Indonesia*, version 1, DOI [10.5281/zenodo.7955410](https://zenodo.org/records/7955410). Source publication date: 21 April 2022. Downloaded and processed: 27 November 2026. Licence: [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).

This package contains the unchanged source downloads, extracted files, and derived 15-minute tables. Attribution to the original authors is required when reusing the data. The processing and endpoint estimates below were made for this package and are not claims by the original authors.

## What is actually available

| Source | Contents | Main use |
| --- | --- | --- |
| 12 ISO archives, Type 1-12 | Seven undated weekday curves per type, with apparent power in kVA | Indonesian load-shape library and sensitivity analysis |
| Home 1 Excel workbook | 3,745 five-minute records on a 4,400 VA connection, 23 June-6 July 2021; active/reactive/apparent power, PF, voltage and current | Direct active-power demand and electrical-quantity validation |

The weekly source curves were already interpolated by the depositors from measurements taken at 5-, 10- and 15-minute intervals. Their near-one-minute spacing is not independent one-minute measurement. The record does not establish that each type is an independent household, provide a type-to-contract-rating lookup, or give the calendar dates of the weekday curves. Type IDs are therefore preserved. The overall title lists 1,300/2,200/3,300/4,400/5,500 VA; individual type ratings are left unknown. In particular, 3,300 VA has not been relabelled 3,500 VA.

There are no device-level channels or appliance inventories in this deposit. It does not supply a full year of measured demand, a national household sample, or a confirmed 900 VA series.

## Files to use

- `data/combined_profiles_15min_long.csv`: the unified long table, with 9,312 rows, preserving profile identity, dated versus undated status, power quantity and provenance. Unknown kW values remain blank.
- `data/weekly_apparent_power_15min.csv`: 8,064 rows = 12 types x 7 weekdays x 96 intervals. Contains both strict apparent-power values and explicitly labelled endpoint-filled estimates.
- `data/weekly_apparent_power_15min_wide.csv`: the same endpoint-filled apparent-power curves as 84 columns and 96 rows, convenient for model input.
- `data/home1_4400va_15min.csv`: 1,248 quarter-hour rows covering the 13 calendar days from 23 June through 5 July 2021. Includes kW, kvar, kVA, derived P/S, interval-energy estimates and flags.
- `data/home1_4400va_original_5min_clean.csv`: the original meter readings in consistent units with corrected date/time parsing. The isolated observation at 6 July 00:02 is retained here.
- `data/weekly_profile_quality.csv`: source coverage, intervals and integration checks for each weekday curve.
- `data/quality_summary.json`: compact quality and quantity summary.
- `data/download_checksums.json`: validation of all 13 downloads against the source MD5 checksums.
- `data/weekly_profiles_overview.png` and `data/home1_active_power_overview.png`: visual checks.
- `data/extracted_original_files/`: the CSV curves and PNG plots extracted from each ISO without modification.
- `raw/`: the 13 unchanged source files. `record_metadata.json` is the downloaded source metadata.
- `scripts/build_15min.py`: reproducible conversion. `requirements.txt` lists dependencies.

## The 15-minute conversion

1. Source time is used directly; observations are not grouped into arbitrary sets of 15 rows.
2. The CSV time axis runs approximately from 0 to 24 with increments near 0.0166. The accompanying plots label it `Jam` (hours). The converter consequently interprets CSV time as decimal hours, despite the broad record description referring to time in minutes. This inference is recorded in the output.
3. Each published curve is treated as piecewise linear. Its integral over each interval [00:00, 00:15), [00:15, 00:30), etc., divided by 0.25 hours, gives a time-weighted mean power. This preserves the area under the interpreted curve.
4. The strict column is populated only where the full quarter-hour is covered by the source curve and has no excessive internal gap. There are 7,896 strict weekly values and 168 incomplete edge intervals.
5. A separate estimate extends the nearest endpoint over short missing edges, up to 15 minutes for the weekly curves. All 168 affected intervals carry `edge_extension_used=true` and a coverage fraction. The original files and strict values make this optional assumption explicit.
6. The meter workbook's `TIME` cells include an elapsed Excel day count. The converter combines the `DATE` field with only the time-of-day component. It does not add the elapsed day count again.
7. Meter readings are integrated as a piecewise-linear signal to the clock-aligned 15-minute grid. The first reading is at 00:02, so the first two minutes of 23 June use a separately flagged constant endpoint estimate. The later observation on 6 July supports interpolation through the final interval of 5 July.
8. The workbook does not establish whether its power records represent instantaneous samples or preceding-interval averages. This package explicitly uses the former interpretation. Resolving meter interval semantics with the authors would strengthen exact bill-energy calculations.
9. Calendar timestamps are preserved as source local-clock timestamps. Jabodetabek uses WIB, but the file's timestamp timezone is not explicitly documented, so the converter does not silently attach or convert a timezone.

All quarter-hours have 15-minute width. Aggregation removes intrainterval peaks and does not preserve 1- or 5-minute maxima. Integration checks pass within numerical rounding. For Home 1, integrated active demand is approximately 219.80 kWh across the 13 calendar days under the stated interpolation and endpoint convention. This is a short-period result, not measured annual consumption.

## Power quantities

- Apparent power S is in kVA; active power P is in kW; reactive power Q is in kvar. These columns are separate.
- The twelve weekly types supply S only. Their S values have not been renamed kW or summed with active power.
- A signed PF appears in the meter source while P remains positive and Q can be negative. Preserve that meter convention; negative PF alone is not evidence of active export. The 15-minute ratio `pf_ratio_mean_p_over_mean_s` is mean P divided by mean S and does not retain the signed native PF convention.
- `apparent_power_shape_daily_mean1` is a dimensionless shape normalised to a daily mean of one. Scaling this to known active energy would be an additional modelling assumption that normalised active and apparent profiles coincide. It does not create measured kW data.

## How this can improve the Indonesia PV-BESS-HEMS study

Use the Home 1 active-power series for direct out-of-sample household checks where its measurement boundary is suitable. Use the weekly apparent-power templates to broaden and stress-test Indonesian background-demand shapes, with explicit assumptions about active-power shape and with type identity retained. First verify which templates correspond to which connection classes before using them to calibrate class-level daytime-use distributions.

Join compatible records as a library of profiles, not as one physical household. The undated Monday-Sunday templates have no validated calendar alignment with the dated Home 1 series. Their weekday ordering can define an illustrative week, but it is not evidence that measurements occurred during that consecutive week.

For national analysis, combine locally calibrated shapes with official customer and electricity-sales distributions. Keep variability in household demand, weather and financial assumptions separate. A one-week template repeated through a year is a synthetic annual profile and should be labelled as such. Appliance ownership, service windows and flexible-load energy still need survey or device-level evidence; they cannot be recovered uniquely from these aggregate curves.

The original manuscript and its optimisation results have not been changed or rerun by this conversion.

## Reproduce

From the extracted package folder:

```bash
python -m pip install -r requirements.txt
python scripts/build_15min.py . data_rebuilt
```

The script verifies source checksums, extracts the ISO files, writes the quarter-hour tables and checks curve-integral conservation. It requires no private partner data. `record_metadata.json` retains the exact file URLs for downloading the source again if needed.
