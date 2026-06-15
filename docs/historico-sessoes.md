# Histórico de Sessões — O que foi implementado

> Ordem cronológica inversa (mais recente primeiro)

---

## Sessão 25 — 15/06/2026

- **Férias Equipe refatorada — 12 meses simultâneos com scroll natural da página** — `renderEquipeCalendar()` agora renderiza todos os meses de Janeiro a Dezembro do ano selecionado, empilhados verticalmente. `_renderEquipeMes(year, month)` extraído como helper reutilizável (título + cabeçalho Dom–Sáb + grade). Commits `75e7fd6`, `40472e5`, `2c3dcba`.
  - Seletor de meses (12 botões) removido — desnecessário com todos os meses visíveis.
  - Listener de scroll do mouse (`wheel`) removido — navegação pelo scroll natural da página.
  - Botão 2027 estilizado em amarelo (`#f5e600`) com borda/texto dourado.
  - Botão "Novo Afastamento" usa `new Date().getMonth()+1` em vez de `equipeCurrentMonth`.
  - Iterações intermediárias: 4 meses com scroll (throttle 300ms + piso jan/2026) — descartadas em favor da abordagem final mais simples.

## Sessão 24 — 14/06/2026

- **Bug corrigido — reprocessamento de edições antigas quando cache do Actions expira** — `load_state()` agora busca `ultima_edicao` no Firestore (`automacao_config/estado_diario`) quando o arquivo de cache não existe; `save_state()` também persiste no Firestore a cada execução. Commit `4f9199a`.
- **Estrutura modular `docs/` restaurada e atualizada** — todos os arquivos de `docs/` reescritos para refletir o estado atual do site. Criados: `enio.md`, `thays.md`, `emilly.md`, `miguel.md`, `mariana.md`, `isabela.md`. Commits `347d2d6`, `5f093e7`, `5051d57`.

## Sessão 23 — 13/06/2026

- **Seção Férias Equipe totalmente funcional** — 4 bugs corrigidos:
  - Clique em qualquer dia abre o modal. Commit `8fa2d99`.
  - Permissão Firestore corrigida (`afastamentos_equipe` adicionada às regras). Commit `5c7132e`.
  - Bug de dados sumindo no F5 (`mostrarSiteAutenticado` não chamava `loadEquipeFirestore`). Commit `ddb11a9`.
  - Bug de calendário vazio (`loadEquipeFirestore` agora re-renderiza se seção ativa). Commit `054fef2`.
  - Cache `pma-equipe-fs` no localStorage adicionado. Commit `261278d`.
- **Badges da Férias Equipe por pessoa com cor única** — legenda de tipo removida. `_equipeCorPessoa(nome)` usa `EQUIPE_PESSOA_CORES_FIXAS` (prioridade) ou `EQUIPE_PESSOA_PALETTE`. Cores fixas: Fábio=`#06b6d4`, Larice=`#ec4899`, Natália=`#14b8a6`, Luma=`#eab308`. Commits `f4dc21c`, `8066d0e`, `62b2cee`, `63a3669`, `00066e7`.

## Sessão 22

- **Cache de performance para calendário de afastamentos** — elimina delay "⏳ Carregando...". Docs brutos salvos em `localStorage['pma-afastamentos-fs']`. `_afastamentosAplicarCache()` aplica síncrono antes de qualquer chamada de rede. Commits `3d527a0`, `dd535ad`.
- **Cache da seção Férias/Folgas/Licenças corrigido** — `carregarConteudoFirestore()` agora aplica localStorage de todas as seções sincronamente primeiro, depois busca Firestore em paralelo com `Promise.all`. Commit `3d527a0`.

## Sessão 21

- **Ícones dos botões da landing e header atualizados** — Férias Equipe: `👥 → ⛱️`. Adote: `🏘️ → <img>` com gavel.png real.
- **Cores dos badges de defensores fixadas no CSS estático** — Emilly: `#f43f5e`; Miguel: `#10b981`. Adicionados ao `BADGE_CSS_KNOWN`.

