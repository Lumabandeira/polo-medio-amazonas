# Estrutura do Site (index.html)

> Atualizado em 09/08/2026 — reflete sessões 1–32

## Arquivo Único

Existe apenas **um** `index.html` na raiz do projeto. Para publicar no GitHub Pages, usar este mesmo arquivo.

## Autenticação (Firebase Auth)

Ao carregar, um overlay cobre toda a tela até o login. Após autenticar:
- **Admin:** vê badge `ADMIN` + botões ✏️ Editar nas seções editáveis
- **Viewer:** vê o site normalmente, sem botões de edição

## Seções Principais (navegação via landing page)

| Botão na Landing | ID da seção | Função JS |
|-----------------|-------------|----------|
| ⚖️ Atribuições | `#atribuicoes` | `showSection('atribuicoes')` |
| 📋 Escala Semanal | `#escala-semanal` | `showSection('escala-semanal')` → `renderEscalaSemanal()` |
| 📋 Designações | `#designacoes` | `showSection('designacoes')` |
| ⛱️ Férias Equipe | `#equipe` | `showSection('equipe')` |
| 🏘️ Adote | `#adote` | `showSection('adote')` |
| 🧳 Viagens e Eventos | `#viagens-eventos` | `showSection('viagens-eventos')` → `renderViagensEventos()` |
| 🚨 Plantão | `#plantao` | `showSection('plantao')` → `renderPlantao()` |
| 📰 Diário Oficial | `#diario` | `showSection('diario')` |
| 💰 Prestação de Contas | `#prestacao-contas` | `showSection('prestacao-contas')` — **admin-only**. Tem botão tanto na landing (`#btn-prestacao-contas`) quanto no header-nav (`#header-btn-prestacao-contas`, ao lado de Diário Oficial, largura reduzida com texto em 2 linhas pra caber na barra); ambos ficam `display:none` para viewers e são mostrados/ocultados juntos na mesma checagem de admin. |

## Abas dentro da seção Designações (`#designacoes`)

Ordem na barra (sessão 32): Defensorias · Calendários de afastamentos · Lista de Substituições · Resumo de Afastamentos · Designações diárias.

| ID da aba | Nome | Função de render |
|-----------|------|-----------------|
| `defensorias` | 📋 Defensorias | `renderDefensorias()` |
| `calendario` | 📅 Calendários de afastamentos | `renderCalendar()` |
| `lista-substituicoes` | 📋 Lista de Substituições | `renderListaSubstituicoes()` — tem filtro por mês próprio (ver abaixo) |
| `detalhes` | 📊 Resumo de Afastamentos | `renderDetalhesAfastamentos()` |
| `designacoes-periodo` | 📅 Designações diárias | `renderDesignacoes()` — nome do id no código não mudou (só o rótulo visível), continua `designacoes-periodo` |

> ⚠️ A aba "Tabela Completa" foi **removida** em sessão anterior. O Calendário Visual é a aba principal de ausências.

### Filtro por mês em Lista de Substituições (sessão 32)

Antes a lista só criava uma seção por mês para os que tinham registro, tudo em rolagem
contínua. Agora `renderListaSubstituicoes()` sempre gera as 12 seções (`.month-section`,
id `ls-month-{mês}`), com botões de filtro (`#ls-filter-container`, mesma classe visual
`.month-filter-btn` das outras duas grades de mês do site) que mostram só o mês
selecionado — meses sem registro exibem uma mensagem em vez de sumir da navegação.

- `filterListaSubstituicoesByMonth(mes)` busca apenas dentro de `#lista-substituicoes-container`
  e `#ls-filter-container` — não interfere no filtro de Designações Diárias
  (`filterByMonth`, global) nem no da Escala Semanal (`filterEscalaByMonth`, escopado a
  `#escala-content`). Os três reaproveitam as mesmas classes CSS mas nunca se enxergam.
- `filtroListaMes` (variável global, padrão = mês atual) guarda a seleção e **persiste**
  quando o filtro "Filtrar por DP" muda (o dropdown já existente, `filtroListaDP`) —
  trocar de DP não volta pro mês padrão.

## Sinos de Notificação (admin only, barra de abas)

| ID do botão | Coleção Firestore | Painel |
|-------------|-------------------|--------|
| `#btn-sino` | `afastamentos_admin` (automação) | `#notif-overlay` — azul |
| `#btn-sino-remocao` | `remocoes_admin` | `#notif-remocao-overlay` — âmbar |
| `#btn-sino-designacao` | `designacoes_cumulativas_admin` | painel verde |

## Fontes de Dados no JavaScript

| Variável global | Origem | Uso |
|----------------|--------|-----|
| `jsonDesignacoes` | `docs/designacoes-2026.json` | defensores, DPs, historico_titulares |
| `jsonAfastamentos` | `docs/afastamentos-2026.json` | eventos base de afastamentos |
| `afastamentos[ano][mes][dia]` | JSON + Firestore mesclados | badges no calendário |
| `detalhesAfastamentos[ano][mes][dia]` | JSON + Firestore mesclados | modal de detalhes — `_afastamentosAplicarCache()` (sessão 32) limpa as entradas de origem Firestore (`item.firestoreId`) antes de remesclar, pra função ser segura mesmo se rodar mais de uma vez na sessão (antes duplicava linhas no popup do dia) |
| `afastamentosFirestoreMap` | `afastamentos_admin` | registros criados via admin |
| `trabalhoRemoto[ano][mes][dia]` | `afastamentos_admin` (`tipo:'trabalho_remoto'`) | badge transparente no calendário — não é ausência |
| `equipeAfastamentos[ano][mes][dia]` | `afastamentos_equipe` | calendário Férias Equipe |
| `defensorNames` | construído de `jsonDesignacoes.defensores` | labels de badge |
| `defensorColors` | construído de `jsonDesignacoes.defensores` em `buildDefensorNames()` | cor hex por defensor, usada no contorno do badge de trabalho remoto |

## Nomes/Chaves dos Defensores Ativos

| Nome completo | Chave JSON | Badge cor |
|---------------|-----------|----------|
| Ênio Jorge Lima Barbalho Junior | `enio` | paleta dinâmica |
| Thays Lidianne Campos de Azevedo Pereira | `thays` | paleta dinâmica |
| Ícaro Oliveira Avelar Costa | `icaro` | `#3b82f6` (azul) |
| Eliaquim Antunes de Souza Santos | `eliaquim` | `#f97316` (laranja) |
| Emilly Bianca Ferreira dos Santos | `emilly` | `#f43f5e` (vermelho-rosa) |
| Miguel Eduardo de Azevedo Martins Filho | `miguel` | `#10b981` (verde-esmeralda) |

## Seções Editáveis pelo Admin (Firestore)

| Seção | doc Firestore | Mecanismo |
|-------|--------------|----------|
| Regra de Alternância | `secoes/regra_alternancia` | contentEditable + RTE |
| Férias/Folgas/Licenças dos Membros | `secoes/ferias_folgas` | contentEditable + RTE |
| Atribuições — células da tabela | `secoes/atribuicoes_celulas` | contentEditable por TD + RTE |
| Atribuições — link da resolução | `secoes/atribuicoes_resolucao` | form inline |
| Adote — cabeçalho | `secoes/adote_info` | contentEditable |
| Adote — células da tabela | `secoes/adote_celulas` | contentEditable por TD + RTE |
| Adote — bloco Expandir | `secoes/adote_expandir` | contentEditable + RTE |
| Titulares por DP | `titulares_admin/{dpKey}` | modal de edição |
| Status Ativo/Ex-membro do Defensor | `defensores_admin/{defKey}` | dropdown 🟢 Membro / ⚪ Ex-membro no card, em `renderDefensorias()` |
| Afastamentos | `afastamentos_admin/{id}` | formulário modal completo |
| Férias Equipe | `afastamentos_equipe/{id}` | formulário modal |
| Plantão (período/defensor/assessoria) | `plantao_admin/{id}` | formulário modal (1 período) **ou** colar CSV em lote — ver seção própria abaixo |

