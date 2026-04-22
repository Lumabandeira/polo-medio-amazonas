# Polo Médio Amazonas 2026 — Guia de Contexto para IA

## O que é este projeto

Site HTML responsivo (`index.html`) para gerenciar designações semanais e ausências dos Defensores Públicos do Polo Médio Amazonas em 2026. Tecnologias: HTML5, CSS3, JavaScript vanilla. Publicado via GitHub Pages em https://lumabandeira.github.io/polo-medio-amazonas/

- **5 defensores ativos**, **12 Defensorias Públicas**
- Regra central: alternância semanal obrigatória entre **Grupo A** e **Grupo B**

---

## Firebase (autenticação e banco de dados)

O site usa **Firebase** para login e edição de conteúdo. Console: https://console.firebase.google.com/project/polo-medio-as

### Serviços ativos
- **Firebase Auth** — login por e-mail/senha. 40 usuários (3 admins + 37 viewers).
- **Firestore** — banco de dados em tempo real. Projeto: `polo-medio-as`

### Estrutura do Firestore
```
usuarios/{uid}
  role: "admin" | "viewer"
  nome: "..."

secoes/regra_alternancia
  html: "..."           ← conteúdo editável da seção Regra de Alternância
  atualizado_por: "..."
  atualizado_em: timestamp

secoes/ferias_folgas
  html: "..."           ← conteúdo editável da seção Férias/Folgas/Licenças
  atualizado_por: "..."
  atualizado_em: timestamp

titulares_admin/{dpKey}   ← histórico de titulares editado pelo admin (por DP)
  historico_titulares: [
    { defensor: "icaro", inicio: "2026-01-01", fim: null,
      portaria_entrada: "...", do_entrada: "https://...",
      portaria_saida: null, do_saida: null },
    { defensor: "elaine", inicio: "2025-01-01", fim: "2025-12-31",
      portaria_entrada: "...", do_entrada: "https://...",
      portaria_saida: "...", do_saida: "https://..." }
  ]
  atualizado_por: "email@..."
  atualizado_em: timestamp

afastamentos_admin/{id}   ← afastamentos adicionados pelo admin via calendário ou automação
  defensor: "elton"       ← chave do defensor (mesmo padrão dos JSONs)
  tipo: "ferias" | "folga" | "licenca_especial"
  data_inicio: "2026-04-15"
  data_fim: "2026-04-20"   ← pode ser "" quando automação grava designação aberta ("a contar do dia X")
  portaria_numero: "Portaria nº 123/2026-GSPG/DPE/AM"
  portaria_url: "https://..."   ← link do PDF do Diário Oficial
  portaria_sei: "26.0.000..."
  designacoes: [{ dp: "5", substituto: "eliaquim" }, ...]
  criado_por: "email@..."
  criado_em: timestamp
  atualizado_por: "email@..."
  atualizado_em: timestamp
  origem: "automacao-diario-oficial"   ← presente apenas em registros da automação
  lido: false              ← false = aparece no sino; true = dispensado pelo admin
  edicao_do: "2606"        ← número da edição do DO que originou o registro
  data_publicacao_do: "2026-03-06"  ← data de publicação da edição (YYYY-MM-DD)
  precisa_revisao: true    ← true quando data_fim está vazia (designação aberta)
  motivo_revisao: "sem data fim — designação aberta (\"a contar do dia X\")"
```

> **Nota:** Os dados dos JSONs locais (`docs/afastamentos-2026.json` e `docs/designacoes-2026.json`) continuam sendo a base. A coleção `afastamentos_admin` contém apenas os registros adicionados/editados pelo admin via interface. Os dois são mesclados em memória ao carregar a página.

### Regras de segurança do Firestore
- Leitura: apenas usuários autenticados
- Escrita: apenas usuários com `role == "admin"`
- Coleções protegidas: `usuarios`, `secoes`, `afastamentos_admin`, `titulares_admin`

### Como funciona o login no site
1. Página carrega → overlay de login cobre tudo
2. Usuário digita e-mail + senha → Firebase Auth valida
3. Site lê `role` no Firestore (`usuarios/{uid}`)
4. Admin: vê badge "ADMIN" + botões ✏️ Editar nas seções
5. Viewer: vê o site normalmente sem botões de edição

### Seções editáveis (admin)
- **Regra de Alternância** (`#regra_alternancia-html`) — edição inline com contentEditable
- **Férias/Folgas/Licenças** (`#ferias_folgas-html`) — edição inline com contentEditable
- Edições salvas em `secoes/{id}` no Firestore e carregadas a cada login

### Funções JS do Firebase no index.html
- `fazerLogin()` — autentica com Firebase Auth
- `fazerLogout()` — encerra sessão
- `carregarConteudoFirestore()` — carrega conteúdo editável do Firestore
- `iniciarEdicao(secaoId)` — ativa contentEditable na seção
- `salvarSecao(secaoId)` — salva HTML no Firestore
- `cancelarEdicao(secaoId)` — restaura conteúdo original
- `mostrarToast(msg)` — exibe notificação temporária
- `loadTitularesFirestore()` — carrega histórico de titulares do Firestore e mescla com JSON base
- `reloadTitularesData()` — restaura snapshot do JSON e reaplicar dados do Firestore
- `abrirModalTitulares(dpKey)` — abre modal de edição de titulares para uma DP
- `salvarTitularesDp()` — valida e salva histórico de titulares no Firestore
- `fecharModalTitulares()` — fecha modal e reverte alterações não salvas
- `toggleModoEdicao()` — alterna modo de edição (mostra/oculta botões ✏️)
- `getTitularForDPOnDay(dpNum, mes, dia)` — resolve titular de uma DP em data específica

### Para adicionar novos usuários
Firebase Console → Authentication → Adicionar usuário → copiar UID → Firestore → coleção `usuarios` → novo documento com o UID → campos `role` e `nome`

---

## Mapa de Tarefas → Arquivos a Ler

Antes de qualquer alteração, leia **apenas** os arquivos listados para a tarefa. Não leia o projeto todo.

