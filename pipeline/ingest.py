"""Step 1: fetch official texts and save dated snapshots. Lists changed sources in changed.json."""
import io, json, re
import requests
from bs4 import BeautifulSoup
from .common import ROOT, SOURCES, load_yaml, today, latest_source

HEADERS = {"User-Agent": "sheria-wazi-bot (set a contact email here)"}


def fetch_text(url):
    r = requests.get(url, headers=HEADERS, timeout=90)
    r.raise_for_status()
    if "pdf" in r.headers.get("content-type", "").lower() or url.lower().endswith(".pdf"):
        from pypdf import PdfReader
        text = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(r.content)).pages)
    else:
        text = BeautifulSoup(r.text, "html.parser").get_text("\n")
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def main():
    changed = []
    for s in load_yaml("sources.yml")["sources"]:
        if not s.get("url"):
            print(f"skip {s['id']}: no url in sources.yml")
            continue
        try:
            text = fetch_text(s["url"])
        except Exception as e:
            print(f"FAILED {s['id']}: {e}")
            continue
        if len(text) < 500:
            print(f"skip {s['id']}: fetched text is suspiciously short")
            continue
        if text == latest_source(s["id"]):
            print(f"unchanged {s['id']}")
            continue
        d = SOURCES / s["id"]
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{today()}.txt").write_text(text, encoding="utf-8")
        changed.append(s["id"])
        print(f"saved {s['id']}")
    (ROOT / "changed.json").write_text(json.dumps(changed))


if __name__ == "__main__":
    main()
