#!/usr/bin/env python3
"""Validate every mods/<product>/<author>/<mod_name>/ against the RAD mod standard.

Schema source of truth: .github/workflows/scripts/mod.schema.json (canonical
in this repo — the mod standard has a single consumer, so it is not vendored
from dev-docs the way the cross-product BOM schema is).
See CONTRIBUTING.md and https://dev.researchanddesire.com/meta/community-mods/.

Checks (structure, not taste):
  - folder depth is exactly mods/<product>/<author>/<mod_name>/
  - no whitespace in any path component under mods/
  - mod.yml + README.md present
  - at least one CAD file in cad/ (a .step is required)
  - at least one image in img/
  - mod.yml validates against mod.schema.json (JSON Schema draft-07)
  - mod.yml.product matches the product folder; author matches the author folder
  - every path in mod.yml.images exists
  - no rogue per-mod LICENSE file (license is fixed by the root path-map)
"""

from __future__ import annotations

import json
import os
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2)

try:
    from jsonschema import Draft7Validator
except ImportError:
    print("ERROR: jsonschema is required (pip install jsonschema)", file=sys.stderr)
    raise SystemExit(2)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
SCHEMA_PATH = os.path.join(SCRIPT_DIR, "mod.schema.json")
MODS_ROOT = os.path.join(REPO_ROOT, "mods")
PRODUCTS = {"lockbox", "dtt", "ossm", "radr"}
SKIP_AUTHORS = {"SAMPLE_AUTHOR"}  # template folder, not a real submission
CAD_EXTS = {".step", ".stp", ".f3d", ".f3z", ".scad", ".obj"}
IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def has_file_with_ext(directory: str, exts: set[str]) -> bool:
    if not os.path.isdir(directory):
        return False
    for entry in os.listdir(directory):
        if os.path.splitext(entry)[1].lower() in exts:
            return True
    return False


def find_mod_dirs() -> list[str]:
    """A mod dir is mods/<product>/<author>/<mod_name>/."""
    mods: list[str] = []
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
                if os.path.isdir(mdir) and not mod.startswith("."):
                    mods.append(mdir)
    return mods


def lint_mod(mod_dir: str, validator: Draft7Validator) -> list[str]:
    rel = os.path.relpath(mod_dir, REPO_ROOT)
    errors: list[str] = []

    parts = rel.split(os.sep)
    if len(parts) != 4:
        errors.append(f"{rel}: must be exactly mods/<product>/<author>/<mod_name>/")
        return errors
    _, product, author, _mod = parts

    if any(" " in p for p in parts):
        errors.append(f"{rel}: no whitespace allowed in path components")

    # Required files
    mod_yml = os.path.join(mod_dir, "mod.yml")
    if not os.path.isfile(mod_yml):
        errors.append(f"{rel}: missing mod.yml")
    if not os.path.isfile(os.path.join(mod_dir, "README.md")):
        errors.append(f"{rel}: missing README.md")
    if os.path.isfile(os.path.join(mod_dir, "LICENSE")) or os.path.isfile(
        os.path.join(mod_dir, "LICENSE.txt")
    ):
        errors.append(f"{rel}: remove per-mod LICENSE — license is fixed by the root path-map")

    # CAD + image presence
    if not has_file_with_ext(os.path.join(mod_dir, "cad"), CAD_EXTS):
        errors.append(f"{rel}: cad/ must contain at least one CAD file (.step required)")
    elif not has_file_with_ext(os.path.join(mod_dir, "cad"), {".step", ".stp"}):
        errors.append(f"{rel}: cad/ must include a STEP (.step) file (open format)")
    if not has_file_with_ext(os.path.join(mod_dir, "img"), IMG_EXTS):
        errors.append(f"{rel}: img/ must contain at least one image")

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

    if data.get("product") not in (None,) and data.get("product") != product:
        errors.append(
            f"{rel}/mod.yml: product '{data.get('product')}' != folder '{product}'"
        )
    if data.get("author") not in (None,) and data.get("author") != author:
        errors.append(
            f"{rel}/mod.yml: author '{data.get('author')}' != folder '{author}'"
        )

    for img in data.get("images", []) or []:
        if isinstance(img, str) and not os.path.isfile(os.path.join(mod_dir, img)):
            errors.append(f"{rel}/mod.yml: image not found: {img}")

    return errors


def main() -> int:
    if not os.path.exists(SCHEMA_PATH):
        print(f"ERROR: schema not found at {SCHEMA_PATH}", file=sys.stderr)
        return 2
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        validator = Draft7Validator(json.load(fh))

    mods = find_mod_dirs()
    if not mods:
        print("No mods found under mods/ — nothing to lint.")
        return 0

    all_errors: list[str] = []
    for mod_dir in mods:
        errs = lint_mod(mod_dir, validator)
        rel = os.path.relpath(mod_dir, REPO_ROOT)
        if errs:
            all_errors.extend(errs)
        else:
            print(f"OK  {rel}")

    if all_errors:
        print("\nMod lint failed:\n", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        print("\nSee CONTRIBUTING.md for the mod standard.", file=sys.stderr)
        return 1

    print("\nAll mods conform to the standard.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