### Adicionar férias / folga / licença
1. `docs/regras/ausencias.md` — limites, tipos e interpretação de textos
2. `docs/escalas/ferias-folgas-2026.md` — tabela mestra de ausências
3. `docs/defensores/[nome-do-defensor].md` — dados do defensor afetado
4. `docs/site/processo-atualizacao.md` — ordem obrigatória de atualização do site

### Criar ou atualizar tabela semanal de designações
1. `docs/regras/alternancia.md` — regra de Grupo A/B + checklist
2. `docs/regras/destaques-cores.md` — classes CSS e regra de fins de semana
3. `docs/site/padroes-codigo.md` — estrutura HTML das tabelas
4. `docs/escalas/ferias-folgas-2026.md` — quem está ausente no período

### Verificar quem é o defensor de uma DP
1. `docs/defensorias/lista-completa.md` — lista com defensor de cada DP

### Entender os grupos de alternância
1. `docs/defensorias/grupos-alternancia.md` — Grupo A e Grupo B (resumo rápido)
2. `docs/regras/alternancia.md` — regras detalhadas e exemplos

### Alterar estrutura ou comportamento do site (HTML/CSS/JS)
1. `docs/site/estrutura-html.md` — abas, IDs, organização geral
2. `docs/site/padroes-codigo.md` — padrões de código
3. `docs/site/validacoes-js.md` — funções JavaScript automáticas

### Consultar ausências de um defensor específico
1. `docs/defensores/[nome-do-defensor].md`

### Visão geral do calendário de ausências
1. `docs/escalas/calendario-visual-2026.md`

### Consultar designações diárias de janeiro/2026
1. `docs/escalas/designacoes-janeiro-2026.md`

---

## Estrutura de Arquivos do Projeto

```
index.html                          ← site completo (único arquivo do site)
CLAUDE.md                           ← este arquivo
limpar-backfill.py                  ← limpeza de registros duplicados/fragmentados do backfill
backfill-calendario-do-estruturado.py ← backfill histórico do DO (100% regex, sem API)
verificar-diario-oficial.py         ← automação diária (cron GitHub Actions)
docs/
├── INDEX.md                        ← índice de todos os arquivos docs/
├── defensores/
│   ├── jose-antonio.md
│   ├── icaro.md
│   ├── eliaquim.md
│   ├── elton.md
│   └── elaine.md
├── defensorias/
│   ├── lista-completa.md
│   └── grupos-alternancia.md
├── regras/
│   ├── alternancia.md
│   ├── ausencias.md
│   └── destaques-cores.md
├── escalas/
│   ├── ferias-folgas-2026.md
│   ├── calendario-visual-2026.md
│   └── designacoes-janeiro-2026.md
└── site/
    ├── estrutura-html.md
    ├── padroes-codigo.md
    ├── validacoes-js.md
    └── processo-atualizacao.md
github-pages/
├── README.md
└── .nojekyll
```

---

## Estado atual do site (atualizado em 22/04/2026 — sessão 9)

