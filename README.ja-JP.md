# astrbot_dw_ext_br_south_waterq

[English](README.md) | [简体中文](README.zh-CN.md) | [Português (Brasil)](README.pt-BR.md) | [日本語](README.ja-JP.md)

[![CI](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/ci.yml/badge.svg)](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/ci.yml)
[![Code smell report](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/code-smell-report.yml/badge.svg)](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/code-smell-report.yml)
[![License: MPL 2.0](https://img.shields.io/badge/license-MPL--2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Ask DeepWiki](https://img.shields.io/badge/Ask-DeepWiki-blue.svg)](https://deepwiki.com/h0ffmann/astrbot_dw_ext_br_south_waterq)

> この文書は翻訳です。内容に差異がある場合は、[英語版](README.md)を正とします。

この拡張機能は、AstrBot プラグイン [astrbot_plugin_disaster_warning](https://github.com/Pancakes-Labs/astrbot_plugin_disaster_warning) 用です。
ブラジル南部の海水浴場の水質に関する警報を送信します。データの提供元は FEPAM（リオグランデ・ド・スル州 RS）、IMA（サンタカタリーナ州 SC）、IAT（パラナ州 PR）です。
地点が遊泳不適になったとき、および遊泳適に戻ったときにメッセージを送信します。

> [!WARNING]
> データは参考情報です。公式の警報ではありません。必ず海岸の掲示を確認し、地元当局の指示に従ってください。採水の結果は数日前のものである場合があります。

> [!CAUTION]
> この拡張機能は Python コードとしてホストと同じプロセスで動作します。インストールすると、ホストとホストのデータへのアクセスを信頼することになります。

## ドキュメント

[Wiki](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/wiki) には、同じ言語で詳しい情報があります。

## 要件

- ホストに拡張システムが必要です。このシステムは、ホストのリリース版にはまだ含まれていません。
- ホストのバージョンは 1.6.5 以上である必要があります。

## インストール

ホストのインストール機能はまだ利用できません。次の手順で手動でインストールしてください。

1. プラグインのデータディレクトリを開きます。`extensions` ディレクトリがない場合は作成します。
2. このリポジトリを `extensions/br_south_waterq` に置きます。ディレクトリ名は拡張機能の ID と同じにする必要があります。
3. プラグイン設定の `extensions.enabled_ids` に `br_south_waterq` を追加します。
4. プラグインを再読み込みします。

## 設定方法

設定は `extensions.settings` に記述します。この値は JSON テキストです。

```json
{
  "enabled_ids": ["br_south_waterq"],
  "settings": "{\"br_south_waterq\": {\"language\": \"en\", \"states\": [\"SC\"]}}"
}
```

## 設定項目

| 設定項目 | 既定値 | 説明 |
| :--- | :--- | :--- |
| `language` | `zh-CN` | メッセージの言語です。値は `zh-CN`、`en`、`pt-BR`、`ja-JP` です。 |
| `poll_interval` | `21600` | 州ごとに取得する間隔（秒）です。既定値は 6 時間です。 |
| `states` | `["RS", "SC", "PR"]` | 監視する州のリストです。不明なコードは無視します。既知のコードがない場合は、すべての州を使用し、警告を記録します。 |

## メッセージを送信するタイミング

- 起動後、各州の最初の取得は現在の結果を記録するだけで、メッセージは送信しません。
- 地点が遊泳不適になると、メッセージを 1 件送信します。同じ地点に新しい遊泳不適の公報が出ると、さらに 1 件送信します。
- 地点が遊泳適に戻ると、メッセージを 1 件送信します。
- 採水から 90 日を超えた結果、または採水日が不明な結果は送信しません。

シーズン外は、RS と PR のプログラムには古い結果しかありません。そのため、これらの州のメッセージは送信されません。

## データソース

| 州 | ソース | 更新頻度 |
| :--- | :--- | :--- |
| RS | FEPAM（PROCERGS API） | `poll_interval` ごとに取得します |
| SC | IMA | `poll_interval` ごとに取得します |
| PR | IAT（GeoPR ArcGIS レイヤー） | `poll_interval` ごとに取得します |

各機関はシーズン中、週に 1 回程度公報を公開します。メッセージは CONAMA 274/2000 の基準を使用します。API の文書は [docs/brazil-water-quality-sources.md](docs/brazil-water-quality-sources.md) にあります（英語）。

州を追加するには、`providers/` にモジュールを追加し、`states.py` に 1 行追加します。

## 開発

テストはホストの実際のクラスを使用します。`just setup` は、固定バージョンのホストを `.host/` に取得します。
[just](https://github.com/casey/just) と [uv](https://github.com/astral-sh/uv) が必要です。Nix を使う場合は、`nix develop` でこれらのツールを利用できます。

```sh
just setup
just check
```

`just check` は、フォーマット、コード規則、型、複雑度、テストの確認を実行します。CI も同じコマンドを実行します。
`just mock` は `dist/mock.html` を生成します。このファイルをブラウザで開くと、拡張機能の実際のメッセージを模擬チャットで確認できます。
`just` を実行すると、すべてのコマンドを確認できます。`just live` は、実際の FEPAM、IMA、IAT のサービスを呼び出すテストを実行します。
別のホストのコピーを使うには、`DW_HOST_DIR` を設定します。

## 記述ルール

英語の文章は ASD-STE100 Simplified Technical English で記述してください。同梱のスキルは `.claude/skills/asd-ste100` にあります。
次のコマンドでファイルを確認できます。

```sh
python3 .claude/skills/asd-ste100/scripts/ste-lint.py README.md
```

## ライセンス

コードは [Mozilla Public License 2.0](LICENSE) の下で提供されます。`extension.png` は CC-BY-4.0 です。`meta.json` を参照してください。
`.claude/skills/asd-ste100` のファイルは MIT ライセンスです。`.claude/skills/asd-ste100/LICENSE` を参照してください。
