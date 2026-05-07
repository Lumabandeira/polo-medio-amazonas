# Polo Médio Amazonas 2026 — Guia de Contexto para IA

## O que é este projeto

Site HTML responsivo (`index.html`) para gerenciar designações semanais e ausências dos Defensores Públicos do Polo Médio Amazonas em 2026. Tecnologias: HTML5, CSS3, JavaScript vanilla. Publicado via GitHub Pages em https://lumabandeira.github.io/polo-medio-amazonas/

- **6 defensores ativos** (Ênio · Thays · Ícaro · Eliaquim · Emilly · Miguel), **12 Defensorias Públicas**
- DPs 1–6 ocupadas; DPs 7–12 vagas desde 02/05/2026 (Concurso de Remoção)
- Regra central: alternância semanal obrigatória entre **Grupo A** e **Grupo B**

---

## Firebase (autenticação e banco de dados)

O site usa **Firebase** para login e edição de conteúdo. Console: https://console.firebase.google.com/project/polo-medio-as

### Serviços ativos
- **Firebase Auth** — login por e-mail/senha. 42 usuários (3 admins + 39 viewers).
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

remocoes_admin/{id}   ← portarias de Concurso de Remoção OU cessação de designação
  tipo: "cessacao_designacao"  ← presente apenas em cessações; ausente = concurso de remoção
  portaria_numero: "Portaria nº 602/2026-GDPG/DPE/AM"  ← portaria cessadora (para cessações)
  portaria_cessada: "Portaria nº 206/2026-GSPG/DPE/AM" ← portaria cujos efeitos foram cessados (só em cessações)
  portaria_url: "https://..."     ← PDF do Diário Oficial
  concurso: "Concurso de Remoção nº 1/2026"  ← vazio em cessações
  data_vigencia: "2026-05-02"     ← para cessações: último dia de vigência da designação cessada
  saindo: [{ dp: "1", defensor: "Nome completo" }, ...]   ← em cessações: DP ficará vaga
  chegando: [{ dp: "1", defensor: "Nome completo" }, ...]  ← vazio em cessações
  origem: "automacao-diario-oficial"
  lido: false              ← false = aparece no sino; true = dispensado
  edicao_do: "2640"
  data_publicacao: "2026-04-15"
  criado_por: "automacao@github-actions"
  criado_em: timestamp

designacoes_cumulativas_admin/{id}   ← designações cumulativas sem data fim detectadas pela automação
  defensor_nome:    "Eliaquim Antunes de Souza Santos"  ← nome completo do designado
  defensor_abrev:   "eliaquim"   ← abrev interna, se reconhecida; "" caso contrário
  dp_designada:     "9"          ← número da DP
  data_inicio:      "2026-05-04"
  portaria_numero:  "Portaria nº .../2026-..."
  portaria_url:     "https://..."   ← PDF do Diário Oficial
  processo_sei:     "..."
  origem:           "automacao-diario-oficial"
  lido:             false    ← false = aparece no sino verde; true = dispensado
  edicao_do:        "2650"
  data_publicacao_do: "2026-05-06"
  criado_por:       "automacao@github-actions"
  criado_em:        timestamp
