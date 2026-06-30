# seniorbot

`seniorbot` is a keyboard-first automation library for Senior Gestão Empresarial running through Microsoft RemoteApp.

The ERP content is treated as an opaque RemoteApp surface. The library focuses the top-level `RAIL_WINDOW`, sends deterministic keyboard commands, and synchronizes on observable Windows boundaries such as native dialogs and created files.

## Install

```powershell
pip install -e ".[windows,dev]"
```

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
