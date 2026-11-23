#!/usr/bin/env python3
"""Validate every project entry under mods/<ecosystem>/<project_slug>/.

Schema source of truth: .github/workflows/scripts/mod.schema.json (canonical
in this repo — the project standard has a single consumer, so it is not vendored
from dev-docs like schemas shared across repositories).
See CONTRIBUTING.md and https://dev.researchanddesire.com/meta/community-mods/.

Checks (structure, not taste):
  - folder depth is exactly mods/<ecosystem>/<project_slug>/
  - no spaces in the ecosystem or project-slug path components
  - mod.yml + README.md present
  - every project declares a license
  - indexed projects (mod.yml has source_url) have no local LICENSE
  - hosted OSSM projects use CERN-OHL-S-2.0 and have no local LICENSE
  - other hosted projects include a project-root LICENSE
  - at least one declared local image, or an HTTP(S) URL for indexed projects
  - mod.yml validates against mod.schema.json (JSON Schema draft-07)
  - mod.yml.product matches the ecosystem folder
  - mod.yml.author names the person, team, or community responsible
  - every local (non-URL) path in mod.yml.images exists

CAD and source files are optional: a hosted project may consist of documentation,
images, configuration, or other useful project material.
"""

from __future__ import annotations

import json
import os
import sys
from urllib.parse import urlparse

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2)

try:
    from jsonschema import Draft7Validator, FormatChecker
except ImportError:
    print("ERROR: jsonschema is required (pip install jsonschema)", file=sys.stderr)
    raise SystemExit(2)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
SCHEMA_PATH = os.path.join(SCRIPT_DIR, "mod.schema.json")
MODS_ROOT = os.path.join(REPO_ROOT, "mods")
IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif"}
OSSM_HOSTED_LICENSE = "CERN-OHL-S-2.0"


def find_mod_dirs() -> list[str]:
    """Find flat project directories and any misplaced project metadata.

    Direct children of an ecosystem are catalog candidates, including projects
    that accidentally omit ``mod.yml``. Metadata found at any other depth is
    also returned so that malformed nested paths receive a clear shape error
    instead of silently disappearing from validation.
    """
    metadata_dirs: set[str] = set()
    if not os.path.isdir(MODS_ROOT):
        return []

    for directory, child_dirs, filenames in os.walk(MODS_ROOT):
        child_dirs[:] = [name for name in child_dirs if not name.startswith(".")]
        if "mod.yml" in filenames:
            metadata_dirs.add(directory)

    projects = set(metadata_dirs)
    for ecosystem in sorted(os.listdir(MODS_ROOT)):
        ecosystem_dir = os.path.join(MODS_ROOT, ecosystem)
        if not os.path.isdir(ecosystem_dir) or ecosystem.startswith("."):
            continue
        for project_slug in sorted(os.listdir(ecosystem_dir)):
            project_dir = os.path.join(ecosystem_dir, project_slug)
            if not os.path.isdir(project_dir) or project_slug.startswith("."):
                continue

            # A container with project metadata further below is not itself a
            # project. The metadata directory will receive the precise shape
            # error; ordinary flat directories still get checked for missing
            # required files.
            prefix = project_dir + os.sep
            has_nested_metadata = any(
                metadata_dir.startswith(prefix) for metadata_dir in metadata_dirs
            )
            if project_dir in metadata_dirs or not has_nested_metadata:
                projects.add(project_dir)
    return sorted(projects)


def local_license_files(project_dir: str) -> list[str]:
    """Return conventional license files stored at the project root."""
    return sorted(
        entry
        for entry in os.listdir(project_dir)
        if (entry.lower() == "license" or entry.lower().startswith("license."))
        and os.path.isfile(os.path.join(project_dir, entry))
    )


def license_file_has_text(project_dir: str, filename: str) -> bool:
    """A hosted project's license file must contain actual disclosed terms."""
    try:
        with open(os.path.join(project_dir, filename), encoding="utf-8") as fh:
            return bool(fh.read().strip())
    except (OSError, UnicodeError):
        return False


def valid_http_url(value: str) -> bool:
    """Require a complete HTTP(S) URL, not merely a matching scheme prefix."""
    try:
        parsed = urlparse(value)
        _ = parsed.port  # malformed ports raise ValueError
    except ValueError:
        return False
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.hostname)
        and not any(character.isspace() for character in value)
    )


def local_image_error(project_dir: str, image: str) -> str | None:
    """Return why a declared local image is invalid, or None when usable."""
    if os.path.isabs(image):
        return "local image paths must be relative"
    normalized = os.path.normpath(image)
    parts = normalized.split(os.sep)
    if not parts or parts[0] != "img":
        return "local image paths must be inside img/"
    if os.path.splitext(normalized)[1].lower() not in IMG_EXTS:
        return f"unsupported image extension (expected one of {sorted(IMG_EXTS)})"
    project_root = os.path.realpath(project_dir)
    resolved = os.path.realpath(os.path.join(project_dir, normalized))
    try:
        if os.path.commonpath([project_root, resolved]) != project_root:
            return "local image paths must stay inside the project directory"
    except ValueError:
        return "local image path is invalid"
    if not os.path.isfile(resolved):
        return "image not found"
    return None


