#!/usr/bin/env python3
"""Create or update Formula/commiter.rb from a published GitHub Release."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FORMULA_PATH = Path("Formula/commiter.rb")
HOMEPAGE = "https://github.com/neural-int/commiter-cli"
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA256_RE = re.compile(r"^[a-fA-F0-9]{64}$")
URL_RE = re.compile(r'^(  url )"[^"]+"', re.MULTILINE)
SHA_RE = re.compile(r'^(  sha256 )"[0-9a-fA-F]+"', re.MULTILINE)
URL_VALUE_RE = re.compile(r'^  url "([^"]+)"', re.MULTILINE)
SHA_VALUE_RE = re.compile(r'^  sha256 "([0-9a-fA-F]+)"', re.MULTILINE)
INSTALL_RE = re.compile(r"(?ms)^  def install\n.*?^  end$")
TEST_RE = re.compile(r"(?ms)^  test do\n.*?^  end$")
CURRENT_URL_RE = re.compile(
    rf"^{re.escape(HOMEPAGE)}/releases/download/"
    r"v(\d+\.\d+\.\d+)/commiter_\1_darwin_arm64\.zip$"
)

FORMULA_TEMPLATE = """\
class Commiter < Formula
  desc "Local-first Git commit planning CLI"
  homepage "{homepage}"
  url "{url}"
  sha256 "{sha256}"
  license "MIT"

  livecheck do
    url :stable
    regex(/^v?(\\d+(?:\\.\\d+)+)$/i)
  end

  depends_on arch: :arm64
  depends_on macos: :sonoma

  def install
    bin.install "bin/commiter"
    libexec.install "libexec/commiter-mlx-helper"
    libexec.install "libexec/mlx.metallib"
  end

  def caveats
    <<~EOS
      commiter requires Git and a local LLM backend.
      The default Ollama backend requires a local Ollama 0.31.2+ instance on loopback.
      After installing, run:

        commiter setup
        commiter doctor
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{{bin}}/commiter version")
    helper = libexec/"commiter-mlx-helper"
    assert_predicate libexec/"mlx.metallib", :exist?
    assert_predicate helper, :executable?
    system "codesign", "--verify", "--strict", helper
    assert_equal "metal_ok\\n", shell_output("#{{helper}} --smoke-metal")
  end
end
"""


class FormulaError(Exception):
    """Invalid Formula state or rejected release payload."""


def expected_url(version: str) -> str:
    return (
        f"{HOMEPAGE}/releases/download/v{version}/"
        f"commiter_{version}_darwin_arm64.zip"
    )


def version_tuple(version: str) -> tuple[int, int, int]:
    if not VERSION_RE.fullmatch(version):
        raise FormulaError(f"version must be MAJOR.MINOR.PATCH, got {version!r}")
    major, minor, patch = version.split(".")
    return int(major), int(minor), int(patch)


def parse_current_formula(text: str) -> tuple[str, str, str]:
    urls = URL_VALUE_RE.findall(text)
    shas = SHA_VALUE_RE.findall(text)
    if len(urls) != 1 or len(shas) != 1:
        raise FormulaError(
            "Formula/commiter.rb must contain exactly one url and sha256 stanza"
        )

    url = urls[0]
    sha256 = shas[0].lower()
    match = CURRENT_URL_RE.fullmatch(url)
    if match is None:
        raise FormulaError(
            "Formula/commiter.rb url must be a commiter darwin/arm64 Release ZIP"
        )
    if not SHA256_RE.fullmatch(sha256):
        raise FormulaError("Formula/commiter.rb sha256 must be a 64-character hex digest")
    return match.group(1), url, sha256


def update_formula(
    formula_path: Path,
    version: str,
    sha256: str,
    payload_url: str | None = None,
) -> str:
    version = version.strip()
    sha256 = sha256.strip().lower()
    payload_url = payload_url.strip() if payload_url else None

    version_tuple(version)
    if not SHA256_RE.fullmatch(sha256):
        raise FormulaError("sha256 must be a 64-character hex digest")

    url = expected_url(version)
    if payload_url is not None and payload_url != url:
        raise FormulaError(f"url must be {url}, got {payload_url!r}")

    if not formula_path.exists():
        formula_path.parent.mkdir(parents=True, exist_ok=True)
        formula_path.write_text(
            FORMULA_TEMPLATE.format(homepage=HOMEPAGE, url=url, sha256=sha256),
            encoding="utf-8",
        )
        return "created"

    text = formula_path.read_text(encoding="utf-8")
    current_version, current_url, current_sha256 = parse_current_formula(text)
    install_count = len(list(INSTALL_RE.finditer(text)))
    if install_count != 1:
        raise FormulaError("Formula/commiter.rb must contain exactly one install stanza")
    test_count = len(list(TEST_RE.finditer(text)))
    if test_count != 1:
        raise FormulaError("Formula/commiter.rb must contain exactly one test stanza")
    incoming = version_tuple(version)
    current = version_tuple(current_version)

    if incoming < current:
        raise FormulaError(
            f"refusing to downgrade commiter from {current_version} to {version}"
        )
    if incoming == current:
        if url == current_url and sha256 == current_sha256:
            return "unchanged"
        raise FormulaError(
            f"refusing to change url/sha256 for commiter {version}; "
            "publish a new version instead"
        )

    rendered_template = FORMULA_TEMPLATE.format(
        homepage=HOMEPAGE, url=url, sha256=sha256
    )
    install_match = INSTALL_RE.search(rendered_template)
    if install_match is None:
        raise FormulaError("Formula template is missing its install stanza")
    updated = INSTALL_RE.sub(install_match.group(0), text, count=1)
    test_match = TEST_RE.search(rendered_template)
    if test_match is None:
        raise FormulaError("Formula template is missing its test stanza")
    updated = TEST_RE.sub(lambda _: test_match.group(0), updated, count=1)
    updated = URL_RE.sub(rf'\1"{url}"', updated, count=1)
    updated = SHA_RE.sub(rf'\1"{sha256}"', updated, count=1)
    if updated == text:
        raise FormulaError("Formula rewrite produced no changes")
    formula_path.write_text(updated, encoding="utf-8")
    return "updated"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument(
        "--url",
        help="Optional payload URL. If set, it must match the constructed Release URL.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        status = update_formula(
            FORMULA_PATH,
            args.version,
            args.sha256,
            args.url,
        )
    except FormulaError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
