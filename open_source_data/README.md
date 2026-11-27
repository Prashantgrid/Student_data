# Public and synthetic reference data

- `zenodo_7955410/`: the original public source downloads, extracted files, derived 15-minute data, quality checks and conversion script. Source: Abdul Wachid Syamroni and Abduh Aziz Basharah, DOI https://doi.org/10.5281/zenodo.7955410, CC BY 4.0. Preserve attribution and the detailed README.
- `reference_weather/`: the saved Jakarta reference-weather input and its metadata, from the earlier study archive. This is a reference location, not the verified location of each household. The study source register identifies NASA POWER as the weather source.
- `synthetic_pv_substitute_v14/`: the synthetic public substitute from v14, with its metadata. It is not measured PV generation and will not exactly reproduce results from the confidential partner PV library.

The twelve Zenodo weekly types supply apparent power in kVA; they have not been renamed kW. The separate 4,400 VA workbook supplies active power. Source type-to-connection-rating assignments remain unknown. Derived quarter-hour series retain coverage and interpolation flags.