### O que já foi implementado ✅
- **Sistema de login completo** — overlay de tela cheia, Firebase Auth, roles admin/viewer
- **Badge ADMIN** no header (visível só para admins, posicionado em top:75px left:20px)
- **Botão Sair** no header (top:60px right:20px)
- **Botão Início** no header (aparece ao entrar nas abas, some na landing)
- **Seções editáveis inline** — "Regra de Alternância" e "Férias/Folgas/Licenças" com título + conteúdo editáveis via contentEditable, salvos no Firestore
- **Coluna Diário Oficial no modal do calendário** — link clicável para o PDF ao clicar em dia com afastamento
- **Aba Tabela Completa removida** — Calendário Visual é a aba principal
- **Botões "Nova Aba" e "Sincronizar Planilha" removidos** — e todo código/CSS associado limpo
- **2 usuários admin cadastrados** — bandeira.lkp@gmail.com (Luma) e fabiobastos@defensoria.am.def.br (Fábio Bastos) no Firebase Auth + Firestore com `role: "admin"`
- **Calendário interativo para admins** — CRUD completo de afastamentos via Firestore (`afastamentos_admin`). Detalhes abaixo em "Arquitetura do calendário interativo".
- **Datas de cobertura do substituto liberadas** — removidos os atributos `min`/`max` dos inputs e a lógica de clamping que forçava as datas para dentro do afastamento (causava bug de só permitir selecionar 1 dia). A validação agora ocorre apenas no momento de salvar, com mensagem de erro.
- **Validação de sobreposição entre substitutos** — ao salvar, o sistema verifica se dois substitutos da mesma DP têm períodos de cobertura sobrepostos (inclusive dias iguais na fronteira). Exibe mensagem `❌ [Nome A] e [Nome B] (DP) têm períodos de cobertura sobrepostos.` e bloqueia o salvamento.
- **Edição dos defensores titulares de cada DP** — interface completa para admin gerenciar histórico de titulares. Detalhes abaixo em "Arquitetura da edição de titulares".
- **Toggle switch "Editar" no header** — `<label id="btn-editar-header">` com checkbox interno (`#toggle-editar-checkbox`) na área azul do header (top:60px right:140px, ao lado do botão Sair). Deslizante cinza/verde que alterna modo de edição. Visível apenas na aba Defensorias para admins. Exibe/oculta todos os botões ✏️ por linha na tabela Designações Atuais e os botões de edição das seções (Alternância, Observação). Desativa automaticamente ao trocar de aba ou voltar ao Início. Após salvar/cancelar no modal de titulares, `renderDefensorias()` chama `_aplicarModoEdicao()` para re-aplicar o estado.
- **Controle de visibilidade admin-only por especificidade CSS** — regra `.btn-editar.admin-only { display: none }` garante que botões de edição fiquem ocultos por padrão; inline style via `_aplicarModoEdicao()` sobrescreve quando admin ativa o modo edição.
- **Registros base (JSON) editáveis pelo admin no calendário** — botão ✏️ adicionado a registros "base" (vindos dos JSONs) no modal "Detalhes do Afastamento". Ao clicar, abre o formulário pré-populado com os dados do JSON. Ao salvar, cria registro no Firestore com campo `json_base_id` apontando para o evento JSON original, que é então suprimido da renderização. Globais: `jsonEventosMap` (id→evento) e `jsonOverrideMap` (jsonEventoId→firestoreId). Função auxiliar: `converterDesignacoesJSONParaFirestore(ev)`.
- **Modal de visualização somente leitura no calendário** — ícone 🔍 no modal "Detalhes do Afastamento", visível para todos os usuários (admin e viewer). Abre modal "🔍 Detalhes do Afastamento" (cabeçalho azul) com: defensor, tipo, data início/fim do afastamento completo, processo SEI, e por DP: substituto, data início/fim de cobertura, portaria clicável. Funciona para registros base (JSON) e Firestore. Função: `abrirVisualizacaoAfastamento(tipo, id)` onde `tipo` é `'firestore'` ou `'json'`. Helper: `formatarData(dateStr)` converte `YYYY-MM-DD` → `DD/MM/YYYY`.
- **Detecção automática de ex-membros na aba Defensorias** — `renderDefensorias` detecta "orphan ex-members": qualquer defensor cadastrado como titular via UI (Firestore) que não tenha mais DP ativa aparece automaticamente no accordion "Ex-membros", sem necessidade de editar o JSON. Lógica: `orphanExMembros = Object.keys(defHistorico).filter(k => !defensores[k] && !defCurrentDPs[k])`. Mariana Silva Paixão corrigida no JSON de `externo: true` para `externo: false, ativo: false`.
- **Dropdown "Defensor Ausente" e badges do calendário dinâmicos** — `buildDefensorNames()` e `populateDefensorDropdown()` chamados em `loadJSONData()` após carregar os JSONs. O `<select id="form-af-defensor">` é montado automaticamente de `jsonDesignacoes.defensores` com dois `<optgroup>`: "Membros Ativos" e "Ex-membros". `defensorNames` (antes `const`, agora `let`) também é construído do JSON. Cores de badge novas geradas da `BADGE_PALETTE`; cores já definidas no CSS ficam em `BADGE_CSS_KNOWN` para não serem sobrescritas. Badge da **Mariana Paixão** fixado em `#ff69b4` (rosa Pantera Cor-de-Rosa) no CSS estático e adicionada ao `BADGE_CSS_KNOWN`.
- **Botão "+ Adicionar ao histórico" no modal de titulares** — botão no rodapé do modal de edição de titulares (antes de Cancelar/Salvar). Cria entrada de histórico passado em branco (`fim: ''`) sem fechar o titular atual ativo. Ordenação corrigida: `fim === null` (ativo) vai ao topo; `fim === ''` (histórico novo) vai ao final; datas preenchidas ordenadas por mais recente primeiro.
- **Dropdown de ex-membros inclui orphanExMembros** — `populateDefensorDropdown()` agora calcula ex-membros livres do Firestore (nomes em `historico_titulares` sem DP ativa que não constam em `defensores`) e os adiciona ao optgroup "Ex-membros". Também chamado ao final de `loadTitularesFirestore()`.
- **Integração calendário ↔ Designações Semanais** — `loadAfastamentosFirestore()` agora chama `renderDesignacoes()` após `renderCalendar()`. Células de DP com titular ausente e substituto "ainda não definido" exibem indicador amarelo (`.sem-cobertura`: fundo `#fff8e1`, texto `#b45309`, itálico) com tooltip "Titular ausente — sem substituto definido". Substitutos definidos aparecem em itálico normalmente.
- **Layout do formulário de afastamento reorganizado** — modal ampliado de 680px para 900px. Campos do topo em grid 4-col: Defensor (span 2) + Data Início + Data Fim na linha 1; Tipo + Processo (span 3) na linha 2. Dentro de cada substituto: Substituto + Cobertura início + Cobertura fim em grid 3-col (`.sub-top-grid` com classe `.com-datas` quando substituto selecionado); Portaria + Link DO lado a lado (`.sub-grid-portaria`).
- **`dp12-vaga` e `_atualizarNomesVaga()`** — placeholder `"dp12-vaga"` cadastrado em `titulares_admin/12` para a 12ª DP (vaga sem defensor designado). Função `_atualizarNomesVaga()` chamada em `loadTitularesFirestore()` gera automaticamente labels legíveis como `"12ª DP (vaga)"` para qualquer chave-placeholder não encontrada em `defensores`. Badge fallback: `defensorNames[key] || key`.
- **Dropdown de substituto dinâmico e com fallback** — `_opcoesSubstituto()` agora lê `jsonDesignacoes.defensores` e lista apenas membros com `ativo !== false` (sem ex-membros). Qualquer defensor de fora do polo usa "Outro (digitar nome)". `_criarSubstitutoRow` tem fallback: se o valor salvo no Firestore não bate com nenhuma opção ativa, converte automaticamente para `"_outro"` e resolve o nome via `jsonDesignacoes.defensores[key].nome`.
- **`getTitularForDPOnDay` com intervalo inclusivo** — comparação corrigida de `date < fim` para `date <= fim`. O campo "ÚLTIMO DIA" no modal de titulares é agora corretamente o último dia em que o defensor está vigente (inclusivo em ambas as pontas). **Atenção:** o script Python `titular_em_data` no backfill ainda usa `d < fim` (right-exclusive) — se reexecutar o backfill, verificar se algum titular de fim de período está sendo mal resolvido.
- **Backfill `abrevs_validos` restrito a membros ativos** — `backfill-calendario-do-estruturado.py` agora só reconhece como substituto interno membros com `ativo !== false` e sem `externo: true`. Ex-membros como "oswaldo" viram `substituto: "_outro"` + `substituto_nome_externo`.
- **Badges de vaga ordenados por último no calendário** — `renderCalendar()` ordena o array do dia antes de renderizar badges: chaves que contêm `"vaga"` vão ao final, evitando espaço em branco entre defensores reais.
- **Modal de detalhes: datas inline** — células Defensor e Substituto exibem o período em cinza abaixo do nome (`font-size:0.8em; white-space:nowrap`). Campos adicionados em todos os `push()` para `detalhesAfastamentos`: `afastamento_inicio`, `afastamento_fim`, `sub_inicio`, `sub_fim`.
- **Modal de detalhes: ícones de ação verticais** — coluna Ações usa `display:flex; flex-direction:column` em vez de inline, empilhando 🔍 ✏️ 🗑️.
- **Modal de detalhes: células mescladas por afastamento** — itens agrupados por `firestoreId`/`jsonEventoId` antes de renderizar; colunas Defensor, Tipo e Ações recebem `rowspan=N` na primeira linha do grupo; linhas seguintes omitem essas colunas.
- **Modal de detalhes: separador azul entre grupos** — classe `.grupo-inicio` aplicada na primeira `<tr>` de cada grupo (exceto o primeiro). CSS usa `box-shadow: inset 0 2px 0 0 #1e3a8a` para contornar o `border-collapse` da tabela.
- **Nova aba "Lista de Substituições"** — aba entre Calendário e Resumo de Afastamentos. Função `renderListaSubstituicoes()` lê `afastamentosFirestoreMap` + `jsonEventosMap` (respeitando `jsonOverrideMap`), agrupa por mês de `data_inicio`, ordena por data→defensor, renderiza tabela com rowspan e separador azul (mesmo formato do modal). Botões 🔍 ✏️ 🗑️ funcionam; sem botão "+ Novo Afastamento". `confirmarDeletarAfastamento` corrigido para aceitar `mes=null, dia=null` (não reabre modal quando chamado da lista). Chamada automática em `loadAfastamentosFirestore()` e `showTab('lista-substituicoes')`.
- **Aba "Resumo de Afastamentos" dinamizada** — antes era HTML estático e desatualizado. Agora o conteúdo é gerado por `renderDetalhesAfastamentos()` que lê os mesmos dados do calendário. Agrupa por defensor (ordem do JSON, ativos primeiro) e por mês de início. Formato: `🔵 Nome completo` / bullet por mês com lista de "Tipo DD-DD/MM". Mapa `DEFENSOR_EMOJI` com chaves corretas do JSON (`jose-antonio`, `miguel`, etc.). Chamada automática em `loadAfastamentosFirestore()` e `showTab('detalhes')`.
- **Filtro por DP na aba Lista de Substituições** — `<select id="filtro-lista-dp">` com opções "Todas as DPs" + "1ª DP" … "12ª DP". Variável global `filtroListaDP`. Ao filtrar, `renderListaSubstituicoes()` mantém o **registro inteiro** (todas as DPs do afastamento) quando qualquer DP do registro bate com o filtro — preserva o contexto do afastamento completo. Registros sem match são ocultados; meses sem match some do render.
- **Sino 🔔 de notificações da automação** — botão `#btn-sino` ao lado do título "📋 Lista de Substituições" (visível apenas para admins). Badge vermelho com contagem de não lidos. Ao clicar, abre painel lateral deslizante (`#notif-overlay` / `.notif-panel`) com feed de registros com `origem: "automacao-diario-oficial"` e `lido !== true`, agrupados por edição do DO (mais recente primeiro). Cada item mostra: ✋ se `precisa_revisao: true`, 🤖 caso contrário; defensor, DPs, tipo, período, portaria, motivo de revisão. Botões: [✏️ Editar] abre formulário; [🗑️ Dispensar] seta `lido: true` no Firestore e remove do badge. Variável global `notificacoesData[]`. Funções: `carregarNotificacoesAutomacao()`, `_atualizarBadgeSino()`, `abrirPainelNotificacoes()`, `fecharPainelNotificacoes()`, `dispensarNotificacao(id)`. Chamada em `mostrarSiteAutenticado()` após login.
- **Automação atualizada (`verificar-diario-oficial.py`)** — grava `lido: false`, `edicao_do`, `data_publicacao_do` em todos os registros novos. Data de publicação extraída da URL da edição (regex `Edicao_NNN-AAAA_DDMMAAAA`). Designações "a contar do dia X" sem data fim agora **gravadas** com `precisa_revisao: true` + `motivo_revisao` em vez de descartadas. Prompt do Claude atualizado para retornar `data_fim: ""` nesses casos. Ciclo completo: automação grava → sino aparece → admin revisa → dispensa ou edita.

