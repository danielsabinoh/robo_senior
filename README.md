# seniorbot

`seniorbot` é uma automação por teclado para o Senior Gestão Empresarial executado via Microsoft RemoteApp.

O conteúdo do ERP é tratado como uma tela fechada: o robô foca a janela RemoteApp do Senior, envia comandos de teclado previsíveis e sincroniza a execução por sinais observáveis do Windows, como janelas nativas e arquivos criados.

## Instalação

```powershell
pip install -e ".[windows,dev]"
```

## Uso rápido

Valide os parâmetros e os caminhos sem acionar o Senior:

```powershell
seniorbot f141cis --dry-run --serie 036 --cfops 5101 5102 --date 2026-07-01
```

Execute a exportação F141CIS:

```powershell
seniorbot f141cis --yes --serie 036 --cfops 5101 5102 6101 6102 5910 6910
```

No uso manual, sem `--yes`, o SeniorBot pergunta a data inicial e final do filtro. Pressione ENTER para usar a data de hoje.

O `--yes` pula apenas a confirmação inicial, mas ainda pergunta as datas do filtro.

Para informar as datas direto no comando:

```powershell
seniorbot f141cis --yes --start-date 01/07/2026 --end-date 01/07/2026
```

Para rodar sem perguntar datas, como no agendamento, use:

```powershell
seniorbot f141cis --yes --use-today
```

Para abrir a Area de Trabalho Remota, iniciar o Senior e depois executar a F141CIS:

```powershell
seniorbot f141cis --open-rdp --yes
```

Quando `--date` é usado para reprocessar um dia, essa data também vira o padrão do filtro da tela, a menos que `--start-date` e `--end-date` sejam informados.

Quando `--output` não é informado, o arquivo é salvo automaticamente na pasta mensal:

```text
C:\exportacoes\MM AAAA\DD.MM.xlsx
```

Exemplo para 1 de julho de 2026:

```text
C:\exportacoes\07 2026\01.07.xlsx
```

Para apontar a exportação para a pasta consultada pela planilha mãe, use `--base-dir`:

```powershell
seniorbot f141cis --yes --base-dir "C:\Controle de Faturamento"
```

Quando o caminho de saída usa uma unidade local, o SeniorBot salva pelo caminho RemoteApp equivalente `\\tsclient\...` e aguarda o arquivo local ficar pronto.

Se o arquivo do dia já existir, ele é movido antes para `_backups` dentro da pasta do mês. Exemplo:

```text
C:\exportacoes\07 2026\_backups\01.07.backup-20260701-170000.xlsx
```

Ao final, o SeniorBot mostra um resumo com arquivo, pasta, tamanho e horário.

Os logs ficam em `logs\` dentro da pasta do projeto, a menos que `--log-dir` seja informado.

## Credenciais locais

As credenciais da Area de Trabalho Remota e do Senior nao ficam no codigo. Copie o exemplo:

```powershell
New-Item -ItemType Directory -Force .local
Copy-Item remoteapp.env.example .local\remoteapp.env
```

Depois edite `.local\remoteapp.env` com os dados da sua maquina. Essa pasta e arquivos `.env` sao ignorados pelo Git.

Variaveis esperadas:

```text
RDP_HOST=10.15.1.130
RDP_PASSWORD=sua_senha_do_windows_remoto
SENIOR_SHORTCUT_PATH=\\SRVAPP01\SapiensProducao\Sapiens\Gestão Empresarial (ERP).lnk
SENIOR_USER=seu_usuario_do_senior
SENIOR_PASSWORD=sua_senha_do_senior
```

Se o IP da Area de Trabalho Remota estiver sendo digitado antes da janela carregar, aumente:

```text
MSTSC_READY_DELAY=5
```

## Agendamento

Para criar ou atualizar a tarefa diária das 17:00 no Agendador de Tarefas do Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_f141cis_task.ps1
```

A tarefa usa `launchers\seniorbot-f141cis-scheduled.cmd`, que executa sem pausa e sem confirmação manual. O Senior ainda precisa estar aberto na tela inicial para a automação atual funcionar.

## Exemplo em Python

```python
from pathlib import Path

from seniorbot import SeniorBot

bot = SeniorBot()
bot.export_xlsx(Path(r"C:\Temp\consulta.xlsx"))
```

## Princípios do projeto

- Não usar coordenadas de mouse.
- Não depender de reconhecimento de imagem.
- Preferir `pywinauto` para foco de janelas, diálogos e entrada de teclado.
- Separar os fluxos específicos do ERP das camadas reutilizáveis de janela, teclado e sincronização.
- Usar timeouts explícitos e esperas observáveis em vez de pausas fixas sempre que possível.

## Testes

```powershell
python -m unittest
```