```

> **Nota:** Os dados dos JSONs locais (`docs/afastamentos-2026.json` e `docs/designacoes-2026.json`) continuam sendo a base. A coleção `afastamentos_admin` contém apenas os registros adicionados/editados pelo admin via interface. Os dois são mesclados em memória ao carregar a página.

### Regras de segurança do Firestore
- Leitura: apenas usuários autenticados
- Escrita: apenas usuários com `role == "admin"`
- Coleções protegidas: `usuarios`, `secoes`, `afastamentos_admin`, `titulares_admin`, `remocoes_admin`, `designacoes_cumulativas_admin`

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
verificar-diario-oficial.py         ← Projeto 1: afastamentos de titulares → Firestore (06:00 Manaus)
verificar-diario-completo.py        ← Projeto 2: todas as portarias → JSON (04:00 Manaus)
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

## Estado atual do site (atualizado em 04/05/2026 — sessão 16)

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
- **Sino 🔔 de notificações da automação (afastamentos)** — botão `#btn-sino` na **barra de abas**, ao lado da aba "📋 Lista de Substituições" (visível apenas para admins). **Camouflado** quando sem pendências (`opacity:0; pointer-events:none`); exibe badge vermelho com contagem quando há registros não lidos. Ao clicar, abre painel lateral (`#notif-overlay` / `.notif-panel`) com registros `origem:"automacao-diario-oficial"` e `lido !== true`, agrupados por edição do DO. Cada item: ✋ se `precisa_revisao:true`, 🤖 caso contrário; defensor, DPs, tipo, período, portaria, motivo. Botões: [✏️ Editar] abre formulário pré-populado; [🗑️ Dispensar] grava `lido:true`. Global: `notificacoesData[]`. Funções: `carregarNotificacoesAutomacao()`, `_atualizarBadgeSino()`, `abrirPainelNotificacoes()`, `fecharPainelNotificacoes()`, `dispensarNotificacao(id)`. **Posição atual:** movido do `<h2>` da aba para a barra de abas em 24/04/2026 (commit `382c90e`). **Nota CSS:** `color` não afeta emoji 🔔 — camouflagem feita com `opacity`, não `color`.
- **Sino 🔔 de Alterações de Titularidade** — botão `#btn-sino-remocao` na **barra de abas**, ao lado da aba "📋 Defensorias". Mesma lógica de camouflage por opacity. Lê coleção `remocoes_admin` (onde `origem:"automacao-diario-oficial"` e `lido !== true`). Painel `#notif-remocao-overlay` com cabeçalho âmbar (`#b45309`), título "🔔 Alterações de Titularidade". Renderiza dois tipos de registro (campo `tipo` do Firestore):
  - **`tipo: "cessacao_designacao"`** (borda vermelha, ícone 🏛️): portarias que cessam efeitos de designações anteriores → DP ficará vaga. Exibe: defensor saindo, DP, último dia de vigência, portaria cessada. Sem botão Editar; apenas [🗑️ Dispensar] + lembrete para atualizar titulares na aba Defensorias.
  - **Sem `tipo` / tipo ausente** (borda âmbar, ícone 🔄): Concurso de Remoção. Exibe: portaria, vigência, quem sai e quem chega. Botões: [✏️ Editar] + [🗑️ Dispensar].
  - Funções: `_atualizarBadgeSinoRemocao()`, `abrirPainelRemocao()`, `fecharPainelRemocao()`, `editarRemocao(id)`, `salvarEdicaoRemocao(id, numRows)`, `dispensarRemocao(id)`. Global: `remocaoNotifData[]`. **`carregarNotificacoesAutomacao()` usa try/catch independentes** para cada coleção (evita que falha em `remocoes_admin` apague dados de `afastamentos_admin`).
