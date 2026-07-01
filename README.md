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
seniorbot f141cis --dry-run --serie 036 --cfops 5101 5102 --output C:\Temp\f141cis.xlsx
```

Execute a exportacao F141CIS:

```powershell
seniorbot f141cis --yes --serie 036 --cfops 5101 5102 6101 6102 5910 6910 --output C:\Temp\f141cis.xlsx
```

Quando o caminho de saida usa uma unidade local, como `C:\Temp\f141cis.xlsx`, o SeniorBot salva pelo caminho RemoteApp equivalente `\\tsclient\C\Temp\f141cis.xlsx` e aguarda o arquivo local ficar pronto.

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