## Trabalho em Trânsito (tipo especial dentro de Afastamentos)

Exibido na interface como "💻 Trabalho em Trânsito" (é um tipo de trabalho remoto — o valor
interno do campo `tipo` continua `trabalho_remoto`, só o rótulo exibido mudou). Criado no mesmo
modal "Novo Afastamento" da aba Calendário (`abrirFormAfastamento`), selecionando
`tipo: 'trabalho_remoto'` no `<select id="form-af-tipo">`. Mesma coleção Firestore
(`afastamentos_admin/{id}`), mas **tratado à parte** em `mergeAfastamentoFirestoreRecord()` — ver
`_mergeTrabalhoRemotoRecord()` em `index.html`:

- **Não** entra em `afastamentos[ano][mes][dia]` (isso é o que faz "Designações semanais" tratar o
  titular como ausente) — vai para `trabalhoRemoto[ano][mes][dia]` à parte.
- A seção "Defensorias Afetadas" do formulário fica oculta (`popularDPsAfetadas()` retorna cedo
  quando o tipo é `trabalho_remoto`) — não há substituto, o defensor responde normalmente por suas DPs.
- Aparece no calendário como badge **transparente com contorno tracejado** (cor do próprio defensor,
  via `defensorColors`), em vez do badge sólido normal — diferencia visualmente de uma ausência real.
- O popup de detalhe do dia (clique na célula, dentro do próprio Calendário) mostra o registro
  normalmente (`detalhesAfastamentos`), inclusive editar/excluir — mas os registros com
  `tipo === 'trabalho_remoto'` são **filtrados fora** de "Lista de Substituições"
  (`renderListaSubstituicoes`) e "Resumo de Afastamentos" (`renderDetalhesAfastamentos`).
- Resultado: trabalho em trânsito só aparece no Calendário — não altera Designações semanais, Lista de
  Substituições nem Resumo de Afastamentos.

## Plantão (`#plantao`)

Lista dinâmica (não mais tabela de tamanho fixo) na coleção `plantao_admin/{id}`
— schema: `data_inicio`, `data_fim` (YYYY-MM-DD), `defensor`, `assessoria`
(texto livre — plantonistas nem sempre são os 6 titulares do polo), `criado_por`,
`criado_em`. Renderizada por `renderPlantao()`, ordenada por `data_inicio`.

**Agrupamento por lote (`lote_nome`):** cada período tem um campo opcional
`lote_nome` (texto livre, ex. "3º Trimestre 2026") identificando a leva de
períodos publicada de uma vez — a administração decide o formato a cada vez
(trimestre, semestre, etc.), então não há enum fixo. `renderPlantao()` agrupa
`plantaoRegistros` por `lote_nome` via `_plantaoAgruparPorLote()`: um bloco
(cabeçalho `<h3>` + tabela própria) por lote, ordenados pelo maior `data_inicio`
de cada grupo, **decrescente** (lote mais recente no topo); períodos sem
`lote_nome` caem no grupo "Sem lote definido", sempre por último independente de
data. Cabeçalho mostra a contagem de períodos e um badge "🔵 atual"
(`_plantaoLoteContemHoje()`) quando a data de hoje cai dentro do intervalo do
grupo. Preenchido pelo formulário de 1 período (pré-preenchido com o lote do
período mais recente já cadastrado, pra não redigitar o mesmo nome dentro da
mesma leva) e pelo "Importar CSV" (campo único "Nome do lote", aplicado a todos
os períodos do lote colado — mesmo padrão do campo de portaria, ver abaixo).

**Renomear lote inteiro (admin):** botão "✏️ renomear" no cabeçalho de cada
grupo — mesmo padrão de edição inline de `_plantaoEditarInfo()`/`_plantaoSalvarInfo()`.
`_plantaoRenomearLoteIniciar(idx)` troca o `<h3>` por um `<input>` + Salvar/Cancelar;
`_plantaoRenomearLoteSalvar(idx)` roda `Promise.all` atualizando `lote_nome` em
todos os documentos daquele grupo (`_plantaoGruposAtuais[idx].registros`, cache do
último `renderPlantao()` — evita embutir o nome do lote, texto livre com aspas/
caracteres arbitrários, dentro de um atributo `onclick`).

**Proteção contra seed duplicado (bug real de 21/08/2026):** `_plantaoImportarSeed()`
antigamente só checava `plantaoRegistros.length` (estado em memória) antes de gravar
os 13 períodos do seed — se o admin clicasse "Importar dados iniciais" antes do
1º `loadPlantaoFirestore()` terminar (aba aberta rápido demais), o array local
ainda estava `[]` mesmo com períodos já existindo no Firestore, e o seed inteiro
era regravado por cima, duplicando registros. Corrigido em duas camadas:
1. `renderPlantao()` só oferece o botão de importar quando `plantaoCarregouUmaVez`
   é `true` (setado ao final da 1ª leitura real do Firestore em
   `loadPlantaoFirestore()`) — antes disso mostra "⏳ Carregando períodos..." em
   vez do estado vazio.
2. `_plantaoImportarSeed()` revalida direto no Firestore (`.limit(1).get()`)
   imediatamente antes de gravar, além de uma trava `_plantaoImportandoSeed`
   contra duplo-clique — defesa em profundidade, independe da UI ter mostrado o
   botão certo ou não.

**Link de portaria por período:** cada linha da tabela tem uma coluna "Portaria"
(`_plantaoLinkPortariaHtml()`), resolvida nesta ordem de prioridade:
1. `alteracao_url`/`alteracao_numero` — preenchidos só quando esse período específico
   foi alterado por uma portaria pontual publicada depois da portaria geral (ex.:
   substituição de um plantonista numa semana). Renderiza como badge laranja "🔄".
   É o único caso em que a linha mostra sua própria portaria em destaque — não
   mostra a original ao lado (decisão explícita: só a que vale hoje).
2. `portaria_url`/`portaria_numero` — portaria própria do período (comum: é o que o
   formulário de 1 período e o "Importar CSV" gravam por padrão — ver abaixo).
3. Fallback: link geral da seção (`plantaoInfoAtual`), cache síncrono de
   `secoes/plantao_info`, atualizado por `_plantaoCarregarInfo()` e replicado nas
   células via `_plantaoAtualizarColunaPortaria()` (evita recursão entre
   `renderPlantao()` ↔ `_plantaoCarregarInfo()`, já que ambos se chamam).

**Rótulo do link — mesmo padrão das tabelas de Afastamentos** (ex.
`index.html:4862`, coluna "Diário Oficial"): `_rotuloEdicaoDiario(url)` (função
genérica, sem prefixo de seção — também usada por Viagens e Eventos, ver abaixo)
extrai o número da edição do link (`.../Edicao_NNNN...`) e mostra "Edição NNNN"; sem
padrão reconhecível, cai em "Abrir PDF". O campo `..._numero` do formulário
(opcional) só serve como *override* manual do rótulo — útil quando o link não segue
esse padrão de nome de arquivo; a maioria dos casos não precisa preenchê-lo.
`alteracao_obs` (texto livre) vira `title` (tooltip) do badge de alteração.

