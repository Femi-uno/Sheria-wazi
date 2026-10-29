import datetime, json, os, re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
ARTICLES = ROOT / "content" / "articles"
SOURCES = ROOT / "sources"
HELD = ROOT / "held"
DRAFTS = ROOT / "drafts"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")


def today():
    return datetime.date.today().isoformat()


def load_yaml(name):
    return yaml.safe_load((ROOT / name).read_text(encoding="utf-8"))


def source_titles():
    return {s["id"]: s["title"] for s in load_yaml("sources.yml")["sources"]}


def read_article(path):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", Path(path).read_text(encoding="utf-8"), re.S)
    if not m:
        raise ValueError(f"{path}: missing frontmatter")
    return yaml.safe_load(m.group(1)), m.group(2).strip()


def write_article(path, meta, body):
    head = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=100)
    Path(path).write_text(f"---\n{head}---\n\n{body}\n", encoding="utf-8")


def norm(s):
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", s).strip().lower()


def latest_source(source_id):
    files = sorted((SOURCES / source_id).glob("*.txt"))
    return files[-1].read_text(encoding="utf-8") if files else None


def changed_sources():
    p = ROOT / "changed.json"
    return set(json.loads(p.read_text())) if p.exists() else set()


def ask(system, user, max_tokens=4000):
    import anthropic  # imported late so the other steps run without an API key
    r = anthropic.Anthropic().messages.create(
        model=MODEL, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}])
    return "".join(b.text for b in r.content if b.type == "text")


def ask_json(system, user, max_tokens=4000):
    t = ask(system + "\nReturn only valid JSON. No code fences, no commentary.", user, max_tokens).strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    return json.loads(t)
