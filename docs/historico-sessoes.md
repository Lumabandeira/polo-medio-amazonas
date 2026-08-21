# Histórico de Sessões — O que foi implementado

> Ordem cronológica inversa (mais recente primeiro)

---

## Sessão 35 — 21/08/2026

- **Diagnóstico de esvaziamento de `plantao_admin`**: usuária relatou que a Escala de Plantão
  apareceu vazia no site (botão "Importar dados iniciais" reapareceu). Investigação: backups
  locais (`backups/firestore/2026-08-10_*`) confirmaram 12 períodos gravados em 05/08/2026;
  nenhum script do repositório (backup, backfill, limpeza) toca `plantao_admin`, e o único
  caminho de exclusão do site (`confirmarDeletarPlantao()`) apaga 1 período por vez com
  confirmação individual — conclusão: exclusão manual fora do fluxo normal (Console do Firebase
  ou clique período a período), não um bug do site. Usuária reimportou o seed pelo botão.
- **Correção de typo**: "Karolayne" → "Karolyne" (nome da servidora Luma Karolyne Pantoja
  Bandeira) — erro isolado em `PLANTAO_SEED_2026` (`index.html`), divergente do resto do
  repositório. Corrigido no código e nos 2 documentos já gravados que tinham herdado o erro via
  reimportação do seed (script Python pontual com a service account).
- **Link de portaria por período na Escala de Plantão**: nova coluna "Portaria" na tabela —
  antes só existia um link geral fixo no topo (`plantao_info`), sem diferenciar períodos
  alterados por portaria pontual posterior à publicação original (já ocorreu antes, ver
  substituições no Diário Oficial). 5 campos novos opcionais em `plantao_admin/{id}`:
  `portaria_numero`/`portaria_url` (portaria própria do período) e
  `alteracao_numero`/`alteracao_url`/`alteracao_obs` (quando a escala foi alterada — vira badge
  laranja "🔄" em destaque; decisão explícita da usuária de não mostrar a portaria original ao
  lado). Linhas sem portaria própria caem no link geral, cacheado em `plantaoInfoAtual` para uso
  síncrono em toda a tabela sem repetir leitura do Firestore por linha. Editável só pelo
  formulário de 1 período — CSV e seed continuam com os 4 campos base (caso raro, não compensa
  complicar o parser). Testado no navegador local (servidor estático, sem login real,
  `userRole='admin'` simulado via console): 4 casos, incluindo um payload de XSS no
  `alteracao_obs` que revelou e levou à correção de um bug real — o `title` do badge precisa de
  `esc(...).replace(/"/g, '&quot;')`, não só `esc()`, porque esse helper do site só escapa
  `&`/`<`/`>` (seguro em texto de nó HTML, mas não dentro de um atributo); mesmo padrão já usado
  em `_viagensEscAttr()`. Ver `docs/site/estrutura-html.md` (seção "Plantão") e `docs/firebase.md`
  para o detalhamento completo.
- **Ajuste de estilo do rótulo (mesmo dia):** usuária pediu pra usar, no link de portaria do
  Plantão, o mesmo modelo já usado na coluna "Diário Oficial" das tabelas de Afastamentos —
  ícone 📄 azul negrito com texto "Edição NNNN" extraído automaticamente da URL
  (padrão `Edicao_NNNN` no nome do arquivo), em vez do admin precisar digitar um rótulo. Nova
  função `_plantaoRotuloEdicao(url)`; `portaria_numero`/`alteracao_numero` do formulário viraram
  override opcional (só necessário se o link não seguir esse padrão — cai em "Abrir PDF").