- **Detecção de membros com efeito futuro** — defensores com início de designação após hoje (`inicio > today && fim === null`) são detectados por `getFutureTitular(dpKey)` e mapeados em `defFutureDPs`. O filtro `orphanExMembros` exclui quem está em `defFutureDPs`, evitando que apareçam como ex-defensores antes da vigência. A aba Defensorias exibe esses membros como "futuros" nos cards das DPs.
- **Automação de Concurso de Remoção (`verificar-diario-oficial.py`)** — novas funções: `_texto_tem_remocao_polo_medio(text)` (pré-filtro por regex), `_extrair_trechos_remocao(text)`, `parse_remocao(text, state)` (usa Claude Sonnet para extrair portaria, data de vigência, saindo[], chegando[]), `salvar_remocao_firestore(data, ...)` (grava em `remocoes_admin` com dedup por `portaria_numero`). Constante `FIRESTORE_COLECAO_REMOCOES = "remocoes_admin"`. Roda após o bloco de afastamentos no `main()`.
- **Automação atualizada (`verificar-diario-oficial.py`)** — grava `lido: false`, `edicao_do`, `data_publicacao_do` em todos os registros novos. Data de publicação extraída da URL da edição (regex `Edicao_NNN-AAAA_DDMMAAAA`). Designações "a contar do dia X" sem data fim agora **gravadas** com `precisa_revisao: true` + `motivo_revisao` em vez de descartadas. Prompt do Claude atualizado para retornar `data_fim: ""` nesses casos. Ciclo completo: automação grava → sino aparece → admin revisa → dispensa ou edita.
- **Projeto 2 — Automação completa do Diário Oficial (`verificar-diario-completo.py`)** — script independente do Projeto 1. Termos-gatilho amplos: "Polo Médio Amazonas" + 6 cidades + 5 servidores (Luma Karolyne Pantoja Bandeira, Fábio Bastos de Souza, Natália Cristina de Moraes, Arnoud Lucas Andrade da Silva, Larice Bruce Pereira) + titulares vigentes do JSON. Extrai e categoriza **todas** as portarias relevantes (não só afastamentos) e atualiza `docs/diario-oficial-completo-2026.json`. Usa API key separada (`ANTHROPIC_API_KEY_COMPLETO`) para rastrear custos independentemente. Limit mensal: $5,00. Workflow `.github/workflows/verificar-diario-completo.yml` roda às **04:00 de Manaus** (08:00 UTC). Na primeira execução, inicializa estado a partir da edição mais recente do JSON (17/04/2026) sem reprocessar histórico. Testado em 22/04/2026 — sucesso em 25s, sem custo (sem edições novas).
- **Bug corrigido — validação de datas no formulário de afastamento** — substitutos "ainda não definido" tinham inputs de data ocultos com valores obsoletos no DOM, bloqueando indevidamente o salvamento (ex: cobertura fim = 31/05 quando afastamento fim = 30/05). Corrigido com `if (!sub.substituto) continue;` no loop de validação (`salvarAfastamentoFirestore`, linha ~4133 do index.html). Commit `5522829`.
- **Concurso de Remoção — 3 novos defensores assumiram em 02/05/2026** — Ênio Jorge Lima Barbalho Junior (1ª DP), Thays Lidianne Campos de Azevedo Pereira (2ª DP) e Emilly Bianca Ferreira dos Santos (5ª DP). Adicionados ao dicionário `defensores` no JSON com chaves `enio`, `thays`, `emilly`. José Antônio Pereira da Silva e Elton Dariva Staub marcados `ativo: false` (sem DPs no polo → accordion Ex-membros). DPs 7ª a 11ª marcadas vagas a partir de 02/05/2026 em `historico_titulares` (fim: "2026-05-02", entrada `defensor: null` subsequente). 12ª DP já estava vaga desde 06/04/2026. Commits `5ac5a0a` e `89f23f0`.
- **Bug corrigido — `getCurrentTitular` e `getTitularForDPOnDay` retornavam primeira entrada, não a mais recente** — quando dois registros sobrepostos cobriam a data atual (ex.: entrada antiga com `fim: null` + nova entrada com `inicio: "2026-05-02"` também `fim: null`), a função retornava a entrada mais antiga. Corrigido: ambas agora percorrem todo o array e retornam a entrada com o `inicio` mais recente entre as válidas. Commit `5ac5a0a`.
- **`orphanCurrentMembros` — defensores do Firestore com nome como texto livre** — quando um novo defensor é cadastrado via admin UI (titulares_admin) antes de existir no JSON, o Firestore guarda o nome completo como string (não a chave do JSON). A renderização da aba Defensorias agora detecta quem tem DP ativa mas não consta no dicionário `defensores` e exibe o card normalmente. Commit `61bb356`.
- **Lista unificada `allAtivos` ordenada por DP (1ª → 6ª)** — `renderDefensorias` agora constrói um array único fundindo `internos` (dicionário JSON) e `orphanCurrentMembros` (Firestore texto livre), ordenado pela menor DP atual de cada defensor. Elimina duplicação e garante exibição na ordem correta. `allAtivos.length` usado no contador "Total de Defensores". Commit `760f628`.
- **Bug corrigido — placeholders `dpX-vaga` inflavam o contador de defensores** — chaves no formato `dp7-vaga` … `dp12-vaga` (geradas por `_atualizarNomesVaga()` para DPs vagas) eram incluídas em `orphanCurrentMembros` e faziam o total aparecer como 12 em vez de 6. Corrigido adicionando filtro `!/^dp\d+-vaga$/i.test(defKey)` na construção de `orphanCurrentMembros` (`renderDefensorias`, linha ~6198). Commit `6ff2deb`.
- **Atenção — titulares_admin no Firestore para DPs 1, 2, 5** — provavelmente armazenam os novos defensores como nome completo (texto livre) em vez das chaves JSON (`enio`, `thays`, `emilly`), pois foram cadastrados antes do JSON ser atualizado. O site exibe corretamente via `orphanCurrentMembros`, mas para limpar o histórico o admin deve abrir o modal ✏️ dessas DPs e salvar novamente — o sistema vai reescrever com as chaves corretas.
- **Automação migrada de Haiku para Sonnet (`verificar-diario-oficial.py`)** — `parse_designations` e `parse_remocao` agora usam `claude-sonnet-4-5-20251001` em vez de `claude-haiku-4-5-20251001`. O Haiku apresentou erros recorrentes de interpretação (ex.: identificar o substituto como ausente). Commit `8d037d0` (07/05/2026).
- **Bug corrigido — automação identificava substituto como defensor_ausente** — quando o DO dizia "Designar ÍCARO para substituir na 5ª DP", o Haiku identificava Ícaro como ausente em vez da titular da 5ª DP (Emilly). Adicionado bloco `ATENÇÃO` no prompt de `parse_designations` deixando explícito que `defensor_ausente` = titular da DP afetada e `substituto` = pessoa designada, com exemplo concreto. Commit `8d037d0` (07/05/2026).
- **Bug corrigido — designações cumulativas classificadas erroneamente como afastamentos** — portarias com verbo DESIGNAR + cumulativamente + sem data fim ("a contar do dia X" sem "até Y") eram salvas em `afastamentos_admin` e apareciam no sino azul. Caso exemplo: Eliaquim → 9ª DP a partir de 04/05/2026 (portaria de 06/05/2026). Correção: prompt do Claude agora tem terceiro array `designacoes_cumulativas` com regras explícitas de classificação; nova função `salvar_designacoes_cumulativas_firestore()` grava em `designacoes_cumulativas_admin`. Commit `457244c` (07/05/2026).
- **Sino 🔔 de Designações Cumulativas** — botão `#btn-sino-designacao` na **barra de abas**, ao lado do `#btn-sino-remocao` (ambos junto à aba "📋 Defensorias"). Cabeçalho **verde** (`#166534`/`#16a34a`) para diferenciar dos outros dois sinos (azul = afastamentos, âmbar = remoções). Lê coleção `designacoes_cumulativas_admin` (onde `origem:"automacao-diario-oficial"` e `lido !== true`). Painel exibe: defensor, DP designada, data de início, portaria clicável, instrução "📋 Atualize o titular na aba Defensorias". Apenas botão [🗑️ Dispensar] — sem Editar (a ação é na aba Defensorias). Funções: `_atualizarBadgeSinoDesignacao()`, `abrirPainelDesignacao()`, `fecharPainelDesignacao()`, `dispensarDesignacao(id)`. Global: `designacaoNotifData[]`. `carregarNotificacoesAutomacao()` tem terceiro bloco `try/catch` independente para esta coleção. Commit `457244c` (07/05/2026).

