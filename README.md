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

No modo `--open-rdp`, o SeniorBot abre a Área de Trabalho Remota com redirecionamento de disco habilitado. Assim o caminho `\\tsclient\C\...` aponta para o `C:` do seu computador local, e a planilha mãe consegue consultar o arquivo normalmente. Se precisar salvar somente dentro do computador remoto, use `--rdp-save-remote`.

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
SENIOR_SHORTCUT_PATH="C:\Users\Public\Desktop\Senior Produção\Sapiens\Gestão Empresarial (ERP).lnk"
SENIOR_USER=seu_usuario_do_senior
SENIOR_PASSWORD=sua_senha_do_senior
```

Mantenha o `SENIOR_SHORTCUT_PATH` com aspas quando houver espaços ou acentos.

Por padrão, o robô digita os textos pelo teclado. Se precisar testar colagem pela área de transferência, habilite:

```text
RDP_USE_CLIPBOARD=true
```

Para abrir o Senior dentro da sessão remota, o padrão é reutilizar o último comando do Executar. Ou seja: o robô aperta `Win+R` e depois ENTER, sem digitar o caminho do atalho:

```text
SENIOR_RUN_REUSE_LAST=true
```

Antes de usar esse modo, abra manualmente o Executar dentro da Área de Trabalho Remota, digite o caminho do atalho do Senior uma vez e pressione ENTER.

Quando `--open-rdp` é usado, o SeniorBot assume que o Senior já está aberto dentro da sessão remota. Ele não procura uma janela local do Senior; depois do login, aguarda a caixa inicial, envia 4 TABs, ENTER, e só então abre a F141CIS com F11.

Depois de exportar com sucesso no modo `--open-rdp`, o SeniorBot confirma a mensagem de arquivo salvo e fecha a sessão remota com `ALT+F4`, ENTER, `ALT+F4`, ENTER. Se a janela RDP local ainda ficar aberta, ele encerra o `mstsc.exe` como reforço. Para manter a sessão aberta durante testes, use `--keep-rdp-open`.

Se precisar ajustar a espera antes dessa caixa inicial:

```text
seniorbot f141cis --open-rdp --yes --senior-startup-delay 5
```

Se o IP da Area de Trabalho Remota estiver sendo digitado antes da janela carregar, aumente:

```text
MSTSC_READY_DELAY=5
```

Se a senha da Area de Trabalho Remota estiver sendo digitada antes da tela de senha aparecer, aumente:

```text
RDP_PASSWORD_READY_DELAY=4
```

Como a tela de senha pode aparecer antes ou depois do aviso de certificado, o robô tenta detectar essa janela nos dois momentos. Para aumentar o tempo dessa detecção:

```text
RDP_PASSWORD_PROMPT_TIMEOUT=8
```

Se o aviso de certificado aparecer depois da senha e o robô confirmar cedo demais, aumente:

```text
RDP_CERTIFICATE_READY_DELAY=4
```

Se o usuário/senha do Senior estiver sendo digitado antes da tela de login carregar, aumente:

```text
SENIOR_LOGIN_READY_DELAY=5
```

## Agendamento

Para criar ou atualizar a tarefa diária das 17:00 no Agendador de Tarefas do Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_f141cis_task.ps1 -ServerDestination "\\srv-banco\Compartilhado\exportacoes"
```

A tarefa executa `scripts\run_f141cis_daily.ps1`, que faz o fluxo completo: abre a Área de Trabalho Remota, exporta a F141CIS, copia os arquivos para o servidor e apaga da pasta local somente depois de confirmar a cópia.

Para usar outro horário:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_f141cis_task.ps1 -ServerDestination "\\srv-banco\Compartilhado\exportacoes" -TaskTime "17:30"
```

## Cópia para o servidor

Se a planilha mãe ficar no servidor, copie a pasta local de exportações para uma pasta compartilhada no servidor e aponte o Power Query para essa pasta compartilhada.

Exemplo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync_exportacoes_to_server.ps1 -Destination "\\srv-banco\Compartilhado\exportacoes"
```

Por padrão, a origem é `C:\exportacoes`. Para usar outra origem:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync_exportacoes_to_server.ps1 -Source "C:\exportacoes" -Destination "\\srv-banco\Compartilhado\exportacoes"
```

O script usa cópia incremental: leva arquivos novos e atualizados para o servidor, mas não apaga arquivos do destino.

Para copiar e apagar os arquivos locais confirmados no servidor:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync_exportacoes_to_server.ps1 -Destination "\\srv-banco\Compartilhado\exportacoes" -DeleteSourceAfterCopy
```

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
