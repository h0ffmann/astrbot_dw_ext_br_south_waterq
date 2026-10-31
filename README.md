# astrbot_dw_ext_br_south_waterq

[English](README.md) | [简体中文](README.zh-CN.md) | [Português (Brasil)](README.pt-BR.md) | [日本語](README.ja-JP.md)

[![CI](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/ci.yml/badge.svg)](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/ci.yml)
[![Code smell report](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/code-smell-report.yml/badge.svg)](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/code-smell-report.yml)
[![License: MPL 2.0](https://img.shields.io/badge/license-MPL--2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Ask DeepWiki](https://img.shields.io/badge/Ask-DeepWiki-blue.svg)](https://deepwiki.com/h0ffmann/astrbot_dw_ext_br_south_waterq)

This extension is for the AstrBot plugin [astrbot_plugin_disaster_warning](https://github.com/Pancakes-Labs/astrbot_plugin_disaster_warning).
It sends bathing water quality alerts for the South of Brazil. The data comes from FEPAM (RS), IMA (SC) and IAT (PR).
It sends a message when a point becomes unsuitable, and when a point is suitable again.

> [!WARNING]
> The data is for reference only. It is not an official warning. Always read the signs at the beach and obey your local authorities. The result of a sample can be some days old.

> [!CAUTION]
> The extension runs as Python code in the same process as the host. When you install it, you trust it with the host and with the host data.

## Documentation

The [wiki](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/wiki) has more information in the same languages.

## Requirements

- The host must have the extension system. This system is not yet in a release of the host.
- The host version must be 1.6.5 or higher.

## Installation

The install flow of the host is not yet available. Do these steps to install by hand:

1. Open the data directory of the plugin. Make an `extensions` directory if it does not exist.
2. Put this repository in `extensions/br_south_waterq`. The directory name must be the same as the extension id.
3. Add `br_south_waterq` to `extensions.enabled_ids` in the plugin configuration.
4. Reload the plugin.

## Configuration

Put the settings in `extensions.settings`. This value is JSON text:

```json
{
  "enabled_ids": ["br_south_waterq"],
  "settings": "{\"br_south_waterq\": {\"language\": \"en\", \"states\": [\"SC\"]}}"
}
```

## Settings

| Setting | Default | Description |
| :--- | :--- | :--- |
| `language` | `zh-CN` | The language of the messages. The values are `zh-CN`, `en`, `pt-BR` and `ja-JP`. |
| `poll_interval` | `21600` | The time between two requests for each state, in seconds. The default is 6 hours. |
| `states` | `["RS", "SC", "PR"]` | The list of states to monitor. The extension ignores an unknown code. If no code is known, it uses all states and writes a warning. |

## When the extension sends a message

- The first poll of each state after a start records the current results. It sends no message.
- A point that becomes unsuitable gives one message. A new unsuitable bulletin for that point gives one more message.
- A point that is suitable again gives one message.
- The extension never sends a result with a sample older than 90 days, or with no known sample date.

In the off-season, the programs of RS and PR have only old results. Thus, the extension sends no message for these states.

## Data sources

| State | Source | Update frequency |
| :--- | :--- | :--- |
| RS | FEPAM (PROCERGS API) | The extension reads the feed at each `poll_interval` |
| SC | IMA | The extension reads the feed at each `poll_interval` |
| PR | IAT (GeoPR ArcGIS layer) | The extension reads the feed at each `poll_interval` |

The agencies publish about one bulletin each week in the season. The messages use the criterion of CONAMA 274/2000. The API documents are in [docs/brazil-water-quality-sources.md](docs/brazil-water-quality-sources.md).

To add a state, add a provider module in `providers/` and one line to `states.py`.

## Development

The tests use the real classes of the host. `just setup` gets a pinned copy of the host in `.host/`.
You need [just](https://github.com/casey/just) and [uv](https://github.com/astral-sh/uv). With Nix, `nix develop` gives you these tools.

```sh
just setup
just check
```

`just check` runs the format, lint, type, complexity and test checks. The CI runs the same command.
`just mock` makes `dist/mock.html`. Open this file in a browser to see the real messages of the extension in a mock chat.
Run `just` to see all commands. `just live` runs the tests that call the real FEPAM, IMA and IAT services.
Set `DW_HOST_DIR` to use a different copy of the host.

## Writing rules

Write the English text in ASD-STE100 Simplified Technical English. The vendored skill is in `.claude/skills/asd-ste100`.
This command checks a file:

```sh
python3 .claude/skills/asd-ste100/scripts/ste-lint.py README.md
```

## License

The code is under the [Mozilla Public License 2.0](LICENSE). The file `extension.png` is under CC-BY-4.0. See `meta.json`.
The files in `.claude/skills/asd-ste100` are under the MIT License. See `.claude/skills/asd-ste100/LICENSE`.
