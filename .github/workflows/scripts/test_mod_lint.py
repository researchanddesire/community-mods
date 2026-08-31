#!/usr/bin/env python3
"""Regression tests for the project catalog linter."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml
from jsonschema import Draft7Validator, FormatChecker

import mod_lint


class ModLintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)
        with open(mod_lint.SCHEMA_PATH, encoding="utf-8") as fh:
            self.validator = Draft7Validator(
                json.load(fh), format_checker=FormatChecker()
            )
        self.root_patch = mock.patch.object(
            mod_lint, "REPO_ROOT", str(self.repo_root)
        )
        self.mods_patch = mock.patch.object(
            mod_lint, "MODS_ROOT", str(self.repo_root / "mods")
        )
        self.root_patch.start()
        self.mods_patch.start()

    def tearDown(self) -> None:
        self.mods_patch.stop()
        self.root_patch.stop()
        self.temp_dir.cleanup()

    @staticmethod
    def metadata(product: str = "ossm", author: str = "alice") -> dict:
        return {
            "title": "Example Project",
            "author": author,
            "product": product,
            "description": "A regression-test project.",
            "mod_version": 1,
            "compatibility": ["Tested configuration"],
            "images": ["img/cover.png"],
            "license": (
                "CERN-OHL-S-2.0" if product == "ossm" else "LicenseRef-Example"
            ),
            "safety": {
                "affects_restraint_release": False,
                "affects_applied_force": False,
                "affects_electrical": False,
                "notes": "No safety-relevant behavior in this fixture.",
            },
        }

    def make_project(
        self,
        *,
        product: str = "ossm",
        author: str = "alice",
        slug: str = "example-project",
        metadata: dict | None = None,
        readme: bool = True,
        image: bool = True,
        license_file: bool = False,
    ) -> Path:
        project_dir = self.repo_root / "mods" / product / author / slug
        project_dir.mkdir(parents=True)
        data = metadata if metadata is not None else self.metadata(product, author)
        (project_dir / "mod.yml").write_text(
            yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
        )
        if readme:
            (project_dir / "README.md").write_text("# Example\n", encoding="utf-8")
        if image:
            image_dir = project_dir / "img"
            image_dir.mkdir()
            (image_dir / "cover.png").write_bytes(b"fixture")
        if license_file:
            (project_dir / "LICENSE").write_text(
                "Example project license terms.\n", encoding="utf-8"
            )
        return project_dir

    def lint(self, project_dir: Path) -> list[str]:
        return mod_lint.lint_mod(str(project_dir), self.validator)

    def test_indexed_project_accepts_upstream_license_and_image_url(self) -> None:
        data = self.metadata()
        data.update(
            source_url="https://example.com/alice/example-project",
            license="MIT",
            images=["https://example.com/project-banner.png"],
        )
        project_dir = self.make_project(metadata=data, image=False)

        self.assertEqual([], self.lint(project_dir))

    def test_indexed_project_forbids_local_license(self) -> None:
        data = self.metadata()
        data.update(
            source_url="https://example.com/alice/example-project",
            license="MIT",
            images=["https://example.com/project-banner.png"],
        )
        errors = self.lint(
            self.make_project(metadata=data, image=False, license_file=True)
        )

        self.assertTrue(any("must not include a local LICENSE" in e for e in errors))

    def test_indexed_project_requires_complete_source_and_image_urls(self) -> None:
        malformed_source = self.metadata()
        malformed_source.update(
            source_url="https://",
            license="MIT",
            images=["https://example.com/project-banner.png"],
        )
        source_errors = self.lint(
            self.make_project(metadata=malformed_source, image=False)
        )
        self.assertTrue(any("complete HTTP(S) URL" in e for e in source_errors))

        malformed_image = self.metadata()
        malformed_image.update(
            source_url="https://example.com/alice/example-project",
            license="MIT",
            images=["https://"],
        )
        image_errors = self.lint(
            self.make_project(
                slug="malformed-image-url", metadata=malformed_image, image=False
            )
        )
        self.assertTrue(any("complete HTTP(S) image URL" in e for e in image_errors))

    def test_every_project_requires_a_declared_license(self) -> None:
        data = self.metadata()
        del data["license"]
        errors = self.lint(self.make_project(metadata=data))

        self.assertTrue(any("'license' is a required property" in e for e in errors))

    def test_license_is_a_registered_spdx_id_or_license_ref(self) -> None:
        invalid_data = self.metadata(product="dtt")
        invalid_data["license"] = "Totally-Made-Up"
        errors = self.lint(
            self.make_project(
                product="dtt",
                slug="invalid-license",
                metadata=invalid_data,
                license_file=True,
            )
        )
        self.assertTrue(any("recognized SPDX identifier" in e for e in errors))

        valid_data = self.metadata(product="radr")
        valid_data["license"] = "LicenseRef-Custom-Terms"
        project = self.make_project(
            product="radr",
            slug="custom-license",
            metadata=valid_data,
            license_file=True,
        )
        self.assertEqual([], self.lint(project))

    def test_hosted_ossm_project_requires_exact_license_and_no_local_copy(self) -> None:
        valid_project = self.make_project(slug="valid")
        self.assertEqual([], self.lint(valid_project))

        wrong_data = self.metadata()
        wrong_data["license"] = "MIT"
        wrong_errors = self.lint(
            self.make_project(slug="wrong-license", metadata=wrong_data)
        )
        self.assertTrue(
            any(mod_lint.OSSM_HOSTED_LICENSE in error for error in wrong_errors)
        )

        local_errors = self.lint(
            self.make_project(slug="local-license", license_file=True)
        )
        self.assertTrue(
            any("must not include a project-local LICENSE" in e for e in local_errors)
        )

    def test_other_hosted_project_requires_matching_local_license_text(self) -> None:
        valid_project = self.make_project(product="dtt", license_file=True)
        self.assertEqual([], self.lint(valid_project))

        errors = self.lint(self.make_project(product="radr", license_file=False))
        self.assertTrue(any("must include a project-root LICENSE" in e for e in errors))

        empty_license = self.make_project(
            product="lockbox", slug="empty-license", license_file=True
        )
        (empty_license / "LICENSE").write_text("  \n", encoding="utf-8")
        empty_errors = self.lint(empty_license)
        self.assertTrue(
            any("must contain the disclosed license terms" in e for e in empty_errors)
        )

    def test_hosted_project_needs_no_cad_or_source_but_does_need_an_image(self) -> None:
        project_dir = self.make_project(slug="no-cad-or-source")
        self.assertFalse((project_dir / "cad").exists())
        self.assertFalse((project_dir / "src").exists())
        self.assertEqual([], self.lint(project_dir))

        errors = self.lint(self.make_project(slug="missing-image", image=False))
        self.assertTrue(any("needs at least one image" in e for e in errors))

        remote_only_data = self.metadata()
        remote_only_data["images"] = ["https://example.com/remote-only.png"]
        remote_only_errors = self.lint(
            self.make_project(slug="remote-only", metadata=remote_only_data)
        )
        self.assertTrue(
            any("needs at least one image" in e for e in remote_only_errors)
        )

    def test_readme_and_complete_safety_disclosure_remain_required(self) -> None:
        missing_readme = self.lint(self.make_project(slug="no-readme", readme=False))
        self.assertTrue(any("missing README.md" in e for e in missing_readme))

        data = self.metadata()
        del data["safety"]["notes"]
        safety_errors = self.lint(
            self.make_project(slug="incomplete-safety", metadata=data)
        )
        self.assertTrue(any("'notes' is a required property" in e for e in safety_errors))

        whitespace_data = self.metadata()
        whitespace_data["safety"]["notes"] = "   \n"
        whitespace_errors = self.lint(
            self.make_project(slug="blank-safety", metadata=whitespace_data)
        )
        self.assertTrue(any("does not match" in e for e in whitespace_errors))

    def test_author_and_ecosystem_must_match_their_folders(self) -> None:
        data = self.metadata(product="ossm", author="different-author")
        data["product"] = "dtt"
        errors = self.lint(self.make_project(metadata=data))

        self.assertTrue(any("product 'dtt' != folder 'ossm'" in e for e in errors))
        self.assertTrue(
            any("author 'different-author' != folder 'alice'" in e for e in errors)
        )

    def test_ecosystem_enum_and_folder_shape_remain_enforced(self) -> None:
        data = self.metadata(product="unknown")
        invalid_project = self.make_project(
            product="unknown", metadata=data, license_file=True
        )
        self.assertIn(str(invalid_project), mod_lint.find_mod_dirs())
        ecosystem_errors = self.lint(invalid_project)
        self.assertTrue(any("is not one of" in e for e in ecosystem_errors))

        shallow_dir = self.repo_root / "mods" / "ossm" / "alice"
        shape_errors = self.lint(shallow_dir)
        self.assertTrue(any("must be exactly mods/" in e for e in shape_errors))

        whitespace_errors = self.lint(
            self.make_project(author="alice smith", slug="whitespace")
        )
        self.assertTrue(any("no spaces allowed" in e for e in whitespace_errors))

    def test_discovery_includes_malformed_shallow_metadata(self) -> None:
        shallow_dir = self.repo_root / "mods" / "ossm" / "alice"
        shallow_dir.mkdir(parents=True)
        (shallow_dir / "mod.yml").write_text(
            yaml.safe_dump(self.metadata(), sort_keys=False), encoding="utf-8"
        )

        self.assertIn(str(shallow_dir), mod_lint.find_mod_dirs())
        self.assertTrue(
            any("must be exactly mods/" in error for error in self.lint(shallow_dir))
        )


if __name__ == "__main__":
    unittest.main()
