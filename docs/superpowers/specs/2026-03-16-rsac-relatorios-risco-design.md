# Design: RSAC Exportação de Relatórios de Risco

## Contexto

Projeto novo para automação de exportação dos Relatórios de Risco Social, Ambiental e Climático no ecossistema Jarbis.

Referências obrigatórias:

- Projeto 1: `dash_portal_chamados`
  - Preservar boas práticas de organização e a abordagem de utilitários web em `utils/rpa_actions.py`
- Projeto 2: `analisecredito_f3`
  - Preservar a separação `Dispatcher` e `Performer`
  - Preservar uso da `lib_sisbr_desktop`
  - Preservar padrão de integração com banco/Jarbis inspirado no `database.py`

Restrições já confirmadas:

- Responder e registrar logs em pt-BR
- Credenciais e segredos ficam no `.env`
- Seletores web ainda não foram entregues; serão recebidos depois para derivação de XPath
- O projeto deve seguir a lógica do perfil Jarbis: `docs/screens/<screen>/spec.txt` e `visuals/`
- O código deve ser legível para um júnior
- Evitar validações desnecessárias que aumentem a complexidade sem ganho real

Exceção temporária aprovada:

- Como os seletores e `OuterHTML` ainda não foram entregues nesta etapa, a implementação pode avançar normalmente nas camadas de arquitetura, integração, Excel, banco, SharePoint e esqueleto do fluxo
- A fase de automação web RSA ficará formalmente bloqueada até o recebimento desses artefatos
- Antes da implementação da camada web, deverão ser criados os diretórios e arquivos em `docs/screens/...` conforme o padrão Jarbis

## Artefatos validados

Os arquivos existentes no projeto foram validados estruturalmente:

- `Models/Config.xlsx`
  - Arquivo abre corretamente
  - O modelo atual contém abas `Settings`, `Constants`, `Assets` e `QueueItems`
  - O projeto novo, porém, adotará `Settings` e `Items`
- `Models/Modelo_PlanilhaPrincipal.xlsx`
  - Arquivo abre corretamente
  - Possui abas por cooperativa, incluindo abas como `3333`, `3043`, `3059`, `3320`, `3350`, `3351`, `3233`, `3261`, `3332`, `3348`, `4198`, `4332`, `4364`
- `Models/rpas1004_00_RELATORIO_RISCO_COOPERATIVA_20260313_182416_0644.XLSX.XLSX.XLSX`
  - Arquivo abre corretamente
  - Possui a aba `Relatório Database`

Conclusão da validação:

- O modelo principal e o relatório baixado são compatíveis com uma estratégia de copiar dados por cooperativa, limpando apenas a área de dados da aba correspondente e preservando a estrutura da planilha modelo

## Decisões de design aprovadas

### Configuração

O projeto usará um `Config.xlsx` próprio com duas abas principais:

- `Settings`
  - Armazena parâmetros de negócio, links base, padrões de nome de arquivo, destino SharePoint, competência, destinatários, placeholders e demais ajustes globais
- `Items`
  - Representa a carga operacional do Dispatcher
  - Mantém a lógica atual de itens que já existe hoje
  - Preserva o contrato da aba `QueueItems`, apenas renomeada para `Items`

### Contrato da aba `Items`

O projeto novo deve preservar a estrutura lógica já existente na aba `QueueItems`, agora sob o nome `Items`, com estas colunas:

- `Reference`
- `Tipo Relatorio`
- `Timeout`
- `Cooperativa`
- `PA`
- `Nome Cooperativa 1`
- `Nome Cooperativa 2`
- `Destinatarios`
- `Sharepoint`
- `Nome Arquivo`
- `Extensao`

Regras aprovadas:

- fórmulas existentes devem ser preservadas
- placeholders como `{Data}` e `{YYYY-MM}` fazem parte do contrato do arquivo
- o projeto deve suportar substituição de placeholders em valores e fórmulas, sem simplificar esse modelo
- `Settings` também pode conter valores dinâmicos de negócio, links base, padrões e destinatários
- dados específicos por cooperativa/item lidos em `Items` têm precedência sobre defaults globais de `Settings`
- `Settings` atua como fonte de defaults globais e placeholders compartilhados
- a `Reference` oficial do item vem da própria planilha `Items`; o código não deve recalculá-la
- o código deve apenas resolver placeholders e validar que a `Reference` final não está vazia

