# seniorbot

`seniorbot` is a keyboard-first automation library for Senior Gestão Empresarial running through Microsoft RemoteApp.

The ERP content is treated as an opaque RemoteApp surface. The library focuses the top-level `RAIL_WINDOW`, sends deterministic keyboard commands, and synchronizes on observable Windows boundaries such as native dialogs and created files.

## Install

```powershell
pip install -e ".[windows,dev]"
```

## Uso rapido

Valide os parametros e os caminhos sem acionar o Senior:

```powershell
seniorbot f141cis --dry-run --serie 036 --cfops 5101 5102 --date 2026-07-01
```

Execute a exportacao F141CIS:

```powershell
seniorbot f141cis --yes --serie 036 --cfops 5101 5102 6101 6102 5910 6910
```

No uso manual, sem `--yes`, o SeniorBot pergunta a data inicial e final do filtro. Pressione ENTER para usar a data de hoje.

Para informar as datas direto no comando:

```powershell
seniorbot f141cis --yes --start-date 01/07/2026 --end-date 01/07/2026
```

Quando `--date` e usado para reprocessar um dia, essa data tambem vira o padrao do filtro da tela, a menos que `--start-date` e `--end-date` sejam informados.

Quando `--output` nao e informado, o arquivo e salvo automaticamente na pasta mensal:

```text
C:\exportacoes\MM AAAA\DD.MM.xlsx
```

Exemplo para 1 de julho de 2026:

```text
C:\exportacoes\07 2026\01.07.xlsx
```

Para apontar a exportacao para a pasta consultada pela planilha mae, use `--base-dir`:

```powershell
seniorbot f141cis --yes --base-dir "C:\Controle de Faturamento"
```

Quando o caminho de saida usa uma unidade local, o SeniorBot salva pelo caminho RemoteApp equivalente `\\tsclient\...` e aguarda o arquivo local ficar pronto.

Se o arquivo do dia ja existir, ele e movido antes para `_backups` dentro da pasta do mes. Exemplo:

```text
C:\exportacoes\07 2026\_backups\01.07.backup-20260701-170000.xlsx
```

Ao final, o SeniorBot mostra um resumo com arquivo, pasta, tamanho e horario.

Os logs ficam em `logs\` dentro da pasta do projeto, a menos que `--log-dir` seja informado.

## Agendamento

Para criar ou atualizar a tarefa diaria das 17:00 no Agendador de Tarefas do Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_f141cis_task.ps1
```

A tarefa usa `launchers\seniorbot-f141cis-scheduled.cmd`, que executa sem pausa e sem confirmacao manual. O Senior ainda precisa estar aberto na tela inicial para a automacao atual funcionar.

## Example

```python
from pathlib import Path

from seniorbot import SeniorBot

bot = SeniorBot()
bot.export_xlsx(Path(r"C:\Temp\consulta.xlsx"))
```

## Design principles

- No mouse coordinates.
- No image recognition.
- Prefer `pywinauto` for Windows focus, dialogs, and keyboard input.
- Keep ERP-specific workflows separate from reusable window, keyboard, and synchronization layers.
- Use explicit timeouts and observable waits instead of fixed sleeps.

## Tests

```powershell
python -m unittest
```
