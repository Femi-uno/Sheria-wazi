"""Step 4: render content/articles/*.md to a static site in dist/."""
import html, os, shutil
import markdown
from .common import *

BASE = os.environ.get("SITE_BASE", "").rstrip("/")
SHOW_UNVERIFIED = os.environ.get("PUBLISH_UNVERIFIED", "true").lower() == "true"
SITE = "Sheria Wazi"
E = html.escape


def badge(meta):
    s = meta.get("status", "unverified")
    if s == "verified":
        txt = f"Checked against source on {meta.get('last_checked')}"
        cls = "badge ok"
    elif s == "needs-recheck":
        txt, cls = "Source changed: recheck pending", "badge"
    else:
        txt, cls = "Draft: not yet verified", "badge"
    if meta.get("reviewed_by"):
        txt += f". Reviewed by {E(str(meta['reviewed_by']))}"
    return f'<span class="{cls}">{txt}</span>'


def page(title, body, desc=""):
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{E(title)}</title><meta name="description" content="{E(desc)}">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700&family=Source+Serif+4:wght@400;600&display=swap">
<link rel="stylesheet" href="{BASE}/style.css"></head><body><div class="wrap">
<header><a href="{BASE}/"><span class="brand">{SITE}</span></a><p class="tag">Kenyan law in plain language</p></header>
<main>{body}</main>
<footer>General legal information, not legal advice. Articles are drafted by AI from official sources and checked automatically against them. For your own situation, speak to an advocate.</footer>
</div></body></html>"""


def article_page(slug, meta, body):
    srcs = "<br>".join(E(s["title"] + (f", {s['section']}" if s.get("section") else "")) for s in meta.get("sources", []))
    links = "<br>".join(f'<a href="{E(l["url"])}">{E(l["title"])}</a>' for l in meta.get("links", []))
    inner = (f'<article><p><a class="back" href="{BASE}/">Back to all articles</a></p>{badge(meta)}'
             f'<h1>{E(meta["title"])}</h1>{markdown.markdown(body)}'
             f'<div class="src"><b>Sources</b>{srcs}{"<br>" + links if links else ""}</div>'
             '<div class="note">This is general information. Laws change, and fees and procedures are updated often. '
             'Confirm details with the source before you act, and speak to an advocate about your own case.</div></article>')
    return page(f"{meta['title']} | {SITE}", inner, meta.get("summary", ""))


def index_page(items):
    cats = sorted({m["category"] for _, m, _ in items})
    chips = "".join(f'<button class="chip" data-cat="{E(c)}" aria-pressed="false">{E(c)}</button>' for c in ["All"] + cats)
    cards = "".join(
        f'<a class="item" href="{BASE}/{s}/" data-cat="{E(m["category"])}" data-text="{E((m["title"] + " " + m["summary"]).lower())}">'
        f'<h2>{E(m["title"])}</h2><p>{E(m["summary"])}</p><div class="meta">{E(m["category"])} &nbsp;{badge(m)}</div></a>'
        for s, m, _ in items)
    js = """<script>var q='',c='All';function f(){document.querySelectorAll('.item').forEach(function(e){
e.style.display=((c==='All'||e.dataset.cat===c)&&e.dataset.text.indexOf(q)>-1)?'':'none'});
document.getElementById('none').hidden=!!document.querySelector('.item:not([style*="none"])')}
document.getElementById('q').oninput=function(e){q=e.target.value.toLowerCase();f()};
document.querySelectorAll('.chip').forEach(function(b){b.onclick=function(){c=b.dataset.cat;
document.querySelectorAll('.chip').forEach(function(x){x.setAttribute('aria-pressed',x===b)});f()}});
document.querySelector('.chip').setAttribute('aria-pressed','true');</script>"""
    body = ('<section class="hero"><h1>Know the law that affects your day</h1>'
            '<p>Short explainers on Kenyan law. Each one names the Act or Article it comes from.</p></section>'
            '<input type="search" id="q" placeholder="Search, for example “tenant” or “arrest”" aria-label="Search articles">'
            f'<div class="chips">{chips}</div>{cards}<p id="none" class="empty" hidden>No articles match. Try a different word or choose All.</p>{js}')
    return page(f"{SITE}: Kenyan law in plain language", body, "Plain-language explainers on Kenyan law, each linked to its source.")


def main():
    out = ROOT / "dist"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir()
    shutil.copy(ROOT / "pipeline" / "style.css", out / "style.css")
    items = []
    for p in sorted(ARTICLES.glob("*.md")):
        meta, body = read_article(p)
        if meta.get("status", "unverified") == "unverified" and not SHOW_UNVERIFIED:
            continue
        items.append((p.stem, meta, body))
        (out / p.stem).mkdir()
        (out / p.stem / "index.html").write_text(article_page(p.stem, meta, body), encoding="utf-8")
    (out / "index.html").write_text(index_page(items), encoding="utf-8")
    (out / ".nojekyll").write_text("")
    print(f"built {len(items)} article(s)")


if __name__ == "__main__":
    main()
