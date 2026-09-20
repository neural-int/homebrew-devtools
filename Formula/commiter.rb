class Commiter < Formula
  desc "Local-first Git commit planning CLI"
  homepage "https://github.com/neural-int/commiter-cli"
  url "https://github.com/neural-int/commiter-cli/releases/download/v1.2.1/commiter_1.2.1_darwin_arm64.zip"
  sha256 "7b9ee0959ac7343ceaac6c796ec972bcc2c93247d9858cfbe6c63b4ce3be078c"
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
