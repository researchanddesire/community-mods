#!/usr/bin/env python3
"""Generate the static R+D Project Hub gallery from the legacy mods/ tree.

Scans mods/<ecosystem>/<author>/<project_slug>/mod.yml and emits a single
self-contained site/index.html (cards + client-side search). Deployed to
mods.researchanddesire.com by gallery.yml. The legacy directory and metadata
names remain stable for contributor and URL compatibility.
"""

from __future__ import annotations

import base64
import html
import json
import os
import re
import shutil
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2)

# Optional: render README markdown -> sanitized HTML for the in-page viewer.
# Both libs ship in CI (see gallery.yml). Without them we fall back to escaped
# plain text so the build never produces unsanitized contributor HTML.
try:
    import markdown as _markdown
except ImportError:
    _markdown = None
try:
    import nh3 as _nh3
except ImportError:
    _nh3 = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
MODS_ROOT = os.path.join(REPO_ROOT, "mods")
OUT_DIR = os.path.join(REPO_ROOT, "site")
ECOSYSTEMS = {"lockbox", "dtt", "ossm", "radr"}
SKIP_AUTHORS = {"SAMPLE_AUTHOR"}
ECOSYSTEM_LABELS = {
    "lockbox": "Chastity Lockbox",
    "dtt": "Deep Throat Trainer",
    "ossm": "OSSM",
    "radr": "RADR",
}
REPO_SLUG = os.environ.get("GITHUB_REPOSITORY", "researchanddesire/community-mods")
REPO_URL = f"https://github.com/{REPO_SLUG}"
LOGO_PATH = os.path.join(SCRIPT_DIR, "assets", "rad-logo.png")
SOCIAL_IMAGE_PATH = os.path.join(SCRIPT_DIR, "assets", "project-hub-og.png")
CANONICAL_URL = "https://mods.researchanddesire.com/"
SOCIAL_IMAGE_URL = f"{CANONICAL_URL}project-hub-og.png"


def logo_data_uri() -> str:
    """The R+D logo as an inline base64 data URI (keeps the site self-contained).

    Returns '' if the file is missing or is still an unresolved Git LFS pointer
    (e.g. a clone without LFS pulled); the gallery then falls back to a text mark.
    """
    try:
        with open(LOGO_PATH, "rb") as fh:
            data = fh.read()
    except OSError:
        return ""
    if data.startswith(b"version https://git-lfs"):
        return ""
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


def render_readme(md_text: str, rel: str) -> str:
    """Markdown -> sanitized HTML, with relative img/links rewritten to GitHub.

    Contributor READMEs are untrusted, so the output is always sanitized (or
    falls back to escaped plain text if the optional libs are unavailable).
    """
    if _markdown is not None and _nh3 is not None:
        rendered = _markdown.markdown(
            md_text, extensions=["fenced_code", "tables", "sane_lists"]
        )
        rendered = _nh3.clean(rendered)
        # The modal already shows the project title as a heading, so drop the
        # README's own leading H1 (conventionally the same title) to avoid
        # showing it twice.
        rendered = re.sub(r"^\s*<h1>.*?</h1>\s*", "", rendered, count=1, flags=re.S)
    else:
        rendered = "<pre>" + html.escape(md_text) + "</pre>"

    raw_base = f"https://raw.githubusercontent.com/{REPO_SLUG}/main/{rel}/"
    blob_base = f"{REPO_URL}/blob/main/{rel}/"

    def rewrite(match: re.Match) -> str:
        attr, quote, url = match.group(1), match.group(2), match.group(3)
        if url.startswith(("http://", "https://", "//", "#", "mailto:", "data:")):
            return match.group(0)
        base = raw_base if attr == "src" else blob_base
        return f"{attr}={quote}{base}{url.lstrip('./')}{quote}"

    return re.sub(r"""(src|href)=(["'])([^"']*)\2""", rewrite, rendered)