### Chave de referência do item

A `Reference` canônica do item será:

`{cooperativa}_RSAC_RISCO_{MMYYYY}`

Exemplo:

`3333_RSAC_RISCO_032026`

### Consolidação

- A execução gera um arquivo único consolidado mensal
- O consolidado nasce como cópia do `Modelo_PlanilhaPrincipal.xlsx`
- O nome do arquivo precisa evidenciar mês e ano
- Se houver reprocessamento ou retomada no mesmo mês, a automação deve localizar o consolidado já criado e continuar a partir dele

### Preenchimento da planilha

Para cada cooperativa:

- localizar a aba homônima no consolidado, por exemplo `3333`
- localizar a tabela pela linha de cabeçalho equivalente ao relatório
- preservar a linha de cabeçalho
- limpar apenas a área de dados abaixo do cabeçalho até a última linha usada da tabela
- preservar estrutura, títulos, formatação, fórmulas e demais elementos
- inserir os dados novos do relatório baixado correspondente

### Identificação da cooperativa no relatório baixado

Validação feita no arquivo de exemplo:

- `A3` representa a central
- `B5` contém os critérios, incluindo `SINGULAR`
- a linha de cabeçalho da tabela está em `A6:F6`
- os dados começam na linha 7
- a cooperativa alvo aparece na coluna `B` das linhas de dados
- a competência aparece na coluna `E`

Contrato aprovado para leitura do relatório:

- usar a primeira linha de dados válida da coluna `B` como fonte principal para identificar a cooperativa
- usar `B5` como validação auxiliar da singular
- assumir, nesta etapa, que o layout é estável com cabeçalho na linha 6 e dados iniciando na linha 7

### Evidências e limpeza

- Manter os arquivos individuais baixados de forma organizada apenas como temporários locais de trabalho
- Executar rotina de limpeza local para remover temporários com mais de 15 dias

### E-mail final

O e-mail de encerramento do job deve ser enviado em todos os cenários:

- sucesso total
- sucesso parcial
- falha

O conteúdo precisa resumir o que concluiu e o que ficou pendente ou com erro.

### Estratégia operacional do Performer

Foi aprovada a abordagem 1:

- o `Dispatcher` cria itens por cooperativa e competência
- o `Performer` pega vários itens pendentes de uma mesma competência
- o `Performer` faz uma única navegação no Sisbr/portal RSA
- o portal permite selecionar várias cooperativas na mesma tela
- o processamento do lote atualiza cooperativas individualmente no consolidado e no banco

## Arquitetura proposta

### Visão geral

Separação em quatro camadas:

1. `Dispatcher`
2. `Performer`
3. `Serviços de domínio`
4. `Camada de automação / integrações`

### Dispatcher

Responsabilidades:

- ler `Config.xlsx`
- interpretar `Settings` e `Items`
- ler a `Reference` de `Items`, resolver placeholders e validar o valor final
- verificar duplicidade por `Reference`
- inserir apenas itens inexistentes no banco/Jarbis

Não faz:

- download de relatório
- manipulação do consolidado
- upload para SharePoint

### Performer

Responsabilidades:

- buscar itens pendentes da competência
- identificar ou criar o consolidado mensal
- detectar cooperativas ainda não preenchidas no consolidado
- abrir Sisbr 2.0 com `lib_sisbr_desktop`
- acessar o módulo RSA no Sisbr e localizar/controlar automaticamente a aba web do portal RSA
- selecionar cooperativas em lote
- exportar relatórios
- processar arquivos baixados individualmente
- atualizar o consolidado
- salvar incrementalmente
- fazer upload para SharePoint
- organizar evidências locais
- enviar e-mail final

### Contrato final da solução

Quando a solução estiver completa, o `Performer` será responsável pelo fluxo fim a fim:

- abrir Sisbr 2.0
- acessar o módulo RSA
- localizar e controlar automaticamente a aba web do portal RSA
- selecionar cooperativas em lote
- exportar relatórios
- atualizar consolidado
- publicar incrementalmente no SharePoint