### O que ainda falta implementar ⏳
- ~~**Dispensar registro incorreto do Eliaquim em `afastamentos_admin`**~~ ✅ Deletado manualmente no Firestore Console em 07/05/2026. O registro correto (em `designacoes_cumulativas_admin`) será criado automaticamente na próxima execução da automação caso a edição de 06/05/2026 ainda não tenha sido reprocessada.
- **Cadastrar os outros 36 usuários restantes** (1 admin + 35 viewers) no Firebase Auth + Firestore — Larice Bruce e José Antônio já cadastrados em 23/04/2026
- **Dados privados da equipe** — WhatsApp, contatos internos (estrutura no Firestore planejada mas não implementada)
- **Botão "Plantão"** — nova seção na landing page com escala de plantão de defensores e servidores. Arquitetura a definir na próxima sessão (dados estáticos no HTML? JSON? Firestore?).
- **Botão "Escala de Férias"** (futuro) — calendário visual de férias da equipe (defensores + servidores). Ideia: grid anual/mensal mostrando períodos de férias de cada pessoa. Arquitetura a definir.
- ~~**Limpar titulares_admin das DPs 1, 2, 5 no Firestore**~~ ✅ Concluído em 04/05/2026 — admin reabriu o modal ✏️ de cada DP e salvou; chaves corretas (`enio`, `thays`, `emilly`) gravadas no Firestore.
- ~~**Dispensar notificações erradas do sino 🔔 de afastamentos**~~ ✅ Já dispensadas (confirmado em 04/05/2026 — não aparecem mais no painel).
- ~~**Excluir afastamentos do José Antônio no Firestore**~~ ✅ Deletado via script em 04/05/2026 — doc `CpewjdQkUjofHP3xVe9v` (férias 08–25/jun) removido da coleção `afastamentos_admin`. Era o único registro futuro no Firestore.
- **Comportamento da 7ª DP (SSU) na aba Designações Semanais** — mostra "—" em vez de "dp7-vaga" como as DPs 8–12. Isso ocorre porque o site usa o JSON (que tem `defensor: null`) em vez do Firestore (que tem `dp7-vaga`). Comportamento correto — significa DP vaga. Miguel NÃO está mais vinculado à 7ª DP (Firestore tem `fim: 2026-04-29` para ele; `dp7-vaga` vigente desde 2026-04-30).
- ~~**Afastamento do Miguel com 7ª DP indevida**~~ ✅ Corrigido em 04/05/2026 — o registro de Tratamento de Saúde (02/05–09/06) foi criado quando Miguel ainda era titular de 6ª e 7ª DPs. O formulário de edição recalcula DPs pelos titulares atuais (só mostra 6ª DP). Admin abriu o ✏️ e salvou → Firestore sobrescrito sem a 7ª DP.

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
5. Envia trechos ao **Claude Sonnet 4.5** (`claude-sonnet-4-5-20251001`, `max_tokens=2048`) com prompt que pede JSON com dois arrays: `afastamentos` (ausências com substituto) e `cessacoes` (portarias que "cessam efeitos" / "tornam sem efeito" designações anteriores — DP ficará vaga). Portarias de cessação **não** geram afastamentos.
6. `salvar_afastamentos_firestore()` grava afastamentos em `afastamentos_admin`; `salvar_cessacoes_firestore()` grava cessações em `remocoes_admin` com `tipo:"cessacao_designacao"` e dedup por `portaria_cessada`.
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

