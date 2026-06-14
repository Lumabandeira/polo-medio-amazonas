# Polo Médio Amazonas 2026 — Guia de Contexto para IA

## O que é este projeto

Site HTML responsivo (`index.html`) para gerenciar designações semanais e ausências dos Defensores Públicos do Polo Médio Amazonas em 2026. Tecnologias: HTML5, CSS3, JavaScript vanilla. Publicado via GitHub Pages em https://lumabandeira.github.io/polo-medio-amazonas/

- **6 defensores ativos:** Ênio · Thays · Ícaro · Eliaquim · Emilly · Miguel
- **12 Defensorias Públicas:** DPs 1–6 ocupadas; DPs 7–12 vagas desde 02/05/2026
- **Regra central:** alternância semanal obrigatória entre Grupo A (1ª, 3ª, 6ª DP) e Grupo B (2ª, 4ª, 5ª DP)
- **Firebase:** Auth + Firestore (`polo-medio-as`). Login obrigatório; admins veem botões de edição.

---

## Mapa de Tarefas → Arquivos a Ler

Antes de qualquer alteração, leia **apenas** os arquivos listados para a tarefa.

| Tarefa | Arquivos |
|--------|---------|
| Adicionar férias / folga / licença de defensor | `docs/regras/ausencias.md` · `docs/defensores/[nome].md` · `docs/site/processo-atualizacao.md` |
| Verificar quem é o defensor de uma DP | `docs/defensorias/lista-completa.md` |
| Entender os grupos de alternância | `docs/defensorias/grupos-alternancia.md` · `docs/regras/alternancia.md` |
| Alterar estrutura ou comportamento do site (HTML/CSS/JS) | `docs/site/estrutura-html.md` · `docs/site/padroes-codigo.md` · `docs/site/validacoes-js.md` |
| Consultar ausências de um defensor específico | `docs/defensores/[nome].md` |
| Entender o Firestore (schema, auth, funções JS) | `docs/firebase.md` |
| Entender ou modificar a automação do Diário Oficial | `docs/automacao.md` |
| Entender decisões de arquitetura ou padrão de cache | `docs/arquitetura.md` |
| Ver o que foi implementado em sessões anteriores | `docs/historico-sessoes.md` |

---

## Estrutura de Arquivos

```
index.html                            ← site completo (único arquivo do site)
CLAUDE.md                             ← este índice
verificar-diario-oficial.py           ← Projeto 1: afastamentos → Firestore (06:00 Manaus)
verificar-diario-completo.py          ← Projeto 2: todas portarias → JSON (04:00 Manaus)
backfill-calendario-do-estruturado.py ← backfill histórico do DO
limpar-backfill.py                    ← limpeza de registros duplicados do backfill
docs/
├── INDEX.md                          ← índice de todos os arquivos docs/
├── firebase.md                       ← schema Firestore, auth, funções JS
├── automacao.md                      ← Projeto 1, Projeto 2, backfill
├── arquitetura.md                    ← decisões, padrão de cache, arquiteturas internas
├── historico-sessoes.md              ← log do que foi implementado por sessão
├── defensores/                       ← um arquivo por defensor (ativos e ex-membros)
├── defensorias/                      ← lista-completa.md · grupos-alternancia.md
├── regras/                           ← alternancia.md · ausencias.md · destaques-cores.md
├── escalas/                          ← ferias-folgas-2026.md (desatualizado após abr/2026)
└── site/                             ← estrutura-html.md · padroes-codigo.md · validacoes-js.md · processo-atualizacao.md
```

---

## Estado atual (sessão 24 — 14/06/2026)

**O que falta implementar:**
- Cadastrar os outros 36 usuários restantes no Firebase (1 admin + 35 viewers)
- Dados privados da equipe (WhatsApp, contatos internos)
- Botão "Plantão" — nova seção com escala de plantão (arquitetura a definir)

Para o histórico completo do que foi implementado → `docs/historico-sessoes.md`

---

## Regras Críticas

- **Arquivo único:** existe apenas um `index.html` na raiz. Nunca duplicar.
- **Alternância semanal:** Grupo A e Grupo B alternam toda semana sem exceção.
- **Destaques apenas em dias úteis:** nunca aplicar classes `itacoatiara` ou `silves` em sábados/domingos.
- **Máximo 2 defensores ausentes** ao mesmo tempo; mínimo 3 ativos.
- **Nunca editar seções do Firestore diretamente no HTML** — o conteúdo vem do Firestore e sobrescreve o HTML padrão ao carregar.
- **Fonte de verdade para afastamentos:** Firestore (`afastamentos_admin`). JSONs são a base; Firestore tem prioridade.

---

## Encerramento de sessão (ordem obrigatória)

1. Atualizar arquivos `docs/` afetados pela sessão
2. Atualizar este CLAUDE.md (seção "Estado atual" + número/data da sessão)
3. Commitar tudo junto
