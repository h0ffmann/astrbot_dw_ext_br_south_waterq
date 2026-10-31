# astrbot_dw_ext_br_south_waterq

[English](README.md) | [简体中文](README.zh-CN.md) | [Português (Brasil)](README.pt-BR.md) | [日本語](README.ja-JP.md)

[![CI](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/ci.yml/badge.svg)](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/ci.yml)
[![Code smell report](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/code-smell-report.yml/badge.svg)](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/actions/workflows/code-smell-report.yml)
[![License: MPL 2.0](https://img.shields.io/badge/license-MPL--2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![Ask DeepWiki](https://img.shields.io/badge/Ask-DeepWiki-blue.svg)](https://deepwiki.com/h0ffmann/astrbot_dw_ext_br_south_waterq)

> Este texto é uma tradução. Em caso de diferença, vale a [versão em inglês](README.md).

Esta extensão funciona com o plugin do AstrBot [astrbot_plugin_disaster_warning](https://github.com/Pancakes-Labs/astrbot_plugin_disaster_warning).
A extensão envia alertas de balneabilidade para o Sul do Brasil. Os dados vêm da FEPAM (RS), do IMA (SC) e do IAT (PR).
A extensão envia uma mensagem quando um ponto fica impróprio e quando um ponto volta a ficar próprio.

> [!WARNING]
> Os dados servem apenas como referência. Os dados não são um alerta oficial. Leia sempre as placas na praia e siga as autoridades locais. O resultado de uma coleta pode ter alguns dias.

> [!CAUTION]
> A extensão executa código Python no mesmo processo do host. A instalação concede à extensão acesso ao host e aos dados do host.

## Documentação

A [wiki](https://github.com/h0ffmann/astrbot_dw_ext_br_south_waterq/wiki) tem mais informações nos mesmos idiomas.

## Requisitos

- O host deve ter o sistema de extensões. Nenhuma versão publicada do host tem esse sistema.
- A versão do host deve ser 1.6.5 ou superior.

## Instalação

O fluxo de instalação do host ainda não está disponível. Siga estes passos para instalar manualmente:

1. Abra o diretório de dados do plugin. Crie o diretório `extensions` se ele não existir.
2. Coloque este repositório em `extensions/br_south_waterq`. O nome do diretório deve ser igual ao id da extensão.
3. Adicione `br_south_waterq` a `extensions.enabled_ids` na configuração do plugin.
4. Recarregue o plugin.

## Configuração

Coloque as opções em `extensions.settings`. O valor é um texto JSON:

```json
{
  "enabled_ids": ["br_south_waterq"],
  "settings": "{\"br_south_waterq\": {\"language\": \"en\", \"states\": [\"SC\"]}}"
}
```

## Opções

| Opção | Padrão | Descrição |
| :--- | :--- | :--- |
| `language` | `zh-CN` | O idioma das mensagens. Os valores são `zh-CN`, `en`, `pt-BR` e `ja-JP`. |
| `poll_interval` | `21600` | O tempo entre duas consultas de cada estado, em segundos. O padrão é 6 horas. |
| `states` | `["RS", "SC", "PR"]` | A lista de estados monitorados. A extensão ignora um código desconhecido. Se nenhum código for conhecido, a extensão usa todos os estados e registra um aviso. |

## Quando a extensão envia uma mensagem

- A primeira consulta de cada estado após o início registra os resultados atuais. Essa consulta não envia mensagem.
- Um ponto que fica impróprio gera uma mensagem. Um novo boletim impróprio do mesmo ponto gera outra mensagem.
- Um ponto que volta a ficar próprio gera uma mensagem.
- A extensão nunca envia um resultado com coleta de mais de 90 dias ou sem data de coleta conhecida.

Fora da temporada, os programas do RS e do PR têm apenas resultados antigos. Por isso, a extensão não envia mensagens para esses estados.

## Fontes de dados

| Estado | Fonte | Frequência de atualização |
| :--- | :--- | :--- |
| RS | FEPAM (API da PROCERGS) | A extensão lê os dados a cada `poll_interval` |
| SC | IMA | A extensão lê os dados a cada `poll_interval` |
| PR | IAT (camada ArcGIS do GeoPR) | A extensão lê os dados a cada `poll_interval` |

As agências publicam cerca de um boletim por semana durante a temporada. As mensagens usam o critério da CONAMA 274/2000. Os documentos das APIs estão em [docs/brazil-water-quality-sources.md](docs/brazil-water-quality-sources.md), em inglês.

Para adicionar um estado, adicione um módulo em `providers/` e uma linha a `states.py`.

## Desenvolvimento

Os testes usam as classes reais do host. O comando `just setup` baixa uma cópia fixa do host em `.host/`.
Você precisa de [just](https://github.com/casey/just) e [uv](https://github.com/astral-sh/uv). Com Nix, o comando `nix develop` fornece essas ferramentas.

```sh
just setup
just check
```

O comando `just check` executa as verificações de formato, regras de código, tipos, complexidade e testes. A CI executa o mesmo comando.
O comando `just mock` gera `dist/mock.html`. Abra esse arquivo em um navegador para ver as mensagens reais da extensão em um chat simulado.
Execute `just` para ver todos os comandos. O comando `just live` executa os testes que consultam os serviços reais da FEPAM, do IMA e do IAT.
Defina `DW_HOST_DIR` para usar outra cópia do host.

## Regras de escrita

Escreva o texto em inglês em ASD-STE100 Simplified Technical English. A skill incluída neste repositório está em `.claude/skills/asd-ste100`.
Este comando verifica um arquivo:

```sh
python3 .claude/skills/asd-ste100/scripts/ste-lint.py README.md
```

## Licença

O código está sob a [Mozilla Public License 2.0](LICENSE). O arquivo `extension.png` está sob CC-BY-4.0. Consulte `meta.json`.
Os arquivos em `.claude/skills/asd-ste100` estão sob a licença MIT. Consulte `.claude/skills/asd-ste100/LICENSE`.
