# data/parse_usc.py
# Usage: python data/parse_usc.py data/raw/usc26/<date>
import sys, json, pathlib, hashlib, datetime, re
from lxml import etree

SKIP_TAGS = {"notes", "note", "sourceCredit", "quotedContent", "meta", "toc", "editorialNote"}
SECTION_NUM = re.compile(r"^\d+[A-Za-z]*(?:-\d+)?$")

def local(tag):
    return tag.split("}")[-1] if isinstance(tag, str) else ""

def clean_text(el):
    parts = []
    def walk(node):
        if local(node.tag) in SKIP_TAGS:
            return
        if node.text:
            parts.append(node.text)
        for child in node:
            walk(child)
            if child.tail:
                parts.append(child.tail)
    walk(el)
    return re.sub(r"\s+", " ", "".join(parts)).strip()

def in_amendment_or_notes(sec):
    return any(local(a.tag) in {"quotedContent", "notes"} for a in sec.iterancestors())

src = pathlib.Path(sys.argv[1])
out_path = pathlib.Path("data/processed/usc26_sections.jsonl")
out_path.parent.mkdir(parents=True, exist_ok=True)
today = datetime.date.today().isoformat()

seen = set()
stats = {"written": 0, "skipped_nested": 0, "skipped_bad_number": 0,
         "skipped_short": 0, "skipped_duplicate": 0, "repealed": 0}

with out_path.open("w", encoding="utf-8") as out:
    for xml_file in sorted(src.rglob("*.xml")):
        tree = etree.parse(str(xml_file))
        for sec in tree.iter("{*}section"):
            if in_amendment_or_notes(sec):
                stats["skipped_nested"] += 1
                continue

            num_el = sec.find("{*}num")
            head_el = sec.find("{*}heading")
            num = clean_text(num_el).replace("§", "").strip().rstrip(".").strip() if num_el is not None else ""
            if not SECTION_NUM.match(num):
                stats["skipped_bad_number"] += 1
                continue

            heading = clean_text(head_el) if head_el is not None else ""
            full = clean_text(sec)
            # remove the leading "§ N. Heading" that repeats in the body
            body = full
            prefix = f"§ {num}."
            if body.startswith(prefix):
                body = body[len(prefix):].strip()
            if heading and body.startswith(heading):
                body = body[len(heading):].strip()

            if len(body) < 40:
                stats["skipped_short"] += 1
                continue

            citation = f"26 U.S.C. § {num}"
            if citation in seen:
                stats["skipped_duplicate"] += 1
                continue
            seen.add(citation)

            repealed = "repealed" in heading.lower() or body.lower().startswith("repealed")
            status = "repealed" if repealed else "in_code"
            if repealed:
                stats["repealed"] += 1

            record = {
                "citation": citation,
                "section_number": num,
                "heading": heading,
                "status": status,
                "text": body,
                "source_file": xml_file.name,
                "source_url": f"https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title26-section{num}",
                "retrieved_on": today,
                "text_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            stats["written"] += 1

print("Results:", stats)
print(f"Output: {out_path}")