### Escopo desta fase

Nesta fase atual, está liberado implementar:

- arquitetura do projeto
- integração com banco/Jarbis
- leitura de `Config.xlsx`
- serviços de Excel e consolidado
- upload SharePoint
- e-mail
- limpeza de temporários
- esqueleto do fluxo do Performer

Nesta fase atual, está bloqueado implementar a automação web RSA definitiva até o recebimento de seletores e `OuterHTML`.

### Serviços de domínio

Módulos focados em regra de negócio, sem acoplamento direto à UI:

- leitura de `Settings` e `Items`
- geração de `Reference`
- resolução do consolidado mensal
- validação e leitura dos relatórios baixados
- atualização das abas por cooperativa
- montagem de caminhos e nomes de arquivo
- reconciliação de estado do item
- limpeza de temporários
- resumo final de execução

### Camada de automação e integrações

Adaptadores técnicos:

- `lib_sisbr_desktop` para Sisbr 2.0
- `utils/rpa_actions.py` para automação web Selenium
- integração com `database.py` e Jarbis
- integração com SharePoint Graph
- integração com envio de e-mail

## Fluxo operacional

### Dispatcher

1. Ler `Settings`
2. Ler `Items`
3. Ler a `Reference` de cada linha válida, resolver placeholders e validar o resultado
4. Verificar se a `Reference` já existe
5. Inserir item com status inicial quando necessário
6. Registrar em log quando o item for reaproveitado

### Performer

1. Buscar itens pendentes da competência
2. Localizar ou criar o consolidado mensal
3. Avaliar quais abas de cooperativas ainda estão vazias ou incompletas
4. Cruzar isso com os itens pendentes
5. Abrir Sisbr e acessar o módulo RSA
6. Localizar e controlar automaticamente a aba web do portal RSA
7. Selecionar cooperativas em lote na competência
8. Exportar os relatórios
9. Para cada relatório baixado:
   - validar o arquivo
   - identificar a cooperativa
   - limpar a área de dados da aba correspondente
   - gravar novos dados
   - salvar o consolidado incrementalmente
   - reenviar o consolidado ao SharePoint, sobrescrevendo a versão anterior
   - atualizar o item correspondente
10. Ao fim do lote, manter a última versão consolidada já publicada
11. Organizar e manter evidências locais
12. Limpar temporários locais antigos
13. Enviar e-mail final

## Modelo de dados do item

O contrato de persistência deve respeitar a lógica já usada no F3:

- `project_id`
- `job_id`
- `data`
- `status`
- `reference`
- `parent_id` opcional

### Status permitidos

A spec deve respeitar o enum operacional informado pelo usuário:

- `aguardando`
- `em andamento`
- `cancelado`
- `finalizado`

### Política de status

- `aguardando`
  - item criado pelo Dispatcher e ainda não concluído
- `em andamento`
  - item em processamento pelo lote do Performer
  - também pode representar item interrompido no meio do fluxo, apto à reconciliação automática na próxima execução
- `cancelado`
  - reservado para descarte explícito, se houver regra futura
- `finalizado`
  - item concluído após download, atualização da aba, salvamento do consolidado e upload incremental concluído no SharePoint

### Estrutura sugerida do campo `data`

```json
{
  "reference": "3333_RSAC_RISCO_032026",
  "cooperativa": "3333",
  "mes": "03",
  "ano": "2026",
  "competencia": "03/2026",
  "etapa_atual": "upload_incremental_concluido",
  "mensagem_erro": null,
  "nome_arquivo_relatorio": "rpas1004_00_RELATORIO_RISCO_COOPERATIVA_20260313_182416_0644.XLSX.XLSX.XLSX",
  "nome_arquivo_consolidado": "RSAC_03-2026.xlsx",
  "sharepoint_destino": "https://...",
  "ultima_atualizacao": "2026-03-16T12:00:00"
}
```

Observação:

- O progresso fino fica em `data` e nos logs
- O status do item permanece simples para manter aderência ao banco existente

## Retomada e tolerância a falhas

### Fonte de verdade operacional