### Custos (Claude Sonnet 4.5, preços conservadores no script)
- Entrada: $3/M tokens; Saída: $15/M tokens
- Execução com edição nova sem menção ao Polo Médio: **$0** (pré-filtro pula a chamada)
- Execução com designação detectada: ~$0.015–0.03 por edição
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

## Projeto 2 — Automação da aba "Diário Oficial" (✅ IMPLEMENTADO — sessão 10 em 22/04/2026)

### Contexto e diferença para o Projeto 1

O **Projeto 1** (`verificar-diario-oficial.py`) é estrito: detecta apenas afastamentos dos titulares vigentes e grava no Firestore (`afastamentos_admin`). Roda às 06:00 de Manaus. API key: `ANTHROPIC_API_KEY`. Limite: $2,00/mês.

O **Projeto 2** (`verificar-diario-completo.py`) é amplo: detecta **todas** as portarias relevantes ao polo (defensores, servidores, cidades) e atualiza `docs/diario-oficial-completo-2026.json`. Roda às 04:00 de Manaus. API key: `ANTHROPIC_API_KEY_COMPLETO`. Limite: $5,00/mês. Os dois projetos são **totalmente independentes**.

### Arquitetura implementada

- **Script:** `verificar-diario-completo.py`
- **Saída:** `docs/diario-oficial-completo-2026.json` (lido diretamente pelo site via `fetch()`)
- **Estado:** `docs/.estado-diario-completo.json` (cache independente no Actions)
- **Workflow:** `.github/workflows/verificar-diario-completo.yml`
- **Secrets necessários:** `ANTHROPIC_API_KEY_COMPLETO` (obrigatório) + `SMTP_*` (opcionais)
- **Não precisa de `FIREBASE_SERVICE_ACCOUNT`** — sem escrita no Firestore

