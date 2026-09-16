# homebrew-devtools

Homebrew tap for neural-int CLI and developer tools.

## Install

```sh
brew install neural-int/devtools/commiter
```

This tap currently packages:

| Formula | Description | Platform |
| --- | --- | --- |
| `commiter` | Local-first Git commit planning CLI | Apple Silicon, macOS 15+ |

Source: <https://github.com/neural-int/commiter-cli>

After installation:

```sh
commiter setup
commiter doctor
```

## Formula updates

`commiter` Formula bumps are not pushed to `main` directly.

When `neural-int/commiter-cli` publishes a GitHub Release, it sends a `commiter-release` `repository_dispatch` to this repository with the version, tag, ZIP URL, and SHA-256. `.github/workflows/update-commiter.yml` then:

1. Verifies the published Release and ZIP checksum
2. Updates `Formula/commiter.rb`, or creates it if missing
3. Runs `brew audit --strict`, `brew install`, and `brew test`
4. Opens a PR from `automation/commiter-vX.Y.Z`

Formula versions only move forward. A dispatch for an older tag, or for the same tag with a different SHA-256, is rejected. To change a published artifact, cut a new version.

Merge that PR to publish the Formula update. Users can then run:

```sh
brew update
brew upgrade commiter
```

## Issues

For issues with `commiter` itself, please report them to:
https://github.com/neural-int/commiter-cli

Use this repository only for Homebrew installation or Formula-related issues.
