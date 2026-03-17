# Design: RSAC Performer Orchestrator

## Objetivo

Entregar a próxima fase do projeto `rsac_relatorios_risco`: um `Performer` offline-orquestrador que consome a fila de itens do banco, respeita a lógica de `attempts` inspirada na lib UiPath `snc_database`, processa uma cooperativa por vez, reutiliza o consolidado mensal já criado e deixa a camada web RSA apenas como dependência plugável.

Esta fase não implementa ainda:

- seletores finais do portal RSA
- integração real com Selenium em produção
- integração real autenticada com banco/Jarbis, SharePoint e e-mail

Mas deve deixar o fluxo do `Performer` pronto para conectar essas dependências sem alterar a regra de negócio.

## Referências validadas

### Projeto atual

O projeto já possui:

- `dispatcher` funcional
- leitura de `Config.xlsx`
- parser do relatório exportado
- atualização de abas do consolidado
- regras iniciais de reconciliação
- scaffold da camada web RSA
- `utils/rpa_actions.py` portada do projeto de referência

### Lib UiPath `snc_database`

A atividade [UpdateItem.xaml](C:\Users\Guilherme Flexa\Documents\RPAs\Projetos Uipath\snc_database\UpdateItem.xaml) valida apenas os status:

- `processando`
- `sucesso`
- `exceção negocial`
- `erro sistêmico`

Comportamento confirmado:

- item nasce como `pendente`
- ao mudar para `processando`, a lib abre uma nova entrada em `attempts`
- ao mudar para `sucesso`, `exceção negocial` ou `erro sistêmico`, a lib fecha a última tentativa aberta
- a lib não recoloca item para `pendente`

Conclusão:

- a política de reprocessamento não pertence ao `UpdateItem`
- ela pertence ao coletor do `Performer`

## Regras de negócio aprovadas

### Unidade de processamento

O `Performer` trabalha item a item.

Fluxo de alto nível:

1. coleta um item elegível
2. altera status imediatamente
3. processa a cooperativa correspondente
4. salva/publica o consolidado
5. encerra o item
6. coleta o próximo

O portal RSA também será usado item a item:

- escolhe uma única cooperativa no combobox
- exporta o relatório daquela cooperativa
- atualiza a aba correspondente

### Competência

- o robô roda uma vez por mês
- a competência vem do item coletado no banco
- não há mistura de competências dentro do mesmo ciclo operacional esperado

### Consolidado mensal

- deve ser localizado ou criado uma vez no começo da execução
- se já existir para a competência do item, o robô deve reutilizá-lo
- o consolidado precisa ser salvo incrementalmente
- em caso de parada do robô, a próxima execução deve continuar populando o mesmo arquivo

### Status e tentativas

Status padrão do item:

- `pendente`
- `processando`
- `sucesso`
- `erro sistêmico`
- `exceção negocial`

Regra de attempts:

- `processando` abre nova tentativa
- `sucesso`, `erro sistêmico` e `exceção negocial` encerram a última tentativa aberta

### Reprocessamento

O `Performer` não coleta apenas `pendente`.

Ele deve considerar elegíveis:

- `pendente`
- `erro sistêmico`
- `exceção negocial`

Desde que:

- `len(attempts) < MaxAttempts`

Itens que nunca devem ser coletados:

- `processando`
- `sucesso`

### Fonte de `MaxAttempts`

`MaxAttempts` vem do `Config.xlsx`, em `Settings`.

Uso aprovado:

- se `attempts < MaxAttempts`, o item pode ser recolhido automaticamente
- se `attempts >= MaxAttempts`, o item deixa de ser elegível para reprocessamento automático

## Arquitetura proposta

### 1. Coletor de fila

Responsabilidades:

- buscar itens elegíveis no banco
- aplicar filtro por status elegível
- aplicar filtro por `MaxAttempts`
- devolver o próximo item processável

O coletor não decide sucesso nem mexe em Excel.

### 2. Atualizador de item

Responsabilidades:

- abrir tentativa ao marcar `processando`
- fechar tentativa ao marcar `sucesso`, `erro sistêmico` ou `exceção negocial`
- preservar a lógica compatível com a lib UiPath

Esse componente deve espelhar o comportamento da `UpdateItem`.

### 3. Resolver do consolidado

Responsabilidades:

- descobrir o nome/caminho do consolidado mensal a partir da competência do item
- localizar arquivo existente
- criar cópia do modelo quando ainda não existir

### 4. Runner do item

Responsabilidades:

- receber um item já coletado
- executar o fluxo completo daquela cooperativa
- coordenar:
  - fluxo RSA
  - leitura do relatório
  - atualização da aba
  - save local
  - upload incremental
  - atualização final do item

### 5. Orquestrador do Performer

Responsabilidades:

- iniciar a execução
- localizar/criar consolidado mensal
- entrar em loop de coleta
- chamar o runner de item
- acumular resumo operacional
- disparar e-mail final

## Fluxo detalhado do Performer

1. iniciar execução
2. carregar `MaxAttempts` e demais defaults operacionais
3. localizar ou criar o consolidado mensal da competência
4. solicitar próximo item elegível
5. se não houver item elegível, encerrar loop
6. atualizar item para `processando` e abrir nova tentativa
7. executar fluxo da cooperativa:
   - abrir módulo RSA
   - preencher filtros
   - selecionar cooperativa
   - exportar relatório
   - ler relatório baixado
   - atualizar aba da cooperativa
   - salvar consolidado
   - publicar no SharePoint
8. se tudo der certo, atualizar item para `sucesso`
9. se falhar por regra de negócio, atualizar item para `exceção negocial`
10. se falhar por erro técnico, atualizar item para `erro sistêmico`
11. voltar ao passo 4
12. enviar e-mail final com resumo

## Classificação de falhas

### `exceção negocial`

Usar quando houver falha esperada de regra/negócio, por exemplo:

- aba da cooperativa não existe no consolidado
- cabeçalho da tabela está ausente ou ambíguo
- relatório exportado não corresponde à cooperativa esperada
- item ultrapassou uma pré-condição operacional prevista

### `erro sistêmico`

Usar quando houver falha técnica, por exemplo:

- erro de código
- falha de I/O
- indisponibilidade do banco
- falha de upload
- falha inesperada da camada web

## Contratos de dados sugeridos

### Item do banco

Campos relevantes lidos pelo `Performer`:

- `item_id`
- `job_id`
- `project_id`
- `reference`
- `status`
- `data`
- `attempts`

Campos esperados dentro de `data`:

- `cooperativa`
- `competencia`
- `sharepoint`
- `nome_arquivo`
- `extensao`
- outros dados já definidos pelo `Dispatcher`

### Resumo da execução

Estrutura mínima:

- `competencia`
- `concluidos`
- `erros_sistemicos`
- `excecoes_negociais`
- `ignorados_por_max_attempts`
- `consolidado_path`

## Testes previstos

### Unitários

- elegibilidade por status e `MaxAttempts`
- abertura e fechamento de tentativa
- classificação entre erro sistêmico e exceção negocial
- resolução/criação do consolidado mensal
- loop do orquestrador até esgotar itens elegíveis

### Integração local

- item fake do banco gera processamento completo até atualização do consolidado
- falha durante o item gera update correto de status e `attempts`
- retomar com consolidado já existente reutiliza o mesmo arquivo

## Recomendação final

Implementar primeiro um `Performer` offline-orquestrador, com interfaces injetáveis para:

- coletor do banco
- updater de item
- fluxo RSA
- SharePoint
- e-mail

Essa abordagem mantém a regra de negócio estável e permite conectar as integrações reais depois sem reescrever o coração do `Performer`.
