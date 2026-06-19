#!/usr/bin/env python3
"""Generate the static Mod Hub gallery from the mods/ tree.

Scans mods/<product>/<author>/<mod_name>/mod.yml and emits a single
self-contained site/index.html (cards + client-side search). Deployed to
mods.researchanddesire.com by gallery.yml. Mirrors the Magpie Mod Hub /
mods.vorondesign.com pattern: the gallery is generated, never hand-edited.
"""

from __future__ import annotations

import html
import json
import os
import shutil
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
MODS_ROOT = os.path.join(REPO_ROOT, "mods")
OUT_DIR = os.path.join(REPO_ROOT, "site")
PRODUCTS = {"lockbox", "dtt", "ossm", "radr"}
SKIP_AUTHORS = {"SAMPLE_AUTHOR"}
PRODUCT_LABELS = {
    "lockbox": "Chastity Lockbox",
    "dtt": "Deep Throat Trainer",
    "ossm": "OSSM",
    "radr": "RADR",
}
REPO_SLUG = os.environ.get("GITHUB_REPOSITORY", "researchanddesire/community-mods")
REPO_URL = f"https://github.com/{REPO_SLUG}"


def collect_mods() -> list[dict]:
    mods: list[dict] = []
    if not os.path.isdir(MODS_ROOT):
        return mods
    for product in sorted(os.listdir(MODS_ROOT)):
        pdir = os.path.join(MODS_ROOT, product)
        if not os.path.isdir(pdir) or product not in PRODUCTS:
            continue
        for author in sorted(os.listdir(pdir)):
            adir = os.path.join(pdir, author)
            if not os.path.isdir(adir) or author.startswith(".") or author in SKIP_AUTHORS:
                continue
            for mod in sorted(os.listdir(adir)):
                mdir = os.path.join(adir, mod)
                mod_yml = os.path.join(mdir, "mod.yml")
                if not os.path.isfile(mod_yml):
                    continue
                try:
                    with open(mod_yml, encoding="utf-8") as fh:
                        data = yaml.safe_load(fh) or {}
                except yaml.YAMLError:
                    continue
                rel = os.path.relpath(mdir, REPO_ROOT).replace(os.sep, "/")
                images = data.get("images") or []
                thumb = f"{rel}/{images[0]}" if images else ""
                mods.append(
                    {
                        "title": str(data.get("title", mod)),
                        "author": str(data.get("author", author)),
                        "product": product,
                        "description": str(data.get("description", "")),
                        "compatibility": data.get("compatibility") or [],
                        "thumb": thumb,
                        "folder": f"{REPO_URL}/tree/main/{rel}",
                        "readme": f"{REPO_URL}/blob/main/{rel}/README.md",
                    }
                )
    return mods


def render(mods: list[dict]) -> str:
    payload = json.dumps(mods)
    options = "".join(
        f'<option value="{code}">{html.escape(label)}</option>'
        for code, label in PRODUCT_LABELS.items()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RAD Mod Hub</title>
<style>
  :root {{ --bg:#0f1115; --card:#181b22; --fg:#e7e9ee; --muted:#9aa3b2; --accent:#21c7c7; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font:16px/1.5 system-ui,sans-serif; background:var(--bg); color:var(--fg); }}
  header {{ padding:2rem 1.5rem 1rem; max-width:1100px; margin:0 auto; }}
  h1 {{ margin:0 0 .25rem; }}
  .sub {{ color:var(--muted); }}
  .controls {{ display:flex; gap:.75rem; flex-wrap:wrap; max-width:1100px; margin:1rem auto 0; padding:0 1.5rem; }}
  input,select {{ background:var(--card); color:var(--fg); border:1px solid #2a2f3a; border-radius:8px; padding:.6rem .8rem; font:inherit; }}
  input {{ flex:1; min-width:200px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(260px,1fr)); gap:1rem; max-width:1100px; margin:1.5rem auto; padding:0 1.5rem 3rem; }}
  .card {{ background:var(--card); border:1px solid #2a2f3a; border-radius:12px; overflow:hidden; display:flex; flex-direction:column; }}
  .card img {{ width:100%; height:170px; object-fit:cover; background:#11141a; }}
  .card .body {{ padding:.9rem 1rem 1rem; display:flex; flex-direction:column; gap:.4rem; flex:1; }}
  .badge {{ align-self:flex-start; font-size:.72rem; text-transform:uppercase; letter-spacing:.04em; color:var(--accent); border:1px solid var(--accent); border-radius:999px; padding:.1rem .5rem; }}
  .card h3 {{ margin:.1rem 0 0; font-size:1.05rem; }}
  .card .desc {{ color:var(--muted); font-size:.92rem; flex:1; }}
  .card .meta {{ color:var(--muted); font-size:.8rem; }}
  .card .links {{ display:flex; gap:.6rem; margin-top:.3rem; }}
  .card a {{ color:var(--accent); text-decoration:none; font-size:.9rem; }}
  .empty {{ color:var(--muted); text-align:center; padding:3rem; grid-column:1/-1; }}
  a.top {{ color:var(--accent); }}
</style>
</head>
<body>
<header>
  <h1>RAD Mod Hub</h1>
  <p class="sub">Community-built upgrades for Research and Desire products.
  Not safety-tested or warranted by RAD. <a class="top" href="{REPO_URL}">Repo &amp; submit a mod →</a></p>
</header>
<div class="controls">
  <input id="q" type="search" placeholder="Search mods…" autocomplete="off">
  <select id="product"><option value="">All products</option>{options}</select>
</div>
<div class="grid" id="grid"></div>
<script>
const MODS = {payload};
const grid = document.getElementById('grid');
const q = document.getElementById('q');
const product = document.getElementById('product');
function card(m) {{
  const img = m.thumb ? `<img src="${{m.thumb}}" alt="" loading="lazy">` : '';
  const compat = (m.compatibility || []).join(', ');
  return `<div class="card">${{img}}<div class="body">
    <span class="badge">${{m.product}}</span>
    <h3>${{m.title}}</h3>
    <div class="desc">${{m.description}}</div>
    <div class="meta">by ${{m.author}}${{compat ? ' · ' + compat : ''}}</div>
    <div class="links"><a href="${{m.readme}}">Open README</a><a href="${{m.folder}}">View folder</a></div>
  </div></div>`;
}}
function render() {{
  const term = q.value.toLowerCase();
  const p = product.value;
  const items = MODS.filter(m =>
    (!p || m.product === p) &&
    (!term || (m.title + ' ' + m.description + ' ' + m.author + ' ' + (m.compatibility||[]).join(' ')).toLowerCase().includes(term))
  );
  grid.innerHTML = items.length ? items.map(card).join('') : '<p class="empty">No mods match.</p>';
}}
q.addEventListener('input', render);
product.addEventListener('change', render);
render();
</script>
</body>
</html>
"""


def main() -> int:
    mods = collect_mods()
    os.makedirs(OUT_DIR, exist_ok=True)
    # Copy thumbnails into the site output, preserving their relative path so the
    # generated index.html resolves them.
    for m in mods:
        thumb = m.get("thumb")
        if not thumb:
            continue
        src = os.path.join(REPO_ROOT, thumb)
        dst = os.path.join(OUT_DIR, thumb)
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
        else:
            m["thumb"] = ""  # missing image → render without a thumbnail
    out_html = os.path.join(OUT_DIR, "index.html")
    with open(out_html, "w", encoding="utf-8") as fh:
        fh.write(render(mods))
    print(f"Wrote {out_html} with {len(mods)} mod(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
