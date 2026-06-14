# Índice da Documentação — Polo Médio Amazonas 2026

> Atualizado em 14/06/2026. Para o mapa de tarefas → arquivos, consulte `CLAUDE.md` na raiz.

---

## Arquivos raiz de docs/

| Arquivo | Conteúdo |
|---------|---------|
| `firebase.md` | Schema do Firestore, autenticação, regras de segurança, funções JS do Firebase |
| `automacao.md` | Projeto 1 (afastamentos), Projeto 2 (diário completo), backfill, secrets |
| `arquitetura.md` | Decisões de design, padrão de cache localStorage, arquiteturas internas |
| `historico-sessoes.md` | Log cronológico do que foi implementado por sessão |
| `diario-oficial-completo-2026.json` | Saída do Projeto 2, atualizado automaticamente |
| `designacoes-2026.json` | Defensores, DPs e histórico de titulares (base do site) |
| `afastamentos-2026.json` | Eventos base de afastamentos (Firestore tem prioridade) |
| `diario-oficial-categorias.md` | Regras de categorização de portarias para o Claude |
| `diario-oficial-polo-medio-2026.md` | ⚠️ Legado — não usar |
| `diario-oficial-polo-medio-2026.json` | ⚠️ Legado — não usar |

---

## defensores/

Um arquivo por defensor. Contém status, DPs titulares, grupo de alternância e histórico de ausências.

| Arquivo | Defensor | Status |
|---------|---------|--------|
| `enio.md` | Ênio Jorge Lima Barbalho Junior | ✅ Ativo (desde 02/05/2026) |
| `thays.md` | Thays Lidianne Campos de Azevedo Pereira | ✅ Ativo (desde 30/04/2026) |
| `icaro.md` | Ícaro Oliveira Avelar Costa | ✅ Ativo |
| `eliaquim.md` | Eliaquim Antunes de Souza Santos | ✅ Ativo |
| `emilly.md` | Emilly Bianca Ferreira dos Santos | ✅ Ativo (desde 02/05/2026) |
| `miguel.md` | Miguel Eduardo de Azevedo Martins Filho | ✅ Ativo (desde 01/03/2026) |
| `jose-antonio.md` | José Antônio Pereira da Silva | ❌ Ex-membro (saiu 02/05/2026) |
| `elton.md` | Elton Dariva Staub | ❌ Ex-membro (saiu 02/05/2026) |
| `elaine.md` | Elaine Maria Sousa Frota | ❌ Ex-membro (saiu 02/05/2026) |
| `mariana.md` | Mariana Silva Paixão | ❌ Ex-membro (saiu 30/12/2025 — 11º Concurso de Remoção) |
| `isabela.md` | Isabela do Amaral Sales | ❌ Ex-membro (cedida a órgão externo — nunca atuou no polo) |

## defensorias/

| Arquivo | Conteúdo |
|---------|---------|
| `lista-completa.md` | Lista das 12 DPs com defensor titular atual, grupos e ex-membros |
| `grupos-alternancia.md` | Definição do Grupo A e Grupo B (composição pós mai/2026) |

## regras/

| Arquivo | Conteúdo |
|---------|---------|
| `alternancia.md` | Regra de alternância semanal, exemplos e checklists |
| `ausencias.md` | Limites de ausência, tipos (férias/folga/licença), interpretação de textos |
| `destaques-cores.md` | Classes CSS `itacoatiara` e `silves`, regra de fins de semana |

## escalas/

> ⚠️ Estes arquivos têm dados de **janeiro/2026**. A fonte de verdade atual é o **Firestore** (`afastamentos_admin`), acessível via interface admin no site.

| Arquivo | Conteúdo | Situação |
|---------|---------|---------|
| `ferias-folgas-2026.md` | Tabela mestra de ausências (gerada manualmente) | Desatualizado após abr/2026 |
| `calendario-visual-2026.md` | Calendário visual mês a mês com emojis | Desatualizado após abr/2026 |
| `designacoes-janeiro-2026.md` | Tabelas diárias de janeiro/2026 | Histórico — não atualizar |

## site/

| Arquivo | Conteúdo |
|---------|---------|
| `estrutura-html.md` | Seções, abas, IDs, fontes de dados JS, cache localStorage |
| `padroes-codigo.md` | HTML das tabelas, abreviações dos defensores, formato de datas |
| `validacoes-js.md` | Funções JS principais: inicialização, calendário, RTE, sinos |
| `processo-atualizacao.md` | Como atualizar afastamentos, titulares e seções editáveis via admin UI |

## raiz de docs/

| Arquivo | Conteúdo | Situação |
|---------|---------|---------|
| `diario-oficial-completo-2026.json` | JSON atualizado automaticamente pelo Projeto 2 (verificar-diario-completo.py) | ✅ Ativo |
| `designacoes-2026.json` | Defensores, DPs e histórico de titulares (base) | ✅ Ativo — fonte base do site |
| `afastamentos-2026.json` | Eventos base de afastamentos | ✅ Ativo — base; Firestore tem prioridade |
| `diario-oficial-categorias.md` | Regras de categorização de portarias para o Claude | Referência para a automação |
| `diario-oficial-polo-medio-2026.md` | Transcrição bruta legada (formato antigo) | ⚠️ Legado — não usar |
| `diario-oficial-polo-medio-2026.json` | JSON legado (substituído pelo completo-2026.json) | ⚠️ Legado — não usar |
