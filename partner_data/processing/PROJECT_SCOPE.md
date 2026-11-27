# Agreed project objective

Working specification supplied by Prashant on 23 November 2026.

Build an open-source, Python-based household sizing tool with a simple GUI.
Ferbos should be able to upload customer data through an Excel template and
receive a tailored comparison of four investment configurations:

1. PV only
2. PV + HEMS
3. PV + BESS
4. PV + HEMS + BESS

A grid-only case supplies the common reference for savings and investment
appraisal. The initial Indonesian policy analysis considers self-consumption
without export revenue. Export compensation must be an explicit input if a
different scenario is evaluated.

## Required inputs

- Measured household demand with timestamps, units, interval definition and
  meter boundary. Gross load can be supplied directly or reconstructed where
  grid, PV and battery measurements allow it.
- Appliance inventory, quantity and rated power. Include measured appliance
  profiles where available.
- Appliance operating constraints: availability, preferred timing, permitted
  delays, cycle duration, required service, and relevant comfort or storage limits.
- Rooftop area and applicable installation limits.
- Location and a defined solar-generation resource or suitable PV profile.
- Connection rating and available reactive-power/power-factor information.
- PV, battery and HEMS costs, electricity tariffs, and economic assumptions
  needed for consistent lifetime-cost and payback calculations.

Missing fields should produce a specific qualification or a labelled scenario,
not an undisclosed substitute value.

## Appliance estimation and HEMS

Use measured appliance profiles first. Where they are unavailable, estimate
profiles using reference datasets, such as the proposed UK-DALE option, together
with each home's appliance inventory, ratings and operating constraints.
Calibrate estimates against measured aggregate household demand. Keep a residual
for demand not assigned to identified appliances.

Calibration must reconcile appliance-plus-residual demand with household demand.
That reconciliation alone does not prove the appliance allocation is unique or
correct. Label estimated appliance profiles, retain plausible alternatives, and
show how uncertainty changes HEMS value and the selected configuration.

Only appliance demand with defined service constraints can be shifted. Do not
replace appliance modelling with an arbitrary flexible percentage of total load.
No fabricated appliance profile should be presented as a measurement.

## Optimization and outputs

For each of the four configurations, optimize the permitted PV capacity, battery
energy and power capacity, and dispatch or appliance schedules. Use common
demand, solar, financial assumptions and service requirements across options.
For a configuration without a battery, battery capacity is zero. For one without
HEMS, keep the baseline appliance schedule.

Report optimal capacities, achievable load shifting, electricity bill savings,
investment costs, payback and the most economical configuration under the chosen
objective. Use a consistent lifetime-cost or NPV comparison to rank options and
report payback separately. A zero optimal capacity is a valid outcome.

## Household coverage requested

| PLN group | Requested connection ratings (VA) |
|---|---|
| R-1 | 900; 1,300; 2,200 |
| R-2 | 3,500; 4,400; 5,500 |
| R-3 | 6,600; 7,700; 10,600, or higher where available |

Target two or three households per rating, preferably with 15-minute demand
records. These are the requested sampling targets, not a verification of tariff
classification. Preserve the actual rating reported in each supplied dataset.

## Role of this reconstruction package

This package completes the initial gross-demand preparation and coverage audit
for the existing eight homes. It does not yet implement appliance estimation,
investment optimization or the GUI.

The present sample contains high-rated connections and incomplete or conditional
load measurements. It does not by itself support conclusions for every requested
rating or Indonesian households as a population. Do not scale these homes down
and present the results as measured lower-rating households.

The next analysis should use the audited demand candidates with their stated
qualifications, obtain the missing appliance constraints and household coverage,
and build the four-way comparison before packaging the workflow into a GUI.
