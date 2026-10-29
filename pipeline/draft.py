"""Step 2: draft articles for queued topics, using only the stored source text."""
import json, re
from .common import *

SYSTEM = """You write plain-language explainers on Kenyan law for the general public.
Use ONLY the source excerpts provided. Never rely on memory for legal content.
Rules:
- Markdown body, at most 450 words, short paragraphs and lists, reading age about 14. No top-level title.
- Do not state fees, deadlines, amounts or counts unless they appear in a quote you supply.
- Every statement of a legal right, duty, rule, procedure or limit must be backed by an entry in "claims".
- Each claim: {"text": what you assert, "source_id": id given, "section": the section/article label as it appears in the text, "quote": an exact, verbatim passage (max 300 chars) copied from the excerpt that supports it}.
- If the excerpts are not enough to write a reliable article, return {"insufficient": true}.
Output JSON: {"summary": one sentence, "body_md": string, "claims": [...]}."""


def excerpt(text, keywords, limit=30000):
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    scored = sorted(range(len(paras)), key=lambda i: -sum(paras[i].lower().count(k.lower()) for k in keywords))
    keep, size = set(), 0
    for i in scored:
        if size + len(paras[i]) > limit:
            continue
        keep.add(i)
        size += len(paras[i])
    return "\n\n".join(paras[i] for i in sorted(keep))


def main():
    DRAFTS.mkdir(exist_ok=True)
    for t in load_yaml("topics.yml")["topics"]:
        slug = t["slug"]
        if (ARTICLES / f"{slug}.md").exists() or (HELD / f"{slug}.json").exists():
            continue
        texts = {i: latest_source(i) for i in t["sources"]}
        if not all(texts.values()):
            print(f"skip {slug}: missing source text for {[i for i, v in texts.items() if not v]}")
            continue
        material = "\n\n".join(f"=== SOURCE {i} ===\n{excerpt(v, t.get('focus', []))}" for i, v in texts.items())
        data = ask_json(SYSTEM, f"Topic: {t['title']}\n\n{material}", max_tokens=6000)
        if data.get("insufficient"):
            print(f"insufficient sources for {slug}")
            continue
        data.update(slug=slug, title=t["title"], category=t["category"])
        (DRAFTS / f"{slug}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"drafted {slug}")


if __name__ == "__main__":
    main()