### O que ainda falta implementar ⏳
- **Cadastrar os outros 38 usuários restantes** (1 admin + 37 viewers) no Firebase Auth + Firestore
- **Dados privados da equipe** — WhatsApp, contatos internos (estrutura no Firestore planejada mas não implementada)

### Descartado (não vale implementar)
- **Coleção `defensores_admin` no Firestore** — descartado: ex-membros livres já detectados automaticamente via orphanExMembros; casos raros de inconsistência com o JSON não justificam a complexidade

### Decisões de arquitetura já tomadas
- Sem automação do Diário Oficial — admin insere links manualmente
- Sem migração de hospedagem — continua no GitHub Pages
- JSONs locais (`docs/afastamentos-2026.json` e `docs/designacoes-2026.json`) = base de referência. **Todos os eventos do `designacoes-2026.json` foram promovidos ao Firestore via UI admin em 18/04/2026** — o Firestore é agora a fonte única de verdade para o calendário. Registros JSON que ainda não têm override no Firestore continuam sendo exibidos normalmente (o site mescla os dois em memória), mas a intenção é que o admin promova qualquer registro que precise de correção.
- Função `syncFromSheets()` removida definitivamente
- Formulário de afastamento dividido em duas fases: (1) cadastrar ausência sem Diário Oficial; (2) registrar substituto + portaria quando o diário sair. Portaria e link DO ficam dentro de cada designação por DP, não no nível do afastamento.
- Edição de titulares não retroage: cada entrada tem data de início explícita; a resolução por data (`getTitularForDPOnDay`) garante que tabelas passadas não são afetadas por mudanças futuras.
- Nomes de defensores em campo texto livre (não dropdown fixo) para acomodar defensores externos ou futuros.
- Registros base do JSON podem ser "promovidos" ao Firestore pelo admin via ✏️ no modal do calendário. O campo `json_base_id` no Firestore vincula ao evento JSON original, que é suprimido da renderização após a promoção.

---

## Arquitetura do calendário interativo (admin)

