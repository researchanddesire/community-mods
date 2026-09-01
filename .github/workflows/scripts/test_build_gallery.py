#!/usr/bin/env python3
"""Regression tests for the generated R+D Project Hub gallery."""

from __future__ import annotations

import base64
import hashlib
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
            "independently maintained and licensed by its",
            "inclusion is not endorsement, safety certification, or warranty",
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

    def test_real_site_uses_the_approved_brand_and_hero(self) -> None:
        self.assertIn(
            '<h1 id="hero-title">Open-source sex tech.</h1>', self.html
        )
        self.assertIn(
            "Projects and tools, maintained by the people who make them.",
            self.html,
        )
        for rendered in (self.html, self.contributing_html):
            head = rendered.split("</head>", 1)[0]
            header_match = re.search(r"<header[^>]*>.*?</header>", rendered, re.S)
            self.assertIsNotNone(header_match)
            header = header_match.group(0)
            self.assertIn("<strong>Research and Desire</strong>", header)
            self.assertIn("<small>Project Hub</small>", header)
            self.assertIn('<span class="logo" aria-hidden="true">', header)
            self.assertIn(build_gallery.logo_data_uri(), head)
            self.assertNotIn('class="km-ack"', header)
            self.assertNotIn('class="km-logo"', header)
            self.assertNotIn("No ranking. No house version.", rendered)

        logo_bytes = Path(build_gallery.LOGO_PATH).read_bytes()
        self.assertEqual(b"\x89PNG\r\n\x1a\n", logo_bytes[:8])
        self.assertEqual((1024, 1024), struct.unpack(">II", logo_bytes[16:24]))

    def test_kinkymakers_acknowledgment_is_one_quiet_final_footer_row(self) -> None:
        expected = (
            "With thanks to <strong>KinkyMakers</strong> — the open-source sex-tech "
            "community Research and Desire grew out of."
        )
        for rendered in (self.html, self.contributing_html):
            normalized = re.sub(r"\s+", " ", rendered)
            self.assertEqual(1, rendered.count('class="km-ack"'))
            self.assertEqual(1, rendered.count('class="km-logo"'))
            self.assertIn(build_gallery.kinkymakers_logo_data_uri(), rendered)
            self.assertIn(expected, normalized)
            self.assertGreater(rendered.index('class="km-ack"'), rendered.index("<footer>"))
            self.assertLess(rendered.index('class="km-ack"'), rendered.index("</footer>"))
            self.assertNotIn("KinkyMakers Discord", rendered)

        svg = Path(build_gallery.KINKYMAKERS_LOGO_PATH).read_text(encoding="utf-8")
        embedded = re.search(r"data:image/png;base64,([^\"]+)", svg)
        self.assertIsNotNone(embedded)
        logo_bytes = base64.b64decode(embedded.group(1))
        self.assertEqual(b"\x89PNG\r\n\x1a\n", logo_bytes[:8])
        self.assertEqual((199, 200), struct.unpack(">II", logo_bytes[16:24]))
        self.assertEqual(
            "dabe4e38e910ae2649368c11ce06f63db82c7e9c34fde7e349b78cbf656ab642",
            hashlib.sha256(logo_bytes).hexdigest(),
        )

    def test_gallery_navigation_links_to_contributing_page_relatively(self) -> None:
        # Relative navigation works at both the custom-domain root and the
        # retained GitHub Pages /community-mods/ project path.
        self.assertIn('<a href="./" aria-current="page">Projects</a>', self.html)
        self.assertIn('<a href="contributing/">Contributing</a>', self.html)
        self.assertIn('<a href="contributing/">Contribute a project</a>', self.html)
        self.assertIn('<a href="../">Projects</a>', self.contributing_html)
        self.assertIn(
            '<a href="./" aria-current="page">Contributing</a>',
            self.contributing_html,
        )

    def test_contributing_page_is_generated_from_canonical_guidance(self) -> None:
        for phrase in (
            "Two contribution paths — equal in the hub",
            "Indexed project",
            "Hosted project",
            "Open the pull request",
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
            'open-source sex tech projects and tools">',
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
        self.assertNotIn("SPDX", self.contribution_guidance)
        self.assertNotIn("DCO", self.contribution_guidance)
        self.assertNotIn("Signed-off-by", self.contribution_guidance)
        self.assertNotIn("forbidden", self.contribution_guidance.casefold())
        self.assertIn(
            "Hosted OSSM project files are already covered by the repository license.",
            self.contribution_guidance,
        )

    def test_project_card_modal_shell_remains_in_the_real_gallery(self) -> None:
        for fragment in (
            '<div class="modal" id="modal" hidden>',
            'role="dialog"',
            'id="modal-actions"',
            'id="modal-content"',
            'id="q"',
            'id="ecosystem"',
            'id="tags"',
            'id="clear"',
            ".modal[hidden] { display:none; }",
        ):
            self.assertIn(fragment, self.html)

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
    },
    focus() {
      document.activeElement = this;
      this.focusCalls = (this.focusCalls || 0) + 1;
    }
  }, initial);
}
const modalBackButton = makeElement();
const modalEndLink = makeElement();
const elements = {
  grid: makeElement(), modal: makeElement({
    hidden: true,
    querySelector(selector) {
      return selector === '.modal-back' ? modalBackButton : null;
    },
    querySelectorAll() { return [modalBackButton, modalEndLink]; }
  }),
  'modal-content': makeElement(), 'modal-actions': makeElement(),
  q: makeElement(), ecosystem: makeElement(), tags: makeElement(),
  clear: makeElement({hidden: true})
};
const topbarStub = makeElement({offsetHeight: 100});
const document = {
  handlers: Object.create(null),
  activeElement: null,
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
assert(elements.grid.innerHTML.includes('class="card" data-id='), 'card identity');
assert(elements.grid.innerHTML.includes('role="button" tabindex="0"'), 'card keyboard semantics');

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

const firstCard = {
  dataset: {id: PROJECTS[0].id},
  focus() { document.activeElement = this; this.focusCalls = (this.focusCalls || 0) + 1; }
};
const cardTarget = {closest(selector) {
  if (selector === 'a') return null;
  if (selector === '.card') return firstCard;
  return null;
}};
emit(elements.grid, 'click', {target: cardTarget});
assert(elements.modal.hidden === false, 'card click opens modal');
assert(document.activeElement === modalBackButton, 'opening focuses modal back button');
assert(elements['modal-content'].innerHTML.includes('KinkyMakers OSSM'), 'modal project');
assert(elements['modal-content'].innerHTML.includes('class="readme"'), 'modal README body');
assert(elements['modal-actions'].innerHTML.includes('Project source'), 'modal project action');
emit(document, 'keydown', {key: 'Escape'});
assert(elements.modal.hidden === true, 'Escape closes modal');
assert(document.body.style.overflow === '', 'Escape restores body scroll');
assert(document.activeElement === firstCard, 'Escape restores card focus');

let prevented = false;
emit(elements.grid, 'keydown', {
  key: 'Enter', target: cardTarget, preventDefault() { prevented = true; }
});
assert(prevented && elements.modal.hidden === false, 'Enter opens modal');
emit(document, 'keydown', {key: 'Escape'});
assert(document.activeElement === firstCard, 'keyboard close restores card focus');

prevented = false;
emit(elements.grid, 'keydown', {
  key: ' ', target: cardTarget, preventDefault() { prevented = true; }
});
assert(prevented && elements.modal.hidden === false, 'Space opens modal');
let tabPrevented = false;
emit(elements.modal, 'keydown', {
  key: 'Tab', shiftKey: true, preventDefault() { tabPrevented = true; }
});
assert(tabPrevented && document.activeElement === modalEndLink, 'Shift+Tab wraps to modal end');
tabPrevented = false;
emit(elements.modal, 'keydown', {
  key: 'Tab', shiftKey: false, preventDefault() { tabPrevented = true; }
});
assert(tabPrevented && document.activeElement === modalBackButton, 'Tab wraps to modal start');
emit(elements.modal, 'click', {target: {closest(selector) {
  return selector === '[data-close]' ? {} : null;
}}});
assert(elements.modal.hidden === true, 'backdrop or back button closes modal');
assert(document.body.style.overflow === '', 'close restores body scroll');
assert(document.activeElement === firstCard, 'pointer close restores card focus');

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
