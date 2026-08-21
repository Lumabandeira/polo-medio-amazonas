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
| Mexer na seção Plantão (escala de plantão do interior) | `docs/site/estrutura-html.md` (seção "Plantão") · `docs/firebase.md` (schema `plantao_admin`/`plantao_info`) |
| Mexer na seção Viagens e Eventos (tabelas de viagens/eventos da equipe) | `docs/site/estrutura-html.md` (seção "Viagens e Eventos") · `docs/firebase.md` (schema `viagens_tabela1`/`viagens_tabela2`) |
| Mexer na seção Escala Semanal (atendimento/audiência/plantão por semana) | `docs/site/estrutura-html.md` (seção "Escala Semanal") — somente leitura, sem Firestore próprio |

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

## Estado atual (sessão 35 — 21/08/2026)

**Implementado nesta sessão:** correção de um typo de longa data ("Karolayne" → "Karolyne",
nome da servidora Luma Karolyne Pantoja Bandeira) que só existia no seed `PLANTAO_SEED_2026`
de `index.html` — corrigido no código e nos 2 documentos já gravados em `plantao_admin` que
tinham herdado o erro (script Python pontual com `firebase-service-account.json`, sem alterar
`firestore.rules`). Também investigado por que a coleção `plantao_admin` apareceu vazia no
site (ver `docs/historico-sessoes.md` sessão 35 para o diagnóstico — conclusão: exclusão manual
fora do repositório, sem processo automático capaz disso).

Principal: cada linha da tabela de Plantão ganhou uma coluna "Portaria" com link para o
diário oficial que definiu aquele período — antes só havia um link geral fixo no topo da
página (`plantao_info`), sem diferenciar períodos alterados por portaria pontual posterior
(caso já ocorrido antes, ver histórico de substituições no Diário Oficial). 5 campos novos e
opcionais em `plantao_admin/{id}`: `portaria_numero`/`portaria_url` (portaria própria do
período, raro) e `alteracao_numero`/`alteracao_url`/`alteracao_obs` (quando a escala foi
alterada por portaria pontual — vira badge laranja "🔄" em destaque, sem mostrar a portaria
original ao lado, decisão explícita da usuária). Linhas sem portaria própria caem no link geral
(`plantaoInfoAtual`, cache síncrono de `secoes/plantao_info` — decisão para funcionar em toda
linha sem repetir leitura do Firestore). Só editável pelo formulário de 1 período — CSV/seed
continuam com os 4 campos base. `_plantaoLinkPortariaHtml()`/`_plantaoAtualizarColunaPortaria()`
em `index.html`. Testado no navegador local (servidor estático `.claude/launch.json`, sem login
real, `userRole='admin'` simulado via console) — 4 casos (sem portaria própria, com portaria
própria, com alteração, e um payload de XSS no `alteracao_obs`). O teste revelou e corrigiu um
bug real: o `title` do badge usa `esc(...).replace(/"/g, '&quot;')` (não só `esc()`), porque o
helper `esc()` do site só escapa `&`/`<`/`>` (seguro em texto de nó HTML, mas não dentro de um
atributo) — mesmo padrão já usado em `_viagensEscAttr()`.

**Ajuste ainda nesta sessão:** a usuária pediu pra adotar, no rótulo do link de portaria do
Plantão, o mesmo estilo já usado na coluna "Diário Oficial" das tabelas de Afastamentos —
ícone 📄, azul, negrito, e texto "Edição NNNN" **extraído automaticamente da URL**
(`Edicao_NNNN` no nome do arquivo), em vez de depender de o admin digitar um rótulo. Nova
função `_plantaoRotuloEdicao(url)`; os campos `portaria_numero`/`alteracao_numero` do
formulário viraram *override* opcional (só necessário se o link não seguir esse padrão de
nome — cai em "Abrir PDF"). Testado no navegador com 5 casos (extração automática nos 3
níveis de prioridade, override manual, e link sem padrão reconhecível). Ver
`docs/site/estrutura-html.md` (seção "Plantão") e `docs/firebase.md` para o detalhamento
completo.

