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
                first = images[0] if images else ""
                if isinstance(first, str) and first.startswith(("http://", "https://")):
                    thumb = first
                elif first:
                    thumb = f"{rel}/{first}"
                else:
                    thumb = ""
                mods.append(
                    {
                        "title": str(data.get("title", mod)),
                        "author": str(data.get("author", author)),
                        "product": product,
                        "description": str(data.get("description", "")),
                        "compatibility": data.get("compatibility") or [],
                        "tags": [str(t) for t in (data.get("tags") or [])],
                        "thumb": thumb,
                        "source_url": str(data.get("source_url") or ""),
                        "license": str(data.get("license") or ""),
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
  .layout {{ display:flex; gap:1.5rem; max-width:1100px; margin:1.5rem auto; padding:0 1.5rem 3rem; align-items:flex-start; }}
  .sidebar {{ flex:0 0 220px; position:sticky; top:1rem; }}
  .sidebar h2 {{ font-size:.8rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin:0 0 .6rem; }}
  .sidebar .tags {{ display:flex; flex-direction:column; gap:.3rem; }}
  .tagbtn {{ display:flex; justify-content:space-between; gap:.5rem; align-items:center; background:var(--card); color:var(--fg); border:1px solid #2a2f3a; border-radius:8px; padding:.4rem .7rem; font:inherit; font-size:.9rem; cursor:pointer; text-align:left; }}
  .tagbtn:hover {{ border-color:var(--accent); }}
  .tagbtn.active {{ background:var(--accent); color:#08191a; border-color:var(--accent); font-weight:600; }}
  .tagbtn .count {{ font-size:.75rem; color:var(--muted); }}
  .tagbtn.active .count {{ color:#08191a; }}
  .clear {{ background:none; border:none; color:var(--accent); font:inherit; font-size:.85rem; cursor:pointer; padding:.4rem 0 0; }}
  .main {{ flex:1; min-width:0; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:1rem; }}
  @media (max-width:720px) {{
    .layout {{ flex-direction:column; }}
    .sidebar {{ position:static; flex-basis:auto; width:100%; }}
    .sidebar .tags {{ flex-direction:row; flex-wrap:wrap; }}
  }}
  .card {{ background:var(--card); border:1px solid #2a2f3a; border-radius:12px; overflow:hidden; display:flex; flex-direction:column; }}
  .card img {{ width:100%; height:170px; object-fit:cover; background:#11141a; }}
  .card .body {{ padding:.9rem 1rem 1rem; display:flex; flex-direction:column; gap:.4rem; flex:1; }}
  .chips {{ display:flex; gap:.4rem; align-items:center; flex-wrap:wrap; }}
  .badge {{ align-self:flex-start; font-size:.72rem; text-transform:uppercase; letter-spacing:.04em; color:var(--accent); border:1px solid var(--accent); border-radius:999px; padding:.1rem .5rem; }}
  .lic {{ font-size:.7rem; color:#e0b25a; border:1px solid #e0b25a; border-radius:999px; padding:.1rem .5rem; }}
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
<div class="layout">
  <aside class="sidebar">
    <h2>Browse by tag</h2>
    <div class="tags" id="tags"></div>
    <button class="clear" id="clear" hidden>Clear tags</button>
  </aside>
  <main class="main"><div class="grid" id="grid"></div></main>
</div>
<script>
const MODS = {payload};
const grid = document.getElementById('grid');
const q = document.getElementById('q');
const product = document.getElementById('product');
const tagsEl = document.getElementById('tags');
const clearBtn = document.getElementById('clear');
const selectedTags = new Set();
function card(m) {{
  const img = m.thumb ? `<img src="${{m.thumb}}" alt="" loading="lazy">` : '';
  const compat = (m.compatibility || []).join(', ');
  const lic = m.license ? `<span class="lic" title="License differs from repo default">${{m.license}}</span>` : '';
  const primary = m.source_url
    ? `<a href="${{m.source_url}}">Upstream source ↗</a>`
    : `<a href="${{m.folder}}">View folder</a>`;
  return `<div class="card">${{img}}<div class="body">
    <div class="chips"><span class="badge">${{m.product}}</span>${{lic}}</div>
    <h3>${{m.title}}</h3>
    <div class="desc">${{m.description}}</div>
    <div class="meta">by ${{m.author}}${{compat ? ' · ' + compat : ''}}</div>
    <div class="links"><a href="${{m.readme}}">Open README</a>${{primary}}</div>
  </div></div>`;
}}
// Mods matching everything except the tag facet — used both to render cards and
// to compute tag counts so the sidebar reflects the active search/product.
function baseMatches() {{
  const term = q.value.toLowerCase();
  const p = product.value;
  return MODS.filter(m =>
    (!p || m.product === p) &&
    (!term || (m.title + ' ' + m.description + ' ' + m.author + ' ' + (m.compatibility||[]).join(' ') + ' ' + (m.tags||[]).join(' ')).toLowerCase().includes(term))
  );
}}
function renderTags(base) {{
  const counts = {{}};
  base.forEach(m => (m.tags||[]).forEach(t => {{ counts[t] = (counts[t]||0) + 1; }}));
  const names = Object.keys(counts).sort((a,b) => a.localeCompare(b));
  selectedTags.forEach(t => {{ if (!(t in counts)) counts[t] = 0; if (!names.includes(t)) names.push(t); }});
  if (!names.length) {{ tagsEl.innerHTML = '<span class="meta">No tags yet.</span>'; clearBtn.hidden = true; return; }}
  tagsEl.innerHTML = names.map(t => {{
    const active = selectedTags.has(t) ? ' active' : '';
    return `<button class="tagbtn${{active}}" data-tag="${{t}}">${{t}}<span class="count">${{counts[t]}}</span></button>`;
  }}).join('');
  clearBtn.hidden = selectedTags.size === 0;
}}
function render() {{
  const base = baseMatches();
  const items = base.filter(m =>
    selectedTags.size === 0 || [...selectedTags].every(t => (m.tags||[]).includes(t))
  );
  grid.innerHTML = items.length ? items.map(card).join('') : '<p class="empty">No mods match.</p>';
  renderTags(base);
}}
tagsEl.addEventListener('click', e => {{
  const btn = e.target.closest('.tagbtn');
  if (!btn) return;
  const t = btn.dataset.tag;
  selectedTags.has(t) ? selectedTags.delete(t) : selectedTags.add(t);
  render();
}});
clearBtn.addEventListener('click', () => {{ selectedTags.clear(); render(); }});
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
        if not thumb or thumb.startswith(("http://", "https://")):
            continue  # nothing to copy (no thumb, or an external URL)
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
