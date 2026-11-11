# Test set schema

Each line of eval/test_set.jsonl is one JSON object with these fields:

- id: unique code, for example "STAT-001"
- category: one of "statute", "procedure", "history", "proposal_status", "refusal"
- question: the question as a user would ask it
- answer: the verified answer, written by a licensed reviewer
- citation: the exact official citation, for example "26 U.S.C. § 121"
- source_url: the official page where the citation can be checked
- status: one of "current", "superseded", "proposed", "enacted", "failed", "not_applicable"
- as_of_date: the date the answer was verified (YYYY-MM-DD)
- reviewer: initials of the writer
- checker: initials of the second reviewer

Rules:
- Every question needs a verified answer and a citation, except "refusal" items, which need the expected refusal behavior in the answer field.
- Nothing in this file may be copied into training data.