### Fluxo de dados
1. `loadJSONData()` carrega os JSONs e constrói `afastamentos` e `detalhesAfastamentos`
2. `loadAfastamentosFirestore()` lê `afastamentos_admin` e mescla por cima (additive)
3. `reloadAfastamentosData()` repete os passos 1+2 sem refetch de rede (usa JSONs já em memória)

### Estrutura do formulário de afastamento
- **Nível do afastamento:** defensor, tipo (Férias/Folga/Licença Especial/Outro+texto), data início, data fim, processo SEI/SGI
- **DPs afetadas:** preenchidas automaticamente ao selecionar o defensor, lendo `jsonDesignacoes.defensorias[dp].historico_titulares` para o período do afastamento
- **Por DP:** lista de substitutos (pode ser múltiplos para cobertura escalonada), cada um com: substituto (defensores do polo exceto o ausente, ou "Outro" com campo livre), período de cobertura, portaria, link DO
- **Padrão sem substituto:** "ainda não definido" — campos de detalhe ficam ocultos

### Lógica de exibição no modal
- Para cada DP do afastamento, os dias cobertos por substitutos definidos mostram o nome do substituto
- Os dias do afastamento **não cobertos** por nenhum substituto mostram automaticamente "ainda não definido" (gap filling em `mergeAfastamentoFirestoreRecord`)
- Registros do Firestore mostram botões 🔍✏️🗑️; registros base (JSON) mostram 🔍✏️ (sem 🗑️)
- Botão 🔍 visível para todos (admin e viewer); ✏️ e 🗑️ apenas para admins
- Registros base cujo `json_base_id` consta em `jsonOverrideMap` são suprimidos (substituídos pelo Firestore)

### Validações no salvar (`salvarAfastamentoFirestore`)
1. Defensor e datas do afastamento obrigatórios
2. Data fim não pode ser anterior à data início
3. Tipo "outro" exige texto no campo motivo
4. Por substituto: início da substituição não pode ser anterior ao início do afastamento
5. Por substituto: fim da substituição não pode ser posterior ao fim do afastamento
6. Por substituto: fim da substituição não pode ser anterior ao início da substituição
7. **Por DP:** nenhum par de substitutos pode ter períodos sobrepostos (dias iguais na fronteira = sobreposição)

> **Atenção:** afastamentos salvos antes da correção do bug de clamping podem ter datas de cobertura incorretas no Firestore (ex: cobertura gravada com apenas 1 dia em vez do período completo). Para corrigir, o admin deve reabrir o afastamento e salvar novamente com as datas corretas.

---

## Arquitetura da edição de titulares (admin)

### Fluxo de dados
1. `loadJSONData()` carrega `designacoes-2026.json` e cria snapshot imutável em `_jsonDesignacoesBkDefensorias`
2. `loadTitularesFirestore()` lê `titulares_admin` e substitui `historico_titulares` das DPs correspondentes em memória, depois re-renderiza (Defensorias, Designações, Calendário)
3. `reloadTitularesData()` restaura do snapshot e reaplicar dados do Firestore (usado ao cancelar edição)

### Resolução de titular por data
- `getTitularForDPOnDay(dpNum, mes, dia)` — percorre `historico_titulares` da DP e retorna o defensor vigente usando intervalos right-exclusive (`date >= inicio && date < fim`; `fim == null` = vigente)
- Garante que alterações de titular não retroagem: cada entrada tem data de início explícita

### Modal de edição por DP
- `abrirModalTitulares(dpKey)` — abre modal para uma DP específica, chamado pelo botão ✏️ na tabela Designações Atuais
- `_renderEntradas(dpKey)` — renderiza cards em ordem: vigente primeiro (`fim === null`), históricos por data mais recente, entradas em branco novas por último (`fim === ''`). Cada card: nome (campo texto livre), início, fim, portaria de entrada, link DO entrada (`do_entrada`), portaria de saída, link DO saída (`do_saida`)
- Botão "+ Adicionar novo titular" no topo — fecha o vigente atual (define `fim` = hoje) e cria nova entrada vigente (`fim: null`)
- Botão "+ Adicionar ao histórico" no rodapé (antes de Cancelar/Salvar) — cria entrada histórica em branco (`fim: ''`) sem fechar o titular atual
- `_adicionarEntrada()` — lógica do botão do topo
- `_adicionarHistorico()` — lógica do botão do rodapé
- `_removerEntrada(idx)` — remove entrada (mínimo 1 obrigatório)
- **Atenção:** `fim === null` = titular ativo; `fim === ''` = histórico novo em branco (ainda não preenchido); `fim === 'YYYY-MM-DD'` = histórico com data. A ordenação usa `=== null` (não `!fim`) para distinguir corretamente.

### Nomes de defensores
- Campo de texto livre: aceita nomes de defensores do polo ou nomes externos
- `_resolverDefensor(nomeDigitado)` — tenta casar com `defensores[key].nome` ou `.nome_curto`; se não encontrar, armazena como string livre
- `_resolverNomeDefensor(defVal)` — resolve chave para nome completo, ou retorna valor como está

### Validações no salvar (`salvarTitularesDp`)
1. Nome do defensor obrigatório em toda entrada
2. Data de início obrigatória
3. Se `fim` preenchido, `fim >= inicio`
4. Máximo 1 entrada sem `fim` (vigente) por DP
5. Salva em `titulares_admin/{dpKey}` no Firestore

### Impacto nas outras abas
- **Aba Defensorias:** cards de defensores e tabela Designações Atuais re-renderizados após salvar
- **Aba Designações Semanais:** tabelas semanais usam `getTitularForDPOnDay()` que reflete o titular correto por data
- **Aba Calendário:** re-renderizado para refletir novos titulares nos afastamentos

### Modo de edição (`toggleModoEdicao`)
- Toggle switch `#btn-editar-header` (label) + `#toggle-editar-checkbox` (checkbox interno) na área azul do header — visível apenas na aba Defensorias para admins
- Estado lido diretamente de `checkbox.checked`; verde = modo edição ativo
- `_aplicarModoEdicao()` — mostra/oculta botões ✏️ por linha na tabela e botões `.admin-only` das seções editáveis; chamado também ao final de `renderDefensorias()` para preservar estado após re-render do DOM
- `_desativarModoEdicao()` — desmarca o checkbox e chama `_aplicarModoEdicao()`; acionado ao trocar de aba (`showTab`) ou voltar ao início (`showLanding`/`showSection`)