**Bug real encontrado e corrigido ainda nesta sessão:** a usuária notou várias semanas
duplicadas na tabela de Plantão. Causa: `_plantaoImportarSeed()` só checava
`plantaoRegistros.length` (memória do navegador) antes de gravar — se o admin clicasse
"Importar dados iniciais" antes do 1º `loadPlantaoFirestore()` terminar, o array local
ainda estava vazio mesmo com períodos já existindo no Firestore, e o seed inteiro era
regravado por cima (foi exatamente o que aconteceu na reimportação desta sessão, criando
8 pares duplicados sobre os 10 períodos que já existiam). Corrigido em duas camadas: (1)
`renderPlantao()` só oferece o botão de seed depois que `plantaoCarregouUmaVez` confirma
uma leitura real do Firestore — antes mostra "carregando" em vez do estado vazio; (2)
`_plantaoImportarSeed()` revalida direto no Firestore (`.limit(1).get()`) imediatamente
antes de gravar, com trava contra duplo-clique. Dados corrigidos em produção (script
pontual com a service account, após confirmação explícita da usuária): 8 documentos
duplicados deletados (mantido sempre o original de 05/08 — dados idênticos em cada par,
conferido campo a campo antes de apagar), voltando a 13 períodos únicos. Também gravado
o link definitivo da Portaria 764/2026 em `secoes/plantao_info.url`
(https://defensoria.am.def.br/wp-content/uploads/2026/08/Portaria-no-0764-2026-GSPG-26.0.000010208-2.pdf),
que agora aparece em toda linha sem portaria própria (rótulo "Abrir PDF", já que essa URL
não segue o padrão `Edicao_NNNN`). Ver `docs/site/estrutura-html.md` (seção "Plantão").
Também preenchido `portaria_url` nos 13 períodos com a Edição 2696/2026 (quem publicou a
maioria da escala, informado pela usuária) via script pontual — ação de dado, sem mudança
de código.

**Ajuste:** usuária ficou preocupada que o "Importar CSV" (única via prevista
pra adicionar escalas futuras) não tinha como registrar o link do Diário Oficial — ficaria
sempre dependendo do link geral da seção, que fica desatualizado a cada nova edição. Adicionado
campo opcional "Link do Diário Oficial" no topo do modal de CSV, aplicado a todos os períodos
daquele lote (`_plantaoConfirmarImportacaoCsv()`) — cenário comum é uma edição publicar várias
semanas de uma vez, então um campo por lote (não por linha do CSV) evita ter que editar o texto
manualmente pra incluir a URL em cada linha. Ver `docs/site/estrutura-html.md` (seção "Plantão").

**Agrupamento por lote:** usuária vai empilhar mais escalas na mesma coleção com o tempo (4º
Trimestre 2026, depois 1º Semestre **ou** 1º Trimestre de 2027 — a administração decide o
formato a cada vez) e queria poder nomear/separar cada leva na tabela, em vez de uma lista única
achatada. Novo campo opcional `lote_nome` (texto livre) em cada período, preenchido pelo
formulário de 1 período (pré-preenche com o lote do período mais recente já cadastrado) e pelo
CSV (campo único por lote, mesmo padrão do link). `renderPlantao()` agrupa por `lote_nome`
(`_plantaoAgruparPorLote()`): um bloco por lote, ordenados pelo maior `data_inicio` de cada
grupo decrescente (lote mais recente no topo — decisão da usuária), badge "🔵 atual" no grupo
que contém a data de hoje, botão "✏️ renomear" (admin) que atualiza `lote_nome` em todos os
períodos daquele grupo de uma vez (mesmo padrão de edição inline de `_plantaoEditarInfo()`) —
também decisão da usuária, pra não precisar corrigir um nome período a período. `PLANTAO_SEED_2026`
passou a gravar `lote_nome: '3º Trimestre 2026'` em cada item (constante `PLANTAO_SEED_2026_LOTE`).
Testado no navegador com 2 lotes + 1 sem lote + 1 com payload de XSS/aspas no nome: ordem dos
grupos, contagem, badge "atual", pré-preenchimento do formulário, reset do campo do CSV, e o
`renomear` monta corretamente a lista de IDs a atualizar sem gravar de verdade. Backfill dos 13
períodos já existentes com `lote_nome: "3º Trimestre 2026"` já executado (script pontual). Ver
`docs/site/estrutura-html.md` (seção "Plantão") e `docs/firebase.md`.

**Bug de segurança real encontrado e corrigido ainda nesta sessão:** ao explorar Viagens e
Eventos pra estender o mesmo padrão de link (ver próximo item), percebi que os 3
`href="${esc(url)}"` de `_plantaoLinkPortariaHtml()` (Plantão) usavam só `esc()` — que só escapa
`&`/`<`/`>`, não aspas. Testado e confirmado explorável: uma URL com aspas + `onmouseover=...`
quebrava o atributo `href` e o handler disparava ao passar o mouse. Os testes anteriores desta
sessão só tinham coberto o `title` do badge de alteração (`alteracao_obs`), não os próprios
`portaria_url`/`alteracao_url`. Corrigido com um novo helper genérico `_escAttr(s)` (=
`esc(s).replace(/"/g,'&quot;')`) nos 3 pontos, e `_plantaoRotuloEdicao()` renomeada pra
`_rotuloEdicaoDiario()` (sem prefixo de seção, já que passou a ser usada por Viagens e Eventos
também). Testado de novo com o mesmo payload — não dispara mais.

**Extensão pra Viagens e Eventos:** usuária mostrou a tela de "Importar Períodos via CSV" do
Plantão (chip de referência) e o modal "Editar Afastamento" (mostrando os campos "Processo"
SEI/SGI + número, e "Número da Portaria"/"Link do Diário Oficial" por substituto) como
inspiração, e pediu os mesmos 3 campos em Viagens e Eventos: seletor SEI/SGI + número de
processo, link do Diário Oficial, e número da portaria. Adicionados 4 campos opcionais nas duas
coleções (`viagens_tabela1_admin`/`viagens_tabela2_admin`): `processo_tipo`/`processo_numero`
(mesmo padrão do campo "Processo" de Afastamentos, `index.html:3958`) e
`portaria_numero`/`portaria_url` (mesma convenção de Plantão/Afastamentos/Remoções — reaproveita
`_rotuloEdicaoDiario()` recém-renomeada). Novo bloco no formulário
(`#viagens-form-overlay`), populado/lido em `_viagensAbrirForm()`/`_viagensSalvarEvento()`.
Renderização: `_viagensProcessoHtml(ev)`/`_viagensPortariaHtml(ev)`, novas colunas "Processo" e
"Portaria" na Lista (`_viagensRenderLista()`, colspan do estado vazio ajustado) e uma linha extra
compacta no modal de detalhe do dia do Calendário (`_viagensAbrirDiaModal()`) — não adicionado ao
`title` do hover da barra do calendário (`_viagensDetalheEvento()`), julgado baixo valor pra um
tooltip curto. Testado no navegador: 3 eventos simulados (sem processo/portaria, com dados
normais, e com payloads de XSS/aspas em `processo_numero`/`portaria_numero`/`portaria_url`) —
nenhum disparo mesmo simulando hover em todos os elementos da linha, campos do formulário
populam/resetam corretamente, e a linha extra aparece certo no modal do dia. Ver
`docs/site/estrutura-html.md` (seção "Viagens e Eventos") e `docs/firebase.md` para o
detalhamento completo.

## Estado atual (sessão 34 — 19/08/2026)

**Implementado nesta sessão:** reformulação de "🧳 Viagens e Eventos" (sessão 33) em duas
sub-abas — 📅 Calendário e 📋 Lista, lendo a mesma fonte de dados. Trocado o modelo de dados
da v1 (doc único `secoes/viagens_tabela{1,2}` com array de linhas em texto livre) por
coleções (`viagens_tabela1_admin/{id}`, `viagens_tabela2_admin/{id}`, um doc por evento) com
`data_inicio`/`data_fim` reais — só assim o Calendário consegue posicionar cada evento nos
dias certos. O Calendário mostra as duas tabelas juntas num único grid mensal, cada evento
como uma **barra colorida contínua** ao longo de todo o intervalo de datas (não precisa clicar
pra ver do que se trata — rótulo no primeiro dia, hover mostra o detalhe completo), com
empilhamento automático (algoritmo de "lanes") quando dois eventos se sobrepõem no tempo.
Clicar em qualquer dia abre modal com os eventos daquele dia + botões de adicionar (um por
tabela) com data pré-preenchida. A Lista passou a ordenar automaticamente por data (decisão da
usuária: trocou o inserir/excluir-linha-em-qualquer-posição da v1 por isso, já que agora tem
datas reais) e ganhou filtro por mês + "Ano todo". Cor da seção trocada de roxo → rosa/coral →
cinza-grafite (paleta final, a pedido da usuária, aplicada em botão/cabeçalhos/bordas de forma
consistente). `firestore.rules` recebeu `viagens_tabela1_admin`/`viagens_tabela2_admin`
(admin-only write) — **publicado em produção** via `firebase deploy --only firestore:rules`
(login interativo da usuária, `bandeira.lkp@gmail.com`; a service account do repo não tinha
permissão pra isso). Testado no navegador via console (sem login real): renderização do calendário com
lanes/barras contínuas, modal de dia, formulário com pré-preenchimento e alternância de campos
por tabela, validação de datas, filtro de lista, troca de sub-abas, e escaping seguro (inclusive
em atributos `title`). Ver `docs/site/estrutura-html.md` (seção "Viagens e Eventos") e
`docs/firebase.md` para o detalhamento completo.

**Implementado sessão 33 (19/08/2026):** primeira versão de "🧳 Viagens e Eventos" (nav + landing, logo após
Adote, botão visível a todos os usuários logados — só a edição é admin-only). Duas tabelas
independentes (`VIAGENS_TABELAS[1]`/`[2]` em `index.html`): "Eventos e Próximas Viagens
Previstas" (Data/Membro/Motivo) e "Viagens Trimestrais" (Local/Data/Motivo/Membro), seed
inicial extraído do PDF fornecido pela usuária. Padrão novo no site: linhas guardadas como
array ordenado `linhas:[{id,celulas:[...]}]` (não o mapa `ROW_COL` de Atribuições/Adote,
porque é preciso inserir/excluir linha em **qualquer posição, exceto o cabeçalho**) e célula em
modo edição é `<textarea>` puro (sem RTE) em vez de `contentEditable` — decisão explícita da
usuária por "texto pré-formatado" simples. Cada linha ganha ➕ inserir-acima / 🗑️ excluir no
modo edição; `_viagensColetar()` sincroniza os `<textarea>` visíveis antes de qualquer
inserir/excluir, então editar uma linha e depois inserir/excluir outra não perde o que já foi
digitado. Testado no navegador (sem login real — verificação via console simulando
`userRole='admin'`): renderização das duas tabelas, entrar/sair modo edição, inserir acima,
excluir com confirmação, cancelar restaura snapshot original, e escaping contra
HTML/script injection na célula. `firestore.rules` não precisou de alteração — `secoes/{id}`
já cobre escrita admin-only genericamente. Ver `docs/site/estrutura-html.md` (seção "Viagens e
Eventos") e `docs/firebase.md` para o detalhamento completo.

**Implementado sessão 32 (09/08/2026):** bugfix real de duplicação de afastamentos no popup de
detalhe do dia (`_afastamentosAplicarCache()` não limpava as entradas do Firestore em
`detalhesAfastamentos` antes de remesclar — corrigido); filtro por mês em Lista de
Substituições (mesmo padrão visual de Designações Diárias/Escala Semanal, escopado pra não
interferir nos outros); ajustes de estética/nomenclatura na navegação a pedido da usuária
(Plantão laranja, Escala Semanal com o vermelho que era do Plantão, "Designações semanais"
→ "Designações diárias" e "Calendário" → "Calendários de afastamentos", reordenação de
abas, nova descrição do card Designações, removido contador "Total de Defensores"); botão
"Prestação de Contas" agora também no header-nav (antes só na landing). Ver
`docs/site/estrutura-html.md` e `docs/historico-sessoes.md` (sessão 32) para o
detalhamento completo.

**Implementado sessão 31 (09/08/2026):** nova seção "📋 Escala Semanal" (nav + landing, logo após
Atribuições) — tabela somente leitura de Atendimento/Audiência de Família, Cível e Criminal,
Plantão e as duas UDIS, uma linha por semana. **100% derivada de fontes já existentes** (mesma
lógica de `DPS_CONFIG`/`getWeekGroup()` de Designações Semanais + `getResponsibleForDPOnDay()` +
`plantao_admin`) — sem Firestore próprio, sem edição direta na tabela. Segmenta dia a dia dentro
da semana quando o responsável muda no meio dela. Ver `docs/site/estrutura-html.md` (seção
"Escala Semanal") e `docs/historico-sessoes.md` (sessão 31) para o detalhamento completo.

Também nesta sessão: nova linha "Audiências" na tabela de Atribuições (texto do Anexo I da
Resolução 013/2023, depois resumido); dois bugfixes de titularidade — `_atrResolverDefensor()`
mostrava titulares livres (nomes fora do dicionário `defensores`) como vaga por engano, e
`getTitularForDPOnDay()` reexibia ex-defensores como titulares atuais quando havia lacuna no
`historico_titulares` sem entrada de vaga explícita (afeta Designações Semanais e Escala
Semanal). Ver `docs/firebase.md`.

**Implementado sessão 30 (04/08/2026):** nova seção "🚨 Plantão" (nav + landing) com a escala de plantão
do Polo do Médio Amazonas, extraída da Portaria nº 764/2026-GSPG/DPE/AM. Lista dinâmica em
`plantao_admin/{id}` (não tabela fixa) — cadastro via formulário de 1 período ou colando texto
CSV em lote (parsing 100% local), **sem IA e sem automação de PDF** por decisão explícita da
usuária, já que os sinos de notificação existentes não têm se mostrado confiáveis. Campo de
descrição/link da portaria editável (`secoes/plantao_info`). Descoberta importante: commitar
`firestore.rules` não publica a regra — precisa `firebase deploy --only firestore:rules`. Ver
`docs/historico-sessoes.md` (sessão 30) para o detalhamento completo.

**Implementado sessão 29 (04/08/2026):** novo tipo "💻 Trabalho em Trânsito" no formulário "Novo Afastamento" da
aba Calendário (`abrirFormAfastamento`/`salvarAfastamentoFirestore`, mesma coleção
`afastamentos_admin/{id}`, campo `tipo: 'trabalho_remoto'` — é um tipo de trabalho remoto, o valor
interno não mudou, só o rótulo exibido). Diferente dos demais tipos, **não é
tratado como ausência**: não exige/mostra substituto (seção "Defensorias Afetadas" fica oculta),
não entra em `afastamentos[ano][mes][dia]` (o que faz "Designações semanais" tratar o titular como
ausente) e é filtrado fora de "Lista de Substituições" e "Resumo de Afastamentos". Só afeta a aba
Calendário: badge transparente com contorno tracejado (nova estrutura `trabalhoRemoto[ano][mes][dia]`
+ mapa `defensorColors`), em vez do badge sólido normal, e aparece no popup de detalhe do dia (onde
pode ser editado/excluído normalmente). Ver detalhamento completo em
`docs/site/estrutura-html.md` (seção "Trabalho em Trânsito"). Ainda não testado em produção com
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
- Remoção futura dos sinos de notificação/automação de PDF (afastamentos/remoções/designações
  cumulativas) — decisão da sessão 30, não têm se mostrado confiáveis na prática

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
