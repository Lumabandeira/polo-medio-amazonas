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

afastamentos_admin/{id}   ← afastamentos adicionados pelo admin via calendário
  defensor: "elton"       ← chave do defensor (mesmo padrão dos JSONs)
  tipo: "ferias" | "folga" | "licenca_especial"
  data_inicio: "2026-04-15"
  data_fim: "2026-04-20"
  portaria_numero: "Portaria nº 123/2026-GSPG/DPE/AM"
  portaria_url: "https://..."   ← link do PDF do Diário Oficial
  portaria_sei: "26.0.000..."
  designacoes: [{ dp: "5", substituto: "eliaquim" }, ...]
  criado_por: "email@..."
  criado_em: timestamp
  atualizado_por: "email@..."
  atualizado_em: timestamp
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

## Estado atual do site (atualizado em 15/04/2026 — sessão 3)

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

### O que ainda falta implementar ⏳
- **Cadastrar os outros 38 usuários restantes** (1 admin + 37 viewers) no Firebase Auth + Firestore
- **Dados privados da equipe** — WhatsApp, contatos internos (estrutura no Firestore planejada mas não implementada)

### Descartado (não vale implementar)
- **Coleção `defensores_admin` no Firestore** — descartado: ex-membros livres já detectados automaticamente via orphanExMembros; casos raros de inconsistência com o JSON não justificam a complexidade

### Decisões de arquitetura já tomadas
- Sem automação do Diário Oficial — admin insere links manualmente
- Sem migração de hospedagem — continua no GitHub Pages
- JSONs locais (`docs/afastamentos-2026.json` e `docs/designacoes-2026.json`) = base imutável pela UI. Coleções `afastamentos_admin` e `titulares_admin` no Firestore = registros adicionados/editados pelo admin. Mesclados em memória ao carregar (Firestore sobrescreve JSON).
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

## Regras Críticas (resumo rápido)

- **Arquivo único:** existe apenas um `index.html` na raiz. Nunca duplicar.
- **Alternância semanal:** Grupo A e Grupo B alternam toda semana sem exceção. Ver `docs/regras/alternancia.md`.
- **Destaques apenas em dias úteis:** nunca aplicar classes `itacoatiara` ou `silves` em sábados/domingos.
- **Máximo 2 defensores ausentes** ao mesmo tempo; mínimo 3 ativos.
- **Aba Tabela Completa foi removida** — o Calendário Visual é a aba principal de ausências.
- **Nunca editar seções do Firestore diretamente no HTML** — o conteúdo vem do Firestore e sobrescreve o HTML padrão ao carregar.
