# astrbot_dw_ext_br_south_waterq

[English](README.md) | [简体中文](README.zh-CN.md) | [Português (Brasil)](README.pt-BR.md) | [日本語](README.ja-JP.md)

[![CI](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/ci.yml/badge.svg)](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/ci.yml)
[![Code smell report](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/code-smell-report.yml/badge.svg)](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/code-smell-report.yml)
[![License: MPL 2.0](https://img.shields.io/badge/license-MPL--2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Ask DeepWiki](https://img.shields.io/badge/Ask-DeepWiki-blue.svg)](https://deepwiki.com/h0ffmann/astrbot_dw_ext_br_south_waterq)

> 本文为译文。如有出入，以[英文版](README.md)为准。

本扩展用于 AstrBot 插件 [astrbot_plugin_disaster_warning](https://github.com/Pancakes-Labs/astrbot_plugin_disaster_warning)。
它发送巴西南部的浴场水质预警。数据来自 FEPAM（南里奥格兰德州 RS）、IMA（圣卡塔琳娜州 SC）和 IAT（巴拉那州 PR）。
当某个监测点变为不适宜游泳，或重新变为适宜游泳时，它会发送一条消息。

> [!WARNING]
> 数据仅供参考，不是官方预警。请始终查看海滩现场标识，并遵从当地主管部门的指示。采样结果可能已是数天前的数据。

> [!CAUTION]
> 本扩展以 Python 代码形式与宿主在同一进程中运行。安装本扩展，即表示您信任它可以访问宿主及宿主数据。

## 文档

[Wiki](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/wiki) 以相同语言提供更多信息。

## 要求

- 宿主必须具备扩展系统。该系统尚未包含在宿主的正式版本中。
- 宿主版本必须为 1.6.5 或更高。

## 安装

宿主的安装流程尚不可用。请按以下步骤手动安装：

1. 打开插件的数据目录。如果 `extensions` 目录不存在，请创建该目录。
2. 将本仓库放到 `extensions/br_south_waterq`。目录名必须与扩展 ID 相同。
3. 在插件配置的 `extensions.enabled_ids` 中添加 `br_south_waterq`。
4. 重载插件。

## 配置

在 `extensions.settings` 中填写设置。该值为 JSON 文本：

```json
{
  "enabled_ids": ["br_south_waterq"],
  "settings": "{\"br_south_waterq\": {\"language\": \"en\", \"states\": [\"SC\"]}}"
}
```

## 设置项

| 设置项 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `language` | `zh-CN` | 消息语言。可选值为 `zh-CN`、`en`、`pt-BR` 和 `ja-JP`。 |
| `poll_interval` | `21600` | 每个州两次请求的间隔，单位为秒。默认值为 6 小时。 |
| `states` | `["RS", "SC", "PR"]` | 要监控的州列表。扩展忽略未知代码。如果没有已知代码，扩展使用全部州并写入一条警告。 |

## 扩展何时发送消息

- 启动后，每个州的第一次轮询只记录当前结果，不发送消息。
- 监测点变为不适宜游泳时发送一条消息。该监测点有新的不适宜公报时，再发送一条消息。
- 监测点重新变为适宜游泳时发送一条消息。
- 扩展绝不发送采样时间超过 90 天或采样日期未知的结果。

在非游泳季，RS 和 PR 的项目只有旧结果，因此扩展不会为这两个州发送消息。

## 数据来源

| 州 | 来源 | 更新频率 |
| :--- | :--- | :--- |
| RS | FEPAM（PROCERGS API） | 扩展按 `poll_interval` 读取 |
| SC | IMA | 扩展按 `poll_interval` 读取 |
| PR | IAT（GeoPR ArcGIS 图层） | 扩展按 `poll_interval` 读取 |

各机构在游泳季大约每周发布一份公报。消息采用 CONAMA 274/2000 标准。API 文档见 [docs/brazil-water-quality-sources.md](docs/brazil-water-quality-sources.md)（英文）。

要添加一个州，请在 `providers/` 中添加一个模块，并在 `states.py` 中添加一行。

## 开发

测试使用宿主的真实类。`just setup` 会在 `.host/` 中获取固定版本的宿主。
您需要 [just](https://github.com/casey/just) 和 [uv](https://github.com/astral-sh/uv)。使用 Nix 时，`nix develop` 会提供这些工具。

```sh
just setup
just check
```

`just check` 运行格式、代码规则、类型、复杂度和测试检查。CI 运行相同的命令。
`just mock` 生成 `dist/mock.html`。在浏览器中打开此文件，可在模拟聊天中查看扩展的真实消息。
运行 `just` 可查看所有命令。`just live` 运行调用真实 FEPAM、IMA 和 IAT 服务的测试。
设置 `DW_HOST_DIR` 可使用其他宿主副本。

## 写作规则

英文文本须使用 ASD-STE100 简化技术英语。随仓库提供的技能位于 `.claude/skills/asd-ste100`。
以下命令可检查文件：

```sh
python3 .claude/skills/asd-ste100/scripts/ste-lint.py README.md
```

## 许可证

代码采用 [Mozilla Public License 2.0](LICENSE)。文件 `extension.png` 采用 CC-BY-4.0，详见 `meta.json`。
`.claude/skills/asd-ste100` 中的文件采用 MIT 许可证，详见 `.claude/skills/asd-ste100/LICENSE`。
