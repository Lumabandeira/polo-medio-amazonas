# Polo Médio Amazonas 2026 — Guia de Contexto para IA

## O que é este projeto

Site HTML responsivo (`index.html`) para gerenciar designações semanais e ausências dos Defensores Públicos do Polo Médio Amazonas em 2026. Tecnologias: HTML5, CSS3, JavaScript vanilla. Publicado via GitHub Pages em https://lumabandeira.github.io/polo-medio-amazonas/

- **5 defensores ativos:** Ênio · Thays · Eliaquim · Emilly · Miguel (Ícaro saiu em 01/06/2026 — 3ª DP coberta cumulativamente pelo Eliaquim)
- **12 Defensorias Públicas:** DPs 1, 2, 4, 5, 6 com titular; 3ª DP vaga (cumulativa); DPs 7–12 vagas desde 02/05/2026
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
| Mexer na seção Prestação de Contas (prontos pagamentos) | `docs/site/estrutura-html.md` (seção "Prestação de Contas") · `docs/firebase.md` (schema `prestacoes_contas`) |

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

## Estado atual (sessão 29 — 04/08/2026)

**Implementado nesta sessão:** novo tipo "💻 Trabalho Remoto" no formulário "Novo Afastamento" da
aba Calendário (`abrirFormAfastamento`/`salvarAfastamentoFirestore`, mesma coleção
`afastamentos_admin/{id}`, campo `tipo: 'trabalho_remoto'`). Diferente dos demais tipos, **não é
tratado como ausência**: não exige/mostra substituto (seção "Defensorias Afetadas" fica oculta),
não entra em `afastamentos[ano][mes][dia]` (o que faz "Designações semanais" tratar o titular como
ausente) e é filtrado fora de "Lista de Substituições" e "Resumo de Afastamentos". Só afeta a aba
Calendário: badge transparente com contorno tracejado (nova estrutura `trabalhoRemoto[ano][mes][dia]`
+ mapa `defensorColors`), em vez do badge sólido normal, e aparece no popup de detalhe do dia (onde
pode ser editado/excluído normalmente). Ver detalhamento completo em
`docs/site/estrutura-html.md` (seção "Trabalho Remoto"). Ainda não testado em produção com
Firebase real — só verificado que o `index.html` carrega sem erro de sintaxe/console.

**Implementado sessão 28 (31/07/2026):** correção do nome completo do Defensor Eliaquim, que estava sem o
sobrenome "Santos" ("Eliaquim Antunes de Souza" → "Eliaquim Antunes de Souza Santos") em
`index.html`, `docs/designacoes-2026.json`, `docs/escalas/ferias-folgas-2026.md` e
`docs/regras/ausencias.md`. Commit `7340fb9`. As transcrições do Diário Oficial
(`docs/diario-oficial-completo-2026.json`/`.md`) não foram alteradas por serem citação literal do
texto oficial publicado.

Ao corrigir também os titulares da 3ª/4ª/9ª DP pelo site, o campo "Nome do defensor" do modal
"Titulares por DP" não reconheceu o texto digitado como a chave `eliaquim` (JSON ainda em cache no
navegador no momento do salvamento) e gravou como texto livre no Firestore — o card do Eliaquim em
"👥 Defensores Públicos" ficou com o nome certo mas sem o seletor 🟢 Membro / ⚪ Ex-membro. Mecanismo
documentado em `docs/firebase.md` (`_resolverDefensor()`). **Resolvido:** usuária regravou o nome
nas 3 DPs com o cache já atualizado — seletor voltou a aparecer normalmente.

**Implementado sessão 27 (30/07/2026):** controle de admin para marcar/reativar um defensor como ex-membro
diretamente pelo site (seção "👥 Defensores Públicos"). Antes, só existia edição de titularidade
por DP (`titulares_admin`); o status geral do defensor (ativo/ex-membro, usado para separar as
listas) só vinha do campo `ativo` do JSON estático `docs/designacoes-2026.json`, sem forma de
alterar pela interface. Agora há override em `defensores_admin/{defKey}` (Firestore), carregado
por `loadDefensoresAdminFirestore()` e gravado por `alterarStatusDefensor()`. Só se aplica a
defensores com chave no dicionário `defensores` — titulares "livres" continuam com o comportamento
automático já existente. Na UI é um `<select>` de status (🟢 Membro / ⚪ Ex-membro, função
`statusDefensorSelectHtml()`) — trocado do desenho inicial em botão porque um botão "Ex-membro"
num card de membro ativo dava a impressão de que ele já era ex-membro. `firestore.rules` (regra de
`defensores_admin`) já publicada no Console e testada em produção com o Ícaro (marcado como
ex-membro pela Luma com sucesso). Ver `docs/firebase.md` e `docs/site/estrutura-html.md`.

**Também nesta sessão:** sincronizada a documentação com a saída real do Ícaro do polo (último dia
01/06/2026, 3ª DP) — `docs/defensores/icaro.md` (agora ex-membro), `docs/defensores/eliaquim.md`
(cobertura cumulativa da 3ª DP desde 02/06/2026, além da 9ª DP que já cobria) e
`docs/defensorias/lista-completa.md`. **Pendente:** número de portaria/memorando da designação
cumulativa do Eliaquim na 3ª DP, e a titularidade da 3ª DP em `titulares_admin` no Firestore ainda
precisa ser corrigida pelo site (o status 🟢/⚪ não mexe em DP — isso é editado separadamente em
"Titulares por DP").

**Implementado sessão 26 (06/07/2026):** seção "💰 Prestação de Contas" (admin-only) — prontos
pagamentos por tomador (máx. 2 abertos simultâneos, categorias `consumo`/`pessoa_juridica`/`pessoa_fisica`
distintas entre si), Mapa Demonstrativo de Despesa com totais automáticos, anexos por despesa
(Recibo/NF, comprovação de mercado, justificativa, atesto, fotos, outros documentos) com upload
para Firebase Storage, e exportação do Mapa Demonstrativo em PDF A4 paisagem (jsPDF + AutoTable).
Storage ativado (upgrade pra plano Blaze) e `storage.rules`/`firestore.rules` publicadas no
Console. Tudo testado e validado com dados reais.

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
