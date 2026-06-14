# Processo de Atualização do Site

> Atualizado em 14/06/2026. O site usa Firestore como fonte de verdade — **não edite afastamentos diretamente no HTML**.

---

## Adicionar Férias / Folga / Licença de Defensor

Todo o fluxo acontece via interface admin no próprio site:

1. Fazer login como admin
2. Ir na aba **Calendário** (dentro de Designações)
3. Clicar em **"+ Novo Afastamento"** (ou clicar em um dia e depois em ➕)
4. Preencher: defensor, tipo, data início, data fim, processo SEI/SGI
5. Para cada DP afetada (preenchida automaticamente): indicar substituto + período de cobertura + portaria
6. Salvar → grava em `afastamentos_admin` no Firestore
7. O calendário e a Lista de Substituições se atualizam automaticamente

> Os dados base continuam nos JSONs (`docs/afastamentos-2026.json`). Registros do Firestore são mesclados por cima em memória. Para corrigir um registro JSON existente, usar o botão ✏️ no modal do dia — isso cria um override no Firestore com campo `json_base_id`.

---

## Atualizar Titular de uma DP

1. Fazer login como admin
2. Ir na aba **Defensorias** (dentro de Designações)
3. Clicar em **✏️** na coluna da DP desejada na tabela "Designações Atuais"
4. No modal: fechar o titular atual (preencher data fim) e adicionar novo titular
5. Salvar → grava em `titulares_admin/{dpKey}` no Firestore

---

## Adicionar Férias / Folga da Equipe (servidores)

1. Fazer login como admin
2. Ir na seção **⛱️ Férias Equipe**
3. Clicar em qualquer dia do calendário → botão **"+ Adicionar"**
4. Preencher: nome, tipo, data início, data fim
5. Salvar → grava em `afastamentos_equipe` no Firestore

---

## Editar Seções de Texto (Alternância / Férias dos Membros)

1. Fazer login como admin
2. Abrir a aba onde a seção aparece
3. Clicar em **✏️ Editar** ao lado do título da seção
4. Editar com a toolbar RTE (negrito, itálico, cores, listas, emojis...)
5. Clicar em **✓ Salvar** → grava em `secoes/{id}` no Firestore

---

## Editar Tabela de Atribuições

1. Fazer login como admin
2. Ir na seção ⚖️ **Atribuições**
3. Clicar em **✏️ Editar tabela**
4. Clicar na célula desejada e editar (toolbar RTE disponível)
5. Clicar em **✓ Salvar** → grava em `secoes/atribuicoes_celulas`

---

## Verificações após qualquer alteração

- [ ] Informação aparece no **Calendário** visual?
- [ ] Informação aparece na **Lista de Substituições**?
- [ ] Informação aparece no **Resumo de Afastamentos**?
- [ ] Cards da aba **Defensorias** refletem o titular correto?
- [ ] Tabelas de **Designações Semanais** mostram o substituto correto?
- [ ] Abrir o console (F12) — sem erros de alternância (`validateAlternation`)?

---

## Publicação no GitHub Pages

O site é publicado automaticamente via GitHub Pages a partir do `index.html` da raiz. Não é necessário nenhum passo manual — qualquer commit na branch `main` atualiza o site em alguns minutos.
