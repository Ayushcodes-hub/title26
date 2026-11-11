# data/parse_usc.py
# Usage: python data/parse_usc.py data/raw/usc26/<date>
import sys, json, pathlib, hashlib, datetime, re
from lxml import etree

SKIP_TAGS = {"notes", "note", "sourceCredit", "quotedContent", "meta", "toc", "editorialNote"}
SECTION_NUM = re.compile(r"^\d+[A-Za-z]*(?:-\d+)?$")

def local(tag):
    return tag.split("}")[-1] if isinstance(tag, str) else ""

def clean_text(el):
    if el is None:
        return ""
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
stats = {"written": 0, "in_code": 0, "repealed": 0, "renumbered": 0,
         "skipped_nested": 0, "skipped_bad_number": 0,
         "skipped_short": 0, "skipped_duplicate": 0}

with out_path.open("w", encoding="utf-8") as out:
    for xml_file in sorted(src.rglob("*.xml")):
        tree = etree.parse(str(xml_file))
        for sec in tree.iter("{*}section"):
            if in_amendment_or_notes(sec):
                stats["skipped_nested"] += 1
                continue

            num_el = sec.find("{*}num")
            head_el = sec.find("{*}heading")

            # Repealed and renumbered sections use brackets, e.g. "[ 4"
            raw_num = clean_text(num_el)
            num = re.sub(r"[\[\]§.\s]", "", raw_num)
            if not SECTION_NUM.match(num):
                stats["skipped_bad_number"] += 1
                continue

            heading = clean_text(head_el)
            body = clean_text(sec)

            # Strip the leading "§ N." and the heading if they repeat
            body = re.sub(r"^\W*§?\s*\[?\s*\d+[A-Za-z]*\.?\]?\s*", "", body, count=1)
            if heading and body.startswith(heading) and not heading.lower().startswith(("repealed","renumbered")):
                body = body[len(heading):].strip()

            low_h, low_b = heading.lower(), body.lower()
            if low_h.startswith("repealed") or low_b.startswith("repealed"):
                status = "repealed"
            elif low_h.startswith("renumbered") or low_b.startswith("renumbered"):
                status = "renumbered"
            else:
                status = "in_code"

            if status == "in_code" and len(body) < 40:
                stats["skipped_short"] += 1
                continue

            citation = f"26 U.S.C. § {num}"
            if citation in seen:
                stats["skipped_duplicate"] += 1
                continue
            seen.add(citation)

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
            stats[status] += 1

print("Results:", stats)
print(f"Output: {out_path}")