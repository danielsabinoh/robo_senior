# Manual Completo do Projeto SeniorBot

Documento para operação, manutenção e transferência de conhecimento.

Projeto: `Robo-Senior` / pacote `seniorbot`

Objetivo principal: automatizar a exportação diária do relatório de faturamento da tela F141CIS do Senior Gestão Empresarial, salvar os arquivos em planilhas diárias, copiar os arquivos para o servidor da empresa e permitir que a planilha mãe consolide os dados pelo Power Query.

---

## 1. Visão Geral Para Quem Nunca Programou

Este projeto é um robô de teclado. Ele não conversa diretamente com o banco de dados do Senior e não usa API do Senior. Ele faz o mesmo caminho que uma pessoa faria:

1. Abre a Área de Trabalho Remota.
2. Entra no ambiente remoto.
3. Abre o Senior.
4. Faz login no Senior.
5. Abre a tela F141CIS.
6. Preenche filtros de data, série e CFOP.
7. Exibe a grade.
8. Abre o menu de exportação.
9. Salva a planilha do dia.
10. Fecha o Senior e a sessão remota.
11. Copia a planilha local para o servidor.
12. Apaga a cópia local somente depois de confirmar que o arquivo chegou ao servidor.

O projeto existe porque a rotina manual exigia exportar todos os dias uma planilha filha, como:

```text
C:\exportacoes\07 2026\01.07.xlsx
C:\exportacoes\07 2026\02.07.xlsx
C:\exportacoes\07 2026\03.07.xlsx
```

A planilha mãe consulta essas filhas pelo Power Query.

No desenho final, a planilha mãe deve consultar a pasta no servidor, não a pasta local do computador do operador. Assim outros usuários conseguem atualizar a planilha mãe sem depender do disco local do operador.

---

## 2. Fluxo Final Esperado

O fluxo diário agendado é:

1. O Windows dispara a tarefa `SeniorBot F141CIS diario` às 17:00.
2. A tarefa chama o arquivo `.local\seniorbot-f141cis-daily.cmd`.
3. Esse arquivo chama `scripts\run_f141cis_daily.ps1`.
4. O script executa:

```powershell
python -m seniorbot f141cis --open-rdp --yes --use-today --delay 0 --serie 036 --cfops 5101 5102 6101 6102 5910 6910
```

5. O robô abre o RDP, abre o Senior e exporta o arquivo do dia.
6. O arquivo é salvo primeiro em:

```text
C:\exportacoes\MM AAAA\DD.MM.xlsx
```

Exemplo:

```text
C:\exportacoes\07 2026\03.07.xlsx
```

7. Depois o script copia a pasta local para o servidor.
8. Depois de confirmar que o arquivo existe no servidor com o mesmo tamanho, ele apaga o arquivo local.

Importante: o script de cópia não apaga arquivos antigos do servidor. Ele acrescenta e atualiza arquivos.

---

## 3. Pastas e Caminhos Importantes

Pasta do projeto:

```text
C:\Users\Giuliano\Robo-Senior
```

Pasta local de exportação:

```text
C:\exportacoes
```

Pasta mensal local:

```text
C:\exportacoes\07 2026
```

Arquivo diário:

```text
C:\exportacoes\07 2026\03.07.xlsx
```

Pasta de logs do robô:

```text
C:\Users\Giuliano\Robo-Senior\logs
```

Arquivo de credenciais local:

```text
C:\Users\Giuliano\Robo-Senior\.local\remoteapp.env
```

Arquivo gerado para o Agendador:

```text
C:\Users\Giuliano\Robo-Senior\.local\seniorbot-f141cis-daily.cmd
```

Arquivo gerado para abrir o RDP:

```text
C:\Users\Giuliano\Robo-Senior\.local\seniorbot-rdp.rdp
```

Pasta no servidor:

```text
\\srv-banco\Servidor Antigo\Compartilhado\Exportacoes
```

Use o caminho real configurado na empresa. O exemplo acima foi usado durante os testes.

---

## 4. Pré-Requisitos

O computador que executa o robô precisa ter:

- Windows.
- Python instalado.
- Acesso à rede da empresa.
- Permissão para acessar o servidor `srv-banco`.
- Permissão para abrir a Área de Trabalho Remota.
- Permissão para entrar no Senior.
- O projeto em `C:\Users\Giuliano\Robo-Senior`.
- O arquivo `.local\remoteapp.env` preenchido.
- O Power Query da planilha mãe apontando para a pasta do servidor.

Instalação das dependências Python:

```powershell
cd C:\Users\Giuliano\Robo-Senior
pip install -e ".[windows,dev]"
```

---

## 5. Credenciais e Arquivo `.env`

As senhas não devem ficar no GitHub. Elas ficam em:

```text
.local\remoteapp.env
```

Para criar o arquivo:

```powershell
cd C:\Users\Giuliano\Robo-Senior
New-Item -ItemType Directory -Force .local
Copy-Item remoteapp.env.example .local\remoteapp.env
```

Depois edite:

```text
.local\remoteapp.env
```

Campos principais:

```text
RDP_HOST=10.15.1.130
RDP_PASSWORD=sua_senha_do_windows_remoto
SENIOR_SHORTCUT_PATH="C:\Users\Public\Desktop\Senior Produção\Sapiens\Gestão Empresarial (ERP).lnk"
SENIOR_USER=seu_usuario_do_senior
SENIOR_PASSWORD=sua_senha_do_senior
SENIOR_RUN_REUSE_LAST=true
RDP_REDIRECT_DRIVES=true
```

O arquivo `.gitignore` já ignora `.local` e arquivos `.env`, então essas senhas não devem subir para o GitHub.

---

## 6. Como Testar Manualmente

Entre na pasta do projeto:

```powershell
cd C:\Users\Giuliano\Robo-Senior
```

Teste sem acionar o Senior:

```powershell
python -m seniorbot f141cis --dry-run --use-today
```

Teste completo pelo RDP, usando o dia atual:

```powershell
python -m seniorbot f141cis --open-rdp --yes --use-today
```

Teste completo pelo RDP mantendo a sessão aberta no fim:

```powershell
python -m seniorbot f141cis --open-rdp --yes --use-today --keep-rdp-open
```

Use `--keep-rdp-open` quando estiver diagnosticando algo visualmente.

---

## 7. Como Instalar ou Atualizar a Tarefa Agendada

Abra o PowerShell na pasta do projeto:

```powershell
cd C:\Users\Giuliano\Robo-Senior
```

Instale a tarefa diária às 17:00:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_f141cis_task.ps1 -ServerDestination "\\srv-banco\Servidor Antigo\Compartilhado\Exportacoes" -LocalExportPath C:\exportacoes
```

Para mudar o horário:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_f141cis_task.ps1 -ServerDestination "\\srv-banco\Servidor Antigo\Compartilhado\Exportacoes" -LocalExportPath C:\exportacoes -TaskTime "17:30"
```

O nome da tarefa criada é:

```text
SeniorBot F141CIS diario
```

Para consultar pelo terminal:

```powershell
schtasks /Query /TN "SeniorBot F141CIS diario"
```

Para consultar com detalhes:

```powershell
schtasks /Query /TN "SeniorBot F141CIS diario" /V /FO LIST
```

Para remover a tarefa:

```powershell
schtasks /Delete /TN "SeniorBot F141CIS diario" /F
```

Para desativar sem apagar:

```powershell
schtasks /Change /TN "SeniorBot F141CIS diario" /Disable
```

Para ativar novamente:

```powershell
schtasks /Change /TN "SeniorBot F141CIS diario" /Enable
```

---

## 8. Onde Ver a Tarefa no Windows

1. Aperte `Win + R`.
2. Digite:

```text
taskschd.msc
```

3. Pressione ENTER.
4. Clique em `Biblioteca do Agendador de Tarefas`.
5. Procure por:

```text
SeniorBot F141CIS diario
```

Ela fica na pasta raiz:

```text
\
```

Não procure dentro das pastas da Microsoft.

---

## 9. Cópia Para o Servidor

Script responsável:

```text
scripts\sync_exportacoes_to_server.ps1
```

Uso simples:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync_exportacoes_to_server.ps1 -Destination "\\srv-banco\Servidor Antigo\Compartilhado\Exportacoes"
```

Uso apagando o local depois de confirmar a cópia:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync_exportacoes_to_server.ps1 -Destination "\\srv-banco\Servidor Antigo\Compartilhado\Exportacoes" -DeleteSourceAfterCopy
```