### Termos-gatilho (amplos)
1. `"Polo\s+(?:do\s+)?Médio\s+Amazonas"` — frase fixa
2. Cidades: Itacoatiara, São Sebastião do Uatumã, Itapiranga, Urucurituba, Urucará, Silves
3. Servidores (primeiro+segundo nome): Luma Karolyne, Fábio Bastos, Natália Cristina, Arnoud Lucas, Larice Bruce
4. Titulares vigentes (carregados do `designacoes-2026.json`)

### Prompt Claude (categorização)
Extrai `numero`, `sei`, `sgi`, `categorias[]`, `trechos[]`, `resumo` de cada portaria relevante.
Categorias: `polo_medio`, `defensor`, `servidor`, `substituicao`, `nomeacao_diretoria`, `comarca`, `projeto`, `plantao`, `coordenacao`, `designacoes`.

### Lógica de atualização do JSON
- Primeira execução: inicializa `ultima_edicao` a partir do maior número de edição já presente no JSON (17/04/2026) — não reprocessa histórico
- Edição já existente no JSON: mescla portarias novas (dedup por número de portaria)
- Edição nova: cria entrada completa com `edicao`, `data`, `data_formatada`, `url`, `portarias_estruturadas`
- Commit automático do JSON pelo workflow quando houver portarias novas

### Rodar localmente (teste/debug)
```bash
py -m pip install requests pdfplumber beautifulsoup4 anthropic
set ANTHROPIC_API_KEY_COMPLETO=sk-ant-...
py verificar-diario-completo.py
```

### O que NÃO fazer (preservar Projeto 1)
- **Não misturar** os scripts — cada um tem seu próprio workflow, estado e API key
- **Não gravar em `afastamentos_admin`** — só o Projeto 1 escreve ali

---

## Regras Críticas (resumo rápido)

- **Arquivo único:** existe apenas um `index.html` na raiz. Nunca duplicar.
- **Alternância semanal:** Grupo A e Grupo B alternam toda semana sem exceção. Ver `docs/regras/alternancia.md`.
- **Destaques apenas em dias úteis:** nunca aplicar classes `itacoatiara` ou `silves` em sábados/domingos.
- **Máximo 2 defensores ausentes** ao mesmo tempo; mínimo 3 ativos.
- **Aba Tabela Completa foi removida** — o Calendário Visual é a aba principal de ausências.
- **Nunca editar seções do Firestore diretamente no HTML** — o conteúdo vem do Firestore e sobrescreve o HTML padrão ao carregar.