def collect_mods() -> list[dict]:
    mods: list[dict] = []
    if not os.path.isdir(MODS_ROOT):
        return mods
    for product in sorted(os.listdir(MODS_ROOT)):
        pdir = os.path.join(MODS_ROOT, product)
        if not os.path.isdir(pdir) or product not in ECOSYSTEMS:
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
                readme_path = os.path.join(mdir, "README.md")
                readme_html = ""
                if os.path.isfile(readme_path):
                    with open(readme_path, encoding="utf-8") as rfh:
                        readme_html = render_readme(rfh.read(), rel)
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
                        "id": rel,
                        "title": str(data.get("title", mod)),
                        "author": str(data.get("author", author)),
                        "product": product,
                        "ecosystem_label": ECOSYSTEM_LABELS[product],
                        "description": str(data.get("description", "")),
                        "compatibility": data.get("compatibility") or [],
                        "tags": [str(t) for t in (data.get("tags") or [])],
                        "thumb": thumb,
                        "source_url": str(data.get("source_url") or ""),
                        "license": str(data.get("license") or ""),
                        "folder": f"{REPO_URL}/tree/main/{rel}",
                        "readme": f"{REPO_URL}/blob/main/{rel}/README.md",
                        "readme_html": readme_html,
                    }
                )
    mods.sort(key=lambda project: (project["title"].casefold(), project["author"].casefold()))
    return mods