## Sessão 20

- **Designações Semanais e Calendário abrem no mês vigente** — `currentMonth` inicializado com `new Date().getMonth()`.
- **Calendário suporta múltiplos anos — seletor 2026/2027** — variável `currentYear`. Botões `[2026]`/`[2027]`. `switchYear(year)`.
- **`afastamentos` e `detalhesAfastamentos` tornados year-aware** — estrutura migrada de `[mes][dia]` para `[ano][mes][dia]`.
- **Card da aba Defensorias exibe "Último dia"** — quando `hist.fim` preenchido.
- **Nova seção "Férias Equipe"** — botão ⛱️ azul-céu. Calendário de badges por mês. CRUD em `afastamentos_equipe`. Globals: `equipeCurrentYear`, `equipeCurrentMonth`, `equipeAfastamentos`, `equipeMap`.

## Sessão 19

- **Coluna "Forma de Trabalho" e linha do Raimundo removidas da tabela Adote**.
- **Cabeçalho editável do Adote migrado para `<h2>`** — form inline `#adote-info-form`.
- **Cache localStorage para seção Adote** — `pma-adote-celulas` e `pma-adote-expandir`. Detecção de cache desatualizado via `_adoteCacheDesatualizado(celulas)`.
- **Navegação rápida no header** — `#header-nav` com 4 botões (⚖️ Atribuições, 📋 Designações, 🏘️ Adote, 📰 Diário Oficial).
- **Subtítulo do header alterado** — agora lista as 6 comarcas.
- **Texto de descrição dos botões da landing aumentado** — `0.95em → 1.24em`.

## Sessão 18

- **Restauração de scroll removida** — evento `beforeunload` e listener de scroll com debounce eliminados.
- **Cache em memória das células Atribuições** — `_atrCelulasCache`. `loadTitularesFirestore()` re-renderiza Atribuições se ativa.
- **Nova seção "Adote uma Comarca"** — botão teal 🏘️. Tabela 5×4 editável. Bloco "Expandir Presença". Persistência em `secoes/adote_celulas` e `secoes/adote_expandir`. Commits `34bc812`, `eab7214`, `8c89247`, `3d04444`.
- **`_rteMountTabelaHandlers()`** — função RTE compartilhada extraída de `_rteMountAtribuicoes()`.

## Sessão 17 — 26/05/2026

- **Toggle switch "Editar" removido do header** — botões admin sempre visíveis após login. `toggleModoEdicao()` → no-op.
- **Régua de edição (RTE) completa** — toolbar `#rich-editor-toolbar` com negrito, itálico, cores, emojis, links, undo/redo. Paleta estilo Word. Painel de emojis com 5 categorias.
- **Redesign dos botões Editar/Salvar/Cancelar** — ~60% menores, fundo branco, borda azul, ícone SVG caneta.
- **Nova seção "Atribuições, Colidências e Substituições Automáticas"** — botão ⚖️ indigo. Duas tabelas (DPs 1–6 e 7–12). Dados estáticos em `ATRIBUICOES_STATIC[]`. `_atrResolverDefensor(dpKey)`. Commit `6a751ce`.
- **Link da resolução na seção Atribuições** — `secoes/atribuicoes_resolucao`. Commit `3383b7b`.
- **Células da tabela Atribuições editáveis** — modo planilha. Dupla aplicação (execCommand + `td.style.*`). `secoes/atribuicoes_celulas`. Commit `86b56b3`.

## Sessões 14–16

- **Sino 🔔 de Designações Cumulativas** — `#btn-sino-designacao`, painel verde, coleção `designacoes_cumulativas_admin`. Commit `457244c`.
- **Bug corrigido — automação identificava substituto como defensor_ausente** — bloco `ATENÇÃO` adicionado ao prompt do Claude. Commit `8d037d0`.
- **Automação migrada de Haiku para Sonnet** — `claude-sonnet-4-5-20251001`. Commit `8d037d0`.
- **Bug corrigido — designações cumulativas classificadas como afastamentos** — novo array `designacoes_cumulativas` no prompt; `salvar_designacoes_cumulativas_firestore()`. Commit `457244c`.