Com origem personalizada:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync_exportacoes_to_server.ps1 -Source "C:\exportacoes" -Destination "\\srv-banco\Servidor Antigo\Compartilhado\Exportacoes" -DeleteSourceAfterCopy
```

Comportamento:

- Cria pastas no servidor quando necessário.
- Copia arquivos novos.
- Atualiza arquivos que mudaram.
- Não apaga arquivos antigos do servidor.
- Se `-DeleteSourceAfterCopy` estiver ativo, apaga o arquivo local somente se o arquivo existir no destino e tiver o mesmo tamanho.

Exemplo:

Local:

```text
C:\exportacoes\07 2026\03.07.xlsx
```

Servidor antes:

```text
\\srv-banco\...\Exportacoes\07 2026\01.07.xlsx
\\srv-banco\...\Exportacoes\07 2026\02.07.xlsx
```

Servidor depois:

```text
\\srv-banco\...\Exportacoes\07 2026\01.07.xlsx
\\srv-banco\...\Exportacoes\07 2026\02.07.xlsx
\\srv-banco\...\Exportacoes\07 2026\03.07.xlsx
```

---

## 10. Power Query e Planilha Mãe

Para evitar que outro usuário dependa do disco local do operador, a planilha mãe deve consultar a pasta no servidor.

Recomendado:

```text
\\srv-banco\Servidor Antigo\Compartilhado\Exportacoes
```

Não recomendado:

```text
C:\exportacoes
```

Motivo: se a planilha mãe consultar `C:\exportacoes`, outro usuário não conseguirá atualizar os dados porque esse caminho aponta para o computador local dele, não para o computador do operador original.

---

## 11. Fluxo de Teclado da F141CIS

O roteiro principal está em:

```text
seniorbot\screens.py
```

Fluxo resumido:

1. Confirma caixa inicial do Senior, quando estiver no modo RDP:
   - espera `--senior-startup-delay`;
   - envia 4 TABs;
   - envia ENTER.
2. Espera 1,5 segundo.
3. Envia F11.
4. Digita `F141CIS`.
5. ENTER.
6. Preenche data inicial.
7. TAB.
8. Preenche data final.
9. 8 TABs.
10. Digita série `036`.
11. 11 TABs.
12. ENTER.
13. 4 TABs.
14. Digita os CFOPs:

```text
"5101","5102","6101","6102","5910","6910"
```

15. 2 TABs.
16. 2 setas para cima.
17. 45 TABs.
18. ENTER.
19. ENTER.
20. 8 TABs para focar a grade.
21. Abre menu de exportação com `Shift+F10`.
22. Seleciona exportação com `DOWN` e `ENTER`.

Se a tela do Senior mudar, é nesse roteiro que provavelmente será necessário mexer.

---

## 12. Arquitetura do Projeto

O projeto é dividido em camadas:

### Entrada de comando

Arquivo:

```text
seniorbot\cli.py
```

Responsável por:

- Ler parâmetros do terminal.
- Decidir datas.
- Decidir caminho de saída.
- Abrir RDP quando `--open-rdp` é usado.
- Montar configuração do robô.
- Executar a F141CIS.
- Fechar RDP no fim.
- Configurar logs.

### RDP e abertura do Senior

Arquivo:

```text
seniorbot\remote_desktop.py
```

Responsável por:

- Ler `.local\remoteapp.env`.
- Gerar `.local\seniorbot-rdp.rdp`.
- Abrir `mstsc.exe`.
- Confirmar certificado.
- Enviar senha do RDP quando a tela aparece.
- Abrir Senior dentro da sessão remota.
- Enviar usuário e senha do Senior.

### Roteiro da tela F141CIS

Arquivo:

```text
seniorbot\screens.py
```

Responsável por:

- Abrir F141CIS.
- Preencher datas.
- Preencher série.
- Preencher CFOPs.
- Exibir dados.
- Focar a grade.

### Exportação genérica

Arquivo:

```text
seniorbot\export.py
```

Responsável por:

- Focar janelas quando necessário.
- Abrir menu de contexto.
- Acionar exportação.
- Chamar o salvamento.
- Esperar arquivo aparecer.

### Diálogo de salvar

Arquivo:

```text
seniorbot\dialogs.py
```

Responsável por:

- Salvar arquivo em diálogos nativos do Windows.
- Salvar arquivo em modo RDP/RemoteApp usando teclado e área de transferência.

### Teclado

Arquivo:

```text
seniorbot\keyboard.py
```

Responsável por:

- Enviar ENTER, TAB, F11, ALT+F4, WIN+R, CTRL+V e outros atalhos.
- Converter atalhos para formato aceito pelo `pywinauto`.

### Janelas

Arquivo:

```text
seniorbot\windows.py
```

Responsável por:

- Encontrar janela do RemoteApp.
- Focar janela.
- Procurar diálogo `Salvar como`.

### Configurações internas

Arquivo:

```text
seniorbot\config.py
```

Responsável por:

- Timeouts.
- Padrões de nome de janela.
- Métodos de menu.
- Configurações de exportação.

### Logs

Arquivo:

```text
seniorbot\logging.py
```

Responsável por:

- Criar arquivos de log na pasta `logs`.
- Resetar logging entre execuções.

### Utilitários

Arquivo:

```text
seniorbot\utils.py
```

Responsável por:

- Esperar condição acontecer.
- Esperar arquivo existir e parar de crescer.

---

## 13. Biblioteca de Arquivos do Projeto

### `README.md`

Documentação curta do projeto. Boa para referência rápida.

### `docs\MANUAL_COMPLETO.md`

Fonte editável deste manual.

### `docs\Manual_Completo_SeniorBot.pdf`

Versão PDF deste manual.

### `pyproject.toml`

Define o pacote Python, dependências e comando `seniorbot`.

### `remoteapp.env.example`

Modelo do arquivo de credenciais. Deve ser copiado para `.local\remoteapp.env`.

### `.gitignore`

Define o que não vai para o GitHub. Importante para evitar subir senhas e arquivos temporários.

### `seniorbot\cli.py`

Arquivo central do comando. Onde mexer para adicionar opções de terminal, alterar padrão de data, pasta, fechamento de RDP e comportamento geral.

### `seniorbot\remote_desktop.py`

Onde mexer se a abertura do RDP, login ou abertura do Senior mudar.

### `seniorbot\screens.py`

Onde mexer se o caminho da F141CIS mudar, se a quantidade de TABs mudar ou se novos filtros forem adicionados.

### `seniorbot\export.py`

Onde mexer se o menu de exportação mudar.

### `seniorbot\dialogs.py`

Onde mexer se a janela de salvar mudar.

### `seniorbot\keyboard.py`

Onde mexer se precisar adicionar uma nova tecla ou atalho.

### `seniorbot\windows.py`

Onde mexer se o robô não encontrar a janela do Senior/RemoteApp.

### `seniorbot\config.py`

Onde mexer em timeouts e padrões internos.

### `scripts\install_f141cis_task.ps1`

Instala ou atualiza a tarefa agendada.

### `scripts\run_f141cis_daily.ps1`

Executa o fluxo diário completo: exporta e sincroniza com o servidor.

### `scripts\sync_exportacoes_to_server.ps1`

Copia arquivos locais para o servidor e, opcionalmente, apaga a origem após confirmar.

### `launchers\seniorbot-f141cis-scheduled.cmd`

Launcher antigo. Hoje orienta usar o instalador da tarefa completa.

### `tests\*.py`

Testes automatizados. Eles não abrem o Senior real. Servem para garantir que a lógica e as sequências esperadas continuam coerentes.

---

## 14. Onde Mexer Para Alterações Comuns

### Mudar horário da tarefa

Use:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_f141cis_task.ps1 -ServerDestination "\\srv-banco\Servidor Antigo\Compartilhado\Exportacoes" -TaskTime "18:00"
```

