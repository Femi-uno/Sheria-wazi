"""Step 3: check every citation. Pass = published; fail = held/ with reasons. Also rechecks old articles."""
import json, re
from .common import *

NUM = re.compile(r"\d[\d,.]*\d|\d")
JUDGE = """You are a strict legal fact-checker. For each claim decide whether the quote, on its own, accurately supports the claim text without overstating it, and whether the quote belongs to the section named.
Also list every sentence in the article that states a legal right, duty, rule, deadline, amount or procedure not covered by any claim.
Output JSON: {"claims": [{"i": 0, "supported": true, "reason": ""}], "uncovered": ["..."]}"""


def code_checks(body, claims):
    if not claims:
        return ["article has no claims"]
    errs = []
    for i, c in enumerate(claims):
        src = latest_source(c.get("source_id", ""))
        if src is None:
            errs.append(f"claim {i}: no stored source for '{c.get('source_id')}'")
        elif not c.get("quote") or norm(c["quote"]) not in norm(src):
            errs.append(f"claim {i}: quote not found verbatim in {c['source_id']}")
        if not c.get("section"):
            errs.append(f"claim {i}: no section given")
    hay = norm(" ".join(c.get("quote", "") + " " + c.get("section", "") for c in claims))
    for n in sorted(set(NUM.findall(body))):
        if n.lower() not in hay:
            errs.append(f"number '{n}' appears in the text but in no quote or section")
    return errs


def judge(body, claims):
    payload = {"article": body, "claims": [
        {"i": i, "claim": c["text"], "section": c["section"], "quote": c["quote"]} for i, c in enumerate(claims)]}
    r = ask_json(JUDGE, json.dumps(payload, ensure_ascii=False))
    errs = [f"claim {x['i']} not supported: {x.get('reason', '')}" for x in r["claims"] if not x["supported"]]
    errs += [f"uncovered statement: {u}" for u in r.get("uncovered", [])]
    return errs


def build_meta(d, titles, old=None):
    sections = {}
    for c in d["claims"]:
        sections.setdefault(c["source_id"], [])
        if c["section"] not in sections[c["source_id"]]:
            sections[c["source_id"]].append(c["section"])
    meta = {"title": d["title"], "category": d["category"], "summary": d["summary"], "status": "verified",
            "last_checked": today(), "reviewed_by": (old or {}).get("reviewed_by"),
            "sources": [{"id": k, "title": titles.get(k, k), "section": ", ".join(v)} for k, v in sections.items()],
            "claims": d["claims"]}
    return meta


def process_drafts(titles):
    for p in sorted(DRAFTS.glob("*.json")) if DRAFTS.exists() else []:
        d = json.loads(p.read_text(encoding="utf-8"))
        errs = code_checks(d["body_md"], d["claims"])
        if not errs:
            errs = judge(d["body_md"], d["claims"])
        if errs:
            HELD.mkdir(exist_ok=True)
            (HELD / p.name).write_text(json.dumps({"errors": errs, "draft": d}, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"HELD {d['slug']}: {len(errs)} problem(s)")
        else:
            write_article(ARTICLES / f"{d['slug']}.md", build_meta(d, titles), d["body_md"])
            print(f"verified {d['slug']}")
        p.unlink()


def recheck():
    changed = changed_sources()
    for p in sorted(ARTICLES.glob("*.md")):
        meta, body = read_article(p)
        if not meta.get("claims"):
            continue  # unverified samples stay unverified until regenerated
        cited = {c["source_id"] for c in meta["claims"]}
        if not (cited & changed) and meta.get("status") == "verified":
            continue
        errs = code_checks(body, meta["claims"]) or judge(body, meta["claims"])
        if errs:
            meta["status"] = "needs-recheck"
            meta["recheck_reasons"] = errs
            print(f"needs-recheck {p.stem}")
        else:
            meta = {**meta, "status": "verified", "last_checked": today()}
            meta.pop("recheck_reasons", None)
            print(f"rechecked ok {p.stem}")
        write_article(p, meta, body)


def main():
    process_drafts(source_titles())
    recheck()


if __name__ == "__main__":
    main()
