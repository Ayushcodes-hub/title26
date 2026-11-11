# data/ingest_usc.py
# Usage: python data/ingest_usc.py "<Title 26 XML zip link>"
import sys, io, zipfile, pathlib, hashlib, datetime, json
import requests

url = sys.argv[1]
today = datetime.date.today().isoformat()
out = pathlib.Path("data/raw/usc26") / today
out.mkdir(parents=True, exist_ok=True)

r = requests.get(url, timeout=180)
r.raise_for_status()

with zipfile.ZipFile(io.BytesIO(r.content)) as z:
    z.extractall(out)

manifest = {
    "source": "Office of the Law Revision Counsel, U.S. Code Title 26",
    "source_url": url,
    "downloaded_on": today,
    "archive_sha256": hashlib.sha256(r.content).hexdigest(),
    "files": sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()),
}
(out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2))
print("Saved to", out)
