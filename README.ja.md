# homebrew-devtools

[English](README.md) | 日本語

neural-int の CLI および開発者向けツールのための Homebrew tap リポジトリです。

## インストール

```sh
brew install neural-int/devtools/commiter
```

現在この tap では以下のツールを提供しています:

| Formula | 説明 | 対応環境 |
| --- | --- | --- |
| `commiter` | ローカル完結型（Local-first）の Git コミット設計 CLI | Apple Silicon, macOS 15+ |

ソースコード: <https://github.com/neural-int/commiter-cli>

インストール後のセットアップ:

```sh
commiter setup
commiter doctor
```

## Formula の更新について

`commiter` の Formula 更新は `main` ブランチへ直接 push されることはありません。

`neural-int/commiter-cli` で GitHub Release が公開されると、バージョン、タグ、ZIP のダウンロード URL、および SHA-256 チェックサムを含む `commiter-release` の `repository_dispatch` イベントが本リポジトリに送信されます。その後、`.github/workflows/update-commiter.yml` によって以下の処理が自動実行されます:

1. 公開された Release および ZIP のチェックサムの検証
2. `Formula/commiter.rb` の更新（存在しない場合は新規作成）
3. `brew audit --strict`、`brew install`、`brew test` の実行
4. `automation/commiter-vX.Y.Z` ブランチからの Pull Request 作成

Formula のバージョンは常に前進（新しいバージョンへの更新）のみ許可されます。古いタグへのディスパッチや、同一タグで異なる SHA-256 を持つディスパッチは拒否されます。公開済みの成果物を変更したい場合は、新しいバージョンをリリースしてください。

作成された Pull Request をマージすることで Formula の更新が反映されます。マージ後、利用者は以下のコマンドで更新できます:

```sh
brew update
brew upgrade commiter
```

## Issue・不具合の報告

`commiter` 本体の不具合や要望については、以下へご報告ください:
<https://github.com/neural-int/commiter-cli>

本リポジトリは、Homebrew を通じたインストールに関する問題や Formula 自体の問題にのみご使用ください。
