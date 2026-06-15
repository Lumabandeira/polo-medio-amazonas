# Funções JavaScript Principais

> Atualizado em 14/06/2026. O site usa Firebase Auth + Firestore; não há mais lógica estática de window.onload simples.

## Inicialização

```
loadJSONData()                  ← carrega os dois JSONs (designacoes + afastamentos)
  └→ buildAfastamentosFromJSONRegistros()
  └→ buildDetalhesFromJSONEventos()
  └→ _afastamentosAplicarCache()   ← aplica localStorage antes de qualquer rede
  └→ loadAfastamentosFirestore()   ← mescla Firestore por cima

Firebase onAuthStateChanged()   ← detecta login/logout
  └→ mostrarSiteAutenticado()
       └→ carregarConteudoFirestore()
       └→ loadTitularesFirestore()
       └→ loadAfastamentosFirestore()
       └→ loadEquipeFirestore()
       └→ carregarNotificacoesAutomacao()
```

## Resolução de titular por data

| Função | O que faz |
|--------|----------|
| `getTitularForDPOnDay(dpNum, mes, dia)` | Retorna defensor vigente em uma data específica (intervalo inclusivo) |
| `getCurrentTitular(dp, historico)` | Local a `renderDefensorias` — retorna entrada ativa mais recente |
| `getFutureTitular(dpKey)` | Retorna defensor com início futuro (detecta futuros membros) |
| `_atrResolverDefensor(dpKey)` | Versão global para a seção Atribuições (não chama getCurrentTitular) |

## Calendário de Afastamentos

| Função | O que faz |
|--------|----------|
| `renderCalendar()` | Renderiza calendário mensal com badges por defensor |
| `switchYear(year)` | Troca entre 2026/2027 e re-renderiza |
| `changeMonth(dir)` | Avança/recua mês, ajustando ano ao cruzar dezembro/janeiro |
| `openModal(ano, mes, dia)` | Abre modal de detalhes do dia |
| `abrirVisualizacaoAfastamento(tipo, id)` | Modal 🔍 somente leitura |
| `abrirFormAfastamento(ano, mes, dia, id)` | Abre formulário CRUD de afastamento |
| `salvarAfastamentoFirestore()` | Valida e grava em `afastamentos_admin` |
| `confirmarDeletarAfastamento(id, ano, mes, dia)` | Confirma e deleta registro |
| `loadAfastamentosFirestore()` | Busca `afastamentos_admin`, mescla, re-renderiza |
| `mergeAfastamentoFirestoreRecord(doc)` | Mescla 1 doc Firestore nos objetos `afastamentos`/`detalhes` |
| `renderListaSubstituicoes()` | Renderiza aba Lista de Substituições (agrupa por mês) |
| `renderDetalhesAfastamentos()` | Renderiza aba Resumo de Afastamentos (agrupa por defensor) |

## Férias Equipe

| Função | O que faz |
|--------|----------|
| `loadEquipeFirestore()` | Busca `afastamentos_equipe`, aplica via `_equipeAplicarRegistros()` |
| `_equipeAplicarRegistros(registros)` | Popula `equipeAfastamentos` e `equipeMap`, re-renderiza |
| `_renderEquipeMes(year, month)` | Renderiza um bloco mensal (título + cabeçalho Dom–Sáb + grade); retorna elemento DOM |
| `renderEquipeCalendar()` | Renderiza os 12 meses do ano selecionado (`equipeCurrentYear`), empilhados verticalmente |
| `_equipeCorPessoa(nome)` | Retorna cor fixa (EQUIPE_PESSOA_CORES_FIXAS) ou cor da paleta |
| `abrirModalEquipe(ano, mes, dia)` | Modal de detalhes do dia (todos os afastamentos da equipe) |
| `salvarEquipeFirestore()` | Grava/atualiza em `afastamentos_equipe` |

## Seção Atribuições

| Função | O que faz |
|--------|----------|
| `renderAtribuicoes()` | Constrói as duas tabelas (DPs 1–6 e 7–12) |
| `_atrCarregarCelulas()` | Carrega `secoes/atribuicoes_celulas` (com cache 3 camadas) |
| `_atrEntrarModoEdicao()` | Ativa contentEditable + monta toolbar RTE |
| `_atrSalvarCelulas()` | Grava `{ html, cellStyle }` por TD no Firestore |
| `_atrCarregarResolucao()` | Carrega link da resolução do Firestore |

## Seção Adote

| Função | O que faz |
|--------|----------|
| `renderAdote()` | Monta tabela + chama carregarInfo/Celulas/Expandir |
| `_adoteCarregarCelulas()` | Carrega `secoes/adote_celulas` (com cache 3 camadas) |
| `_adoteEntrarModoEdicao()` | Ativa contentEditable + monta toolbar RTE |
| `_adoteSalvarCelulas()` | Grava células no Firestore + atualiza cache |

## Toolbar Rich Text (RTE)

| Função | O que faz |
|--------|----------|
| `_rteMount(secaoId)` | Monta toolbar para seções de texto (Alternância/Férias) |
| `_rteMountAtribuicoes()` | Monta toolbar para células ATR, chama `_rteMountTabelaHandlers()` |
| `_rteMountAdote()` | Monta toolbar para células Adote, chama `_rteMountTabelaHandlers()` |
| `_rteMountTabelaHandlers()` | **Função compartilhada** — conecta botões usando `_rteTargetEl` |
| `_rteUnmount()` | Oculta toolbar, move para `document.body` |
| `_rteSaveRange()` / `_rteRestoreRange()` | Preserva seleção ao clicar na toolbar |

## Notificações (sinos)

| Função | Sino |
|--------|------|
| `carregarNotificacoesAutomacao()` | Carrega as 3 coleções (try/catch independentes) |
| `_atualizarBadgeSino()` | Badge azul — `afastamentos_admin` |
| `_atualizarBadgeSinoRemocao()` | Badge âmbar — `remocoes_admin` |
| `_atualizarBadgeSinoDesignacao()` | Badge verde — `designacoes_cumulativas_admin` |
| `dispensarNotificacao(id)` | Grava `lido: true` em `afastamentos_admin` |
| `dispensarRemocao(id)` | Grava `lido: true` em `remocoes_admin` |
| `dispensarDesignacao(id)` | Grava `lido: true` em `designacoes_cumulativas_admin` |

## Validações antigas (ainda presentes, uso limitado)

| Função | Status |
|--------|--------|
| `getDayOfWeek(year, month, day)` | Ainda usada internamente |
| `validateWeekendHighlights()` | Ainda roda nas tabelas de Designações Semanais |
| `validateAlternation()` | Ainda roda; reporta erros no console (F12) |
