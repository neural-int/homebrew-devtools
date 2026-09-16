#!/usr/bin/env python3
"""Tests for update_commiter_formula.py."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import update_commiter_formula as updater

SHA_A = "a" * 64
SHA_B = "b" * 64
V101_SHA = "eeecad933fa79db28e69d7c494142337365ccfad255faa754406e51b682b595e"


def formula_text(version: str, sha256: str) -> str:
    return updater.FORMULA_TEMPLATE.format(
        homepage=updater.HOMEPAGE,
        url=updater.expected_url(version),
        sha256=sha256,
    )


class UpdateCommiterFormulaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.formula = Path(self.tmpdir.name) / "Formula" / "commiter.rb"

    def write_formula(self, version: str, sha256: str) -> None:
        self.formula.parent.mkdir(parents=True, exist_ok=True)
        self.formula.write_text(formula_text(version, sha256), encoding="utf-8")

    def test_create(self) -> None:
        status = updater.update_formula(self.formula, "1.0.0", SHA_A)
        self.assertEqual(status, "created")
        text = self.formula.read_text(encoding="utf-8")
        self.assertIn(updater.expected_url("1.0.0"), text)
        self.assertIn(SHA_A, text)
        self.assertIn("url :stable", text)

    def test_update(self) -> None:
        self.write_formula("1.0.1", V101_SHA)
        status = updater.update_formula(self.formula, "1.0.2", SHA_B)
        self.assertEqual(status, "updated")
        text = self.formula.read_text(encoding="utf-8")
        self.assertIn(updater.expected_url("1.0.2"), text)
        self.assertIn(SHA_B, text)
        self.assertNotIn(updater.expected_url("1.0.1"), text)
        self.assertNotIn(V101_SHA, text)

    def test_numeric_patch_update(self) -> None:
        self.write_formula("1.0.9", SHA_A)
        status = updater.update_formula(self.formula, "1.0.10", SHA_B)
        self.assertEqual(status, "updated")

    def test_unchanged(self) -> None:
        self.write_formula("1.0.1", V101_SHA)
        before = self.formula.read_text(encoding="utf-8")
        status = updater.update_formula(
            self.formula,
            "1.0.1",
            V101_SHA.upper(),
            updater.expected_url("1.0.1"),
        )
        self.assertEqual(status, "unchanged")
        self.assertEqual(self.formula.read_text(encoding="utf-8"), before)

    def test_malformed_sha(self) -> None:
        with self.assertRaisesRegex(updater.FormulaError, "64-character hex digest"):
            updater.update_formula(self.formula, "1.0.1", "abc123")
        self.assertFalse(self.formula.exists())

    def test_url_mismatch(self) -> None:
        with self.assertRaisesRegex(updater.FormulaError, r"url must be "):
            updater.update_formula(
                self.formula,
                "1.0.1",
                SHA_A,
                "https://example.invalid/commiter.zip",
            )

    def test_duplicate_url_sha(self) -> None:
        self.formula.parent.mkdir(parents=True, exist_ok=True)
        self.formula.write_text(
            formula_text("1.0.1", SHA_A) + formula_text("1.0.0", SHA_B),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(updater.FormulaError, "exactly one url and sha256"):
            updater.update_formula(self.formula, "1.0.2", SHA_B)

    def test_downgrade(self) -> None:
        self.write_formula("1.0.1", V101_SHA)
        before = self.formula.read_text(encoding="utf-8")
        with self.assertRaisesRegex(
            updater.FormulaError,
            r"refusing to downgrade commiter from 1.0.1 to 1.0.0",
        ):
            updater.update_formula(self.formula, "1.0.0", SHA_A)
        self.assertEqual(self.formula.read_text(encoding="utf-8"), before)

    def test_same_version_sha_mismatch(self) -> None:
        self.write_formula("1.0.1", V101_SHA)
        before = self.formula.read_text(encoding="utf-8")
        with self.assertRaisesRegex(
            updater.FormulaError,
            r"refusing to change url/sha256 for commiter 1.0.1",
        ):
            updater.update_formula(self.formula, "1.0.1", SHA_A)
        self.assertEqual(self.formula.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
