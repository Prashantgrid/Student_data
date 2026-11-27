# Aggregate survey inputs and study parameterisations

Source: CLASP/Ipsos, *Indonesia Residential End-Use Survey* (2020):
https://www.clasp.ngo/research/all/indonesia-residential-end-use-survey-2/
Report: https://www.clasp.ngo/wp-content/uploads/2021/01/Indonesia-Residential-End-Use-Survey.pdf

These files contain aggregate survey-derived inputs and modelling assumptions. They are not respondent-level survey microdata or newly collected household responses.

- `earlier_study_inputs/appliance_priors.json`: saved ownership, unit-count, annual energy and rated-power priors, each with source fields.
- `earlier_study_inputs/end_use_hourly_templates.csv`: normalized usage templates digitized from report figures. These are hourly weights, not measured appliance power traces. Printed/PDF page references and the extraction method are retained.
- `earlier_study_inputs/input_provenance.json`: report hash, page references, consumption anchors and pooled-band limitations.
- `study_v14/`: the v14 appliance parameter source, a machine-readable extract of its literal constants, and an ownership table. Fan ownership and additional-device parameters identified as assumptions remain labelled as such.

Survey ownership bands are 900 VA RTM, 1,300 VA, 2,200 VA and pooled R-2/R-3. No individual-rating microdata have been inferred for the upper bands. Earlier and v14 priors differ in places; retain the version distinction. Full private respondent records were not present in the supplied study packages.
