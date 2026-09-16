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

FORMULA_TEMPLATE = """\
class Commiter < Formula
  desc "Local-first Git commit planning CLI"
  homepage "{homepage}"
  url "{url}"
  sha256 "{sha256}"
  license "MIT"

  livecheck do
    url :homepage
    regex(/^v?(\\d+(?:\\.\\d+)+)$/i)
  end

  depends_on arch: :arm64
  depends_on macos: :sonoma

  def install
    bin.install "commiter"
  end

  def caveats
    <<~EOS
      commiter requires Git and a local Ollama 0.31.2+ instance on loopback.
      After installing, run:

        commiter setup
        commiter doctor
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{{bin}}/commiter version")
  end
end
"""


def expected_url(version: str) -> str:
    return (
        f"{HOMEPAGE}/releases/download/v{version}/"
        f"commiter_{version}_darwin_arm64.zip"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument(
        "--url",
        help="Optional payload URL. If set, it must match the constructed Release URL.",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    args = parse_args()
    version = args.version.strip()
    sha256 = args.sha256.strip().lower()
    payload_url = args.url.strip() if args.url else None

    if not VERSION_RE.fullmatch(version):
        fail(f"version must be MAJOR.MINOR.PATCH, got {version!r}")
    if not SHA256_RE.fullmatch(sha256):
        fail("sha256 must be a 64-character hex digest")

    url = expected_url(version)
    if payload_url is not None and payload_url != url:
        fail(f"url must be {url}, got {payload_url!r}")

    if FORMULA_PATH.exists():
        text = FORMULA_PATH.read_text(encoding="utf-8")
        updated, url_count = URL_RE.subn(rf'\1"{url}"', text, count=1)
        updated, sha_count = SHA_RE.subn(rf'\1"{sha256}"', updated, count=1)
        if url_count != 1 or sha_count != 1:
            fail("Formula/commiter.rb must contain exactly one url and sha256 stanza")
        if updated == text:
            print("unchanged")
            return
        FORMULA_PATH.write_text(updated, encoding="utf-8")
        print("updated")
        return

    FORMULA_PATH.parent.mkdir(parents=True, exist_ok=True)
    FORMULA_PATH.write_text(
        FORMULA_TEMPLATE.format(homepage=HOMEPAGE, url=url, sha256=sha256),
        encoding="utf-8",
    )
    print("created")


if __name__ == "__main__":
    main()