- **Bugfix real: semanas duplicadas no Plantão.** Usuária notou várias semanas repetidas na
  tabela. Diagnóstico: `_plantaoImportarSeed()` só checava `plantaoRegistros.length` (estado em
  memória do navegador) antes de gravar os 13 períodos do seed — na reimportação feita mais
  cedo nesta sessão (ver item acima sobre a coleção vazia), o admin clicou "Importar dados
  iniciais" antes do 1º `loadPlantaoFirestore()` terminar de carregar, então o array local ainda
  lia `[]` mesmo com 10 dos 13 períodos originais (de 05/08) ainda existindo no Firestore — o
  seed inteiro foi regravado por cima, criando 8 pares duplicados (16 docs; os outros 2 dos 10
  originais a usuária já tinha limpado manualmente antes de pedir ajuda). Corrigido em duas
  camadas: `renderPlantao()` só oferece o botão de seed depois que `plantaoCarregouUmaVez`
  confirma uma leitura real do Firestore (antes mostra "carregando" em vez do estado vazio), e
  `_plantaoImportarSeed()` revalida direto no Firestore (`.limit(1).get()`) imediatamente antes
  de gravar, com trava contra duplo-clique. **Dados corrigidos em produção** (script pontual com
  a service account, só depois de confirmação explícita da usuária via `AskUserQuestion`, já que
  a exclusão foi bloqueada uma vez pelo classificador de auto-mode por ser destrutiva): 8
  documentos duplicados deletados (mantido sempre o original de 05/08 — dados idênticos em cada
  par, conferido campo a campo via script antes de apagar, evitando mojibake no console do
  Windows gravando em arquivo UTF-8), voltando a 13 períodos únicos. Também gravado o link
  definitivo da Portaria 764/2026 em `secoes/plantao_info.url`
  (`.../Portaria-no-0764-2026-GSPG-26.0.000010208-2.pdf`), que agora aparece em toda linha sem
  portaria própria — rótulo "Abrir PDF" (essa URL não segue o padrão `Edicao_NNNN`). Ver
  `docs/site/estrutura-html.md` (seção "Plantão").
- **Preenchimento de `portaria_url` em todos os 13 períodos** (dado, não código — script pontual
  com a service account): usuária informou que a Edição 2696 do Diário Oficial
  (`.../Edicao_2696-2026__publicada_em_24_julho_de_2026.pdf`) é quem publicou a maioria da
  escala. Gravado como `portaria_url` em todos os períodos, com `portaria_numero` propositalmente
  vazio — a URL segue o padrão `Edicao_NNNN`, então `_plantaoRotuloEdicao()` já extrai "Edição
  2696" automaticamente, sem precisar de rótulo manual.
- **CSV de Plantão ganha link do Diário Oficial.** Usuária notou que o "Importar CSV" — única via
  prevista pra adicionar escalas futuras em lote — não tinha como registrar a portaria, ficando
  sempre dependente do link geral da seção (que fica desatualizado a cada nova edição publicada).
  Perguntado se o campo deveria ser por linha do CSV ou único por lote; escolhida a opção por
  lote, já que o uso real é uma edição publicar várias semanas de uma vez (como a Edição 2696
  publicou as 13 de hoje) e o ChatGPT não teria como gerar a URL sozinho de qualquer forma.
  Adicionado campo opcional "Link do Diário Oficial" no topo do modal `#plantao-csv-overlay`,
  resetado em `abrirCsvPlantao()` e aplicado como `portaria_url` em todos os documentos criados
  por `_plantaoConfirmarImportacaoCsv()`. Testado no navegador local: campo existe, reseta ao
  reabrir o modal, valor chega correto até o ponto de montagem do objeto salvo (não testado contra
  o Firestore real, mesma cautela de sessões anteriores). Ver `docs/site/estrutura-html.md`
  (seção "Plantão").
