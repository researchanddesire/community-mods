#!/usr/bin/env python3
"""Generate the static R+D Project Hub site from the mods/ catalog.

Scans mods/<ecosystem>/<project_slug>/mod.yml and emits the gallery
plus a branded contribution guide generated from the repository's canonical
CONTRIBUTING.md. Deployed to mods.researchanddesire.com by gallery.yml. The
project author is read from ``mod.yml`` rather than inferred from the folder
structure.
"""

from __future__ import annotations

import base64
import html
import json
import os
import posixpath
import re
import shutil
import sys
from urllib.parse import urlsplit

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
CONTRIBUTING_PATH = os.path.join(REPO_ROOT, "CONTRIBUTING.md")
OUT_DIR = os.path.join(REPO_ROOT, "site")
ECOSYSTEMS = {"lockbox", "dtt", "ossm", "radr"}
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
CONTRIBUTING_URL = f"{CANONICAL_URL}contributing/"
DISCORD_URL = "https://discord.gg/9byY45KtcU"
SITE_DESCRIPTION = (
    "Open-source sex tech projects and tools, maintained by the people who make them."
)


def asset_data_uri(path: str, media_type: str) -> str:
    """Return a local brand asset as a self-contained base64 data URI.

    Returns '' if the file is missing or is still an unresolved Git LFS pointer
    (e.g. a clone without LFS pulled).
    """
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return ""
    if data.startswith(b"version https://git-lfs"):
        return ""
    return f"data:{media_type};base64," + base64.b64encode(data).decode("ascii")


def logo_data_uri() -> str:
    """The R+D logo as an inline data URI, with a text fallback in the UI."""
    return asset_data_uri(LOGO_PATH, "image/png")


def roots_acknowledgement() -> str:
    """Render one quiet KinkyMakers roots credit for the end of each page."""
    return '''<div class="km-ack">
    <div class="km-ack-inner">
      <p>With thanks to <strong>KinkyMakers</strong> — the open-source sex-tech
      community Research and Desire grew out of.</p>
    </div>
  </div>'''


def render_repository_markdown(
    md_text: str, rel: str, local_image_targets: set[str] | None = None
) -> str:
    """Render safe Markdown with repository links and optional local images.

    Repository Markdown can contain contributor-controlled content, so output
    is always sanitized (or falls back to escaped text if optional libraries
    are unavailable). ``rel`` is the source document's repository directory.
    Declared project images in ``local_image_targets`` resolve inside the Pages
    artifact; other relative sources and links resolve against GitHub.
    """
    if _markdown is not None and _nh3 is not None:
        rendered = _markdown.markdown(
            md_text, extensions=["fenced_code", "tables", "sane_lists"]
        )
        rendered = _nh3.clean(rendered)
        # The surrounding page already shows the document title, so drop the
        # Markdown's leading H1 to avoid showing it twice.
        rendered = re.sub(r"^\s*<h1>.*?</h1>\s*", "", rendered, count=1, flags=re.S)
    else:
        rendered = "<pre>" + html.escape(md_text) + "</pre>"

    rel = rel.strip("/")
    def rewrite(match: re.Match) -> str:
        attr, quote, url = match.group(1), match.group(2), match.group(3)
        # Markdown/sanitizer output is already entity-encoded. Decode relative
        # URLs before parsing, then encode the final attribute exactly once.
        decoded_url = html.unescape(url)
        if decoded_url.startswith(("http://", "https://", "//", "#", "mailto:", "data:")):
            return match.group(0)
        parsed = urlsplit(decoded_url)
        path = parsed.path.lstrip("/")
        target = posixpath.normpath(posixpath.join(rel, path))
        if target == ".":
            target = ""
        if target == ".." or target.startswith("../"):
            return f"{attr}={quote}#{quote}"
        if attr == "src" and local_image_targets and target in local_image_targets:
            base = ""
        elif attr == "src":
            base = f"https://raw.githubusercontent.com/{REPO_SLUG}/main/"
        elif parsed.path.endswith("/"):
            base = f"{REPO_URL}/tree/main/"
        else:
            base = f"{REPO_URL}/blob/main/"
        rewritten = f"{base}{target}"
        if parsed.query:
            rewritten += f"?{parsed.query}"
        if parsed.fragment:
            rewritten += f"#{parsed.fragment}"
        # This rewrite runs after Markdown sanitization, so escape the final URL
        # before inserting it back into an HTML attribute. Catalog paths are
        # contributor-controlled and may contain quote characters.
        return f"{attr}={quote}{html.escape(rewritten, quote=True)}{quote}"

    return re.sub(r"""(src|href)=(["'])([^"']*)\2""", rewrite, rendered)