**Nota de segurança:** todos os campos de texto livre desses 5 campos passam por
`esc()` — mas `esc()` sozinho só escapa `&`/`<`/`>` (seguro em texto de nó HTML,
**não** dentro de um atributo). Todo valor que entra num atributo (`href`, `title`)
usa `_escAttr(s)` (= `esc(s).replace(/"/g, '&quot;')`, novo helper genérico — mesmo
padrão de `_viagensEscAttr()`, já existente em Viagens e Eventos). Um bug real foi
encontrado e corrigido nesta sessão: os 3 `href="${esc(url)}"` de
`_plantaoLinkPortariaHtml()` usavam só `esc()`, permitindo quebrar o atributo com uma
URL contendo aspas + `onmouseover=...` (testado e confirmado explorável antes da
correção, sem disparar só por sorte de nenhum teste anterior ter colocado aspas no
próprio `portaria_url`/`alteracao_url` — os testes anteriores só cobriam
`alteracao_obs`). Trocados para `_escAttr(url)`.

`lote_nome`/`portaria_numero`/`portaria_url` são editáveis também pelo "Importar CSV"
(campos únicos "Nome do lote" e "Link do Diário Oficial" no topo do modal, aplicados a
todos os períodos do lote colado — ver abaixo). Já `alteracao_*` só é editável pelo
formulário de 1 período — é exceção pontual, não vale complicar o parser de CSV para
isso. O seed inicial (`PLANTAO_SEED_2026`) grava `data_inicio`/`data_fim`/`defensor`/
`assessoria`/`lote_nome` (todos os 13 itens com `lote_nome: '3º Trimestre 2026'`, via
`.map()` sobre a constante `PLANTAO_SEED_2026_LOTE`).

**Decisão da sessão 26:** sem IA e sem automação de PDF. As automações
existentes (sinos de notificação de afastamentos/remoções/designações
cumulativas) não têm se mostrado confiáveis na prática, então o cadastro de
Plantão é 100% manual, com duas vias:

- **Um período por vez** — botão "➕ Novo período" → modal (`abrirFormPlantao`,
  `salvarPlantaoFirestore`) idêntico em espírito ao modal de Férias Equipe.
- **Vários de uma vez** — botão "📋 Importar CSV" → campos opcionais "Nome do lote"
  (ex. "4º Trimestre 2026" — agrupa esses períodos na tabela) e "Link do Diário
  Oficial" (aplica a todos os períodos deste lote — cenário comum: uma edição
  publica várias semanas de uma vez, ex. Edição 2696/2026 publicou as 13 semanas da
  Portaria 764/2026) + cola texto (uma linha por período,
  `data_inicio;data_fim;defensor;assessoria`, aceita `;`, Tab ou `,` como separador)
  → `_plantaoParseCSV()` faz o parsing 100% local (sem rede, sem IA) →
  pré-visualização com linhas ok/erro → confirma e grava em lote, com o mesmo
  `lote_nome`/`portaria_url` em todos os documentos criados
  (`_plantaoConfirmarImportacaoCsv()`). Dá pra corrigir período a período depois pelo
  formulário, se algum tiver sido publicado numa edição diferente do resto do lote.
  Decisão da sessão 35: sem isso,
  toda importação em lote ficava sem portaria própria, dependendo só do link geral
  da seção — que pode estar desatualizado/incorreto para escalas futuras.
- **Migração inicial**: `PLANTAO_SEED_2026` guarda os 13 períodos extraídos da
  Portaria nº 764/2026-GSPG/DPE/AM; um botão "⬇️ Importar dados iniciais"
  aparece só enquanto `plantao_admin` está vazia e grava esse seed uma única vez.

**Descrição/link da portaria (editável):** logo abaixo do título, campo de texto
+ link opcional, mesmo padrão do link de resolução em Atribuições
(`_atrEditarResolucao`/`_atrSalvarResolucao`) — aqui `_plantaoEditarInfo()` /
`_plantaoSalvarInfo()` / `_plantaoCarregarInfo()`, gravando em `secoes/plantao_info`
(`nome`, `url`). Se o documento não existir ou os campos estiverem vazios, cai no
texto padrão `PLANTAO_INFO_PADRAO` (constante em `index.html`).

Cache local: `pma-plantao-fs` (docs brutos de `plantao_admin`, mesmo padrão de
`pma-equipe-fs`).

## Escala Semanal (`#escala-semanal`)

Tabela **somente leitura** com Atendimento/Audiência de Família, Cível e Criminal,
Plantão, e as duas UDIS (São Sebastião do Uatumã e Silves) — uma linha por semana,
com filtro por mês (mesmo padrão visual de Designações Semanais, mas com filtro
isolado: `filterEscalaByMonth()` só busca dentro de `#escala-content`, não afeta o
filtro de `#designacoes-content`). Não existe nenhum Firestore próprio nem edição —
tudo é calculado em `renderEscalaSemanal()` a partir de outras fontes já existentes:

- **Semanas**: mesma grade segunda-domingo do ano (com o ajuste do recesso forense,
  1ª semana começa 07/01) usada em `renderDesignacoes()`.
- **Quem faz Atendimento vs. Audiência**: reaproveita `DPS_CONFIG`/`getWeekGroup()` —
  a mesma lógica que já destaca amarelo/azul em Designações Semanais. Dentro de cada
  par (1ª/2ª Família, 3ª/4ª Cível, 5ª/6ª Criminal, 11ª/12ª Silves), a DP do grupo
  ativo na semana = Atendimento; a outra = Audiência. **Cível e Silves mostram só uma
  coluna** (o par "acumula" atendimento+audiência na mesma pessoa, conforme o Anexo I
  da Resolução 013/2023 — ver linha "Audiências" na tabela de Atribuições).
- **Quem é a pessoa em cada dia**: `getResponsibleForDPOnDay()` (mesma função de
  Designações Semanais — já considera titular vigente, afastamento e substituto).
  `segmentarResponsavelSemana()` percorre os 5 dias úteis e agrupa em "segmentos":
  se o responsável muda no meio da semana, a célula mostra as duas partes
  (`"até DD/MM"` / `"a partir de DD/MM"`) separadas por uma linha pontilhada.
- **Plantão**: `_escalaBuscarPlantao()` casa a segunda-feira da semana com
  `data_inicio` em `plantaoRegistros` (mesma coleção `plantao_admin` da seção
  Plantão) — fica em branco nas semanas sem período cadastrado.

Estética própria (`escala-*` no CSS): cabeçalho em gradiente vermelho (diferente do
azul padrão do site), grade visível em todas as células, e fundo levemente mais
claro nas colunas de Audiência para diferenciar de Atendimento.

## Prestação de Contas (`#prestacao-contas`, admin-only)

Seção inteira restrita a admin: o botão da landing (`#btn-prestacao-contas`) nasce com `display:none`
e só é revelado em `_aplicarModoEdicao()`. `showSection('prestacao-contas')` também expulsa
qualquer usuário não-admin de volta para `atribuicoes` como segunda camada de proteção.

- **Lista** (`#pc-lista-view`): cards agrupados por tomador, um card por "pronto pagamento" (adiantamento).
  Cada tomador pode ter no máximo **2 prontos pagamentos com `status: "aberto"` simultâneos**,
  em categorias diferentes entre si (`consumo` | `pessoa_juridica` | `pessoa_fisica`) — regra
  aplicada em `_validarCategoriaDisponivel()` antes de salvar ou reabrir.
