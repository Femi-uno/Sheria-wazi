"""Step 5: print a short markdown report (also shown on the Actions run page)."""
import json
from .common import *


def main():
    arts = [read_article(p)[0] | {"slug": p.stem} for p in sorted(ARTICLES.glob("*.md"))]
    by = lambda s: [a["slug"] for a in arts if a.get("status", "unverified") == s]
    held = sorted(p.stem for p in HELD.glob("*.json"))
    print(f"## Pipeline report {today()}\n")
    print(f"- Verified: {len(by('verified'))}\n- Unverified drafts: {len(by('unverified'))}\n"
          f"- Needs recheck: {len(by('needs-recheck'))} {by('needs-recheck') or ''}\n"
          f"- Held (failed checks): {len(held)} {held or ''}\n- Sources changed this run: {sorted(changed_sources()) or 'none'}")
    for s in held:
        d = json.loads((HELD / f"{s}.json").read_text(encoding="utf-8"))
        print(f"\n**{s}** held for:")
        for e in d["errors"][:5]:
            print(f"- {e}")


if __name__ == "__main__":
    main()
