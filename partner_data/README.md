# Partner household data

- `raw/`: supplied research workbooks and appliance inventory. Household identifiers have been replaced consistently by H01-H08, including workbook cells and metadata; the identity lookup is not included.
- `processed/`: reconstructed demand, interval and daily coverage audits, complete observed-day profiles, sizing workbook, constraint matrix and partner-derived residual shapes. The earlier hourly study inputs are separate.
- `processing/`: the original demand reconstruction script, updated to use the same anonymous labels.

Only identifying text has been changed. Power measurements, dates, equipment ratings, data gaps and measurement-boundary flags are retained. These eight supplied homes do not establish representative measured coverage of every PLN rating. Conditional reconstructions must not be treated as directly measured whole-house load without their stated qualifications.

The reconstruction README describes the scientific interpretation of the original export. `original_source_manifest.json` preserves checksums of the original inputs for provenance; those original hashes will differ from the anonymous workbook copies. Use the repository-level manifest to verify the published files. CSV files larger than 500 kB are compressed losslessly with gzip.

The earlier inputs and v14 residual shapes come from different saved study stages. They are supplied for traceability and should not be combined silently or treated as a rerun of the latest manuscript. This repository does not grant third-party redistribution rights beyond the source permissions.
