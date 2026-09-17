class Commiter < Formula
  desc "Local-first Git commit planning CLI"
  homepage "https://github.com/neural-int/commiter-cli"
  url "https://github.com/neural-int/commiter-cli/releases/download/v1.1.1/commiter_1.1.1_darwin_arm64.zip"
  sha256 "ad1c8944f1d3e8aad7aaeaafe13098ce37de027db6d6319e017f65c4fe353ae6"
  license "MIT"

  livecheck do
    url :stable
    regex(/^v?(\d+(?:\.\d+)+)$/i)
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
    assert_match version.to_s, shell_output("#{bin}/commiter version")
  end
end
