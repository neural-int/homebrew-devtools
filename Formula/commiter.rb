class Commiter < Formula
  desc "Local-first Git commit planning CLI"
  homepage "https://github.com/neural-int/commiter-cli"
  url "https://github.com/neural-int/commiter-cli/releases/download/v1.3.2/commiter_1.3.2_darwin_arm64.zip"
  sha256 "881cb706596de407b30ebad212d71f5ab4c3b3d387695a32a5fcc4a9058f6b9a"
  license "MIT"

  livecheck do
    url :stable
    regex(/^v?(\d+(?:\.\d+)+)$/i)
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
    assert_match version.to_s, shell_output("#{bin}/commiter version")
    helper = libexec/"commiter-mlx-helper"
    assert_predicate libexec/"mlx.metallib", :exist?
    assert_predicate helper, :executable?
    system "codesign", "--verify", "--strict", helper
    assert_equal "metal_ok\n", shell_output("#{helper} --smoke-metal")
  end
end
