# Household demand reconstruction

Prepared 23 November 2026 from all four original 2026 research exports.

The exports support a measured demand baseline for part of the sample. There
are 92 complete observed household-days across four homes. Of these, 21 days
at H07 are explicitly identified as total household load in the export.
The other 71 days retain a measurement-boundary or PV-channel qualification.
H01 has calculated household-load observations but no complete observed day.
No original measurements have been overwritten.

PROJECT_SCOPE.md records the agreed four-configuration study and intended
open-source Python tool, including appliance-calibrated HEMS modelling.

| Household | Connection in export (VA) | Complete observed days | Use |
|---|---:|---:|---|
| H01 | 7,700 | 0 | 1,940 calculated-load bins from 27 October 19:15 to 21 November 14:30; use fragments for descriptive analysis or the separately labelled gap sensitivity |
| H02 | 41,500 | 0 | Gross load unresolved: battery power missing |
| H04 | 16,500 | 13 | Inverter-side AC consumption; confirm coverage of all household circuits |
| H05 | 16,500 | 26 | Conditional grid + PV reconstruction; PV-channel/capacity discrepancy unresolved |
| H06 | 5,500 | 0 | Gross load unresolved: PV absent and main-meter location unconfirmed |
| H07 | 33,000 | 21 | Export identifies calculated total household load |
| H03 | 10,500 | 0 | Gross load unresolved: PV/battery power absent and main-meter location unconfirmed |
| H08 | 7,700 | 32 | Inverter-side AC consumption; confirm coverage of all household circuits |

Connection ratings above are copied from the data. No correction to a standard
tariff class or assumption about a household's representativeness is made.

## Reconstruction

For an import-positive net grid meter and no battery:

    household load = net grid import + PV output

This is applied only to H05 when both channels are available in the same
15-minute bin. Negative grid readings are retained as exports. There are 2,722
paired observations and no negative reconstructed load values.

Where the export already says "Calculated total household load", its demand
column is copied directly. PV is not added again. These values use the supplier's
calculation, which cannot be independently checked against separate grid and
battery channels in these files.

Inverter-side AC consumption at H04 and H08 is retained directly as a
conditional load measurement. Its coverage of the whole property remains
unconfirmed. Adding PV to this consumption channel would double count generation.

For a hybrid with a net grid meter, household load would require:

    load = net grid import + PV + battery discharge - battery charge

Battery energy capacity in kWh is not battery power. No battery trajectory is
deduced from installed capacity. H02's demand is therefore left unresolved.
Unconfirmed main meters at H01 before the channel change, H06 and H03
are also left unresolved. Zero demand is never substituted for missing demand.

The source Data sheet already reports kW and a processed sign convention. The
Households sheet's scale_to_kw and sign metadata are not applied a second time.

## Time coverage and energy

The source README defines timestamps as interval starts in Asia/Jakarta,
UTC+07:00. Every exported row describes a 15-minute bin. Many older records have
only one bin per hour, typically at :30. A 60-minute separation between records
does not turn a recorded 15-minute mean into an hourly mean. Missing quarters
remain missing in the observed files.

A complete observed day requires exactly 96 distinct available load bins from
00:00 through 23:45 local time. No interpolation, hourly carry-forward, repetition
of days, or annual scaling is used in the observed datasets.

Approximate interval energy is load kW times 0.25 hours. The export uses a plain
mean of event-based stored readings, approximately every two minutes, rather
than a meter integral. These are approximate energies, including on complete
days. Grid and PV channels are interval means whose underlying readings may
not be synchronized. The energy-balance formula alone cannot verify their
physical measurement accuracy.

Mean energy per complete observed day is approximately 123.55 kWh for H07,
77.37 kWh for H04, 82.62 kWh for H08, and conditionally 122.19 kWh for
H05. These means use different observed dates. They are not annual means
or estimates for the associated connection classes. H01 has no such
observed full-day mean.

Missing bins are absent from observed_load_candidates.csv and appear as missing
candidate demand in the all-household audit. daily_coverage.csv shows each local
date between a home's first and last raw timestamp, including dates with no data.
Its observed-bin energy is a partial sum unless coverage is 96/96. Full-day
energy is left blank on incomplete days.

## H05 discrepancy

The listed PV capacity is 3.2 kWp, while calculated PV output reaches 8.172 kW.
There are 443 bins above the listed capacity. This requires clarification of
capacity, channel mapping or scaling before treating the reconstruction as a
confirmed whole-house baseline. The discrepancy is not corrected by assuming
a larger PV installation or forcing output to the listed capacity.

