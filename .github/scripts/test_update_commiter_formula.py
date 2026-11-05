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
    return updater.render_formula(version, sha256)


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
        self.assertIn('bin.install "bin/commiter"', text)
        self.assertIn('libexec.install "libexec/commiter-mlx-helper"', text)
        self.assertIn('libexec.install "libexec/mlx.metallib"', text)
        self.assertIn("url :stable", text)
        self.assertIn('shell_output("#{helper} --smoke-metal")', text)
        self.assertIn('assert_path_exists libexec/"mlx.metallib"', text)
        self.assertIn(
            'The default Ollama backend requires a local Ollama 0.31.2+ instance on loopback.',
            text,
        )

    def test_update(self) -> None:
        self.write_formula("1.0.1", V101_SHA)
        status = updater.update_formula(self.formula, "1.0.2", SHA_B)
        self.assertEqual(status, "updated")
        text = self.formula.read_text(encoding="utf-8")
        self.assertIn(updater.expected_url("1.0.2"), text)
        self.assertIn(SHA_B, text)
        self.assertNotIn(updater.expected_url("1.0.1"), text)
        self.assertNotIn(V101_SHA, text)
        self.assertIn('bin.install "bin/commiter"', text)
        self.assertIn('libexec.install "libexec/commiter-mlx-helper"', text)
        self.assertIn('libexec.install "libexec/mlx.metallib"', text)

    def test_mlx_caveats_on_create_and_upgrade(self) -> None:
        for previous in (None, "2.0.0"):
            with self.subTest(previous=previous):
                formula = Path(self.tmpdir.name) / str(previous) / "commiter.rb"
                if previous is not None:
                    formula.parent.mkdir(parents=True)
                    formula.write_text(formula_text(previous, SHA_A), encoding="utf-8")
                status = updater.update_formula(formula, "3.0.1", SHA_B)
                self.assertEqual(status, "created" if previous is None else "updated")
                text = formula.read_text(encoding="utf-8")
                self.assertIn("Apple Silicon macOS with the MLX backend", text)
                self.assertIn("Legacy Ollama and single-pass planning are no longer supported.", text)
                self.assertIn("/blob/v3.0.1/docs/migrations/harness004.md", text)
                self.assertIn("commiter setup", text)
                self.assertIn("commiter doctor", text)
                self.assertNotIn("The default Ollama backend", text)

    def test_same_version_repairs_legacy_caveats_without_changing_release(self) -> None:
        legacy = updater.CAVEATS_RE.sub(
            lambda _: updater.LEGACY_CAVEATS, formula_text("3.0.1", SHA_A)
        )
        self.formula.parent.mkdir(parents=True)
        self.formula.write_text(legacy, encoding="utf-8")
        self.assertEqual(updater.update_formula(self.formula, "3.0.1", SHA_A), "updated")
        text = self.formula.read_text(encoding="utf-8")
        self.assertEqual(updater.parse_current_formula(text), ("3.0.1", updater.expected_url("3.0.1"), SHA_A))
        self.assertIn("Apple Silicon macOS with the MLX backend", text)
        self.assertEqual(updater.update_formula(self.formula, "3.0.1", SHA_A), "unchanged")

    def test_update_repairs_existing_install_layout(self) -> None:
        legacy = formula_text("1.0.1", V101_SHA).replace(
            '    bin.install "bin/commiter"\n'
            '    libexec.install "libexec/commiter-mlx-helper"\n'
            '    libexec.install "libexec/mlx.metallib"',
            '    bin.install "commiter"',
        )
        self.formula.parent.mkdir(parents=True, exist_ok=True)
        self.formula.write_text(legacy, encoding="utf-8")

        status = updater.update_formula(self.formula, "1.0.2", SHA_B)

        self.assertEqual(status, "updated")
        text = self.formula.read_text(encoding="utf-8")
        self.assertIn('bin.install "bin/commiter"', text)
        self.assertIn('libexec.install "libexec/commiter-mlx-helper"', text)
        self.assertIn('libexec.install "libexec/mlx.metallib"', text)

    def test_update_repairs_existing_caveats(self) -> None:
        legacy = formula_text("1.0.1", V101_SHA).replace(
            '      commiter requires Git and a local LLM backend.\n'
            '      The default Ollama backend requires a local Ollama 0.31.2+ instance on loopback.\n',
            '      commiter requires Git and a local Ollama 0.31.2+ instance on loopback.\n',
        )
        self.formula.parent.mkdir(parents=True, exist_ok=True)
        self.formula.write_text(legacy, encoding="utf-8")

        status = updater.update_formula(self.formula, "1.0.2", SHA_B)

        self.assertEqual(status, "updated")
        text = self.formula.read_text(encoding="utf-8")
        self.assertIn('commiter requires Git and a local LLM backend.', text)
        self.assertIn('The default Ollama backend requires a local Ollama 0.31.2+ instance on loopback.', text)
        self.assertNotIn('commiter requires Git and a local Ollama 0.31.2+ instance on loopback.', text)

    def test_update_repairs_existing_helper_smoke_test(self) -> None:
        legacy = updater.TEST_RE.sub(
            lambda _: '  test do\n'
            '    assert_match version.to_s, shell_output("#{bin}/commiter version")\n'
            '  end',
            formula_text("1.0.1", V101_SHA),
        )
        self.formula.parent.mkdir(parents=True, exist_ok=True)
        self.formula.write_text(legacy, encoding="utf-8")

        status = updater.update_formula(self.formula, "1.0.2", SHA_B)

        self.assertEqual(status, "updated")
        text = self.formula.read_text(encoding="utf-8")
        self.assertIn('assert_equal "metal_ok\\n", shell_output("#{helper} --smoke-metal")', text)
        self.assertIn('assert_path_exists libexec/"mlx.metallib"', text)

    def test_duplicate_install_stanza(self) -> None:
        text = formula_text("1.0.1", V101_SHA).replace(
            "  def caveats\n",
            '  def install\n    bin.install "commiter"\n  end\n\n  def caveats\n',
        )
        self.formula.parent.mkdir(parents=True, exist_ok=True)
        self.formula.write_text(text, encoding="utf-8")

        with self.assertRaisesRegex(updater.FormulaError, "exactly one install stanza"):
            updater.update_formula(self.formula, "1.0.2", SHA_B)
        self.assertEqual(self.formula.read_text(encoding="utf-8"), text)

    def test_duplicate_test_stanza(self) -> None:
        text = formula_text("1.0.1", V101_SHA).replace(
            "  test do\n",
            '  test do\n    assert true\n  end\n\n  test do\n',
        )
        self.formula.parent.mkdir(parents=True, exist_ok=True)
        self.formula.write_text(text, encoding="utf-8")

        with self.assertRaisesRegex(updater.FormulaError, "exactly one test stanza"):
            updater.update_formula(self.formula, "1.0.2", SHA_B)
        self.assertEqual(self.formula.read_text(encoding="utf-8"), text)

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