- **Agrupamento por lote na tabela de Plantão** (planejado via `EnterPlanMode`, com 2 perguntas
  respondidas pela usuária: ordem dos grupos — mais recente primeiro — e se deveria dar pra
  renomear o lote inteiro de uma vez — sim). Motivação: a usuária vai acumular mais escalas na
  mesma coleção com o tempo (4º Trimestre 2026, depois 1º Semestre ou 1º Trimestre de 2027 — a
  administração decide o formato, não tem como fixar um padrão), e uma lista única "achatada"
  ordenada só por data ia ficar confusa sem separar visualmente cada leva. Novo campo opcional
  `lote_nome` (texto livre) em cada período do `plantao_admin/{id}` — sem coleção separada de
  "lotes", mantendo o padrão de campo string livre já usado na seção (`defensor`/`assessoria`).
  Preenchido pelo formulário de 1 período (`abrirFormPlantao`/`salvarPlantaoFirestore`) — ao abrir
  "Novo período" pré-preenche com o `lote_nome` do período mais recente já cadastrado, pra não
  redigitar o mesmo nome dentro da mesma leva — e pelo "Importar CSV" (campo único "Nome do
  lote", mesmo padrão em lote do campo de link adicionado antes nesta sessão). `renderPlantao()`
  reestruturado: `_plantaoAgruparPorLote()` agrupa `plantaoRegistros` por `lote_nome` (chave `''`
  vira grupo "Sem lote definido", sempre por último) e ordena os grupos pelo maior `data_inicio`
  de cada um, decrescente; cada grupo vira seu próprio bloco (cabeçalho com contagem + badge
  "🔵 atual" via `_plantaoLoteContemHoje()` quando a data de hoje cai no intervalo do grupo,
  seguido da mesma tabela de sempre). Renomear lote inteiro (admin): botão "✏️ renomear" no
  cabeçalho, mesmo padrão de edição inline de `_plantaoEditarInfo()`/`_plantaoSalvarInfo()` —
  `_plantaoRenomearLoteIniciar(idx)`/`_plantaoRenomearLoteSalvar(idx)` usam um índice pro cache
  `_plantaoGruposAtuais` (do último render) em vez de embutir o nome do lote — texto livre, pode
  ter aspas/caracteres arbitrários — dentro de um atributo `onclick`. `PLANTAO_SEED_2026` ganhou
  `lote_nome: '3º Trimestre 2026'` em cada item via `.map()` sobre a nova constante
  `PLANTAO_SEED_2026_LOTE`. Testado no navegador local: 4 lotes simulados (incluindo um sem
  `lote_nome` e um com payload `"><script>alert(1)</script>` no nome) — ordem dos grupos correta,
  contagem, badge "atual" no grupo certo, XSS não disparou (nem no cabeçalho nem no atributo
  `value` do input de renomear, que usa `esc(...).replace(/"/g,'&quot;')` como os outros campos
  desta sessão), pré-preenchimento do formulário e reset do campo do CSV corretos, e o
  `renomear` monta a lista certa de IDs a atualizar (não gravado contra o Firestore real). Ver
  `docs/site/estrutura-html.md` (seção "Plantão") e `docs/firebase.md`. Backfill de
  `lote_nome: "3º Trimestre 2026"` nos 13 períodos já existentes executado logo em seguida
  (script pontual com a service account).
- **Bugfix de segurança real: `href` sem escapar aspas em Plantão.** Ao explorar Viagens e
  Eventos pra estender o padrão de link de portaria (próximo item), notei que os 3
  `href="${esc(url)}"` de `_plantaoLinkPortariaHtml()` usavam só `esc()` — que escapa
  `&`/`<`/`>` mas não aspas. Testado com uma URL contendo `" onmouseover="..."`: o atributo
  quebrava e o handler injetado disparava ao passar o mouse (confirmado via
  `dispatchEvent(new MouseEvent('mouseover'))` antes da correção). Os testes de XSS anteriores
  desta sessão só tinham coberto `alteracao_obs` (o `title` do badge), não os próprios campos de
  URL. Corrigido com um novo helper genérico `_escAttr(s)` nos 3 pontos; `_plantaoRotuloEdicao()`
  renomeada para `_rotuloEdicaoDiario()` (função pura, sem prefixo de seção) já que passou a ser
  compartilhada com Viagens e Eventos. Reconfirmado com o mesmo payload: não dispara mais.
- **Processo (SEI/SGI) e Portaria em Viagens e Eventos.** Usuária mostrou o modal "Editar
  Afastamento" (campos "Processo" SEI/SGI + número, e "Número da Portaria"/"Link do Diário
  Oficial" por substituto) como referência e pediu os mesmos campos em Viagens e Eventos. 4
  campos opcionais novos em `viagens_tabela1_admin`/`viagens_tabela2_admin`:
  `processo_tipo`/`processo_numero` (mesmo padrão do campo "Processo" de Afastamentos,
  `index.html:3958`) e `portaria_numero`/`portaria_url` (mesma convenção já usada em
  Plantão/Afastamentos/Remoções — reaproveita `_rotuloEdicaoDiario()`, não duplica a extração de
  "Edição NNNN"). Novo bloco no formulário único que já atende as duas tabelas
  (`#viagens-form-overlay`), lido/populado em `_viagensSalvarEvento()`/`_viagensAbrirForm()`.
  Renderização via `_viagensProcessoHtml(ev)`/`_viagensPortariaHtml(ev)`: 2 colunas novas
  ("Processo", "Portaria") na Lista de ambas as tabelas (`_viagensRenderLista()`, colspan do
  estado vazio ajustado de `n===2?4:3` para `n===2?6:5`), e uma linha extra compacta no modal de
  detalhe do dia do Calendário (`_viagensAbrirDiaModal()`). Deixado de fora o `title` do hover da
  barra do calendário (`_viagensDetalheEvento()`) — tooltip curto, baixo valor pra esses campos
  ali. Testado no navegador: evento sem processo/portaria (mostra "—"), evento normal (mostra
  "SEI: NNN" e "📄 Edição NNNN" extraído automaticamente da URL), e evento com payloads de
  XSS/aspas nos 3 campos novos simultaneamente — nenhum disparo mesmo com hover simulado em
  todos os elementos da linha (`_viagensEscHtml`/`_viagensEscAttr`, já existentes na seção,
  reaproveitados sem duplicar). Ver `docs/site/estrutura-html.md` (seção "Viagens e Eventos") e
  `docs/firebase.md` para o detalhamento completo.

---

## Sessão 32 — 09/08/2026

- **Bugfix real de duplicação de afastamentos**, encontrado pela usuária ao testar a Escala
  Semanal: no popup de detalhe do dia (aba Calendário), férias/folgas vindas do Firestore
  apareciam duas vezes (ex: Emilly e Miguel em agosto/2026), embora a Lista de Substituições
  mostrasse corretamente. Causa: `_afastamentosAplicarCache()` só empilhava os registros do
  Firestore em `detalhesAfastamentos` via `mergeAfastamentoFirestoreRecord()`, sem nunca limpar
  entradas de uma aplicação anterior — se a função rodasse mais de uma vez na sessão, cada
  afastamento duplicava. Corrigido removendo as entradas de origem Firestore antes de remesclar
  a cada chamada. Ver `docs/site/estrutura-html.md`.
- **Filtro por mês em Lista de Substituições** — botões Janeiro-Dezembro iguais aos de
  Designações Diárias e Escala Semanal, mas escopados ao próprio container (`filterListaSubstituicoesByMonth`),
  sem interferir nos outros dois filtros de mês da página. Todos os 12 meses viram seção
  (antes só os que tinham registro); mês selecionado persiste ao trocar o filtro de DP.
- **Ajustes estéticos e de nomenclatura na navegação**, a pedido da usuária:
  - Botão Plantão → laranja (`#f97316` → `#fed7aa`); Escala Semanal herdou o vermelho que
    era do Plantão (`#7f1d1d` → `#ef4444`). Testadas variações mais claras de ambos os tons
    (com preview visual antes de aplicar) — a usuária optou por manter os tons originais
    depois de testar.
  - Sub-aba "Designações semanais" → **"Designações diárias"** (rótulo, título `<h2>`, texto
    descritivo, aviso em Trabalho em Trânsito e legenda da Escala Semanal) e **movida** para
    depois de "Resumo de Afastamentos" na barra. "Calendário" → **"Calendários de
    afastamentos"**. Só rótulos visíveis mudaram — nenhum `id` ou função interna foi tocado.
  - Card "Designações" na landing: nova descrição ("Designações dos Defensores, Afastamentos
    e Substituições").
  - Removido o contador "Total de Defensores" em 👥 Defensores Públicos, mantendo só "Total
    de Defensorias".
- **Botão "Prestação de Contas" também no header-nav** (antes só existia na landing) — ao
  lado de Diário Oficial, largura reduzida com texto em duas linhas pra caber na barra,
  admin-only (mostrado/ocultado junto com o card da landing na mesma checagem de role).
- Commits: `3a20d13` (estética/nomenclatura), `4505ce6` (bugfix duplicação), `05344fa`
  (legenda Escala Semanal), `0007c39` (filtro de mês em Lista de Substituições), `895f8a2`
  (botão Prestação de Contas no header).

---

## Sessão 31 — 09/08/2026

- **Lida a íntegra do ANEXO I da Resolução nº 13/2023-CSDPE/AM** (atribuições do Polo do Médio
  Amazonas, já com a alteração da Resolução 017/2026 de 7/5/2026) e comparada com a tabela
  "Atribuições" já existente no site — confirmado que todos os campos batiam (atribuição/matéria,
  dígitos pares/ímpares, colidência, substituições, extrajudicial). A comparação inicial de
  colidência apontou divergência, mas era erro de leitura de direção da minha parte — a usuária
  corrigiu (o texto "DP-X é colidente da DP-Y" pertence à *linha* da DP-Y na tabela) e, refeita
  corretamente, os dados do site já estavam certos.
- **Nova linha "Audiências"** na tabela de Atribuições (1ª-6ª DP, texto do regime de revezamento
  do Anexo I, depois resumido para versão mais direta a pedido da usuária — ex: "Reveza com a 2ª
  DP, se responsável pelo atendimento, não acumula audiências").
- **Bugfix em `_atrResolverDefensor()`** (tabela Atribuições): titulares livres (nomes fora do
  dicionário `defensores`) caíam num fallback (`defensorNames[key]`) que `_atualizarNomesVaga()`
  preenche com rótulo genérico `"Nª DP (vaga)"` para *qualquer* chave fora do dicionário — inclusive
  titulares livres reais, não só vagas de fato. A 8ª e a 9ª DP apareciam como vaga mesmo tendo
  titular. Corrigido para usar o nome/chave digitado diretamente, igual ao padrão já usado em
  Designações → Defensorias.
- **Nova seção "📋 Escala Semanal"** (nav superior + landing page, posicionada logo após
  Atribuições) — tabela somente leitura de Atendimento/Audiência de Família, Cível e Criminal,
  Plantão e as duas UDIS, uma linha por semana. **Não é editável e não tem Firestore próprio** —
  100% derivada de fontes já existentes (mesma lógica de `DPS_CONFIG`/`getWeekGroup()` de
  Designações Semanais para saber quem faz atendimento x audiência, `getResponsibleForDPOnDay()`
  para o responsável do dia, e `plantao_admin` para a coluna Plantão). Detalhamento completo em
  `docs/site/estrutura-html.md` (seção "Escala Semanal").
  - Decisão explícita da usuária durante o planejamento: preencher via fontes de dados, nunca
    editar a tabela em si diretamente.
  - Segmentação dia a dia dentro da semana (mostra "até DD/MM... a partir de DD/MM" quando o
    responsável muda no meio da semana), a pedido da usuária, replicando o comportamento de uma
    planilha de referência que ela usa manualmente.
- **Bugfix em `getTitularForDPOnDay()`** — descoberto ao testar a Escala Semanal, mas afeta
  também Designações Semanais: quando nenhum intervalo do `historico_titulares` de uma DP cobre a
  data pedida (ex: última entrada com `fim` preenchido e nada cadastrado depois), a função
  retornava `undefined`, que o chamador (`getResponsibleForDPOnDay`) trata como "JSON ainda não
  carregado" e cai num fallback estático hardcoded (o titular "natural" de cada DP em
  `DPS_CONFIG`) — reexibindo ex-defensores como titulares atuais (ex: Ícaro voltando a aparecer na
  3ª DP a partir de 01/09/2026, mesmo já vaga). Corrigido para retornar `null` explicitamente
  nesse caso, tratado corretamente como vaga. Ver `docs/firebase.md`.
- Estética da Escala Semanal ajustada a pedido da usuária: grade visível em todas as células,
  cabeçalho em vermelho mais vivo (gradiente `#9f1d1d → #dc2626`, diferente do azul padrão do
  site e do tom rosado da planilha de referência), cabeçalho em negrito, e fundo levemente mais
  claro (`#fdeaea`) nas colunas de Audiência para diferenciar de Atendimento.
- Commits: `06631c1` (linha Audiências), `0e6f325` (textos resumidos), `379c662` (bugfix titular
  livre), `8168688` (seção Escala Semanal + bugfix titular vaga + estética + reordenação de botão).

---

## Sessão 30 — 04/08/2026

- **Nova seção "🚨 Plantão"** (nav superior + landing page) — escala de plantão cível/criminal
  do Polo do Médio Amazonas. Dados extraídos de PDF real (Portaria nº 764/2026-GSPG/DPE/AM,
  Anexos I-III, 13 semanas de 29/06 a 27/09/2026), lido diretamente na conversa (Read tool,
  não automação) e revisado pela usuária antes de virar dado "oficial" no site.
  - **Primeira versão (revertida):** tabela de tamanho fixo com células `contentEditable` + RTE,
    no mesmo padrão de "Adote" (`secoes/plantao_celulas`). Descartada porque não permitia
    adicionar/remover períodos — só editar texto de células já existentes.
  - **Versão final:** lista dinâmica na coleção `plantao_admin/{id}` (schema:
    `data_inicio`/`data_fim`/`defensor`/`assessoria`), mesmo padrão de CRUD já usado em Férias
    Equipe. Duas vias de cadastro, **nenhuma usa IA**:
    - Formulário de 1 período (`abrirFormPlantao`/`salvarPlantaoFirestore`).
    - Importação em lote colando texto CSV (`data_inicio;data_fim;defensor;assessoria`, aceita
      `;`, Tab ou `,`) — parsing 100% local em `_plantaoParseCSV()`, com pré-visualização
      (linhas ok/erro) antes de confirmar. A dica no modal sugere copiar o PDF da portaria para
      um chat de IA (ChatGPT etc.) e pedir o texto já em CSV — a extração acontece fora do site,
      com revisão humana antes de colar.
    - `PLANTAO_SEED_2026` guarda os 13 períodos da Portaria 764/2026; botão "⬇️ Importar dados
      iniciais" grava esse seed uma única vez (some depois que a coleção deixa de estar vazia).
  - Campo de descrição + link da portaria, editável (`secoes/plantao_info`), mesmo padrão do
    link de resolução em Atribuições.
  - **Decisão explícita da usuária: sem sino de notificação, sem automação de PDF via IA para
    esta função.** Os sinos existentes (afastamentos/remoções/designações cumulativas) não têm
    se mostrado confiáveis na prática e serão removidos futuramente — não fazia sentido
    replicar o padrão aqui.
  - **Pegadinha descoberta nesta sessão:** editar/commitar `firestore.rules` no repositório
    **não publica** a regra no Firebase — é preciso `firebase deploy --only firestore:rules
    --project polo-medio-as`. A escrita em `plantao_admin` falhou com "Missing or insufficient
    permissions" até o deploy manual ser feito (CLI já estava instalado e autenticado neste
    ambiente). Ver `docs/firebase.md`.
  - Commits: `2cceac4` (primeira versão), `d396e68` (refactor pra lista dinâmica),
    `c0fa01e` (campo de descrição/link), mais ajustes de estilo (`6482140`, `beba695`,
    `11e31ee`, `30b266e`, `2122788`, `12a7fb6`, `73c10d5`, `6bd2949`, `3b32c8d`).

## Sessão 29 — 04/08/2026

- **Novo tipo "💻 Trabalho em Trânsito" no Calendário de Afastamentos** (rótulo ajustado depois de
  "Trabalho Remoto" — é um tipo de trabalho remoto, o valor interno `tipo: 'trabalho_remoto'`
  continua o mesmo, só o texto exibido mudou) — adicionado ao `<select>` de
  tipo no modal "Novo Afastamento" (aba Designações → Calendário), gravado na mesma coleção
  `afastamentos_admin/{id}` (campo `tipo: 'trabalho_remoto'`), mas tratado à parte no merge dos
  dados: **não conta como ausência**.
  - `_mergeTrabalhoRemotoRecord()` (nova função em `index.html`) alimenta uma estrutura própria
    `trabalhoRemoto[ano][mes][dia]`, separada de `afastamentos[ano][mes][dia]` — por isso não faz
    "Designações semanais" (`getResponsibleForDPOnDay`) tratar o titular como ausente.
  - Formulário: `popularDPsAfetadas()` oculta a seção "Defensorias Afetadas" quando o tipo é
    `trabalho_remoto` — não há substituto, o defensor responde normalmente por suas DPs.
  - `renderListaSubstituicoes()` e `renderDetalhesAfastamentos()` filtram fora os registros com
    `tipo === 'trabalho_remoto'` — não aparecem em "Lista de Substituições" nem "Resumo de
    Afastamentos".
  - Badge no calendário: transparente com contorno tracejado na cor do próprio defensor
    (novo mapa `defensorColors`, construído em `buildDefensorNames()`), em vez do badge sólido
    normal — pedido explícito da usuária para diferenciar visualmente de uma ausência real.
  - O popup de detalhe do dia (dentro do próprio Calendário) continua mostrando/editando/excluindo
    o registro normalmente, via `detalhesAfastamentos` (mesmo mecanismo dos outros tipos).
  - Detalhamento técnico completo em `docs/site/estrutura-html.md` (seção "Trabalho em Trânsito").
  - **Não testado em produção** (sem credenciais Firebase nesta sessão) — só verificado que
    `index.html` carrega sem erro de sintaxe/console no preview local.

## Sessão 28 — 31/07/2026

- **Correção do nome completo do Defensor Eliaquim** — estava faltando o sobrenome "Santos"
  ("Eliaquim Antunes de Souza" → "Eliaquim Antunes de Souza Santos"). Corrigido em `index.html`
  (dropdown de afastamento), `docs/designacoes-2026.json` (campo `nome` da chave `eliaquim`),
  `docs/escalas/ferias-folgas-2026.md` e `docs/regras/ausencias.md` (tabelas). Commit `7340fb9`.
  Não alterados: `docs/diario-oficial-completo-2026.json`/`.md` — são transcrições automatizadas
  do texto literal publicado no Diário Oficial; alterar mudaria uma citação de documento oficial.
- **Descoberto e documentado o comportamento do campo "Nome do defensor" no modal Titulares por
  DP** — ao corrigir o nome também nas designações de titular (3ª/4ª/9ª DP) pelo site, o texto
  digitado não bateu com o `nome` do dicionário no momento do salvamento (JSON ainda em cache no
  navegador) e foi gravado como texto livre no Firestore, fazendo o card do Eliaquim perder o
  seletor 🟢 Membro / ⚪ Ex-membro. Ver detalhe do mecanismo (`_resolverDefensor()`) em
  `docs/firebase.md`. **Resolvido:** usuária reabriu "Titulares por DP" nas 3 DPs afetadas e
  regravou o nome com o JSON já com cache atualizado — card voltou ao normal, seletor reapareceu.

## Sessão 26 — 06/07/2026

- **Nova seção "💰 Prestação de Contas" (admin-only)** — botão na landing só visível para `userRole === 'admin'` (`_aplicarModoEdicao()` + segunda checagem em `showSection()`). Nasce a partir da análise de um processo real de prestação de contas de adiantamento (Memorando, Mapa Demonstrativo, Recibos, Justificativas de ausência de pesquisa de mercado, Atesto, Termo/Comprovante de Devolução, Fotos de reparo).
  - Coleção nova `prestacoes_contas/{id}`: cada documento é um "pronto pagamento" (adiantamento) de um tomador, com array `despesas[]` replicando as colunas do Mapa Demonstrativo (tipo, nº, data, fornecedor, descrição, qtd., valor unit./total).
  - Regra de negócio: cada tomador pode ter no máximo 2 prontos pagamentos com `status: "aberto"` simultâneos, em categorias diferentes entre si (`consumo` | `pessoa_juridica` | `pessoa_fisica`) — validada em `_validarCategoriaDisponivel()` antes de criar ou reabrir.
  - Anexos por despesa: 5 slots fixos (Recibo/NF, comprovação de mercado — pesquisa *ou* justificativa de ausência —, justificativa da despesa, atesto, fotos) + lista livre de outros documentos. Upload via Firebase Storage SDK (`firebase-storage-compat.js`, recém-adicionado ao projeto).
  - `storage.rules` criado do zero (Storage nunca tinha regras neste projeto) restringindo `prestacoes-contas/**` a admin; `firestore.rules` ganhou regra própria para `prestacoes_contas` com leitura **e** escrita admin-only (diferente do padrão de leitura aberta do resto do site) — expõe CPF/dados bancários via comprovante de devolução em PIX.
  - Testado no preview simulando estado admin + dados mock via `preview_eval` (sem credenciais reais de Firebase disponíveis nesta sessão): lista de cards, detalhe com totais, validação de limite/categoria, cálculo automático de valor total da despesa — todos corretos, sem erros de console.
  - **Pendente:** deploy de `storage.rules` no Firebase (`firebase deploy --only storage`) — arquivo criado localmente mas nunca publicado.
- **Storage e Firestore rules publicadas no Firebase Console** — o projeto estava no plano Spark e o Storage nunca tinha sido ativado; upgrade para Blaze feito pela usuária, bucket criado, `storage.rules` e `firestore.rules` (com a regra de `prestacoes_contas`) publicados manualmente pelo Console (colar-e-publicar, sem CLI). Validado com upload real de anexo.
- **Exportação do Mapa Demonstrativo em PDF** — botão "📄 Baixar Mapa (PDF)" na tela de detalhe da Prestação de Contas. `baixarMapaPDF()` usa jsPDF + jsPDF-AutoTable (CDN) para gerar uma página A4 paisagem fiel ao modelo em papel, com a barra "COMPROVANTE DE DESPESA" desenhada manualmente acima da tabela (evita `colSpan`/`rowSpan` no `head` do AutoTable). Commit `1cd3d82`.
  - Durante o desenvolvimento, a ferramenta de inspeção de PDF usada nesta sessão (Read tool) mostrou um artefato de renderização (texto sobreposto) que não existe no arquivo real — confirmado com print do PDF de verdade baixado e aberto no Chrome pela usuária, layout correto. Lição: para depurar PDFs gerados por jsPDF, confiar no arquivo baixado de verdade, não nas ferramentas de preview automatizadas.

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
