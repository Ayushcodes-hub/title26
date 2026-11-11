# data/merge_meta.py
# Joins section metadata onto the parsed corpus by section_number.
import json, pathlib

sections_path = pathlib.Path("data/processed/usc26_sections.jsonl")
meta_path = pathlib.Path("data/processed/usc26_meta.jsonl")
out_path = pathlib.Path("data/processed/usc26_corpus.jsonl")

sections = [json.loads(l) for l in sections_path.open(encoding="utf-8")]
meta = {}
for line in meta_path.open(encoding="utf-8"):
    m = json.loads(line)
    meta.setdefault(m["section_number"], m)  # keep first occurrence

matched = unmatched = no_pl_live = 0
with out_path.open("w", encoding="utf-8") as out:
    for s in sections:
        m = meta.get(s["section_number"])
        if m:
            s["public_laws"] = m["public_laws"]
            s["last_amended_pl"] = m["last_amended_pl"]
            s["note_dates"] = m["note_dates"]
            matched += 1
        else:
            s["public_laws"], s["last_amended_pl"], s["note_dates"] = [], None, []
            unmatched += 1
        if s["status"] == "in_code" and not s["public_laws"]:
            no_pl_live += 1
        out.write(json.dumps(s, ensure_ascii=False) + "\n")

used = {s["section_number"] for s in sections}
meta_only = [k for k in meta if k not in used]
print(f"corpus records: {len(sections)}")
print(f"matched to metadata: {matched}")
print(f"no metadata match: {unmatched}")
print(f"live sections with no Public Law: {no_pl_live}")
print(f"metadata sections not in corpus: {len(meta_only)}")
print("examples of metadata-only:", meta_only[:10])
print(f"Output: {out_path}")