def render(mods: list[dict]) -> str:
    # Avoid allowing contributor-controlled strings to terminate the script tag.
    payload = json.dumps(mods).replace("</", "<\\/")
    active_ecosystems = {project["product"] for project in mods}
    options = "".join(
        f'<option value="{code}">{html.escape(label)}</option>'
        for code, label in ECOSYSTEM_LABELS.items()
        if code in active_ecosystems
    )
    logo_uri = logo_data_uri()
    # Defined once on :root so the (large) data URI isn't repeated per <a>.
    logo_var = f'--logo:url("{logo_uri}");' if logo_uri else ""
    # Image logo → empty anchor (logo shows via background); else a text mark.
    logo_inner = "" if logo_uri else "R+D"
    favicon = f'<link rel="icon" type="image/png" href="{logo_uri}">' if logo_uri else ""
    social_image_meta = ""
    if os.path.isfile(SOCIAL_IMAGE_PATH):
        social_image_meta = f'''<meta property="og:image" content="{SOCIAL_IMAGE_URL}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="R+D Project Hub — community-built projects across R+D-adjacent ecosystems">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SOCIAL_IMAGE_URL}">
<meta name="twitter:image:alt" content="R+D Project Hub — community-built projects across R+D-adjacent ecosystems">'''
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>R+D Project Hub</title>
<meta name="description" content="Community-built OSSM variants, controllers, software, hardware, accessories, and tools across R+D-adjacent ecosystems.">
<link rel="canonical" href="{CANONICAL_URL}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="R+D Project Hub">
<meta property="og:title" content="R+D Project Hub">
<meta property="og:description" content="Community-built OSSM variants, controllers, software, hardware, accessories, and tools across R+D-adjacent ecosystems.">
<meta property="og:url" content="{CANONICAL_URL}">
<meta name="twitter:title" content="R+D Project Hub">
<meta name="twitter:description" content="Community-built OSSM variants, controllers, software, hardware, accessories, and tools across R+D-adjacent ecosystems.">
{social_image_meta}
{favicon}
<style>
  :root {{ --bg:#0f1115; --card:#181b22; --fg:#e7e9ee; --muted:#9aa3b2; --accent:#21c7c7; {logo_var} }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font:16px/1.5 system-ui,sans-serif; background:var(--bg); color:var(--fg); }}
  .topbar {{ position:sticky; top:0; z-index:20; background:var(--bg); border-bottom:1px solid #2a2f3a; padding-bottom:1rem; }}
  header {{ padding:1.5rem 1.5rem .75rem; max-width:1100px; margin:0 auto; }}
  .brand {{ display:flex; align-items:center; gap:.75rem; }}
  .logo {{ flex:0 0 auto; width:52px; height:52px; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:1rem; letter-spacing:.01em; color:var(--accent); background:center/contain no-repeat; background-image:var(--logo,none); text-decoration:none; }}
  .brand .logo:hover {{ opacity:.82; }}
  h1 {{ margin:0 0 .15rem; line-height:1.1; }}
  .sub {{ color:var(--muted); margin:0; }}
  .controls {{ display:flex; gap:.75rem; flex-wrap:wrap; max-width:1100px; margin:0 auto; padding:0 1.5rem; }}
  input,select {{ background:var(--card); color:var(--fg); border:1px solid #2a2f3a; border-radius:8px; padding:.6rem .8rem; font:inherit; }}
  input {{ flex:1; min-width:200px; }}
  .layout {{ display:flex; gap:1.5rem; max-width:1100px; margin:1.5rem auto; padding:0 1.5rem 3rem; align-items:flex-start; }}
  .sidebar {{ flex:0 0 220px; position:sticky; top:calc(var(--topbar-h, 0px) + 1rem); }}
  .sidebar-head {{ display:flex; align-items:baseline; justify-content:space-between; gap:.5rem; margin:0 0 .6rem; }}
  .sidebar h2 {{ font-size:.8rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin:0; }}
  .sidebar .tags {{ display:flex; flex-direction:column; gap:.3rem; }}
  .tagbtn {{ display:flex; justify-content:space-between; gap:.5rem; align-items:center; background:var(--card); color:var(--fg); border:1px solid #2a2f3a; border-radius:8px; padding:.4rem .7rem; font:inherit; font-size:.9rem; cursor:pointer; text-align:left; }}
  .tagbtn:hover {{ border-color:var(--accent); }}
  .tagbtn.active {{ background:var(--accent); color:#08191a; border-color:var(--accent); font-weight:600; }}
  .tagbtn .count {{ font-size:.75rem; color:var(--muted); }}
  .tagbtn.active .count {{ color:#08191a; }}
  .clear {{ background:none; border:none; color:var(--accent); font:inherit; font-size:.8rem; cursor:pointer; padding:0; white-space:nowrap; }}
  .main {{ flex:1; min-width:0; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:1rem; }}
  @media (max-width:720px) {{
    .layout {{ flex-direction:column; }}
    .sidebar {{ position:static; flex-basis:auto; width:100%; }}
    .sidebar .tags {{ flex-direction:row; flex-wrap:wrap; }}
  }}
  .card {{ background:var(--card); border:1px solid #2a2f3a; border-radius:12px; overflow:hidden; display:flex; flex-direction:column; cursor:pointer; transition:border-color .15s, transform .15s; }}
  .card:hover {{ border-color:var(--accent); transform:translateY(-2px); }}
  .card:focus-within {{ border-color:var(--accent); }}
  .card img {{ width:100%; height:170px; object-fit:cover; background:#11141a; }}
  .card .body {{ padding:.9rem 1rem 1rem; display:flex; flex-direction:column; gap:.4rem; flex:1; }}
  .chips {{ display:flex; gap:.4rem; align-items:center; flex-wrap:wrap; }}
  .badge {{ align-self:flex-start; font-size:.72rem; text-transform:uppercase; letter-spacing:.04em; color:var(--accent); border:1px solid var(--accent); border-radius:999px; padding:.1rem .5rem; }}
  .provenance {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.04em; color:#b694f5; border:1px solid #b694f5; border-radius:999px; padding:.1rem .5rem; }}
  .lic {{ font-size:.7rem; color:#e0b25a; border:1px solid #e0b25a; border-radius:999px; padding:.1rem .5rem; }}
  .card h3 {{ margin:.1rem 0 0; font-size:1.05rem; }}
  .card .byline {{ color:var(--muted); font-size:.85rem; margin-top:-.15rem; }}
  .card .desc {{ color:var(--muted); font-size:.92rem; flex:1; }}
  .card .meta {{ color:var(--muted); font-size:.8rem; }}
  .project-tags {{ display:flex; flex-wrap:wrap; gap:.32rem; margin-top:.1rem; }}
  .project-tag {{ font-size:.72rem; color:var(--muted); background:var(--bg); border:1px solid #2a2f3a; border-radius:999px; padding:.08rem .45rem; }}
  .more-tags {{ font-size:.72rem; color:var(--muted); padding:.08rem .15rem; }}
  .card .links {{ display:flex; gap:.6rem; margin-top:.3rem; flex-wrap:wrap; }}
  .card a {{ color:var(--accent); text-decoration:none; font-size:.9rem; }}
  .card a:hover {{ text-decoration:underline; }}
  .empty {{ color:var(--muted); text-align:center; padding:3rem; grid-column:1/-1; }}
  a.top {{ color:var(--accent); }}
  footer {{ border-top:1px solid #2a2f3a; background:var(--card); }}
  .footer-inner {{ max-width:1100px; margin:0 auto; padding:2.25rem 1.5rem; display:flex; flex-wrap:wrap; gap:2rem 3.5rem; justify-content:space-between; align-items:flex-start; }}
  .footer-brand {{ max-width:680px; flex:1 1 420px; }}
  .footer-brand .brand {{ margin-bottom:.6rem; }}
  .footer-brand .logo {{ width:42px; height:42px; opacity:.78; }}
  .footer-brand .name {{ color:var(--muted); font-weight:600; font-size:.95rem; }}
  .footer-brand p {{ color:var(--muted); font-size:.92rem; margin:0; }}
  .footer-col h2 {{ font-size:.8rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin:0 0 .6rem; }}
  .footer-links {{ display:flex; flex-direction:column; gap:.45rem; }}
  .footer-links a {{ color:var(--accent); text-decoration:none; font-size:.95rem; }}
  .footer-links a:hover {{ text-decoration:underline; }}
  .footer-bottom {{ border-top:1px solid #2a2f3a; color:var(--muted); font-size:.82rem; }}
  .footer-bottom div {{ max-width:1100px; margin:0 auto; padding:1rem 1.5rem; }}
  /* README viewer modal */
  .modal {{ position:fixed; inset:0; z-index:50; display:flex; }}
  .modal[hidden] {{ display:none; }}
  .modal-backdrop {{ position:absolute; inset:0; background:rgba(0,0,0,.65); }}
  .modal-panel {{ position:relative; margin:auto; background:var(--card); border:1px solid #2a2f3a; border-radius:12px; width:min(840px,94vw); max-height:88vh; display:flex; flex-direction:column; overflow:hidden; }}
  .modal-head {{ display:flex; align-items:center; gap:.75rem; padding:.7rem 1rem; border-bottom:1px solid #2a2f3a; flex-wrap:wrap; }}
  .modal-back {{ background:var(--bg); color:var(--fg); border:1px solid #2a2f3a; border-radius:8px; padding:.4rem .75rem; font:inherit; font-size:.9rem; cursor:pointer; }}
  .modal-back:hover {{ border-color:var(--accent); }}
  .modal-actions {{ display:flex; gap:.9rem; margin-left:auto; flex-wrap:wrap; }}
  .modal-actions a {{ color:var(--accent); text-decoration:none; font-size:.9rem; }}
  .modal-content {{ padding:1.25rem 1.5rem 2.5rem; overflow:auto; }}
  .modal-hero h1 {{ margin:.4rem 0 .1rem; font-size:1.5rem; }}
  .modal-hero .byline {{ color:var(--muted); }}
  .modal-hero .project-tags {{ margin-top:.7rem; }}
  .readme {{ margin-top:1.25rem; }}
  .readme img {{ max-width:100%; height:auto; border-radius:8px; }}
  .readme a {{ color:var(--accent); }}
  .readme pre {{ background:var(--bg); border:1px solid #2a2f3a; border-radius:8px; padding:.8rem; overflow:auto; }}
  .readme code {{ background:var(--bg); border-radius:4px; padding:.1rem .35rem; font-size:.9em; }}
  .readme pre code {{ padding:0; background:none; }}
  .readme h1, .readme h2 {{ border-bottom:1px solid #2a2f3a; padding-bottom:.3rem; }}
  .readme table {{ border-collapse:collapse; }}
  .readme th, .readme td {{ border:1px solid #2a2f3a; padding:.35rem .6rem; }}
  .readme blockquote {{ margin:.5rem 0; padding:.1rem .9rem; border-left:3px solid #2a2f3a; color:var(--muted); }}
  @media (max-width:720px) {{
    .modal-panel {{ width:100vw; height:100vh; max-height:100vh; margin:0; border:none; border-radius:0; }}
  }}
</style>
</head>
<body>
<div class="topbar">
<header>
  <div class="brand">
    <a class="logo" href="https://researchanddesire.com" target="_blank" rel="noopener" aria-label="Research and Desire">{logo_inner}</a>
    <div>
      <h1>R+D Project Hub</h1>
      <p class="sub">Community-built OSSM variants, controllers, software, hardware,
      accessories, and tools across R+D-adjacent ecosystems. Projects are
      independently maintained; inclusion is not endorsement, safety certification,
      or warranty by R+D. <a class="top" href="{REPO_URL}">Project repository →</a></p>
    </div>
  </div>
</header>
<div class="controls">
  <input id="q" type="search" placeholder="Search projects…" aria-label="Search projects" autocomplete="off">
  <select id="ecosystem" aria-label="Filter by ecosystem"><option value="">All ecosystems</option>{options}</select>
</div>
</div>
<div class="layout">
  <aside class="sidebar">
    <div class="sidebar-head">
      <h2>Browse by tag</h2>
      <button class="clear" id="clear" hidden>Clear tags</button>
    </div>
    <div class="tags" id="tags"></div>
  </aside>
  <main class="main"><div class="grid" id="grid"></div></main>
</div>
<footer>
  <div class="footer-inner">
    <div class="footer-brand">
      <div class="brand">
        <a class="logo" href="https://researchanddesire.com" target="_blank" rel="noopener" aria-label="Research and Desire">{logo_inner}</a>
        <span class="name">Hosted by Research and Desire</span>
      </div>
      <p>Each project remains independently maintained and licensed by its
      authors; inclusion is not endorsement, safety certification, or warranty
      by R+D.</p>
    </div>
    <div class="footer-col">
      <h2>Connect</h2>
      <div class="footer-links">
        <a href="https://researchanddesire.com" target="_blank" rel="noopener">researchanddesire.com ↗</a>
        <a href="https://docs.researchanddesire.com" target="_blank" rel="noopener">Documentation ↗</a>
        <a href="https://discord.gg/VtZcudpxT6" target="_blank" rel="noopener">KinkyMakers Discord ↗</a>
        <a href="{REPO_URL}" target="_blank" rel="noopener">Project repository &amp; contribute ↗</a>
      </div>
    </div>
  </div>
  <div class="footer-bottom"><div>© Research and Desire · Projects remain the work of their respective authors.</div></div>
</footer>
<div class="modal" id="modal" hidden>
  <div class="modal-backdrop" data-close></div>
  <div class="modal-panel" role="dialog" aria-modal="true" aria-labelledby="modal-title">
    <div class="modal-head">
      <button class="modal-back" data-close type="button">← Back</button>
      <div class="modal-actions" id="modal-actions"></div>
    </div>
    <div class="modal-content" id="modal-content"></div>
  </div>
</div>
<script>
const PROJECTS = {payload};
const PROJECT_BY_ID = Object.fromEntries(PROJECTS.map(project => [project.id, project]));
const grid = document.getElementById('grid');
const modal = document.getElementById('modal');
const modalContent = document.getElementById('modal-content');
const modalActions = document.getElementById('modal-actions');
const q = document.getElementById('q');
const ecosystem = document.getElementById('ecosystem');
const tagsEl = document.getElementById('tags');
const clearBtn = document.getElementById('clear');
const selectedTags = new Set();
function esc(value) {{
  return String(value ?? '').replace(/[&<>"']/g, ch => ({{
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }})[ch]);
}}
function safeUrl(value) {{
  try {{
    const parsed = new URL(String(value || ''), window.location.href);
    return ['http:', 'https:'].includes(parsed.protocol) ? esc(parsed.href) : '#';
  }} catch {{
    return '#';
  }}
}}
function projectTags(tags, limit) {{
  const all = Array.isArray(tags) ? tags : [];
  if (!all.length) return '';
  const visible = Number.isInteger(limit) ? all.slice(0, limit) : all;
  const more = Number.isInteger(limit) && all.length > limit
    ? `<span class="more-tags">+${{all.length - limit}} more</span>`
    : '';
  return `<div class="project-tags">${{visible.map(tag => `<span class="project-tag">${{esc(tag)}}</span>`).join('')}}${{more}}</div>`;
}}
function card(m) {{
  const imageUrl = m.thumb ? safeUrl(m.thumb) : '#';
  const img = imageUrl !== '#' ? `<img src="${{imageUrl}}" alt="${{esc(m.title)}}" loading="lazy">` : '';
  const compat = (m.compatibility || []).map(esc).join(', ');
  const lic = m.license ? `<span class="lic" title="Declared license">${{esc(m.license)}}</span>` : '';
  const indexed = !!m.source_url;
  const provenance = `<span class="provenance">${{indexed ? 'Indexed' : 'Hosted'}}</span>`;
  const links = indexed
    ? `<a href="${{safeUrl(m.source_url)}}" target="_blank" rel="noopener" data-stop>Project source ↗</a>`
    : `<a href="${{safeUrl(m.folder)}}" target="_blank" rel="noopener" data-stop>Project files ↗</a>`;
  return `<div class="card" data-id="${{esc(m.id)}}" role="button" tabindex="0">${{img}}<div class="body">
    <div class="chips"><span class="badge">${{esc(m.ecosystem_label)}}</span>${{provenance}}${{lic}}</div>
    <h3>${{esc(m.title)}}</h3>
    <div class="byline">by ${{esc(m.author)}}</div>
    <div class="desc">${{esc(m.description)}}</div>
    ${{compat ? `<div class="meta">${{compat}}</div>` : ''}}
    ${{projectTags(m.tags, 4)}}
    <div class="links">${{links}}</div>
  </div></div>`;
}}
// Projects matching everything except the tag facet — used both to render cards
// and to compute tag counts so the sidebar reflects search and ecosystem filters.
function baseMatches() {{
  const term = q.value.toLowerCase();
  const selectedEcosystem = ecosystem.value;
  return PROJECTS.filter(m =>
    (!selectedEcosystem || m.product === selectedEcosystem) &&
    (!term || (m.title + ' ' + m.description + ' ' + m.author + ' ' + (m.compatibility||[]).join(' ') + ' ' + (m.tags||[]).join(' ')).toLowerCase().includes(term))
  );
}}
function renderTags(base) {{
  const counts = Object.create(null);
  base.forEach(m => (m.tags||[]).forEach(t => {{ counts[t] = (counts[t]||0) + 1; }}));
  const names = Object.keys(counts).sort((a,b) => a.localeCompare(b));
  selectedTags.forEach(t => {{ if (!(t in counts)) counts[t] = 0; if (!names.includes(t)) names.push(t); }});
  if (!names.length) {{ tagsEl.innerHTML = '<span class="meta">No tags yet.</span>'; clearBtn.hidden = true; return; }}
  tagsEl.innerHTML = names.map(t => {{
    const active = selectedTags.has(t) ? ' active' : '';
    return `<button class="tagbtn${{active}}" data-tag="${{esc(t)}}">${{esc(t)}}<span class="count">${{counts[t]}}</span></button>`;
  }}).join('');
  clearBtn.hidden = selectedTags.size === 0;
}}
function render() {{
  const base = baseMatches();
  const items = base.filter(m =>
    selectedTags.size === 0 || [...selectedTags].every(t => (m.tags||[]).includes(t))
  );
  grid.innerHTML = items.length ? items.map(card).join('') : '<p class="empty">No projects match.</p>';
  renderTags(base);
}}
// Whole-card click opens the README in an in-page viewer. Inner links keep
// their own behavior (they navigate to GitHub) via the closest('a') guard.
function openModal(m) {{
  if (!m) return;
  const indexed = !!m.source_url;
  const lic = m.license ? `<span class="lic">${{esc(m.license)}}</span>` : '';
  const provenance = `<span class="provenance">${{indexed ? 'Indexed' : 'Hosted'}}</span>`;
  modalActions.innerHTML = indexed
    ? `<a href="${{safeUrl(m.source_url)}}" target="_blank" rel="noopener">Project source ↗</a>`
    : `<a href="${{safeUrl(m.folder)}}" target="_blank" rel="noopener">Project files ↗</a>`;
  const body = m.readme_html || `<p>${{esc(m.description || '')}}</p>`;
  modalContent.innerHTML = `<div class="modal-hero">`
    + `<div class="chips"><span class="badge">${{esc(m.ecosystem_label)}}</span>${{provenance}}${{lic}}</div>`
    + `<h1 id="modal-title">${{esc(m.title)}}</h1><div class="byline">by ${{esc(m.author)}}</div>`
    + `${{projectTags(m.tags)}}</div><div class="readme">${{body}}</div>`;
  modalContent.scrollTop = 0;
  modal.hidden = false;
  document.body.style.overflow = 'hidden';
}}
function closeModal() {{
  modal.hidden = true;
  document.body.style.overflow = '';
}}
grid.addEventListener('click', e => {{
  if (e.target.closest('a')) return;
  const card = e.target.closest('.card');
  if (card) openModal(PROJECT_BY_ID[card.dataset.id]);
}});
grid.addEventListener('keydown', e => {{
  if (e.key !== 'Enter' && e.key !== ' ') return;
  const card = e.target.closest('.card');
  if (!card || e.target.closest('a')) return;
  e.preventDefault();
  openModal(PROJECT_BY_ID[card.dataset.id]);
}});
modal.addEventListener('click', e => {{ if (e.target.closest('[data-close]')) closeModal(); }});
document.addEventListener('keydown', e => {{ if (e.key === 'Escape' && !modal.hidden) closeModal(); }});
tagsEl.addEventListener('click', e => {{
  const btn = e.target.closest('.tagbtn');
  if (!btn) return;
  const t = btn.dataset.tag;
  selectedTags.has(t) ? selectedTags.delete(t) : selectedTags.add(t);
  render();
}});
clearBtn.addEventListener('click', () => {{ selectedTags.clear(); render(); }});
q.addEventListener('input', render);
ecosystem.addEventListener('change', render);
// Keep the sticky sidebar parked just below the sticky top bar, whatever its
// height (it grows when the description wraps on narrow viewports).
const topbar = document.querySelector('.topbar');
function setTopbarH() {{ document.documentElement.style.setProperty('--topbar-h', topbar.offsetHeight + 'px'); }}
if (window.ResizeObserver) new ResizeObserver(setTopbarH).observe(topbar);
window.addEventListener('resize', setTopbarH);
setTopbarH();
render();
</script>
</body>
</html>
"""


def main() -> int:
    mods = collect_mods()
    os.makedirs(OUT_DIR, exist_ok=True)
    social_image_out = os.path.join(OUT_DIR, "project-hub-og.png")
    if os.path.isfile(SOCIAL_IMAGE_PATH):
        shutil.copyfile(SOCIAL_IMAGE_PATH, social_image_out)
    elif os.path.exists(social_image_out):
        os.remove(social_image_out)
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
    print(f"Wrote {out_html} with {len(mods)} project(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