### Mudar pasta local de exportação

No agendamento:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_f141cis_task.ps1 -ServerDestination "\\srv-banco\Servidor Antigo\Compartilhado\Exportacoes" -LocalExportPath "C:\NovaPasta"
```

No comando manual:

```powershell
python -m seniorbot f141cis --open-rdp --yes --use-today --base-dir "C:\NovaPasta"
```

### Mudar pasta do servidor

Reinstale a tarefa com novo destino:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_f141cis_task.ps1 -ServerDestination "\\srv-banco\NovaPasta\Exportacoes"
```

### Mudar CFOPs

Arquivo:

```text
scripts\run_f141cis_daily.ps1
```

Procure:

```powershell
--cfops 5101 5102 6101 6102 5910 6910
```

Altere a lista.

Também existe padrão no código:

```text
seniorbot\screens.py
```

Classe:

```text
F141CISFilters
```

### Mudar série

No script diário:

```powershell
--serie 036
```

### Mudar espera antes da caixa inicial do Senior

No comando:

```powershell
--senior-startup-delay 15
```

No padrão do código:

```text
seniorbot\cli.py
```

Procure:

```text
--senior-startup-delay
```

### Manter RDP aberto para teste

Use:

```powershell
--keep-rdp-open
```

### Salvar no C: remoto em vez de `\\tsclient`