## Sessões 10–13

- **Projeto 2 — `verificar-diario-completo.py`** — automação ampla, atualiza `docs/diario-oficial-completo-2026.json`. Workflow às 04:00 Manaus. API key separada `ANTHROPIC_API_KEY_COMPLETO`. Limite $5/mês.
- **Sino 🔔 de Alterações de Titularidade** — `#btn-sino-remocao`, painel âmbar, coleção `remocoes_admin`. Tipos: `cessacao_designacao` (borda vermelha) e concurso de remoção (borda âmbar).
- **Novo sino 🔔 de afastamentos movido para barra de abas** — commit `382c90e`.
- **`orphanCurrentMembros`** — defensores cadastrados via UI como texto livre exibidos corretamente.
- **Lista unificada `allAtivos` ordenada por DP**.
- **Bug corrigido — placeholders `dpX-vaga` inflavam contador**.

## Sessões 7–9

- **Concurso de Remoção nº 1/2026 (02/05/2026)** — Ênio (1ª DP), Thays (2ª DP), Emilly (5ª DP) assumiram. José Antônio, Elton, Elaine marcados `ativo: false`. DPs 7–11 vagas. Commits `5ac5a0a`, `89f23f0`.
- **Bug corrigido — `getCurrentTitular` retornava primeira entrada, não a mais recente**. Commit `5ac5a0a`.
- **Automação atualizada** — grava `lido: false`, `edicao_do`, `data_publicacao_do`. Designações sem data fim gravadas com `precisa_revisao: true`.
- **`dp12-vaga` e `_atualizarNomesVaga()`** — placeholder para DPs vagas.
- **Dropdown de substituto dinâmico** — `_opcoesSubstituto()` lê JSON, só ativos.
- **`getTitularForDPOnDay` com intervalo inclusivo** — `date <= fim`.
- **Backfill executado e corrigido** — `backfill-calendario-do-estruturado.py`. 8 registros genuínos no Firestore. Script de limpeza `limpar-backfill.py`.

## Sessões 4–6

- **Sino 🔔 de notificações da automação (afastamentos)** — `#btn-sino`, painel azul, coleção `afastamentos_admin` com `origem: "automacao-diario-oficial"`.
- **Filtro por DP na Lista de Substituições**.
- **Modal de detalhes: células mescladas por afastamento, separador azul, datas inline, ícones verticais**.
- **Nova aba "Lista de Substituições"** — `renderListaSubstituicoes()`.
- **Aba "Resumo de Afastamentos" dinamizada** — `renderDetalhesAfastamentos()`.
- **Automação do Diário Oficial via GitHub Actions** — `verificar-diario-oficial.py`, workflow `verificar-diario.yml`, gravação direta no Firestore. Ativo desde 17/04/2026.
- **Integração calendário ↔ Designações Semanais** — células com `.sem-cobertura` quando sem substituto definido.

## Sessões 1–3

- **Sistema de login completo** — Firebase Auth overlay, roles admin/viewer.
- **Badge ADMIN**, botão Sair, botão Início no header.
- **Seções editáveis inline** — Regra de Alternância e Férias/Folgas/Licenças com RTE básico.
- **Coluna Diário Oficial no modal do calendário**.
- **Aba Tabela Completa removida** — Calendário Visual como aba principal.
- **Calendário interativo para admins** — CRUD completo via Firestore.
- **Edição dos defensores titulares por DP** — modal completo, histórico por data.
- **Modal de visualização somente leitura 🔍** — para todos os usuários.
- **Registros base (JSON) editáveis pelo admin** — campo `json_base_id`, `jsonOverrideMap`.
- **Dropdown de defensores dinâmico** — `buildDefensorNames()`, `populateDefensorDropdown()`.
- **Detecção automática de ex-membros** — `orphanExMembros` na aba Defensorias.
