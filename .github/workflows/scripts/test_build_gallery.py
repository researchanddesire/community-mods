#!/usr/bin/env python3
"""Regression tests for the generated R+D Project Hub gallery."""

from __future__ import annotations

import re
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import build_gallery


class ProjectHubBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.projects = build_gallery.collect_mods()
        cls.html = build_gallery.render(cls.projects)
        cls.contribution_guidance = Path(
            build_gallery.CONTRIBUTING_PATH
        ).read_text(encoding="utf-8")
        cls.contributing_html = build_gallery.render_contributing(
            cls.contribution_guidance
        )

    def test_catalog_contains_the_four_expected_projects_in_peer_order(self) -> None:
        self.assertEqual(
            [
                "KinkyMakers OSSM",
                "OSSM ALT Edition",
                "OSSM M5 Remote",
                "OSSM Possum",
            ],
            [project["title"] for project in self.projects],
        )

        sources = {project["source_url"] for project in self.projects}
        self.assertIn("https://github.com/KinkyMakers/OSSM-hardware", sources)
        # Add the R+D fork only after it becomes an independently distinct variant.
        self.assertNotIn("https://github.com/researchanddesire/OSSM", sources)
        kinky_makers = self.projects[0]
        self.assertEqual("CERN-OHL-S-2.0", kinky_makers["license"])
        self.assertEqual(
            "https://raw.githubusercontent.com/KinkyMakers/OSSM-hardware/"
            "c1c70c3acef5ff5d891eb2d86b2c2a9e13f6d36c/"
            "assets/readme/ossm-banner.webp",
            kinky_makers["thumb"],
        )
        self.assertTrue(all(project["license"] for project in self.projects))

    def test_active_ecosystem_options_only_include_catalog_values(self) -> None:
        self.assertIn(
            '<select id="ecosystem" aria-label="Filter by ecosystem">', self.html
        )
        self.assertEqual(1, self.html.count('<option value="ossm">OSSM</option>'))
        for inactive in ("lockbox", "dtt", "radr"):
            self.assertNotIn(f'<option value="{inactive}">', self.html)

    def test_ordered_project_tags_are_normalized(self) -> None:
        by_title = {project["title"]: project for project in self.projects}
        self.assertEqual("variant", by_title["KinkyMakers OSSM"]["tags"][0])
        self.assertEqual("variant", by_title["OSSM ALT Edition"]["tags"][0])
        self.assertEqual(
            ["controller", "hardware", "firmware"],
            by_title["OSSM M5 Remote"]["tags"][:3],
        )
        self.assertEqual(
            ["controller", "software"], by_title["OSSM Possum"]["tags"][:2]
        )
        self.assertFalse(
            any("external" in project["tags"] for project in self.projects)
        )

    def test_hosted_sample_references_an_existing_image(self) -> None:
        sample_dir = (
            Path(build_gallery.REPO_ROOT)
            / "mods"
            / "ossm"
            / "SAMPLE_AUTHOR"
            / "sample_mount"
        )
        with (sample_dir / "mod.yml").open(encoding="utf-8") as metadata_file:
            metadata = build_gallery.yaml.safe_load(metadata_file)

        for image_path in metadata["images"]:
            self.assertTrue((sample_dir / image_path).is_file(), image_path)

    def test_project_led_labels_and_filter_behaviors_are_emitted(self) -> None:
        for phrase in (
            "R+D Project Hub",
            "Search projects…",
            "All ecosystems",
            "No projects match.",
            "independently maintained; inclusion is not endorsement, safety certification,",
            "Indexed",
            "Hosted",
            "Project source",
            "Project files",
            "+${all.length - limit} more",
        ):
            self.assertIn(phrase, self.html)

        # Keep the existing search, conjunctive multi-tag filter, link guard,
        # card keyboard activation, modal escape key, and tag clear behavior.
        for behavior in (
            "function baseMatches()",
            "[...selectedTags].every",
            "if (e.target.closest('a')) return",
            "e.key !== 'Enter' && e.key !== ' '",
            "e.key === 'Escape'",
            "selectedTags.clear(); render();",
        ):
            self.assertIn(behavior, self.html)

    def test_gallery_navigation_links_to_contributing_page_relatively(self) -> None:
        # Relative navigation works at both the custom-domain root and the
        # retained GitHub Pages /community-mods/ project path.
        self.assertIn('<a href="./" aria-current="page">Projects</a>', self.html)
        self.assertIn('<a href="contributing/">Contributing</a>', self.html)
        self.assertIn('<a href="contributing/">Contribute a project</a>', self.html)

    def test_contributing_page_is_generated_from_canonical_guidance(self) -> None:
        for phrase in (
            "Two contribution paths — equal in the hub",
            "Indexed project",
            "Hosted project",
            "DCO sign-off",
        ):
            self.assertIn(phrase, self.contributing_html)

        self.assertIn(
            '<link rel="canonical" href="https://mods.researchanddesire.com/contributing/">',
            self.contributing_html,
        )
        self.assertIn(
            '<meta property="og:url" content="https://mods.researchanddesire.com/contributing/">',
            self.contributing_html,
        )
        self.assertIn(
            '<meta name="twitter:card" content="summary_large_image">',
            self.contributing_html,
        )
        self.assertIn(
            '<meta name="twitter:image:alt" content="R+D Project Hub — '
            'community-built projects across R+D-adjacent ecosystems">',
            self.contributing_html,
        )
        self.assertIn(
            '<meta property="og:image:width" content="1200">',
            self.contributing_html,
        )
        self.assertIn('<a href="../">Projects</a>', self.contributing_html)
        self.assertIn(
            "https://github.com/researchanddesire/community-mods/tree/main/"
            "mods/ossm/SAMPLE_AUTHOR/sample_mount",
            self.contributing_html,
        )
        self.assertNotIn("/main//", self.contributing_html)
        self.assertNotIn("legacy", self.contributing_html.casefold())
        self.assertNotIn("R+D product", self.contributing_html)

    def test_runtime_search_tags_and_modal_keyboard_behavior(self) -> None:
        runtime_match = re.search(r"<script>\n(.*)\n</script>", self.html, re.S)
        self.assertIsNotNone(runtime_match)
        runtime = runtime_match.group(1)
        prelude = r"""
function makeElement(initial = {}) {
  return Object.assign({
    value: '', innerHTML: '', hidden: false, dataset: {}, scrollTop: 0,
    offsetHeight: 90, style: {}, handlers: Object.create(null),
    addEventListener(type, handler) {
      (this.handlers[type] ||= []).push(handler);
    }
  }, initial);
}
const elements = {
  grid: makeElement(), modal: makeElement({hidden: true}),
  'modal-content': makeElement(), 'modal-actions': makeElement(),
  q: makeElement(), ecosystem: makeElement(), tags: makeElement(),
  clear: makeElement({hidden: true})
};
const topbarStub = makeElement({offsetHeight: 100});
const document = {
  handlers: Object.create(null),
  documentElement: {style: {setProperty() {}}},
  body: {style: {}},
  getElementById(id) { return elements[id]; },
  querySelector(selector) {
    if (selector === '.topbar') return topbarStub;
    throw new Error(`Unexpected selector: ${selector}`);
  },
  addEventListener(type, handler) {
    (this.handlers[type] ||= []).push(handler);
  }
};
const window = {
  location: {href: 'https://mods.researchanddesire.com/'},
  ResizeObserver: undefined,
  addEventListener() {}
};
globalThis.document = document;
globalThis.window = window;
function emit(target, type, event) {
  for (const handler of target.handlers[type] || []) handler(event);
}
function assert(condition, message) {
  if (!condition) throw new Error(message);
}
function tagClick(tag) {
  emit(elements.tags, 'click', {
    target: {closest(selector) {
      return selector === '.tagbtn' ? {dataset: {tag}} : null;
    }}
  });
}
"""
        assertions = r"""
assert(elements.grid.innerHTML.includes('KinkyMakers OSSM'), 'initial render');
assert(elements.grid.innerHTML.includes('OSSM Possum'), 'initial peer render');

elements.q.value = 'possum';
emit(elements.q, 'input', {});
assert(elements.grid.innerHTML.includes('OSSM Possum'), 'search includes match');
assert(!elements.grid.innerHTML.includes('OSSM ALT Edition'), 'search excludes mismatch');

elements.q.value = '';
emit(elements.q, 'input', {});
elements.ecosystem.value = 'ossm';
emit(elements.ecosystem, 'change', {});
assert(elements.grid.innerHTML.includes('KinkyMakers OSSM'), 'ecosystem filter');

tagClick('controller');
assert(elements.grid.innerHTML.includes('OSSM Possum'), 'controller tag includes Possum');
assert(elements.grid.innerHTML.includes('OSSM M5 Remote'), 'controller tag includes M5');
assert(!elements.grid.innerHTML.includes('OSSM ALT Edition'), 'controller tag excludes variant');
tagClick('hardware');
assert(elements.grid.innerHTML.includes('OSSM M5 Remote'), 'conjunctive tags include M5');
assert(!elements.grid.innerHTML.includes('OSSM Possum'), 'conjunctive tags exclude Possum');
emit(elements.clear, 'click', {});

PROJECTS.push({
  id: 'synthetic-prototype-tag', title: 'Prototype tag project', author: 'tester',
  product: 'ossm', ecosystem_label: 'OSSM', description: '', compatibility: [],
  tags: ['__proto__'], thumb: '', source_url: 'https://example.com/project',
  license: 'MIT', folder: 'https://example.com/project', readme_html: ''
});
render();
assert(elements.tags.innerHTML.includes('data-tag="__proto__"'), 'prototype-like tag');
PROJECTS.pop();
render();

const firstCard = {dataset: {id: PROJECTS[0].id}};
const cardTarget = {closest(selector) {
  if (selector === 'a') return null;
  if (selector === '.card') return firstCard;
  return null;
}};
emit(elements.grid, 'click', {target: cardTarget});
assert(elements.modal.hidden === false, 'card click opens modal');
assert(elements['modal-content'].innerHTML.includes('KinkyMakers OSSM'), 'modal project');
emit(document, 'keydown', {key: 'Escape'});
assert(elements.modal.hidden === true, 'Escape closes modal');

let prevented = false;
emit(elements.grid, 'keydown', {
  key: 'Enter', target: cardTarget, preventDefault() { prevented = true; }
});
assert(prevented && elements.modal.hidden === false, 'Enter opens modal');
emit(document, 'keydown', {key: 'Escape'});

const linkTarget = {closest(selector) {
  if (selector === 'a') return {};
  if (selector === '.card') return firstCard;
  return null;
}};
emit(elements.grid, 'click', {target: linkTarget});
assert(elements.modal.hidden === true, 'inner link does not open modal');
"""
        result = subprocess.run(
            ["node", "-"],
            input=prelude + runtime + assertions,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_outdated_visible_gallery_phrases_are_absent(self) -> None:
        for phrase in (
            "RAD Mod Hub",
            "Search mods",
            "RAD products",
            "No mods match",
        ):
            self.assertNotIn(phrase, self.html)

    def test_canonical_and_social_metadata_are_current(self) -> None:
        self.assertIn(
            '<link rel="canonical" href="https://mods.researchanddesire.com/">',
            self.html,
        )
        self.assertIn(
            '<meta property="og:image" content="https://mods.researchanddesire.com/project-hub-og.png">',
            self.html,
        )
        self.assertIn(
            '<meta name="twitter:card" content="summary_large_image">', self.html
        )
        self.assertIn('<meta property="og:image:width" content="1200">', self.html)
        self.assertIn('<meta property="og:image:height" content="630">', self.html)

        social_bytes = Path(build_gallery.SOCIAL_IMAGE_PATH).read_bytes()
        self.assertEqual(b"\x89PNG\r\n\x1a\n", social_bytes[:8])
        self.assertEqual((1200, 630), struct.unpack(">II", social_bytes[16:24]))

    def test_readme_rendering_rewrites_relative_links_and_sanitizes_html(self) -> None:
        rendered = build_gallery.render_readme(
            "# Example\n\n![local](img/cover.png)\n\n"
            "[notes](docs/notes.md)\n\n"
            "<script>alert('no')</script><img src=x onerror=alert(1)>\n",
            "mods/ossm/alice/example-project",
        )

        self.assertIn(
            "https://raw.githubusercontent.com/researchanddesire/community-mods/"
            "main/mods/ossm/alice/example-project/img/cover.png",
            rendered,
        )
        self.assertIn(
            "https://github.com/researchanddesire/community-mods/blob/main/"
            "mods/ossm/alice/example-project/docs/notes.md",
            rendered,
        )
        self.assertNotIn("<script", rendered)
        self.assertNotIn("onerror", rendered)

    def test_repository_markdown_resolves_parent_and_directory_links(self) -> None:
        rendered = build_gallery.render_repository_markdown(
            "[parent](../README.md) [directory](../other-project/)",
            "mods/ossm/alice/example-project",
        )
        self.assertIn(
            "https://github.com/researchanddesire/community-mods/blob/main/"
            "mods/ossm/alice/README.md",
            rendered,
        )
        self.assertIn(
            "https://github.com/researchanddesire/community-mods/tree/main/"
            "mods/ossm/alice/other-project",
            rendered,
        )

    def test_repository_markdown_escapes_catalog_paths_after_rewriting(self) -> None:
        rendered = build_gallery.render_repository_markdown(
            "[notes](notes.md?x=1&y=2)",
            'mods/ossm/alice/evil"onmouseover="alert(1)',
        )

        self.assertIn(
            "evil&quot;onmouseover=&quot;alert(1)/notes.md?x=1&amp;y=2",
            rendered,
        )
        self.assertNotIn("&amp;amp;", rendered)
        self.assertNotIn(' onmouseover="', rendered)

    def test_main_writes_html_and_social_card_to_the_pages_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            with mock.patch.object(build_gallery, "OUT_DIR", str(output)):
                self.assertEqual(0, build_gallery.main())

            index = output / "index.html"
            contributing = output / "contributing" / "index.html"
            social = output / "project-hub-og.png"
            self.assertTrue(index.is_file())
            self.assertTrue(contributing.is_file())
            self.assertTrue(social.is_file())
            self.assertEqual(self.html, index.read_text(encoding="utf-8"))
            self.assertEqual(
                self.contributing_html,
                contributing.read_text(encoding="utf-8"),
            )
            self.assertEqual(
                Path(build_gallery.SOCIAL_IMAGE_PATH).read_bytes(), social.read_bytes()
            )


if __name__ == "__main__":
    unittest.main()