Use:

```powershell
--rdp-save-remote
```

Não é o fluxo recomendado para produção porque a planilha mãe precisa acessar a pasta no servidor.

---

## 15. Diagnóstico Por Sintoma

### A tarefa não aparece no Agendador

Consultar pelo terminal:

```powershell
schtasks /Query /TN "SeniorBot F141CIS diario"
```

Se aparecer no terminal, ela existe. No Agendador visual, procure na raiz da `Biblioteca do Agendador de Tarefas`.

### O RDP não abre

Verifique:

- `.local\remoteapp.env`
- `RDP_HOST`
- permissão de Área de Trabalho Remota
- se `mstsc.exe` abre manualmente

### A senha do RDP é digitada cedo demais

No `.local\remoteapp.env`, aumente:

```text
RDP_PASSWORD_READY_DELAY=4
RDP_PASSWORD_PROMPT_TIMEOUT=8
```

### O aviso de certificado não confirma

Aumente:

```text
RDP_CERTIFICATE_READY_DELAY=4
```

### O Senior não abre depois de Win+R

O fluxo atual usa:

```text
Win+R -> TAB -> ENTER
```

Arquivo:

```text
seniorbot\remote_desktop.py
```

Método:

```text
_run_last_command
```

Se precisar digitar o caminho do atalho de novo, altere no `.env`:

```text
SENIOR_RUN_REUSE_LAST=false
```

### O login do Senior começa cedo demais

Aumente:

```text
SENIOR_LOGIN_READY_DELAY=5
SENIOR_LOAD_DELAY=30
```

### O F11 não abre a busca

Possíveis causas:

- Senior ainda não carregou.
- Caixa inicial não foi confirmada.
- Foco não voltou para a janela certa.

Aumente:

```powershell
--senior-startup-delay 15
```

Ou ajuste:

```text
seniorbot\screens.py
```

### A F141CIS abriu, mas filtros ficaram errados

Provável mudança na tela ou quantidade de TABs.

Arquivo:

```text
seniorbot\screens.py
```

Método:

```text
fill_filters
```

### Não abre menu de exportação

Arquivo:

```text
seniorbot\export.py
```

Configuração atual:

```text
context_menu_method="shift_f10"
export_confirm_keys=("{DOWN}", "{ENTER}")
```

Se o menu mudar, talvez seja necessário mudar a sequência `DOWN + ENTER`.

### Erro com `\\tsclient`

O RDP precisa ser aberto com redirecionamento de disco.

No `.local\remoteapp.env`:

```text
RDP_REDIRECT_DRIVES=true
```

O arquivo `.local\seniorbot-rdp.rdp` é gerado automaticamente com:

```text
redirectdrives:i:1
drivestoredirect:s:*
```

### Arquivo não copia para o servidor

