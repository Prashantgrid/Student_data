from pathlib import Path
import csv, hashlib
root = Path(__file__).resolve().parent
with (root / "FILE_MANIFEST.csv").open(newline="") as f:
    rows = list(csv.DictReader(f))
for row in rows:
    path = root / row["path"]
    assert path.is_file(), row["path"]
    data = path.read_bytes()
    assert len(data) == int(row["bytes"]), row["path"]
    assert hashlib.sha256(data).hexdigest() == row["sha256"], row["path"]
print(f"Verified {len(rows)} files: sizes and SHA-256 hashes match.")
