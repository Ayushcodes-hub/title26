# data/parse_usc.py
# Usage: python data/parse_usc.py data/raw/usc26/<date>
import sys, json, pathlib, hashlib, datetime
from lxml import etree

src = pathlib.Path(sys.argv[1])
out_path = pathlib.Path("data/processed/usc26_sections.jsonl")
out_path.parent.mkdir(parents=True, exist_ok=True)
today = datetime.date.today().isoformat()

count = 0
with out_path.open("w", encoding="utf-8") as out:
    for xml_file in sorted(src.rglob("*.xml")):
        tree = etree.parse(str(xml_file))
        for sec in tree.iter("{*}section"):
            num_el = sec.find(".//{*}num")
            head_el = sec.find(".//{*}heading")
            num = (num_el.text or "").strip() if num_el is not None else ""
            heading = " ".join((head_el.itertext() if head_el is not None else [])).strip()
            body = " ".join(t.strip() for t in sec.itertext() if t.strip())
            if not num or len(body) < 40:
                continue
            record = {
                "citation": f"26 U.S.C. {num}",
                "heading": heading,
                "text": body,
                "source_file": xml_file.name,
                "source_url": "https://uscode.house.gov/",
                "retrieved_on": today,
                "text_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1

print(f"Wrote {count} sections to {out_path}")