- **Modelos de Documentos**: card abaixo da lista de Prontos Pagamentos, em `#pc-lista-view`, com
  uma biblioteca de modelos de referência (título "📚 Modelos de Documentos" — sem sufixo). Dois
  modelos gerais no topo, fora de qualquer categoria/serviço porque não variam por tipo de
  serviço — "📝 Modelo de Memorando" (só `.docx`) e "📑 Modelo de Pesquisa de Mercado" (`.docx`
  *ou* `.xlsx`) — e, abaixo, uma lista por categoria (`PC_CATEGORIA_LABELS`) e serviço livre (ex:
  PJ → lavagem de carro; Consumo → água mineral; PF → roçagem), cada serviço com 2 slots
  independentes (Modelo de Justificativa, Modelo de Atesto, só `.docx`). A categoria **Pessoa
  Física** também tem um "🧾 Modelo de Recibo" próprio no topo do seu bloco, antes da lista de
  serviços — só nessa categoria (renderização condicional em `_renderModelosPrestacaoContas()`,
  `categoria === 'pessoa_fisica'`; o campo `recibo` no Firestore continua com as 3 chaves de
  categoria, mas só `pessoa_fisica` é exibido/editável pela UI).
  Doc único `secoes/prestacao_contas_modelos`: 3 arrays (uma por categoria, cada item
  `{servico, justificativa_url, justificativa_nome, atesto_url, atesto_nome}`) + 4 campos soltos
  para os modelos gerais (`memorando_url`/`memorando_nome`/`pesquisa_mercado_url`/`pesquisa_mercado_nome`)
  + `recibo` (objeto `{pessoa_juridica: {url, nome}, consumo: {...}, pessoa_fisica: {...}}`) —
  mesmo padrão de config de seção única de `secoes/plantao_info`. Carregado em
  `_pcCarregarModelos()` (chamado dentro de `renderPrestacoesContas()`), renderizado em
  `_renderModelosPrestacaoContas()`. Por serviço: `pcAdicionarServicoModelo(categoria)` adiciona
  (prompt pro nome, mesmo padrão de `adicionarOutroDocumento()`), `pcRemoverServicoModelo(categoria, idx)`
  remove com confirmação (não apaga arquivo do Storage), `pcUploadModeloArquivo(categoria, idx, tipo, file)`
  sobe o arquivo (`tipo` é `'justificativa'` ou `'atesto'`) via `_uploadParaStorage()`, path
  `prestacoes-contas/_modelos/{categoria}/{idx}-{tipo}-{timestamp}.ext`. Geral:
  `pcUploadModeloGeral(campo, file)` (`campo` é `'memorando'` ou `'pesquisa_mercado'`), path
  `prestacoes-contas/_modelos/_gerais/{campo}-{timestamp}.ext`. Por categoria:
  `pcUploadModeloRecibo(categoria, file)` (`_pcModeloReciboSlotHtml(categoria)`), path
  `prestacoes-contas/_modelos/{categoria}/recibo-{timestamp}.ext`. Todos caem dentro do path
  admin-only já existente em `storage.rules`, sem precisar de redeploy. Não interfere nos slots
  de Anexos por despesa — é só uma biblioteca de referência/download.
- **Detalhe** (`#pc-detalhe-view`): réplica do "Mapa Demonstrativo de Despesa" (planilha em papel
  usada pela Defensoria) — tabela de despesas com totais calculados automaticamente (valor das
  despesas, saldo remanescente).
