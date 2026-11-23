"""Server-rendered social metadata and deployable project-page regressions."""

from __future__ import annotations

import base64
import contextlib
import html
from html.parser import HTMLParser
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from urllib.parse import unquote, urljoin, urlsplit


DEFAULT_SITE = "https://researchanddesire.github.io/community-mods/"
BUILDER = Path(__file__).with_name("build_gallery.py")
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j7n8AAAAASUVORK5CYII="
)


class Head(HTMLParser):
    def __init__(self, document: str) -> None:
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, list[str]] = {}
        self.canonicals: list[str] = []
        self.bases: list[str] = []
        self.title = ""
        self.in_title = False
        self.feed(document.split("</head>", 1)[0])

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "meta":
            name = values.get("property") or values.get("name")
            if name:
                self.meta.setdefault(name, []).append(values.get("content", ""))
        elif tag == "link" and values.get("rel") == "canonical":
            self.canonicals.append(values.get("href", ""))
        elif tag == "base":
            self.bases.append(values.get("href", ""))
        elif tag == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title += data


def load_builder(site_url: str | None = None):
    """Read deployment configuration as a new process import would, in isolation."""
    with mock.patch.dict(os.environ):
        if site_url is None:
            os.environ.pop("SITE_URL", None)
        else:
            os.environ["SITE_URL"] = site_url
        spec = importlib.util.spec_from_file_location("project_preview_builder", BUILDER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module


def project(**overrides) -> dict:
    result = {
        "id": "mods/ossm/example-stand",
        "title": "Example stand",
        "author": "Fixture maintainer",
        "product": "ossm",
        "ecosystem_label": "OSSM",
        "description": "A useful stand.",
        "compatibility": ["OSSM"],
        "tags": ["stand"],
        "thumb": "mods/ossm/example-stand/img/preview.png",
        "source_url": "",
        "license": "CERN-OHL-S-2.0",
        "folder": "https://github.com/example/catalog/tree/main/mods/ossm/example-stand",
        "readme": "https://github.com/example/catalog/blob/main/mods/ossm/example-stand/README.md",
        "readme_html": "<p>Project details.</p>",
        "_local_images": ["mods/ossm/example-stand/img/preview.png"],
    }
    result.update(overrides)
    return result


class ProjectPreviewTests(unittest.TestCase):
    def test_default_deployment_metadata_uses_github_pages(self) -> None:
        builder = load_builder()
        self.assertEqual(DEFAULT_SITE, builder.CANONICAL_URL)
        for document, expected, bases in (
            (builder.render([]), DEFAULT_SITE, ["/community-mods/"]),
            (builder.render_contributing("# Contributing\nDetails."), DEFAULT_SITE + "contributing/", []),
        ):
            with self.subTest(url=expected):
                head = Head(document)
                self.assertEqual([expected], head.canonicals)
                self.assertEqual([expected], head.meta["og:url"])
                self.assertEqual(bases, head.bases)

    def test_project_metadata_is_specific_and_safely_escaped(self) -> None:
        builder = load_builder()
        chosen = project(
            title='Stand "A" & </title><script>alert("title")</script>',
            description='A "quoted" description & <img src=x onerror="alert(1)">.',
        )
        unrelated = project(id="mods/ossm/other-project", title="Other project")
        document = builder.render([unrelated, chosen], project=chosen)
        head = Head(document)
        self.assertIn(chosen["title"], head.title)
        self.assertEqual([chosen["description"]], head.meta["description"])
        self.assertEqual([chosen["description"]], head.meta["og:description"])
        self.assertEqual(head.meta["og:description"], head.meta["twitter:description"])
        self.assertEqual(head.meta["og:title"], head.meta["twitter:title"])
        self.assertEqual(1, len(head.meta["og:title"]))
        self.assertIn(chosen["title"], head.meta["og:title"][0])
        expected_url = DEFAULT_SITE + "projects/ossm/example-stand/"
        self.assertEqual([expected_url], head.canonicals)
        self.assertEqual([expected_url], head.meta["og:url"])
        self.assertEqual(["summary_large_image"], head.meta["twitter:card"])
        raw_head = document.split("</head>", 1)[0]
        self.assertNotIn('<script>alert("title")</script>', raw_head)
        self.assertNotIn('<img src=x onerror="alert(1)">', raw_head)
        self.assertIn(html.escape(chosen["description"], quote=True), raw_head)

    def test_project_route_escapes_each_catalog_segment(self) -> None:
        builder = load_builder()
        chosen = project(id="mods/ossm/café & frame#1")
        route = "projects/ossm/caf%C3%A9%20%26%20frame%231/"
        self.assertEqual(route, builder.project_page_path(chosen))
        head = Head(builder.render([chosen], project=chosen))
        self.assertEqual([DEFAULT_SITE + route], head.canonicals)
        self.assertEqual([DEFAULT_SITE + route], head.meta["og:url"])

    def test_project_images_resolve_local_external_and_fallback_sources(self) -> None:
        builder = load_builder()
        external = "https://images.example.org/stand.png?width=1200&version=2"
        for thumbnail, expected in (
            ("mods/ossm/example-stand/img/preview.png", DEFAULT_SITE + "mods/ossm/example-stand/img/preview.png"),
            (external, external),
            ("", builder.SOCIAL_IMAGE_URL),
        ):
            with self.subTest(thumbnail=thumbnail):
                chosen = project(thumb=thumbnail)
                head = Head(builder.render([chosen], project=chosen))
                self.assertEqual([expected], head.meta["og:image"])
                self.assertEqual([expected], head.meta["twitter:image"])
                self.assertEqual(["summary_large_image"], head.meta["twitter:card"])

    def test_site_url_override_updates_all_page_urls_and_local_images(self) -> None:
        for configured in ("https://projects.example.org", "https://projects.example.org/hub/"):
            with self.subTest(site_url=configured):
                builder = load_builder(configured)
                expected_root = configured.rstrip("/") + "/"
                self.assertEqual(expected_root, builder.CANONICAL_URL)
                chosen = project()
                pages = (
                    (builder.render([]), expected_root, [urlsplit(expected_root).path]),
                    (builder.render_contributing("# Contributing"), expected_root + "contributing/", []),
                    (builder.render([chosen], project=chosen), expected_root + "projects/ossm/example-stand/", [urlsplit(expected_root).path]),
                )
                for document, canonical, bases in pages:
                    head = Head(document)
                    self.assertEqual([canonical], head.canonicals)
                    self.assertEqual([canonical], head.meta["og:url"])
                    self.assertEqual(bases, head.bases)
                    self.assertTrue(head.meta["og:image"][0].startswith(expected_root))
                head = Head(pages[-1][0])
                self.assertEqual([expected_root + chosen["thumb"]], head.meta["og:image"])

    def test_build_emits_share_pages_whose_images_exist_in_the_artifact(self) -> None:
        builder = load_builder()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "site"
            catalog = root / "mods"
            contribution = root / "CONTRIBUTING.md"
            contribution.write_text("# Contributing\nProject guidance.", encoding="utf-8")
            for slug, image in (
                ("local-project", "img/preview.png"),
                ("missing-project", "img/not-present.png"),
                ("indexed-project", "https://images.example.org/upstream.png"),
            ):
                folder = catalog / "ossm" / slug
                folder.mkdir(parents=True)
                (folder / "mod.yml").write_text(builder.yaml.safe_dump({
                    "title": slug.replace("-", " ").title(),
                    "author": "Fixture maintainer", "product": "ossm",
                    "description": "Description for " + slug,
                    "license": "CERN-OHL-S-2.0", "images": [image],
                }), encoding="utf-8")
                (folder / "README.md").write_text("# Project\nDetails.", encoding="utf-8")
            local_image = catalog / "ossm/local-project/img/preview.png"
            local_image.parent.mkdir()
            local_image.write_bytes(PNG)
            with (
                mock.patch.object(builder, "REPO_ROOT", str(root)),
                mock.patch.object(builder, "MODS_ROOT", str(catalog)),
                mock.patch.object(builder, "OUT_DIR", str(output)),
                mock.patch.object(builder, "CONTRIBUTING_PATH", str(contribution)),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(0, builder.main())

            self.assertTrue((output / "index.html").is_file())
            self.assertTrue((output / "contributing/index.html").is_file())
            for slug in ("local-project", "missing-project", "indexed-project"):
                route = "projects/ossm/" + slug + "/"
                page = output / route / "index.html"
                self.assertTrue(page.is_file(), str(page))
                head = Head(page.read_text(encoding="utf-8"))
                self.assertEqual([DEFAULT_SITE + route], head.canonicals)
                self.assertEqual(["Description for " + slug], head.meta["og:description"])
                self.assertEqual(head.meta["og:image"], head.meta["twitter:image"])
                if slug == "indexed-project":
                    self.assertEqual(["https://images.example.org/upstream.png"], head.meta["og:image"])
                    continue
                image_url = head.meta["og:image"][0]
                expected = (DEFAULT_SITE + "mods/ossm/local-project/img/preview.png"
                            if slug == "local-project" else builder.SOCIAL_IMAGE_URL)
                self.assertEqual(expected, image_url)
                image_path = unquote(image_url.removeprefix(DEFAULT_SITE))
                self.assertTrue((output / image_path).is_file(), image_url)
                if slug == "local-project":
                    self.assertEqual(PNG, (output / image_path).read_bytes())
                    browser_base = urljoin(DEFAULT_SITE + route, head.bases[0])
                    self.assertEqual(image_url, urljoin(browser_base, image_path))
            self.assertFalse((output / "mods/ossm/missing-project/img/not-present.png").exists())


if __name__ == "__main__":
    unittest.main()