def render_readme(
    md_text: str, rel: str, local_image_targets: set[str] | None = None
) -> str:
    """Render a project README for the gallery modal."""
    return render_repository_markdown(md_text, rel, local_image_targets)


def declared_local_image_targets(rel: str, images: list) -> list[str]:
    """Return safe artifact-relative targets for declared local images."""
    prefix = rel.rstrip("/") + "/"
    targets: list[str] = []
    for image in images:
        if not isinstance(image, str) or image.startswith(
            ("http://", "https://", "//", "data:")
        ):
            continue
        parsed = urlsplit(image)
        if parsed.scheme or parsed.path.startswith("/"):
            continue
        target = posixpath.normpath(posixpath.join(rel, parsed.path))
        if target.startswith(prefix) and target not in targets:
            targets.append(target)
    return targets


def branding_fragments() -> tuple[str, str, str]:
    """Return CSS, content, and favicon fragments for the shared R+D mark."""
    logo_uri = logo_data_uri()
    logo_var = f'--logo:url("{logo_uri}");' if logo_uri else ""
    logo_inner = "" if logo_uri else "R+D"
    favicon = (
        f'<link rel="icon" type="image/png" href="{logo_uri}">' if logo_uri else ""
    )
    return logo_var, logo_inner, favicon


def collect_mods() -> list[dict]:
    mods: list[dict] = []
    if not os.path.isdir(MODS_ROOT):
        return mods
    for product in sorted(os.listdir(MODS_ROOT)):
        pdir = os.path.join(MODS_ROOT, product)
        if not os.path.isdir(pdir) or product not in ECOSYSTEMS:
            continue
        for project_slug in sorted(os.listdir(pdir)):
            mdir = os.path.join(pdir, project_slug)
            if not os.path.isdir(mdir) or project_slug.startswith("."):
                continue
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
            local_images = declared_local_image_targets(rel, images)
            readme_path = os.path.join(mdir, "README.md")
            readme_html = ""
            if os.path.isfile(readme_path):
                with open(readme_path, encoding="utf-8") as rfh:
                    readme_html = render_readme(
                        rfh.read(), rel, set(local_images)
                    )
            first = images[0] if images else ""
            if isinstance(first, str) and first.startswith(("http://", "https://")):
                thumb = first
            elif isinstance(first, str):
                first_target = posixpath.normpath(
                    posixpath.join(rel, urlsplit(first).path)
                )
                thumb = first_target if first_target in local_images else ""
            else:
                thumb = ""
            mods.append(
                {
                    "id": rel,
                    "title": str(data.get("title", project_slug)),
                    "author": str(data.get("author", "")),
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
                    "_local_images": local_images,
                }
            )
    mods.sort(key=lambda project: (project["title"].casefold(), project["author"].casefold()))
    return mods