### Renderização da aba Defensorias (`renderDefensorias`)
- Cards sem numeração, com label "Primeiro dia" e portarias
- Portaria vira link clicável quando `do_entrada` ou `do_saida` estiver preenchido (abre em nova aba)
- Accordion "Ex-membros" para entradas antigas com `fim` preenchido — inclui dois grupos:
  - `exMembros`: defensores do dicionário `defensores` com `externo: false, ativo: false`
  - `orphanExMembros`: nomes livres (texto) em `defHistorico` que não constam em `defensores` e não têm DP ativa — detectados automaticamente, sem editar JSON
- Tabela Designações Atuais com coluna ✏️ oculta por padrão (classe `cel-editar-dp`)
- Ao final da função, chama `_aplicarModoEdicao()` para re-aplicar modo edição após rebuild do DOM

---

## Automação do Diário Oficial via GitHub Actions (✅ ATIVA — sessão 5 em 17/04/2026)

### Status atual: cron diário rodando, gravação direta no Firestore

Em 17/04/2026 refizemos a automação para gravar os afastamentos detectados **direto no Firestore** (coleção `afastamentos_admin`), em vez de editar o `index.html` como antes. Isso eliminou o bug catastrófico de truncamento que destruiu o site no incidente de 16/04 (run #2: 4595 linhas deletadas em `index.html`, revertido em [`6d79bbe`](https://github.com/Lumabandeira/polo-medio-amazonas/commit/6d79bbe)).

O workflow roda diariamente às **06:00 de Manaus** (10:00 UTC) via `.github/workflows/verificar-diario.yml`. A tarefa agendada local do Windows (`VerificarDiarioOficialDPE`) foi **desabilitada permanentemente**.

### Arquitetura da automação
1. **Scrape** da página pública do Diário Oficial da DPE/AM
2. **Comparação** com `.estado-diario.json` (última edição processada, em cache via `actions/cache@v4`)
3. Para cada edição nova: baixa PDF → extrai texto com `pdfplumber`
4. **Pré-filtro por termos-gatilho** (`_extrair_trechos_relevantes`): procura no texto completo pela frase fixa `Polo (do) Médio Amazonas` + primeiro+segundo nome de cada **titular vigente** (carregados dinamicamente de `docs/designacoes-2026.json` + Firestore `titulares_admin` em `inicializar_defensores_e_termos()`). Se nenhum termo aparece, pula a chamada ao Claude (custo zero). Caso contrário, extrai janelas de ±1500 chars em volta de cada menção e concatena (intervalos sobrepostos são mesclados). Isso resolve o bug original de enviar só `text[:15000]` — as designações do Polo Médio costumam aparecer em páginas tardias do PDF (40k+ chars). **Cidades e servidores foram removidos dos termos** — o DO designa "Nª Defensoria Pública do Estado do Amazonas", nunca pela cidade; servidores são escopo do Projeto 2 (abaixo). Quando um titular muda (ex.: Miguel assumiu DPs 6/7 no lugar de Elaine em 01/03/2026), a automação se atualiza sozinha na próxima execução, sem edição no script.
5. Envia trechos ao **Claude Haiku 4.5** (`claude-haiku-4-5-20251001`, `max_tokens=2048`) com prompt que pede JSON agrupado por afastamento
6. `salvar_afastamentos_firestore()` converte para o schema esperado pelo site (ver abaixo) e grava via `firebase-admin`
7. E-mail automático com resumo dos afastamentos gravados (opcional, via SMTP)

### Schema Firestore real (importante — diferente do schema simplificado antigo)
O site usa duas estruturas. O formulário de edição popula seus campos via `designacoes_dp` (novo); o render do calendário lê ambos por compat. **Sempre grave no formato novo:**

```
afastamentos_admin/{id}
  defensor:         "elton"                ← abrev
  tipo:             "ferias" | "folga" | "licenca_especial" | "outro"
  tipo_custom:      ""                     ← texto livre quando tipo=="outro"
  data_inicio:      "YYYY-MM-DD"
  data_fim:         "YYYY-MM-DD"
  processo_tipo:    "SEI" | "SGI" | ""
  processo_sei:     "25.0.000..."
  portaria_numero:  "Portaria nº .../2026-GSPG/DPE/AM"
  portaria_url:     "https://..."          ← PDF do Diário Oficial
  portaria_sei:     "..."                  ← compat com código antigo (mesmo valor de processo_sei)
  designacoes_dp: [
    {
      dp: "5",
      substitutos: [
        {
          substituto:              "eliaquim" | "_outro" | "",
          substituto_nome_externo: ""       ← usado quando substituto=="_outro"
          data_inicio:             "YYYY-MM-DD",  ← cobertura
          data_fim:                "YYYY-MM-DD",
          portaria_numero:         "...",
          portaria_url:            "..."
        }
      ]
    }
  ]
  criado_por:     "automacao@github-actions" | email do admin
  criado_em:      timestamp
  atualizado_por: ...
  atualizado_em:  timestamp
  origem:         "automacao-diario-oficial" (quando vem do script)
```

O campo antigo `designacoes: [{ dp, substituto }]` ainda é lido pelo site por compat, mas o formulário de edição só popula campos via `designacoes_dp` — se gravar só no antigo, o admin abre o modal de editar e vê "ainda não definido" em vez do substituto.

### Mapeamento de substitutos (interno vs. externo)
- Se o substituto detectado pelo Claude bate (por nome completo ou primeiro+último nome) com um dos 5 titulares do polo → grava `substituto: "abrev"` e `substituto_nome_externo: ""`
- Caso contrário → grava `substituto: "_outro"` e `substituto_nome_externo: "Nome completo"` (assim o formulário de edição seleciona "Outro" no dropdown e preenche o nome no campo livre)

### Dedup
Antes de inserir, `salvar_afastamentos_firestore` busca documentos com mesmo `(defensor, data_inicio, data_fim, tipo)`. Se já existe, pula. Previne duplicação caso o script reprocesse uma edição.

### Configuração necessária
- **Secret `ANTHROPIC_API_KEY`** em https://github.com/Lumabandeira/polo-medio-amazonas/settings/secrets/actions
- **Secret `FIREBASE_SERVICE_ACCOUNT`** (JSON completo da service account Firebase Admin, baixado em https://console.firebase.google.com/project/polo-medio-as/settings/serviceaccounts/adminsdk)
- Secrets SMTP (opcionais): `SMTP_REMETENTE`, `SMTP_SENHA_APP`, `SMTP_DESTINATARIO`. Se ausentes, script loga warning e segue sem enviar e-mail.

### Arquivos-chave da automação
- `verificar-diario-oficial.py` — script principal. Funções: `inicializar_defensores_e_termos`, `_carregar_titulares_vigentes`, `_construir_termos_gatilho`, `_extrair_trechos_relevantes`, `parse_designations`, `salvar_afastamentos_firestore`, `get_firestore_client`, `main`.
- `processar-diario-completo.py` — script histórico/batch com Claude Sonnet (não roda no cron, só sob demanda)
- `raspar-diario-2026.py` — raspador histórico de edições 2564–2629 (não roda no cron)
- `criar-tarefa-agendada.ps1` — script PowerShell do agendador local (obsoleto, substituído pelo workflow GitHub Actions; tarefa `VerificarDiarioOficialDPE` está `Disabled`)
- `.github/workflows/verificar-diario.yml` — workflow GitHub Actions (schedule ativo + workflow_dispatch manual). Instala `firebase-admin` e injeta `FIREBASE_SERVICE_ACCOUNT` via env.
- `docs/.estado-diario.json` — estado persistente. No Actions: cache. Local: disco. Gitignored.
- `docs/config.json` — SMTP. Gerado em runtime via Secrets no Actions; gitignored.
- `firebase-service-account.json` — credencial local para rodar o script manualmente. Gitignored.

### Rodar localmente (teste/debug)
```bash
py -m pip install firebase-admin requests pdfplumber beautifulsoup4 anthropic
set ANTHROPIC_API_KEY=sk-ant-...
py verificar-diario-oficial.py
```
Requer `firebase-service-account.json` na raiz do projeto.

### Custos (Claude Haiku 4.5, preços conservadores no script)
- Entrada: $1/M tokens; Saída: $5/M tokens
- Execução com edição nova sem menção ao Polo Médio: **$0** (pré-filtro pula a chamada)
- Execução com designação detectada: ~$0.004–0.008 por edição
- Limite mensal: `LIMITE_CUSTO_USD = $2.00`. Ao atingir, envia e-mail e pausa automação até virar o mês.

---

## Backfill do calendário a partir do Diário Oficial estruturado (✅ EXECUTADO e CORRIGIDO — 17–18/04/2026)

### Contexto
Em 17/04/2026 o calendário foi retroativamente populado com designações substitutas publicadas no DO desde janeiro/2026. Em 18/04/2026 foram corrigidos dois bugs no script e executada uma limpeza dos registros incorretos gerados na primeira execução.

### Script: `backfill-calendario-do-estruturado.py`
- Lê `docs/diario-oficial-completo-2026.json`, campo `portarias_estruturadas.trechos`
- Parser regex parseia tanto "período de X a Y" quanto "dias A, B e C" e "nos períodos de X a Y e Z a W"
- **Rejeita** trechos com apenas data de início ("a contar do dia X") — marca como "não parseados" para revisão manual
- **Cruza revogações** (`TORNAR SEM EFEITO` / `CESSAR OS EFEITOS`) por `(número, ano)` da portaria citada + conjunto de incisos; remove designações revogadas do plano antes de gravar
- **Resolve titular histórico** por data (right-exclusive: `inicio <= d < fim`), combinando `designacoes-2026.json` com overrides de `titulares_admin` no Firestore
- Mapeia substituto: nome completo ou primeiro+último bate com um dos defensores do polo → `substituto: "abrev"`; caso contrário → `substituto: "_outro"` + `substituto_nome_externo: "Nome"`
- **Filtra ano < 2026** (dezembro/2025 fica fora)
- **`_json_evento_cobre_sub`** — pula qualquer par (dp, substituto) já registrado nos `eventos` do `designacoes-2026.json` (evita duplicatas em relação ao JSON base)
- Merge vs. novo: se já existe afastamento do titular com período sobreposto no Firestore → merge em `designacoes_dp[]`; caso contrário → cria **um único doc** com todas as DPs do mesmo afastamento agrupadas (`tipo: "outro"`, `origem: "backfill-do-estruturado"`)
- Dedup: se já há substituto registrado com mesmo `(substituto, data_inicio, data_fim)` na DP, pula
- CLI: dry-run por padrão. `--commit` grava. `--no-firestore` roda sem Firestore (pendentes não classificados).

### Bugs corrigidos em 18/04/2026
1. **Duplicatas do JSON** — o script não consultava os `eventos` do `designacoes-2026.json` ao decidir se criava registro novo, gerando duplicatas de substitutos já definidos no JSON. Corrigido com `_json_evento_cobre_sub`.
2. **Fragmentação por DP** — criava 1 doc Firestore por DP em vez de 1 doc com todas as DPs do mesmo afastamento. Corrigido agrupando itens `"novo"` por `(titular, data_inicio, data_fim, portaria)` antes de gravar.

### Script de limpeza: `limpar-backfill.py`
Executa **após** o backfill para corrigir registros incorretos existentes no Firestore:
1. **Duplicatas do JSON** — docs de backfill cujos (dp, substituto) já estão no JSON → **deleta**
2. **Docs fragmentados** — múltiplos docs de 1-DP para o mesmo afastamento → **consolida** em 1 doc com todas as DPs
3. **Docs mistos** — parte duplicata + parte nova → **atualiza** removendo só as entradas duplicadas
4. Docs com dados genuinamente novos → **sem ação**

**Resultado da limpeza executada em 18/04/2026:** 36 docs deletados, 6 consolidados.

Uso: `py limpar-backfill.py` (dry-run) / `py limpar-backfill.py --commit` (aplica).

### Resultado total do backfill (após limpeza)
- **8 registros** no Firestore com `origem: "backfill-do-estruturado"` (dados genuinamente novos, não presentes no JSON)
- Todos os eventos do JSON promovidos ao Firestore pelo admin via UI em 18/04/2026
- Correção manual de sobreposição na 2ª DP de José Antônio (Bruna 22-25/jan + Daniel 26-30/jan, via Portaria 52/2026 que revogou a Portaria 41/2026)
- ~~**1 pendente de revisão manual:** Eliaquim → 7ª DP 2026-03-01..2026-03-06 (Portaria 206/2026)~~ ✅ Registrado manualmente em 19/04/2026
- ~~2 não parseadas (Eliaquim 9ª DP a partir de 11/jan; Miguel 7ª DP a partir de 07/mar)~~ ✅ Registradas manualmente em 19/04/2026
  - Eliaquim → 9ª DP: 11/01/2026 a 21/04/2026 (Portaria 4/2026; cessado pela Portaria 370/2026)
  - Miguel → 7ª DP: a partir de 07/03/2026 (Portaria 206/2026)

### Quando reexecutar
Sempre que `docs/diario-oficial-completo-2026.json` for atualizado com edições novas. O script é idempotente (dedup por `(defensor, data_inicio, data_fim, tipo)` e por substituto dentro de `designacoes_dp`). Rodar `limpar-backfill.py` após cada execução com `--commit` é recomendado para limpar eventuais fragmentações.

### Revogações — limitação conhecida
Revogações detectadas são **apenas removidas do plano em memória** antes de gravar — não são aplicadas retroativamente a afastamentos já no Firestore. Se uma portaria revogada já virou afastamento gravado anteriormente, revisar manualmente.

---

## Projeto 2 — Automação da aba "Diário Oficial" (⏳ PENDENTE — iniciar em 18/04/2026)

### Contexto e diferença para o Projeto 1

O **Projeto 1** (acima) é estrito: detecta apenas afastamentos dos **5 titulares vigentes do Polo Médio** e grava em `afastamentos_admin` para aparecer no calendário do site. Os termos-gatilho são mínimos: `Polo Médio Amazonas` + primeiro+segundo nome dos titulares.

O **Projeto 2** é amplo: vai popular uma nova aba **"Diário Oficial"** no site com **todas as portarias relevantes para o Polo Médio**, não apenas afastamentos de defensores. Exemplos de conteúdo desejado:

- Designações/afastamentos de **servidores** lotados no polo (Natália Cristina, Fábio Bastos, Luma Karolyne, Luma Bandeira, Larice Bruce, Arnoud Lucas, Raquel Ferreira dos Santos, etc.)
- Escalas de **plantão** que envolvam o Polo Médio
- Atos de **coordenação regional** (portarias da GSPG/DPE-AM afetando a administração do polo)
- Designações de **estagiários** e comissionados do polo
- Qualquer outra portaria citando o polo ou seus integrantes, mesmo fora do escopo estrito de "afastamento + substituto"

### Arquitetura planejada (a decidir na próxima sessão)

- **Fonte:** `docs/diario-oficial-completo-2026.json` (novo arquivo) OU nova coleção Firestore (`diario_oficial_admin` ou equivalente). Decisão pendente — JSON versionado é mais simples; Firestore permite edição pela UI admin, mas exige CRUD próprio na interface.
- **Termos-gatilho:** lista bem maior, incluindo:
  - Frase fixa "Polo (do) Médio Amazonas"
  - Cidades do polo: Itacoatiara, São Sebastião do Uatumã, Itapiranga, Urucurituba, Urucará, Silves
  - Nomes dos titulares vigentes (reaproveitar `_carregar_titulares_vigentes()`)
  - Nomes dos servidores do polo (fonte a definir — novo arquivo estático? coleção Firestore?)
- **Modelo:** manter Claude Haiku 4.5, mas com prompt diferente (categoriza por tipo de ato em vez de extrair só afastamentos). Aumentar `max_tokens` conforme necessário.
- **UI:** nova aba "Diário Oficial" no `index.html` com feed cronológico de portarias, filtros por tipo/mês, link direto pro PDF da edição.

### Pré-requisitos antes de começar

- Definir estrutura de dados final (schema do JSON ou da coleção Firestore)
- Listar exaustivamente os servidores a serem monitorados (com grafias alternativas)
- Decidir categorização (ex.: `afastamento`, `plantao`, `coordenacao`, `estagiario`, `outro`)
- Avaliar impacto de custo — muitos termos-gatilho = mais janelas extraídas = mais tokens por edição. Revisar `LIMITE_CUSTO_USD` se necessário.

### O que NÃO fazer (preservar Projeto 1)

- **Não misturar** os termos-gatilho do Projeto 2 no script `verificar-diario-oficial.py`. Criar script separado (ex.: `verificar-diario-oficial-completo.py`) ou parametrizar com flag/env var para manter o Projeto 1 enxuto e barato.
- **Não gravar em `afastamentos_admin`** — só o Projeto 1 escreve ali. O Projeto 2 precisa da sua própria coleção/arquivo para não poluir o calendário com plantões, servidores etc.

---

## Regras Críticas (resumo rápido)

- **Arquivo único:** existe apenas um `index.html` na raiz. Nunca duplicar.
- **Alternância semanal:** Grupo A e Grupo B alternam toda semana sem exceção. Ver `docs/regras/alternancia.md`.
- **Destaques apenas em dias úteis:** nunca aplicar classes `itacoatiara` ou `silves` em sábados/domingos.
- **Máximo 2 defensores ausentes** ao mesmo tempo; mínimo 3 ativos.
- **Aba Tabela Completa foi removida** — o Calendário Visual é a aba principal de ausências.
- **Nunca editar seções do Firestore diretamente no HTML** — o conteúdo vem do Firestore e sobrescreve o HTML padrão ao carregar.