def lint_mod(mod_dir: str, validator: Draft7Validator) -> list[str]:
    """Lint one project directory against the catalog contract."""
    rel = os.path.relpath(mod_dir, REPO_ROOT)
    errors: list[str] = []

    parts = rel.split(os.sep)
    if len(parts) != 3 or parts[0] != "mods":
        errors.append(f"{rel}: must be exactly mods/<ecosystem>/<project_slug>/")
        return errors
    _, product, _project_slug = parts

    if any(" " in p for p in parts):
        errors.append(f"{rel}: no spaces allowed in catalog path components")

    # Required files
    mod_yml = os.path.join(mod_dir, "mod.yml")
    if not os.path.isfile(mod_yml):
        errors.append(f"{rel}: missing mod.yml")
    if not os.path.isfile(os.path.join(mod_dir, "README.md")):
        errors.append(f"{rel}: missing README.md")

    if not os.path.isfile(mod_yml):
        return errors

    # mod.yml content
    try:
        with open(mod_yml, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        errors.append(f"{rel}/mod.yml: invalid YAML — {exc}")
        return errors

    if not isinstance(data, dict):
        errors.append(f"{rel}/mod.yml: top level must be a mapping")
        return errors

    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        loc = "/".join(str(p) for p in err.path) or "(root)"
        errors.append(f"{rel}/mod.yml: {loc}: {err.message}")

    is_indexed = bool(data.get("source_url"))
    source_url = data.get("source_url")
    if isinstance(source_url, str) and not valid_http_url(source_url):
        errors.append(f"{rel}/mod.yml: source_url: must be a complete HTTP(S) URL")
    declared_license = data.get("license")
    license_files = local_license_files(mod_dir)

    if is_indexed:
        if license_files:
            errors.append(
                f"{rel}: remove the local LICENSE ({', '.join(license_files)}); "
                "indexed project license terms live upstream"
            )
    elif product == "ossm":
        if declared_license not in (None, OSSM_HOSTED_LICENSE):
            errors.append(
                f"{rel}/mod.yml: hosted OSSM projects must declare "
                f"{OSSM_HOSTED_LICENSE}"
            )
        if license_files:
            errors.append(
                f"{rel}: remove the project-local LICENSE "
                f"({', '.join(license_files)}); hosted OSSM files use the "
                "repository's CERN-OHL-S-2.0 license text"
            )
    else:
        if not license_files:
            errors.append(
                f"{rel}: hosted {product} projects must include a project-root "
                "LICENSE (LICENSE, LICENSE.txt, or LICENSE.md) containing the "
                "project's license terms"
            )
        elif not any(
            license_file_has_text(mod_dir, filename) for filename in license_files
        ):
            errors.append(
                f"{rel}: project-root LICENSE must contain the disclosed license terms"
            )

    # Image presence — a declared local img/ file, or a URL for indexed projects.
    imgs = data.get("images", []) or []
    has_url_img = False
    has_local_img = False
    for image in imgs:
        if not isinstance(image, str):
            continue
        if image.startswith(("http://", "https://")):
            if valid_http_url(image):
                has_url_img = True
            else:
                errors.append(
                    f"{rel}/mod.yml: {image}: must be a complete HTTP(S) image URL"
                )
            continue
        image_error = local_image_error(mod_dir, image)
        if image_error is None:
            has_local_img = True
        else:
            errors.append(f"{rel}/mod.yml: {image}: {image_error}")

    if not has_local_img and not (is_indexed and has_url_img):
        errors.append(
            f"{rel}: needs at least one image declared as a local path under img/"
            + (" or an HTTP(S) URL" if is_indexed else "")
        )

    if data.get("product") not in (None,) and data.get("product") != product:
        errors.append(
            f"{rel}/mod.yml: product '{data.get('product')}' != folder '{product}'"
        )
    return errors


def main() -> int:
    if not os.path.exists(SCHEMA_PATH):
        print(f"ERROR: schema not found at {SCHEMA_PATH}", file=sys.stderr)
        return 2
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        validator = Draft7Validator(json.load(fh), format_checker=FormatChecker())

    projects = find_mod_dirs()
    if not projects:
        print("No projects found under mods/ — nothing to lint.")
        return 0

    all_errors: list[str] = []
    for mod_dir in projects:
        errs = lint_mod(mod_dir, validator)
        rel = os.path.relpath(mod_dir, REPO_ROOT)
        if errs:
            all_errors.extend(errs)
        else:
            print(f"OK  {rel}")

    if all_errors:
        print("\nProject catalog lint failed:\n", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        print("\nSee CONTRIBUTING.md for the project standard.", file=sys.stderr)
        return 1

    print("\nAll projects conform to the standard.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