Teste manual:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync_exportacoes_to_server.ps1 -Destination "\\srv-banco\Servidor Antigo\Compartilhado\Exportacoes"
```

Verifique:

- acesso à rede;
- permissão de escrita;
- caminho correto;
- logs em `logs\sync-exportacoes-*.log`.

### Arquivo local não apaga

O arquivo local só é apagado quando o arquivo no servidor existe e tem o mesmo tamanho.

Se não apagou, o script provavelmente preservou por segurança.

---

## 16. Logs

Logs ficam em:

```text
C:\Users\Giuliano\Robo-Senior\logs
```

Tipos comuns:

```text
seniorbot-AAAAMMDD-HHMMSS.log
sync-exportacoes-AAAAMMDD-HHMMSS.log
```

Quando der erro, sempre veja o log mais recente.

Comando para listar logs mais recentes:

```powershell
Get-ChildItem logs | Sort-Object LastWriteTime -Descending | Select-Object -First 10
```

---

## 17. Testes Automatizados

Rodar todos os testes:

```powershell
cd C:\Users\Giuliano\Robo-Senior
python -m unittest
```

Os testes atuais validam:

- comandos de teclado esperados;
- fluxo de tela F141CIS;
- fluxo RDP;
- caminhos `\\tsclient`;
- cópia e logs;
- comportamento do CLI.

Os testes não garantem que o Senior real não mudou. Eles garantem que o código continua fazendo o que foi desenhado.

---

## 18. Como Gerar Executáveis

Existe script:

```text
scripts\build_exe.ps1
```

Uso:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_exe.ps1
```

Também existem specs:

```text
seniorbot.spec
seniorbot-f141cis.spec
```

Eles são usados pelo PyInstaller para empacotar o robô.

Se estiver usando a instalação atual por Python, os executáveis não são obrigatórios.

---

## 19. Segurança e Cuidados

Nunca suba para o GitHub:

```text
.local\remoteapp.env
*.env
```

Não coloque senha no README.

Não use `/MIR` com `robocopy` nesse processo sem revisar muito bem. O `/MIR` espelha pastas e pode apagar arquivos no destino.

O script atual foi desenhado para não apagar nada do servidor.

Ao alterar sequências de teclado, teste com:

```powershell
python -m seniorbot f141cis --open-rdp --yes --use-today --keep-rdp-open
```

Assim a sessão fica aberta para conferir visualmente.

---

## 20. Rotina Recomendada Para Manutenção

Antes de alterar:

1. Copie a mensagem de erro ou tire print.
2. Veja o log mais recente.
3. Rode o comando manual com `--keep-rdp-open`.
4. Identifique em qual etapa parou.

Depois de alterar:

1. Rode:

```powershell
python -m unittest
```

2. Teste manualmente.
3. Se funcionar, deixe uma descrição de commit.
4. Só então confie no agendamento.

---

## 21. Comandos de Referência

Entrar no projeto:

```powershell
cd C:\Users\Giuliano\Robo-Senior
```

Teste seco:

```powershell
python -m seniorbot f141cis --dry-run --use-today
```

Exportação manual completa:

```powershell
python -m seniorbot f141cis --open-rdp --yes --use-today
```

Exportação mantendo RDP aberto:

```powershell
python -m seniorbot f141cis --open-rdp --yes --use-today --keep-rdp-open
```

Instalar agendamento:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_f141cis_task.ps1 -ServerDestination "\\srv-banco\Servidor Antigo\Compartilhado\Exportacoes" -LocalExportPath C:\exportacoes
```

Consultar agendamento:

```powershell
schtasks /Query /TN "SeniorBot F141CIS diario"
```

Remover agendamento:

```powershell
schtasks /Delete /TN "SeniorBot F141CIS diario" /F
```

Sincronizar manualmente:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync_exportacoes_to_server.ps1 -Destination "\\srv-banco\Servidor Antigo\Compartilhado\Exportacoes"
```

Sincronizar e apagar origem:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\sync_exportacoes_to_server.ps1 -Destination "\\srv-banco\Servidor Antigo\Compartilhado\Exportacoes" -DeleteSourceAfterCopy
```

Rodar testes:

```powershell
python -m unittest
```

---

## 22. Resumo Executivo

O SeniorBot é uma automação de teclado para exportar diariamente o faturamento da F141CIS.

O agendamento diário chama um script que:

1. abre o RDP;
2. abre o Senior;
3. exporta a F141CIS do dia;
4. salva em `C:\exportacoes`;
5. copia para o servidor;
6. apaga o arquivo local confirmado;
7. deixa a planilha mãe consumir os dados no servidor.

Para operação comum, o responsável precisa saber:

- consultar a tarefa `SeniorBot F141CIS diario`;
- olhar logs em `logs`;
- editar `.local\remoteapp.env` quando senha ou tempo mudar;
- reinstalar o agendamento se mudar caminho do servidor ou horário;
- rodar `python -m unittest` após mudanças no projeto.

---

Fim do manual.
