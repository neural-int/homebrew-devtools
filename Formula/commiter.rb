class Commiter < Formula
  desc "Local-first Git commit planning CLI"
  homepage "https://github.com/neural-int/commiter-cli"
  url "https://github.com/neural-int/commiter-cli/releases/download/v3.0.1/commiter_3.0.1_darwin_arm64.zip"
  sha256 "aa5220530f4678683bf6f37417e0e9ea4f40dc0ee3a761932a1d3b46d9ebd497"
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
    assert_path_exists libexec/"mlx.metallib"
    assert_predicate helper, :executable?
    system "codesign", "--verify", "--strict", helper
    assert_equal "metal_ok\n", shell_output("#{helper} --smoke-metal")
  end
end