- **Documentos do Processo removido (sessão 40):** bloco "📁 Documentos do Processo" (Memorando de
  encaminhamento, Termo de Devolução, Comprovante de Devolução), que ficava logo abaixo do Mapa
  Demonstrativo no Detalhe, foi removido a pedido da usuária ("nunca vou usar"). Removidos:
  `_renderDocumentosProcesso()`, `uploadDocumentoProcesso()` e o container estático
  `#pc-detalhe-processo` — sem esses 3, nada mais lê/exibe os campos `memorando_url`/
  `termo_devolucao_url`/`comprovante_devolucao_url` do documento `prestacoes_contas/{id}`. Só a UI
  foi removida — os 3 campos continuam sendo zerados (`null`) ao criar uma prestação nova em
  `salvarPrestacao()` ([index.html:11794](polo-medio-amazonas/index.html:11794), inofensivo, só
  não é mais lido em nenhum lugar) e registros antigos que já tinham algum desses campos
  preenchido não foram limpos no Firestore, só deixaram de ser exibidos/editáveis (mesmo padrão já
  usado quando um slot de outra seção foi só ocultado, não migrado — ver sessão 39, remoção do
  slot de Recibo por categoria). Não confundir com `_pcModelos.memorando_url`/
  `pesquisa_mercado_url` — campos homônimos, mas de outra seção (biblioteca "Modelos de
  Documentos", modelo geral de referência), que não foram tocados.
- **Anexos por despesa**: modal com 5 slots fixos, nesta ordem de exibição — Justificativa,
  Pesquisa de mercado (rótulo exibido; campo/nomes internos continuam `comprovacao_mercado`),
  Recibo/NF, Atesto, Fotos — + lista livre de "Outros documentos" (`_renderCorpoModalAnexos()`).
  A ordem dos 4 primeiros é só de exibição (template fixo, sem campo de ordem) — os campos
  continuam `recibo_url`/`comprovacao_mercado`/`justificativa_url`/`atesto_url`.
  Todos os slots exceto Fotos têm um texto explicativo menor abaixo do título — Justificativa,
  Recibo/NF e Atesto via parâmetro opcional `descricao` de
  `_slotAnexoSimples(campo, label, url, descricao)` (`.pc-anexo-slot-desc`); Pesquisa de mercado
  escrito manualmente (não usa `_slotAnexoSimples` porque tem upload próprio,
  `_uploadComprovacaoMercado()`, gravando `comprovacao_mercado: { url }` em vez de `{campo: url}`).
  Não existe mais seletor de "tipo" (pesquisa de mercado *vs* justificativa de ausência) nesse
  slot — removido a pedido da usuária; o texto pequeno já cobre a alternativa ("ou, na
  impossibilidade, justificativa da ausência de pesquisa."). Upload vai para Firebase Storage em
  `prestacoes-contas/{prestacaoId}/...`; a URL de download fica salva no array `despesas[]` do
  documento Firestore.
- **Visualização inline dos anexos (painel dividido):** o modal de Anexos por despesa
  (`#modal-anexos-overlay`, alargado para `max-width: 1200px` só nesse modal) mostra a lista de
  anexos à esquerda (`.pc-anexos-lista`) e um painel de visualização fixo à direita
  (`.pc-anexos-preview`, `#pc-anexo-preview-painel`) — em telas ≤720px empilha em coluna única.
  Cada slot (Justificativa/Pesquisa de mercado/Recibo/Atesto), cada foto da grade e cada "outro
  documento" tem um botão/clique "👁️ Visualizar" que chama `_visualizarAnexoCampo(campo)` — o
  `campo` é só uma **chave** (`'justificativa_url'`, `'comprovacao_mercado'`, `'recibo_url'`,
  `'atesto_url'`, `'foto:<i>'`, `'outro:<i>'`), guardada em `_anexoPreviewCampo`, nunca a URL/nome
  em si — o painel resolve o valor atual em `_resolverPreviewAnexo(d, campo)` toda vez que
  renderiza, então continua correto depois de um upload/substituição re-renderizar o modal (evita
  reproduzir o tipo de bug de escaping em atributo já visto no projeto, ver sessão 35 no
  `CLAUDE.md`). `_painelPreviewHtml(d)` decide PDF (`<iframe>`) vs imagem (`<img>`) pela extensão
  no fim da URL (todo upload já passa por `_extensaoArquivo()`, então a URL sempre tem extensão).
  Cabeçalho do painel tem "⬇️ Baixar" (`_baixarAnexo()` — `fetch` + `blob` + `<a download>`
  temporário, força download de verdade mesmo sendo URL de outra origem do Storage; se o `fetch`
  falhar cai para `window.open` + toast) e um link pequeno "Abrir em nova guia" como *fallback*.
  `_anexoPreviewCampo` reseta pra `null` ao abrir/fechar o modal e ao remover uma foto/outro
  documento (índices podem deslocar) — não reseta em upload/substituição de slot simples, pra
  manter o mesmo anexo selecionado e já mostrar o arquivo novo. Escopo desta sessão: só o modal de
  Anexos por despesa — "Documentos do Processo" e a biblioteca "Modelos de Documentos" continuam
  com o link "Abrir" (nova guia) de antes. Proporção das colunas ajustada depois a pedido da
  usuária: `.pc-anexos-lista { flex: 3 ... }` / `.pc-anexos-preview { flex: 5 ... }` (lista a
  ~37,5% da largura, preview a ~62,5% — a lista ficou em 75% da largura original, que era 50/50).
- **Baixar os 4 anexos mesclados em 1 PDF:** botão "🧷 Baixar anexos em 1 PDF" no topo de
  `.pc-anexos-lista`, `_baixarAnexosMerge()` (ao lado de `_baixarAnexo()`). Ordem fixa e sempre a
  mesma, `_ANEXOS_ORDEM_MERGE = ['justificativa_url', 'comprovacao_mercado', 'recibo_url',
  'atesto_url']` — resolve cada chave com `_resolverPreviewAnexo(d, campo)` (mesma função do
  painel de preview) e pula silenciosamente qualquer uma que volte `null` (sem lógica condicional
  por slot: "sem Pesquisa de mercado" e "sem Atesto" tratados igual). Usa **pdf-lib**
  (`https://cdn.jsdelivr.net/npm/pdf-lib@1.17.1/dist/pdf-lib.min.js`, carregado junto dos scripts
  de jsPDF) — diferente do jsPDF já usado em `baixarMapaPDF()` (que só gera PDF novo a partir de
  texto/tabela), o pdf-lib consegue copiar as páginas de um PDF já existente
  (`PDFDocument.load()` + `copyPages()`) mantendo o conteúdo original, e embutir imagem como
  página nova (`embedPng`/`embedJpg` pela extensão da URL, mesma checagem já usada no preview).
  Cada anexo é baixado com `fetch()` isoladamente; se um falhar (rede, arquivo corrompido), o erro
  é capturado por item — o merge continua com os demais e avisa em toast quais falharam, só aborta
  de vez se **nenhum** dos 4 entrar no PDF final. Nome do arquivo:
  `Anexos-{tipo}-{numero}-{fornecedor}.pdf` (mesmo sanitizador de `_baixarAnexo()`). Testado no
  navegador com PDFs/imagem reais gerados na hora (jsPDF + canvas): merge de 3 dos 4 anexos (sem
  Pesquisa de mercado) gerando PDF de 4 páginas na ordem certa, caso sem nenhum anexo (toast, sem
  gerar arquivo) e caso de 1 anexo com URL inválida (PDF final sai só com os outros 2, toast avisa
  qual anexo faltou).
- **Arrastar e soltar arquivo (drag & drop):** todos os pontos de upload do modal de Anexos
  (Justificativa/Pesquisa de mercado/Recibo/Atesto, Fotos e Outros documentos) aceitam soltar o
  arquivo direto, além do botão de sempre. 3 funções genéricas perto das funções de upload
  (`_anexoDragOver`/`_anexoDragLeave`/`_anexoDrop(event, tipo, ref)`) — `_anexoDrop` só decide qual
  função de upload **já existente** chamar de acordo com `tipo` (`'slot'`/`'mercado'`/`'fotos'`/
  `'outro'`), nenhuma delas foi alterada. Os 4 slots simples e o de Pesquisa de mercado viraram
  dropzone no próprio `<div class="pc-anexo-slot">`; Fotos e Outros documentos (que eram só um
  botão solto) ganharam um wrapper `.pc-anexo-dropzone` (borda tracejada) em volta do botão. Texto
  pequeno "📥 ou arraste o arquivo aqui" em cada um pra avisar que dá pra soltar ali — nada nisso é
  descobrível só pelo botão. Se mais de 1 arquivo for solto num slot de arquivo único, só o
  primeiro é usado; o aviso ("Apenas o 1º arquivo foi usado...") só é disparado **depois** que a
  promise do upload resolve (`promessa.then(...)`), porque um `mostrarToast()` chamado antes, no
  mesmo trecho síncrono, seria imediatamente sobrescrito pelo "⏳ Enviando arquivo..." da própria
  função de upload (roda antes do 1º `await` dela, no mesmo tick). Rede de segurança:
  `ondragover`/`ondrop` com `event.preventDefault()` no `.form-af-content` do próprio
  `#modal-anexos-overlay` (markup estático do modal), pra um drop fora de qualquer dropzone
  específica não fazer o navegador abrir o arquivo numa aba nova por cima do modal — as dropzones
  específicas chamam `stopPropagation()`, então continuam funcionando normalmente por cima dessa
  rede. Testado no navegador disparando eventos `drop`/`dragover`/`dragleave` sintéticos
  (`DataTransfer`/`File` construídos em JS, já que automação de navegador não simula um drag real
  do SO): upload por drop em slot vazio, 2 arquivos soltos num slot único (só o 1º é usado, aviso
  aparece na ordem certa), 2 fotos soltas de uma vez na dropzone de Fotos, destaque visual
  aparecendo/sumindo em `dragover`/`dragleave`, e um `drop` fora de qualquer dropzone confirmando
  `event.defaultPrevented === true`.
- **Valor Concedido (campo único)**: o formulário tinha "Valor Recebido" e "Valor Concedido"
  redundantes — removido "Valor Recebido", único campo `valor_concedido` (obrigatório) usado em
  cards, Detalhe, tabela de despesas e PDF, e no cálculo de saldo. Registros antigos gravados só
  com `valor_recebido` continuam exibindo o valor certo via `_pcValorConcedido(p)` (fallback
  `valor_concedido ?? valor_recebido`), inclusive ao abrir para edição — `valor_recebido` nunca é
  regravado depois disso.
- **Unidade Gestora Concedente**: bloco de 4 campos no formulário (Órgão/CNPJ, Banco, Agência,
  Conta), pré-preenchidos com os dados fixos da DPE/AM (`PC_UG_CONCEDENTE_PADRAO`) mas editáveis —
  os 4 continuam gravados em `prestacoes_contas/{id}`. No Detalhe (`_renderDetalhePrestacao()`),
  só o "Órgão / CNPJ" aparece nas informações gerais; Banco/Agência/Conta ficam só no cadastro
  (usuária considerou redundante mostrar os dados bancários na tela de exibição). Nenhum dos 4
  entra no PDF exportado.
- **Reordenar despesas**: cada linha da tabela ganhou botões ⬆️/⬇️ (`moverDespesa(prestacaoId, idx, direcao)`,
  perto de `excluirDespesa()`) que trocam de posição duas despesas dentro do array `despesas[]` e
  regravam o array inteiro no Firestore — mesmo padrão de `salvarDespesa()`/`excluirDespesa()`. Sem
  campo de ordem separado: a posição no array já é a ordem exibida (e a usada no PDF exportado).
  ⬆️ desabilitado na primeira linha, ⬇️ desabilitado na última. Sem `confirm()` (ação reversível de
  baixo risco, diferente da exclusão). Objetivo: deixar de exigir excluir e recadastrar uma despesa
  só para mudar a ordem (os anexos ficam presos ao índice da despesa, então iam junto na troca de
  posição de qualquer forma).
- **Prazo de aplicação vencido (destaque em vermelho)**: `_pcAplicacaoVencida(p)` retorna `true`
  quando `p.data_fim_aplicacao` (string `YYYY-MM-DD`) é anterior a hoje **e** `p.status !== 'concluido'`
  (num pronto pagamento já concluído o vencimento do prazo é esperado, não é alerta). Quando `true`,
  a linha "Aplicação" ganha a classe `.pc-aplic-vencida` (label + valor em `#ef4444`) mais o sufixo
  `<span class="pc-aplic-tag">⚠ prazo encerrado</span>`, tanto no card da Lista
  (`_renderListaPrestacoesCards()`) quanto no bloco de informações do Detalhe
  (`_renderDetalhePrestacao()`, `<div class="pc-aplic-vencida">` dentro do `.pc-info-grid`). CSS
  junto das regras `.pc-card-linha` (perto de `index.html:1141`). Só afeta a exibição — não entra
  no PDF nem no Firestore. A comparação usa `new Date().toISOString().split('T')[0]` (UTC), mesmo
  padrão dos outros "hoje" do arquivo.
- Ver `docs/firebase.md` para o schema completo de `prestacoes_contas/{id}` e as regras de
  segurança (mais restritas que o padrão do site: leitura **e** escrita admin-only, por causa de
  CPF/dados bancários nos comprovantes de devolução).
- **Exportar em PDF**: botão "📄 Baixar Mapa (PDF)" no cabeçalho do detalhe, função `baixarMapaPDF()`.
  Usa jsPDF + jsPDF-AutoTable (CDN, `jspdf.umd.min.js` + `jspdf.plugin.autotable.min.js`) para gerar
  uma página A4 paisagem replicando o layout em papel: bloco de cabeçalho, cabeçalho de tabela de 2
  linhas desenhado manualmente (em vez de `colSpan`/`rowSpan` no `head` do AutoTable — ver adiante),
  tabela de despesas e rodapé de totais. Validado com PDF real baixado e aberto no Chrome
  (fornecedor com nome longo quebrando em 3 linhas, valores corretos, sem sobreposição).
  Bloco de cabeçalho (`infoRows`) segue o layout da planilha da administração (sessão 42): Tomador,
  Data do Recebimento, Data Inicial de Aplicação (= recebimento), Data Final para Aplicação, Prazo
  de Prest. de Contas e Valor Concedido, com uma coluna "PRAZO" no meio mostrando os dias de
  aplicação e de prestação de contas (`_pcPrazos(p)`). Tabela com coluna "DESCONTO (SE HOUVER)"
  entre Valor Unit. e Valor Total; título "MAPA DEMONSTRATIVO DE DESPESAS".
- **Cores do PDF no modelo da planilha (sessão 43)**: a pedido da usuária, o bloco de cabeçalho
  (`infoRows`) e a tabela de despesas passaram a usar as cores aproximadas da planilha
  `MAPA_DEMONSTRATIVO` da administração, em vez de preto/branco/cinza neutro. Cada linha de
  `infoRows` ganhou um objeto `{ label, prazo, value, bg, valueColor?, valueBold?, prazoBg?,
  prazoColor? }` (antes era um array posicional `[label, prazo, value]`) — `bg` é pintado com
  `doc.rect(...,'F')` atrás do texto da linha inteira antes de escrever (`infoRowH = 5.3`); `prazoBg`
  pinta só a coluna estreita do número de dias (65/10 no exemplo), sobre o `bg` da linha. Paleta
  (constantes `COR_*` logo antes de `infoRows`): amarelo (Tomador), verde + texto branco em negrito
  (Data do Recebimento), pêssego (as 3 linhas de datas/prazo), lilás + texto azul (os 2 números de
  PRAZO), azul claro (Valor Concedido do cadastro **e** Saldo Remanescente do rodapé), verde claro
  (Valor Concedido do rodapé). Testado gerando um PDF real com dados simulados (sem Firestore) e
  abrindo no visualizador nativo do Chrome via `doc.output('bloburl')` num `<iframe>` — não dá para
  inspecionar cor de PDF pela pré-visualização do jsPDF sem abrir o arquivo de verdade (ver nota da
  sessão 42 duas entradas acima).
- **Zebrado da tabela de despesas, cinza mais claro que o cabeçalho (sessão 43)**: linhas
  brancas/cinzas alternadas, como a planilha — mas **não** via `alternateRowStyles` do AutoTable:
  na versão 3.8.4 (a usada aqui), essa opção pinta as linhas de índice **par** (0, 2, 4…), deixando
  a 1ª despesa cinza em vez de branca (bug real, pego só depois de a usuária comparar com a
  planilha de referência — lá a 1ª despesa é branca). Zebrado feito manualmente no `didParseCell`:
  `data.section === 'body' && data.row.index < despesas.length && data.row.index % 2 === 1` pinta
  só as linhas de índice ímpar com `COR_CINZA_LINHA`; o `data.row.index < despesas.length` exclui
  as 3 linhas de totais no fim do `body` (que têm cor própria via `styles`, sobrepondo qualquer
  zebrado). `COR_CINZA_LINHA` = `[242,242,242]` — mais claro que `COR_CINZA_HEADER` (`[217,217,217]`,
  usado no cabeçalho das colunas) a pedido da usuária.
- **Cabeçalho da tabela mesclado e cinza, sem espaço em branco (sessão 43)**: antes, a barra cinza
  "COMPROVANTE DE DESPESA" era desenhada só sobre as 3 primeiras colunas (Tipo/Nº/Data), deixando um
  espaço em branco à direita na mesma linha, e a linha de baixo (`head` do AutoTable) repetia
  **todos** os 9 títulos de coluna — diferente da planilha de referência, onde Fornecedor…Valor
  Total ficam mesclados verticalmente numa única célula cinza (sem repetir embaixo, sem linha
  divisória, texto centralizado no meio das 2 linhas). Reescrito como um cabeçalho de 2 linhas
  manual: (1) linha de cima desenha "COMPROVANTE DE DESPESA" (cinza, só sobre Tipo/Nº/Data, borda
  nos 4 lados) **e** o preenchimento cinza dos outros 6 títulos, mas só com borda em cima/esquerda/
  direita (`doc.line()`, sem a de baixo — evita linha dupla com a célula de baixo); (2) linha de
  baixo (`head` do AutoTable) só tem texto em Tipo/Nº/Data — as outras 6 células ficam com string
  vazia, `headStyles.fillColor` cinza por padrão e, via `didParseCell`, sem borda no topo
  (`lineWidth: { top: 0, right: 0.1, bottom: 0.1, left: 0.1 }`) só nessas 6 colunas — o resultado
  visual é uma única célula cinza sem linha no meio. O texto de Fornecedor…Valor Total só é escrito
  depois, no hook `didDrawCell` do AutoTable (quando já se sabe a altura real da linha de baixo),
  centralizado no meio das 2 linhas somadas (`headRowATop` até `data.cell.y + data.cell.height`) —
  não dava pra centralizar direito escrevendo antes, porque a altura da linha de baixo só é definida
  pelo AutoTable depois de montar a tabela. Não dá pra usar `columnStyles[i].fillColor`/`lineWidth`
  para pintar só a linha de baixo do cabeçalho, porque essas opções também valem para as células do
  **corpo** da coluna. As larguras de coluna (`colWidths`, incluindo o cálculo da largura "auto" de
  Descrição a partir da largura da página) viraram uma constante única, reaproveitada tanto no
  desenho manual da linha de cima quanto no `columnStyles` do AutoTable, para as duas linhas do
  cabeçalho ficarem exatamente alinhadas. Testado com PDFs reais (2, 4 e 6 despesas), conferindo em
  várias posições de zoom/scroll do visualizador do Chrome que os 6 títulos aparecem uma única vez,
  sem espaço em branco, sem linha divisória e centralizados verticalmente.
- **Datas e prazos (sessão 42)**: o formulário só tem Data do Recebimento (obrigatória), Data Final
  para Aplicação e Prazo de Prestação de Contas — a Data Inicial de Aplicação é sempre igual ao
  recebimento e é gravada automaticamente (`data_inicio_aplicacao = data_recebimento`); leitura
  via `_pcDataRecebimento(p)` (fallback para registros antigos). Prazos em dias, iguais à planilha
  da administração: aplicação = recebimento → data final contando os dois extremos
  (`_pcDiasInclusivos()`); prestação de contas = data final → prazo de prest. de contas, só a
  subtração das datas (`_pcDiasEntre()`, sem +1). Mostrados ao vivo abaixo das datas no
  formulário (`_pcAtualizarPrazosForm()`), no Detalhe (entre parênteses) e no PDF.
- **Tipo de Comprovante (sessão 42)**: Recibo, Cupom Fiscal, Nota Fiscal, Cupom de máquina
  registradora — mesma lista da aba de apoio da planilha da administração.
- **Desconto (sessão 42)**: campo opcional `desconto` em cada despesa; valor total =
  (valor unit. × quant.) − desconto (`_atualizarValorTotalDespesa()`), mesma fórmula da planilha
  da administração. Coluna "Desconto" no Detalhe ("—" quando zero) e no PDF.
  Nota: durante o desenvolvimento, a ferramenta de inspeção de PDF usada para conferir o layout
  mostrou um artefato de renderização que não existe no arquivo real — se for depurar isso de novo,
  confie no PDF baixado de verdade, não na pré-visualização.
- **Alinhamento dos 3 campos de data no formulário (sessão 43)**: os rótulos "Data Final para
  Aplicação" e "Prazo de Prestação de Contas" quebravam em 2 linhas dentro da coluna do
  `.form-grid` (4 colunas), enquanto "Data do Recebimento" ficava em 1 linha só — os 3 campos
  ficavam desalinhados ("escadinha"). Classe nova `.fp-label-nowrap` (`white-space: nowrap` +
  fonte um pouco menor, `0.74em`) nos 3 `.form-group` desses campos, no formulário "Novo/Editar
  Pronto Pagamento" (`#fp-data-recebimento`/`#fp-data-fim`/`#fp-prazo-pc`).
- **Campos vazando do modal "Nova Despesa" (bugfix, sessão 43)**: Descrição do Material/Serviço e
  Valor Total (campos que ocupam a linha inteira do `.form-grid`) vazavam para fora do modal. Causa
  e correção documentadas em `docs/site/padroes-codigo.md` (seção "CSS: `.form-group` como item de
  grid") — resumo: uma opção longa do `<select>` "Tipo de Comprovante" forçava a coluna do grid a
  crescer além do espaço disponível; `min-width: 0` em `.form-group` (aplicado a todos os modais de
  formulário do site, não só a este) resolve na raiz.

## Viagens e Eventos (`#viagens-eventos`)

Botão visível a **todos os usuários logados** (viewer e admin), diferente de Prestação de
Contas — só os controles de edição (➕/✏️/🗑️) são admin-only, decididos no próprio
`renderViagensEventos()`/`_viagensAbrirDiaModal()` via `userRole === 'admin'`.

Duas sub-abas próprias da seção (`_viagensSubTab`, não usa o sistema global de abas de
Designações): **📅 Calendário** e **📋 Lista** — ambas leem a mesma fonte de dados, dois
tipos de evento guardados em coleções separadas:

| # | Título | Campos | Coleção Firestore | Cache localStorage |
|---|--------|--------|--------------------|---------------------|
| 1 | 🧳 Eventos e Próximas Viagens Previstas | `data_inicio`, `data_fim`, `membro`, `motivo` + processo/portaria (ver abaixo) | `viagens_tabela1_admin/{id}` | `pma-viagens-tabela1` |
| 2 | 📅 Viagens Trimestrais | `local`, `data_inicio`, `data_fim`, `motivo`, `membro` + processo/portaria (ver abaixo) | `viagens_tabela2_admin/{id}` | `pma-viagens-tabela2` |

**Processo e portaria (opcionais, ambas as tabelas):** `processo_tipo` (`"SEI"`/`"SGI"`, select) +
`processo_numero` (texto livre) — mesmo padrão do campo "Processo" do formulário de Afastamentos
([index.html:3958](polo-medio-amazonas/index.html:3958)); e `portaria_url` — **só o link**, sem
campo de número manual (diferente de Plantão: aqui o rótulo é sempre o extraído automaticamente
da URL, decisão explícita da usuária pra manter o formulário mais enxuto). Renderização:
`_viagensProcessoHtml(ev)` (`"SEI: NNNN"` ou `"—"`) e `_viagensPortariaHtml(ev)` — sem
`portaria_url` mostra `"—"`; com `portaria_url`, sempre `_rotuloEdicaoDiario(url)` (a mesma
função genérica do Plantão que extrai "Edição NNNN" da URL, `.../Edicao_NNNN...`, caindo em
"Abrir PDF" sem padrão reconhecível). Aparecem como 2 colunas extras na Lista ("Processo" e
"Portaria") e como uma linha extra compacta no modal de detalhe do dia do Calendário. Todo texto
livre desses campos passa por `_viagensEscHtml()`; os atributos `href` usam `_viagensEscAttr()`
(aspas escapadas) — **nunca** só `_viagensEscHtml()`/`esc()` dentro de um atributo, ver nota de
segurança abaixo.

**Por que coleção (um doc por evento) e não um doc único com array:** o Calendário precisa
posicionar cada evento nos dias certos, o que exige datas reais (`data_inicio`/`data_fim` em
`YYYY-MM-DD`) em vez do texto livre que a v1 desta seção usava (ex: `"21 a 23/05/2026"`). Com
datas reais, a Lista passou a fazer sentido **ordenada automaticamente por `data_inicio`** —
substituiu o mecanismo de inserir/excluir linha em posição arbitrária da v1 (decisão da
usuária: adicionar/remover continua livre, só não há mais reordenação manual fora da ordem
cronológica).

### Calendário

`_viagensRenderCalendario()` desenha uma grade mensal com os eventos das **duas tabelas ao
mesmo tempo**, coloridos por tipo (cinza-grafite = tabela 1, azul = tabela 2) — não há seletor
de tabela no calendário. Navegação: botões de ano fixo (2026/2027, `_viagensCalAno`) + uma
linha de 12 botões de mês (`#viagens-cal-mes-filtro`, mesmo estilo `.viagens-filtro-btn` da
Lista, `_viagensMudarMesDireto(idx)` seta `_viagensCalMes` direto) — substituiu as setas
"Mês anterior/Próximo mês" da v1 a pedido da usuária, pra reaproveitar visualmente o mesmo
seletor que ela já gostava na Lista. Sem botão "Ano todo" aqui (não tem equivalente visual
numa grade de um mês só).

- **Barra contínua ao longo do intervalo, sem precisar clicar:** cada evento aparece como uma
  barra colorida em todos os dias entre `data_inicio` e `data_fim` — cantos arredondados só
  nas pontas reais (`start`/`end`/`solo`), quadrados no meio (`mid`), texto do rótulo
  (`_viagensRotuloEvento`: `membro` na tabela 1, `local` na tabela 2) só no primeiro dia pra
  não repetir a mesma frase em cada célula. Hover mostra o detalhe completo via `title`
  (`_viagensDetalheEvento`, escapado com `_viagensEscAttr` — cuidado extra pra aspas dentro de
  atributo, que `_viagensEscHtml` sozinho não cobre).
- **Motivo distribuído nos dias seguintes (só Tabela 1):** decisão da usuária de restringir só
  à Tabela 1 (Eventos e Próximas Viagens) — a Tabela 2 tem um comportamento próprio, mais
  simples: `local` no offset 0 (1º dia do evento), `membro` fixo no offset 1 (2º dia), vazio
  do offset 2 em diante — não é uma distribuição/empacotamento, é só um segundo campo fixo
  (pedido da usuária depois de ver o Local sozinho na barra). Ambos os offsets usam
  `_viagensDiffDias(data_inicio, diaStr)`, então em evento de 1 dia só o `membro` nunca aparece
  na barra (só no hover/clique — não existe "2º dia"). `_viagensEventosDoMes()` pré-calcula
  `ev.motivoChunks` só para eventos da
  tabela 1 (`_viagensDistribuirMotivo(motivo, nDiasContinuacao)`) — empacota o **máximo de
  palavras inteiras** que cabem em cada dia (nunca corta no meio), até `VIAGENS_MOTIVO_MAX_CHARS`
  (22 caracteres, afinado empiricamente pro font-size/padding de `.viagens-cal-bar` em 1280px —
  testado sem overflow real, via `scrollWidth > clientWidth`, em motivos curtos e longos) — não
  é mais uma divisão balanceada por tamanho médio (v1 dessa feature), é greedy: cada dia pega o
  quanto couber, sobra vai pro(s) dia(s) seguinte(s); se o texto acabar antes dos dias, os dias
  restantes ficam vazios; se os dias acabarem antes do texto, o resto só aparece no hover/clique.
  No render, `_viagensDiffDias(data_inicio, diaStr)` calcula o offset
  real do dia dentro do evento (não relativo à grade visível): offset 0 = Membro/Servidor,
  offset N = `motivoChunks[N-1]`. Evento de 1 dia só não tem "dias seguintes" — o Motivo fica
  só no hover/clique, igual antes. Se o evento atravessa a virada do mês, o texto continua
  fluindo normalmente na página do mês seguinte (o offset é sempre relativo à data real de
  início, não ao 1º dia visível) — o nome do Membro **não** reaparece nessa página nova,
  decisão explícita da usuária.
- **Empilhamento sem sobrepor:** `_viagensEventosDoMes()` faz um algoritmo guloso de "lanes"
  (varre os eventos do mês ordenados por `data_inicio`, cada evento pega a primeira lane cujo
  último evento já terminou) — eventos que se sobrepõem no tempo (ex: dois eventos que passam
  por 15/06) ficam em lanes diferentes e alinhadas verticalmente em todos os dias do mês; dias
  sem evento numa lane recebem um spacer invisível (`.empty-spacer`) só pra manter o
  alinhamento das lanes abaixo.
- **Destaque do dia de hoje:** classe `.hoje` comparando com `_viagensHojeStr()`.
- **Clique em qualquer dia** (mesmo vazio) → `_viagensAbrirDiaModal(ano,mes,dia)` — modal
  lista os eventos das duas tabelas que cobrem aquele dia, com ✏️/🗑️ por admin, e dois botões
  "➕" (um por tabela) que já abrem o formulário com a data pré-preenchida.

### Formulário de evento

Um único modal (`#viagens-form-overlay`) reaproveitado pelas duas tabelas —
`_viagensAbrirForm(tabela, id, ano, mes, dia)` alterna a visibilidade do grupo "Local"
(`#viagens-form-local-group`, só tabela 2) e preenche o formulário se `id` for passado
(edição). Campo Local é um `<select>` fixo com os 6 municípios do Polo (Itacoatiara,
Itapiranga, São Sebastião do Uatumã, Silves, Urucará, Urucurituba) + opção "Outro" que revela
um campo de texto livre — decisão da usuária pra evitar erro de digitação/duplicidade
("Urucara" vs "Urucará"). `_viagensSalvarEvento()` valida datas (fim ≥ início) e campos
obrigatórios antes de gravar.

### Lista

Uma tabela por tipo (mesmo layout visual da v1), lida de `_viagensEventos[n]` — sempre
ordenada por `data_inicio` (nunca reordenada manualmente). Filtro por ano + mês
(`_viagensRenderListaFiltro`, classe própria `.viagens-filtro-btn` — não usa mais a
`.month-filter-btn` genérica do site, pra não puxar o tamanho/cor padrão das outras seções):
dois botões de ano fixo (2026/2027, `_viagensFiltrarAno`) à esquerda, depois "Ano todo"
(remove o filtro de mês dentro do ano selecionado) + os 12 meses (`_viagensFiltrarMes`).
`_viagensListaFiltro[n]` é `{ ano, mes }` — `_viagensAnoMesAtual()` inicializa com o ano
vigente (`new Date().getFullYear()`) e `mes: 'todos'`. Texto das células (`motivo`/`membro`/`local`)
sempre escapado via `_viagensEscHtml()` — nunca interpretado como HTML, mesmo em modo leitura.

**Filtro de cidade (só Viagens Trimestrais, tabela 2 — sessão 41):** linha extra de botões
(`#viagens-lista-cidade`) abaixo do filtro de ano/mês: "📍 Todas as cidades" + as 5 cidades de
`VIAGENS_CIDADES` (Itapiranga, São Sebastião do Uatumã, Silves, Urucará, Urucurituba). Estado em
`_viagensListaCidade` (`'todas'` ou o nome), trocado por `_viagensFiltrarCidade(idx)` (recebe o
índice, não o nome, pra não precisar escapar acento/espaço no `onclick`). Combina com ano/mês
(filtros cumulativos) e compara `ev.local` sem diferenciar maiúscula/minúscula. Não afeta o
Calendário nem a tabela 1.

**Seed inicial:** `VIAGENS_TABELAS[n].seed` — os mesmos registros do PDF "Nova Funcionalidade
no site" (sessão 33), agora com `data_inicio`/`data_fim` reais em vez do texto livre original.
Só aparece um botão "⬇️ Importar dados iniciais" (admin, na Lista) quando a coleção
correspondente está vazia — `_viagensImportarSeed(n)` grava tudo num único `db.batch()`. Nunca
roda sozinho; é sempre uma ação explícita do admin.

**Regra do Firestore:** `viagens_tabela1_admin`/`viagens_tabela2_admin` têm `allow write: if
isAdmin()` em `firestore.rules` (leitura já coberta pela regra genérica de qualquer coleção).
Precisa de `firebase deploy --only firestore:rules` pra valer em produção — mesma pegadinha já
documentada na sessão do Plantão (commitar a regra sozinho não publica).

## Cache localStorage (elimina flash de dados)

| Chave | Conteúdo |
|-------|---------|
| `pma-regra-alternancia` | HTML da seção Regra de Alternância |
| `pma-ferias-folgas` | HTML da seção Férias/Folgas/Licenças |
| `pma-atr-celulas` | células JSON de Atribuições |
| `pma-adote-celulas` | células JSON de Adote |
| `pma-adote-expandir` | HTML do bloco Expandir |
| `pma-plantao-fs` | docs brutos de `plantao_admin` |
| `pma-viagens-tabela1` | linhas da tabela "Eventos e Próximas Viagens Previstas" |
| `pma-viagens-tabela2` | linhas da tabela "Viagens Trimestrais" |
| `pma-afastamentos-fs` | docs brutos de `afastamentos_admin` |
| `pma-equipe-fs` | docs brutos de `afastamentos_equipe` |
| `pma-secao` | última seção visitada (restaura na recarga) |
