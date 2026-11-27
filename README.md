# Indonesia household energy study data

| Folder | Contents |
| --- | --- |
| [partner_data](partner_data/) | Household measurement exports, appliance inventory, reconstructed demand and coverage audits; household labels replaced by anonymous IDs |
| [open_source_data](open_source_data/) | Original public Indonesian load profiles, 15-minute conversions, reference weather and a labelled synthetic PV substitute |
| [survey_data](survey_data/) | CLASP/Ipsos aggregate survey inputs, appliance ownership priors and derived usage templates used by the study |

Each folder documents provenance, units and limitations. These are data inputs and processed datasets, not a new optimisation run. Earlier study inputs and v14 parameterisations retain separate version folders.

Large partner CSV files use lossless `.csv.gz` compression. Read with `pandas.read_csv(path)` or decompress with `gzip -dk file.csv.gz`.

`FILE_MANIFEST.csv` gives file sizes and SHA-256 hashes. Run `python verify_manifest.py` to verify a checkout.