A retomada não deve depender somente do status do item. A decisão deve considerar:

- consolidado mensal local
- arquivos individuais já baixados
- status do item no banco
- última versão incremental já publicada no SharePoint

Precedência aprovada:

- para decidir se um item pode ser marcado como `finalizado`, vale a versão incremental efetivamente publicada no SharePoint
- para retomar trabalho após falha, vale o consolidado local mais recente, desde que esteja íntegro

### Estratégia de retomada

- localizar o consolidado do mês, se já existir
- verificar quais abas ainda não foram preenchidas ou não foram reconciliadas
- cruzar com os itens em `aguardando` ou `em andamento`
- se existir relatório individual válido, reaproveitá-lo quando seguro
- se a aba já estiver preenchida e o upload incremental correspondente tiver sido concluído, reconciliar o item para `finalizado`
- itens em `em andamento` não bloqueiam nova tentativa; devem ser reavaliados automaticamente pelo estado real do consolidado
- em caso de divergência entre consolidado local e SharePoint:
  - o SharePoint decide o que já pode ser tratado como `finalizado`
  - o consolidado local íntegro decide a base de reprocessamento das próximas cooperativas

### Tratamento de falhas

- falha ao abrir/login no Sisbr ou chegar ao portal
  - aborta o lote
  - gera e-mail de falha
- falha em cooperativa específica
  - registra erro da cooperativa
  - continua nas demais
- falha ao escrever na aba
  - mantém o item em `em andamento`
  - continua no lote quando possível
- falha no upload SharePoint
  - o consolidado salvo localmente permanece como base de retomada
  - como o upload é incremental por cooperativa, apenas o item cuja atualização ainda não foi publicada deixa de ser finalizado
- falha no envio do e-mail
  - não invalida o processamento principal
  - precisa ser registrada em destaque

## Observabilidade

Logs obrigatórios em pt-BR para ações relevantes. Exemplos:

- `Iniciando leitura do arquivo de configuração`
- `Item 3333_RSAC_RISCO_032026 já existe e será reaproveitado`
- `Clicou na aba Relatórios`
- `Relatório da cooperativa 3333 salvo em C:\...`
- `Aba 3333 atualizada no consolidado mensal`
- `Upload concluído para https://...`
- `Falha ao processar cooperativa 3333: ...`

Saídas mínimas de auditoria:

- log técnico em arquivo
- resumo final estruturado em memória/JSON
- e-mail com totais e lista de erros

## Estrutura sugerida do projeto

```text
rsac_relatorios_risco/
├── agent_jarbis.py
├── docs/
│   ├── screens/
│   │   └── ...
│   └── superpowers/
│       └── specs/
├── Models/
├── src/
│   ├── dispatcher/
│   ├── performer/
│   ├── services/
│   ├── web/
│   └── integrations/
├── temp/
├── tests/
├── utils/
│   └── rpa_actions.py
└── .env
```

## Organização dos módulos

### `src/dispatcher/`

- `config_reader.py`
- `items_loader.py`
- `reference_builder.py`
- `dispatch_items.py`

### `src/performer/`

- `run_batch.py`
- `collect_pending_items.py`
- `process_export_lot.py`
- `reconcile_items.py`

### `src/services/`

- `config_service.py`
- `reference_service.py`
- `consolidado_service.py`
- `relatorio_service.py`
- `sharepoint_service.py`
- `email_service.py`
- `cleanup_service.py`
- `item_status_service.py`

### Regra de localização da tabela no consolidado

Para evitar ambiguidade na implementação:

- a aba será escolhida pelo código da cooperativa
- dentro da aba, a tabela alvo será localizada por match exato da linha de cabeçalho esperada do relatório
- se houver exatamente um match exato, ele será usado
- se não houver match, a cooperativa deve ser tratada como erro de estrutura
- se houver mais de um match, a cooperativa deve ser tratada como erro de ambiguidade estrutural

### Placeholders suportados no `Config.xlsx`

Placeholders mínimos já reconhecidos nesta etapa:

- `{Data}`
  - origem: competência operacional no formato `MMYYYY`
  - uso esperado: `Reference` e nomes dinâmicos