There are also 1,795 slightly negative PV readings, with a minimum of -0.0027 kW.
The main candidate preserves the exact measured grid + PV sum. A separate
gross_load_zero_floor_pv_sensitivity_kw column floors only this PV channel at zero
before adding it to grid power. It is a processing sensitivity, not a correction
known to be true. Raw PV values and both flags remain available.

## Optional short-gap sensitivity

optional_short_gap_complete_day_profiles.csv is a separate modelling scenario.
It fills only one or two consecutive missing quarter-hours (15 or 30 minutes
of missing bins), using linear interpolation between available observations on
both sides. It does not extrapolate and does not bridge longer gaps.

This produces two additional complete days for H01, two for H07 and one
for H08, for 97 household-days across five homes in this optional file.
is_interpolated identifies each modelled value. The file also includes unchanged
complete observed days. All original measurement-status qualifications remain.
No previously ambiguous measurement channel becomes identifiable through filling.

## Use in the sizing study

1. Use primary_complete_day_profiles.csv for analysis restricted to the export's
   explicit total-household-load definition and complete observed days.
2. H04 and H08 can broaden the sample in conditional analyses, keeping
   their measurement-boundary assumption explicit.
3. Keep H05 as a separate conditional case until its PV discrepancy is resolved.
4. Treat the optional gap file as a sensitivity, preserving its interpolation flags.
5. Use the same baseline and period when comparing configurations for a home.
   Check coverage of the solar scenario separately. A load value remains usable
   even where simultaneous PV is missing, but it is not a load/PV pair.

For dispatch across non-consecutive full days, define battery state boundaries
explicitly. Do not let state of charge flow through removed days as though they
were adjacent. A cyclic state per contiguous segment is one possible modelling
assumption and is not imposed by this data preparation.

The reconstruction recovers gross consumption during the existing installation's
operation. It does not recover how occupants would have behaved without PV,
battery control or any existing load management. Keeping this observed gross
load fixed across proposed configurations is an explicit comparison assumption.

These exports contain no appliance power time series, operating windows or
service constraints. Gross demand can support PV/BESS sizing, but it cannot
identify realistic appliance flexibility by itself. No flexible-demand percentage,
device disaggregation or HEMS savings are assigned in this package.

## Files

| File | Contents |
|---|---|
| data/household_summary.csv | Counts, coverage periods, approximate complete-day mean energy and qualifications for all eight homes |
| data/primary_complete_day_profiles.csv | 21 complete observed days explicitly labelled as total household load |
| data/complete_observed_day_profiles.csv | 92 complete observed days, including conditional cases with their status |
| data/observed_load_candidates.csv | All 19,767 identifiable or conditional candidate-load bins, including incomplete days |
| data/interval_audit_all_households.csv | All 67,060 original rows, provenance, candidate load and flags |
| data/daily_coverage.csv | Daily coverage, missing days and partial/full-day approximate energy |
| data/optional_short_gap_complete_day_profiles.csv | 97 complete days in a separately labelled short-gap scenario |
| data/source_manifest.json | Original input filenames, sizes, row counts and SHA-256 hashes |
| data/validation.json | Reconstruction and coverage verification results |
| input/ | Four unchanged original Excel exports |
| reconstruct_demand.py | Reproducible processing code |

## Key fields

| Field | Meaning |
|---|---|
| demand_p_kw, pv_output_kw | Unchanged exported values in kW |
| gross_load_candidate_kw | Export-calculated total, inverter consumption or conditional net-grid-plus-PV value, according to load_basis |
| load_basis | Algebra or measurement used to create the candidate |
| measurement_status | Source-definition qualification; not a statistical confidence score |
| eligible_for_primary_household_analysis | Source explicitly identifies total load and the candidate is nonnegative; this does not imply independent validation or day completeness |
| source_file, source_excel_row | Original Data-sheet filename and 1-based Excel row |
| pv_negative_raw, pv_above_listed_kwp | Raw PV consistency flags; no automatic clipping of the main candidate |
| observed_bin_approx_energy_kwh | Candidate kW multiplied by 0.25 hours |
| is_interpolated | Modelled short-gap value in the optional scenario only |

## Reproduce and verification

Python dependencies: numpy, pandas and openpyxl. No optimization solver is needed.

    python reconstruct_demand.py

Or use explicit input and output folders:

    python reconstruct_demand.py --inputs input --output data

Processing checks verify unique household timestamps, quarter-hour alignment,
the copied-load identity, the exact grid-plus-PV identity, 96-bin complete days,
and exclusion of households with unidentified battery/measurement channels.
These checks passed. They verify processing and coverage, not the upstream
measurement system. The original workbooks are the authoritative definitions.