def render(mods: list[dict]) -> str:
    # Avoid allowing contributor-controlled strings to terminate the script tag.
    public_projects = [
        {key: value for key, value in project.items() if not key.startswith("_")}
        for project in mods
    ]
    payload = json.dumps(public_projects).replace("</", "<\\/")
    active_ecosystems = {project["product"] for project in mods}
    options = "".join(
        f'<option value="{code}">{html.escape(label)}</option>'
        for code, label in ECOSYSTEM_LABELS.items()
        if code in active_ecosystems
    )
    logo_var, logo_inner, favicon = branding_fragments()
    roots_credit = roots_acknowledgement()
    project_count = f"{len(mods)} project{'s' if len(mods) != 1 else ''}"
    social_image_meta = ""
    if os.path.isfile(SOCIAL_IMAGE_PATH):
        social_image_meta = f'''<meta property="og:image" content="{SOCIAL_IMAGE_URL}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="R+D Project Hub — open-source sex tech projects and tools">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SOCIAL_IMAGE_URL}">
<meta name="twitter:image:alt" content="R+D Project Hub — open-source sex tech projects and tools">'''
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>R+D Project Hub</title>
<meta name="description" content="{SITE_DESCRIPTION}">
<link rel="canonical" href="{CANONICAL_URL}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="R+D Project Hub">
<meta property="og:title" content="R+D Project Hub">
<meta property="og:description" content="{SITE_DESCRIPTION}">
<meta property="og:url" content="{CANONICAL_URL}">
<meta name="twitter:title" content="R+D Project Hub">
<meta name="twitter:description" content="{SITE_DESCRIPTION}">
{social_image_meta}
{favicon}
<style>
  :root {{ --bg:#0f1115; --card:#181b22; --fg:#e7e9ee; --muted:#9aa3b2; --accent:#21c7c7; {logo_var} }}
  * {{ box-sizing:border-box; }}
  html {{ scroll-behavior:smooth; }}
  body {{ margin:0; font:16px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--fg); }}
  a,button,input,select {{ font:inherit; }}
  :focus-visible {{ outline:2px solid var(--accent); outline-offset:3px; }}
  .topbar {{ position:sticky; top:0; z-index:20; background:rgba(15,17,21,.96); border-bottom:1px solid #2a2f3a; backdrop-filter:blur(12px); }}
  .site-header {{ min-height:72px; max-width:1100px; margin:0 auto; padding:.75rem 1.5rem; display:flex; align-items:center; gap:1.25rem; }}
  .site-brand {{ display:flex; align-items:center; gap:.72rem; color:var(--fg); text-decoration:none; }}
  .logo {{ flex:0 0 auto; width:44px; height:44px; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:.82rem; letter-spacing:.01em; color:var(--accent); background:center/contain no-repeat; background-image:var(--logo,none); }}
  .site-brand:hover .logo {{ opacity:.82; }}
  .brand-copy {{ display:grid; line-height:1.08; }}
  .brand-copy strong {{ font-size:.96rem; letter-spacing:-.015em; }}
  .brand-copy small {{ margin-top:.25rem; color:var(--muted); font-size:.72rem; }}
  .site-nav {{ margin-left:auto; display:flex; align-items:center; gap:1rem; }}
  .site-nav a {{ min-height:44px; display:inline-flex; align-items:center; color:var(--muted); text-decoration:none; font-size:.9rem; }}
  .site-nav a:hover,.site-nav a:focus-visible {{ color:var(--accent); }}
  .site-nav a[aria-current="page"] {{ color:var(--fg); font-weight:650; }}
  .hero {{ max-width:1100px; margin:0 auto; padding:clamp(3.5rem,8vw,6.5rem) 1.5rem clamp(2.5rem,5vw,4rem); }}
  .hero h1 {{ max-width:900px; margin:0; font-size:clamp(3rem,7vw,6rem); line-height:.95; letter-spacing:-.055em; }}
  .hero p {{ max-width:650px; margin:1.1rem 0 0; color:var(--muted); font-size:clamp(1rem,2vw,1.18rem); }}
  .projects-shell {{ scroll-margin-top:calc(var(--topbar-h,72px) + 1rem); }}
  .projects-head {{ max-width:1100px; margin:0 auto; padding:0 1.5rem .85rem; display:flex; align-items:baseline; justify-content:space-between; gap:1rem; border-bottom:1px solid #2a2f3a; }}
  .projects-head h2 {{ margin:0; font-size:1.35rem; letter-spacing:-.025em; }}
  .projects-head span {{ color:var(--muted); font-size:.82rem; }}
  .controls {{ display:flex; gap:.75rem; flex-wrap:wrap; max-width:1100px; margin:1rem auto 0; padding:0 1.5rem; }}
  input,select {{ background:var(--card); color:var(--fg); border:1px solid #2a2f3a; border-radius:8px; padding:.6rem .8rem; font:inherit; }}
  input {{ flex:1; min-width:200px; }}
  input:focus,select:focus {{ border-color:var(--accent); }}
  .layout {{ display:flex; gap:1.5rem; max-width:1100px; margin:1rem auto 0; padding:0 1.5rem 4.5rem; align-items:flex-start; }}
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
    .site-header {{ align-items:flex-start; flex-wrap:wrap; }}
    .site-nav {{ order:2; width:100%; margin-left:0; }}
    .site-nav .repo-link {{ display:none; }}
    .hero {{ padding:3.25rem 1.25rem 2.75rem; }}
    .hero h1 {{ font-size:clamp(3rem,15vw,4.25rem); }}
  }}
  .card {{ background:var(--card); border:1px solid #2a2f3a; border-radius:12px; overflow:hidden; display:flex; flex-direction:column; cursor:pointer; transition:border-color .15s, transform .15s; }}
  .card:hover {{ border-color:var(--accent); transform:translateY(-2px); }}
  .card:focus-within,.card:focus-visible {{ border-color:var(--accent); }}
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
  .footer-brandline {{ display:flex; align-items:center; gap:.7rem; margin-bottom:.6rem; }}
  .footer-brand .logo {{ width:42px; height:42px; opacity:.78; }}
  .footer-brand .name {{ color:var(--fg); font-weight:650; font-size:.95rem; }}
  .footer-brand p {{ color:var(--muted); font-size:.92rem; margin:0; }}
  .footer-col h2 {{ font-size:.8rem; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin:0 0 .6rem; }}
  .footer-links {{ display:flex; flex-direction:column; gap:.45rem; }}
  .footer-links a {{ color:var(--accent); text-decoration:none; font-size:.95rem; }}
  .footer-links a:hover {{ text-decoration:underline; }}
  .footer-bottom {{ border-top:1px solid #2a2f3a; color:var(--muted); font-size:.82rem; }}
  .footer-bottom div {{ max-width:1100px; margin:0 auto; padding:1rem 1.5rem; }}
  .km-ack {{ border-top:1px solid #2a2f3a; background:var(--bg); }}
  .km-ack-inner {{ max-width:1100px; margin:0 auto; padding:1.2rem 1.5rem; }}
  .km-ack p {{ max-width:760px; margin:0; color:var(--muted); font-size:.82rem; }}
  .km-ack strong {{ color:var(--fg); }}
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
<header class="site-header">
  <a class="site-brand" href="https://researchanddesire.com" target="_blank" rel="noopener" aria-label="Research and Desire home">
    <span class="logo" aria-hidden="true">{logo_inner}</span>
    <span class="brand-copy">
      <strong>Research and Desire</strong>
      <small>Project Hub</small>
    </span>
  </a>
  <nav class="site-nav" aria-label="Site">
    <a href="./" aria-current="page">Projects</a>
    <a href="contributing/">Contributing</a>
    <a class="repo-link" href="{REPO_URL}" target="_blank" rel="noopener">GitHub ↗</a>
  </nav>
</header>
</div>
<main>
  <section class="hero" aria-labelledby="hero-title">
    <h1 id="hero-title">Open-source sex tech.</h1>
    <p>Projects and tools, maintained by the people who make them.</p>
  </section>
  <section class="projects-shell" id="projects" aria-labelledby="projects-title">
    <div class="projects-head">
      <h2 id="projects-title">Projects</h2>
      <span>{project_count}</span>
    </div>
    <div class="controls">
      <input id="q" type="search" placeholder="Search projects…" aria-label="Search projects" autocomplete="off">
      <select id="ecosystem" aria-label="Filter by ecosystem"><option value="">All ecosystems</option>{options}</select>
    </div>
    <div class="layout">
      <aside class="sidebar">
        <div class="sidebar-head">
          <h2>Browse by tag</h2>
          <button class="clear" id="clear" hidden>Clear tags</button>
        </div>
        <div class="tags" id="tags"></div>
      </aside>
      <div class="main"><div class="grid" id="grid"></div></div>
    </div>
  </section>
</main>
<footer>
  <div class="footer-inner">
    <div class="footer-brand">
      <div class="footer-brandline">
        <a class="logo" href="https://researchanddesire.com" target="_blank" rel="noopener" aria-label="Research and Desire home">{logo_inner}</a>
        <span class="name">Research and Desire · Project Hub</span>
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
        <a href="{DISCORD_URL}" target="_blank" rel="noopener">R+D Discord ↗</a>
        <a href="contributing/">Contribute a project</a>
        <a href="{REPO_URL}" target="_blank" rel="noopener">Project repository ↗</a>
      </div>
    </div>
  </div>
  <div class="footer-bottom"><div>© Research and Desire · Projects remain the work of their respective authors.</div></div>
  {roots_credit}
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
let modalTrigger = null;
let openProjectId = null;
let historyClosePending = false;
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
function projectHash(m) {{
  const route = String(m.id || '').replace(/^mods\\//, '');
  return '#project=' + route.split('/').map(encodeURIComponent).join('/');
}}
function projectFromHash() {{
  const prefix = '#project=';
  if (!window.location.hash.startsWith(prefix)) return null;
  try {{
    const route = window.location.hash.slice(prefix.length)
      .split('/').map(decodeURIComponent).join('/');
    return PROJECT_BY_ID['mods/' + route] || null;
  }} catch {{
    return null;
  }}
}}
// Whole-card click opens the README in an in-page viewer. Inner links keep
// their own behavior (they navigate to GitHub) via the closest('a') guard.
function openModal(m, trigger, updateUrl = true) {{
  if (!m) return;
  historyClosePending = false;
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
  modalTrigger = trigger || (updateUrl ? document.activeElement : q);
  openProjectId = m.id;
  modal.hidden = false;
  document.body.style.overflow = 'hidden';
  if (updateUrl && window.location.hash !== projectHash(m)) {{
    window.history.pushState(
      {{projectModal: true, projectId: m.id}}, '', projectHash(m)
    );
  }}
  const closeButton = modal.querySelector('.modal-back');
  if (closeButton) closeButton.focus();
}}
function closeModal(updateUrl = true) {{
  if (modal.hidden) return;
  if (historyClosePending) return;
  if (updateUrl) {{
    const state = window.history.state;
    if (state && state.projectModal && state.projectId === openProjectId) {{
      historyClosePending = true;
      window.history.back();
      return;
    }}
    window.history.replaceState(
      null, '', window.location.pathname + window.location.search
    );
  }}
  modal.hidden = true;
  document.body.style.overflow = '';
  const trigger = modalTrigger;
  modalTrigger = null;
  openProjectId = null;
  if (trigger && typeof trigger.focus === 'function') trigger.focus();
}}
function syncModalFromUrl() {{
  historyClosePending = false;
  const project = projectFromHash();
  if (project) {{
    if (modal.hidden || openProjectId !== project.id) {{
      openModal(project, null, false);
    }}
  }} else {{
    if (window.location.hash.startsWith('#project=')) {{
      window.history.replaceState(
        null, '', window.location.pathname + window.location.search
      );
    }}
    if (!modal.hidden) closeModal(false);
  }}
}}
grid.addEventListener('click', e => {{
  if (e.target.closest('a')) return;
  const card = e.target.closest('.card');
  if (card) openModal(PROJECT_BY_ID[card.dataset.id], card);
}});
grid.addEventListener('keydown', e => {{
  if (e.key !== 'Enter' && e.key !== ' ') return;
  const card = e.target.closest('.card');
  if (!card || e.target.closest('a')) return;
  e.preventDefault();
  openModal(PROJECT_BY_ID[card.dataset.id], card);
}});
modal.addEventListener('click', e => {{ if (e.target.closest('[data-close]')) closeModal(); }});
modalContent.addEventListener('click', e => {{
  const link = e.target.closest('a[href^="#"]');
  if (!link) return;
  e.preventDefault();
  let id = '';
  try {{ id = decodeURIComponent(link.getAttribute('href').slice(1)); }} catch {{ return; }}
  const target = [...modalContent.querySelectorAll('[id]')]
    .find(element => element.id === id);
  if (target) target.scrollIntoView({{block: 'start'}});
}});
modal.addEventListener('keydown', e => {{
  if (e.key !== 'Tab') return;
  const focusable = [...modal.querySelectorAll(
    'button:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])'
  )];
  if (!focusable.length) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  if (e.shiftKey && document.activeElement === first) {{
    e.preventDefault();
    last.focus();
  }} else if (!e.shiftKey && document.activeElement === last) {{
    e.preventDefault();
    first.focus();
  }}
}});
document.addEventListener('keydown', e => {{ if (e.key === 'Escape' && !modal.hidden) closeModal(); }});
window.addEventListener('popstate', syncModalFromUrl);
window.addEventListener('hashchange', syncModalFromUrl);
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
syncModalFromUrl();
</script>
</body>
</html>
"""


def render_contributing(md_text: str) -> str:
    """Render the canonical repository contribution guide as a branded page."""
    logo_var, logo_inner, favicon = branding_fragments()
    roots_credit = roots_acknowledgement()
    guidance = render_repository_markdown(md_text, "")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Contributing a project · R+D Project Hub</title>
<meta name="description" content="How to index or host a project in the R+D Project Hub.">
<link rel="canonical" href="{CONTRIBUTING_URL}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="R+D Project Hub">
<meta property="og:title" content="Contributing a project · R+D Project Hub">
<meta property="og:description" content="How to index or host a project in the R+D Project Hub.">
<meta property="og:url" content="{CONTRIBUTING_URL}">
<meta property="og:image" content="{SOCIAL_IMAGE_URL}">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="R+D Project Hub — open-source sex tech projects and tools">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Contributing a project · R+D Project Hub">
<meta name="twitter:description" content="How to index or host a project in the R+D Project Hub.">
<meta name="twitter:image" content="{SOCIAL_IMAGE_URL}">
<meta name="twitter:image:alt" content="R+D Project Hub — open-source sex tech projects and tools">
{favicon}
<style>
  :root {{ --bg:#0f1115; --card:#181b22; --fg:#e7e9ee; --muted:#9aa3b2; --accent:#21c7c7; {logo_var} }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font:16px/1.6 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--fg); }}
  a {{ font:inherit; }}
  :focus-visible {{ outline:2px solid var(--accent); outline-offset:3px; }}
  .topbar {{ position:sticky; top:0; z-index:20; border-bottom:1px solid #2a2f3a; background:rgba(15,17,21,.96); backdrop-filter:blur(12px); }}
  .site-header {{ min-height:72px; max-width:1100px; margin:0 auto; padding:.75rem 1.5rem; display:flex; align-items:center; gap:1.25rem; }}
  .site-brand {{ display:flex; align-items:center; gap:.72rem; color:var(--fg); text-decoration:none; }}
  .logo {{ flex:0 0 auto; width:44px; height:44px; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:.82rem; color:var(--accent); background:center/contain no-repeat; background-image:var(--logo,none); }}
  .site-brand:hover .logo {{ opacity:.82; }}
  .brand-copy {{ display:grid; line-height:1.08; }}
  .brand-copy strong {{ font-size:.96rem; letter-spacing:-.015em; }}
  .brand-copy small {{ margin-top:.25rem; color:var(--muted); font-size:.72rem; }}
  .site-nav {{ margin-left:auto; display:flex; align-items:center; gap:1rem; }}
  .site-nav a {{ min-height:44px; display:inline-flex; align-items:center; color:var(--muted); text-decoration:none; font-size:.9rem; }}
  .site-nav a:hover,.site-nav a:focus-visible {{ color:var(--accent); }}
  .site-nav a[aria-current="page"] {{ color:var(--fg); font-weight:650; }}
  main {{ max-width:900px; margin:0 auto 3rem; padding:0 1.5rem; }}
  .page-heading {{ padding:clamp(2.75rem,6vw,4.5rem) 0 1.5rem; }}
  .page-heading .eyebrow {{ color:var(--muted); margin:0 0 .3rem; font-size:.76rem; text-transform:uppercase; letter-spacing:.08em; }}
  .page-heading h1 {{ margin:0; font-size:clamp(2.25rem,5vw,3.6rem); line-height:1; letter-spacing:-.04em; }}
  .document {{ background:var(--card); border:1px solid #2a2f3a; border-radius:12px; padding:1.5rem clamp(1.1rem,4vw,3rem) 2.5rem; }}
  .document h2 {{ margin-top:2rem; border-bottom:1px solid #2a2f3a; padding-bottom:.35rem; line-height:1.25; }}
  .document h3 {{ margin-top:1.6rem; line-height:1.3; }}
  .document a {{ color:var(--accent); }}
  .document code {{ background:var(--bg); border-radius:4px; padding:.12rem .35rem; font-size:.9em; overflow-wrap:anywhere; }}
  .document pre {{ background:var(--bg); border:1px solid #2a2f3a; border-radius:8px; padding:1rem; overflow:auto; }}
  .document pre code {{ padding:0; background:none; overflow-wrap:normal; }}
  .document table {{ width:100%; border-collapse:collapse; display:block; overflow-x:auto; }}
  .document th, .document td {{ border:1px solid #2a2f3a; padding:.45rem .65rem; text-align:left; }}
  .document blockquote {{ margin:.75rem 0; padding:.2rem 1rem; border-left:3px solid var(--accent); color:var(--muted); }}
  .document img {{ max-width:100%; height:auto; }}
  .source-note {{ color:var(--muted); font-size:.88rem; margin:1rem 0 0; }}
  .source-note a {{ color:var(--accent); }}
  footer {{ border-top:1px solid #2a2f3a; color:var(--muted); }}
  .footer-inner {{ max-width:900px; margin:0 auto; padding:1.5rem; display:flex; flex-wrap:wrap; gap:.6rem 1.25rem; justify-content:space-between; }}
  footer a {{ color:var(--accent); text-decoration:none; }}
  footer a:hover {{ text-decoration:underline; }}
  .km-ack {{ border-top:1px solid #2a2f3a; background:var(--bg); }}
  .km-ack-inner {{ max-width:900px; margin:0 auto; padding:1.2rem 1.5rem; }}
  .km-ack p {{ max-width:760px; margin:0; color:var(--muted); font-size:.82rem; }}
  .km-ack strong {{ color:var(--fg); }}
  @media (max-width:620px) {{
    .site-header {{ align-items:flex-start; flex-wrap:wrap; }}
    .site-nav {{ order:2; width:100%; margin-left:0; }}
    .site-nav .repo-link {{ display:none; }}
    .document {{ border-radius:8px; }}
  }}
</style>
</head>
<body>
<div class="topbar">
  <header class="site-header">
    <a class="site-brand" href="https://researchanddesire.com" target="_blank" rel="noopener" aria-label="Research and Desire home">
      <span class="logo" aria-hidden="true">{logo_inner}</span>
      <span class="brand-copy">
        <strong>Research and Desire</strong>
        <small>Project Hub</small>
      </span>
    </a>
    <nav class="site-nav" aria-label="Site">
      <a href="../">Projects</a>
      <a href="./" aria-current="page">Contributing</a>
      <a class="repo-link" href="{REPO_URL}" target="_blank" rel="noopener">GitHub ↗</a>
    </nav>
  </header>
</div>
<main>
  <div class="page-heading">
    <p class="eyebrow">Project Hub</p>
    <h1>Contributing a project</h1>
  </div>
  <article class="document">{guidance}</article>
  <p class="source-note">This page is generated from the repository's
  <a href="{REPO_URL}/blob/main/CONTRIBUTING.md">canonical contribution guide</a>
  so the website and pull-request guidance stay together.</p>
</main>
<footer>
  <div class="footer-inner">
    <span>Hosted by Research and Desire</span>
    <span><a href="../">Browse projects</a> · <a href="{DISCORD_URL}" target="_blank" rel="noopener">R+D Discord ↗</a> · <a href="{REPO_URL}">Project repository ↗</a></span>
  </div>
  {roots_credit}
</footer>
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
    # Copy declared local images into the site output, preserving their catalog
    # paths so cards and modal README content resolve identically in previews and
    # on GitHub Pages.
    for m in mods:
        copied: set[str] = set()
        project_root = os.path.realpath(os.path.join(REPO_ROOT, m["id"]))
        for asset in m.get("_local_images", []):
            if not asset.startswith(m["id"].rstrip("/") + "/"):
                continue
            src = os.path.realpath(os.path.join(REPO_ROOT, asset))
            try:
                if os.path.commonpath([project_root, src]) != project_root:
                    continue
            except ValueError:
                continue
            if not os.path.isfile(src):
                continue
            dst = os.path.join(OUT_DIR, *asset.split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            copied.add(asset)

        thumb = m.get("thumb")
        if not thumb or thumb.startswith(("http://", "https://")):
            continue
        if thumb not in copied:
            m["thumb"] = ""  # missing image → render without a thumbnail
    out_html = os.path.join(OUT_DIR, "index.html")
    with open(out_html, "w", encoding="utf-8") as fh:
        fh.write(render(mods))
    with open(CONTRIBUTING_PATH, encoding="utf-8") as fh:
        contribution_guidance = fh.read()
    contributing_dir = os.path.join(OUT_DIR, "contributing")
    os.makedirs(contributing_dir, exist_ok=True)
    contributing_html = os.path.join(contributing_dir, "index.html")
    with open(contributing_html, "w", encoding="utf-8") as fh:
        fh.write(render_contributing(contribution_guidance))
    print(
        f"Wrote {out_html} with {len(mods)} project(s) and {contributing_html}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