- `{YYYY-MM}`
  - origem: competência operacional no formato `YYYY-MM`
  - uso esperado: paths SharePoint e nomes dinâmicos

Regra de resolução:

- placeholders podem aparecer em fórmulas ou valores literais de `Items`
- `Settings` fornece valores globais e contexto de resolução
- `Items` fornece o valor final específico do item/cooperativa

### `src/web/`

- `rsa_portal_flow.py`
- `selectors.py`

### `src/integrations/`

- `database_client.py`
- `jarbis_client.py`
- `sharepoint_client.py`
- `mail_client.py`

## Pontos de preenchimento manual

Devem ficar claramente destacados no código e na documentação:

- credenciais no `.env`
- links base do SharePoint em `Settings`
- padrão de nome do consolidado em `Settings`
- destinatários de e-mail em `Settings` ou `.env`
- seletores/XPath do portal RSA quando forem entregues
- eventual sobrescrita manual de seletores a partir do `OuterHTML` que será entregue em etapa futura

## Estratégia de testes

### Testes locais prioritários

- leitura de `Settings` e `Items`
- geração de `Reference`
- detecção/criação do consolidado mensal
- leitura do relatório baixado
- limpeza e escrita da aba de cooperativa
- montagem dos caminhos SharePoint

### Testes operacionais

- smoke test do Dispatcher
- teste local do processamento de Excel sem automação web
- teste controlado do Performer
- quando os seletores chegarem, teste de automação com browser preservado em falha

## Pipeline inicial de implementação

1. Confirmar os defaults de `Settings` e o mapeamento operacional dos placeholders preservados no `Config.xlsx`
2. Criar esqueleto do projeto e dependências
3. Adaptar `utils/rpa_actions.py`
4. Implementar integração com banco/Jarbis no padrão F3
5. Implementar criação e retomada do consolidado mensal
6. Implementar leitura do relatório baixado e escrita nas abas
7. Implementar limpeza de temporários
8. Implementar upload SharePoint
9. Implementar e-mail final
10. Criar `docs/screens/...` com `spec.txt` e `visuals/` e implementar a automação web RSA quando os seletores/`OuterHTML` forem entregues
11. Criar testes locais e smoke tests

## Riscos e decisões em aberto

- Seletores web ainda não foram recebidos
- A política exata de reaproveitamento do relatório individual local deve ser implementada de forma conservadora

## Contratos fechados nesta etapa

- o `Performer` executa o fluxo fim a fim, inclusive abrindo Sisbr, acessando o módulo RSA e controlando a aba web automaticamente
- a aba `Items` preserva a estrutura lógica da antiga `QueueItems`
- placeholders e fórmulas do `Config.xlsx` fazem parte do contrato do projeto
- dados por item em `Items` têm precedência sobre defaults globais em `Settings`
- a `Reference` oficial vem da planilha `Items`
- a cooperativa do relatório é identificada principalmente pela coluna `B` da primeira linha de dados, com validação auxiliar via `B5`
- a linha de cabeçalho da tabela do relatório fica em `A6:F6` e os dados começam na linha 7
- a limpeza da aba do consolidado preserva cabeçalho, estrutura e formatação, limpando apenas as linhas de dados da tabela
- o consolidado é salvo e reenviado ao SharePoint a cada aba preenchida
- cada item pode ser `finalizado` após upload incremental bem-sucedido da versão do consolidado que já contém sua aba atualizada
- itens em `em andamento` podem ser reprocessados automaticamente na próxima execução
- o SharePoint publicado decide finalização; o consolidado local íntegro decide retomada
- arquivos individuais baixados são temporários locais, com retenção de até 15 dias
- o e-mail final é obrigatório em sucesso total, parcial e falha

## Recomendação final

Prosseguir com implementação em arquitetura orientada a lote por competência, preservando:

- `Dispatcher` e `Performer`
- `lib_sisbr_desktop`
- utilitários web inspirados em `utils/rpa_actions.py`
- persistência compatível com o padrão do F3

Essa abordagem oferece:

- melhor eficiência operacional no portal RSA
- retomada segura após falhas
- menor repetição de navegação
- código mais organizado e sustentável para manutenção futura
