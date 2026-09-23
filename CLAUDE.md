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

## Estado atual (sessão 41 — 23/09/2026)

**Implementado nesta sessão:** filtro de cidade na Lista de "Viagens Trimestrais" (tabela 2 de
Viagens e Eventos) — linha de botões "📍 Todas as cidades" + Itapiranga, São Sebastião do Uatumã,
Silves, Urucará e Urucurituba (`VIAGENS_CIDADES`), abaixo do filtro de ano/mês e cumulativo com
ele. Estado em `_viagensListaCidade`, trocado por `_viagensFiltrarCidade(idx)`. Não afeta o
Calendário nem a tabela 1. Testado no navegador com eventos simulados (contagem por cidade, botão
ativo, mensagem de lista vazia com o nome da cidade). Ver `docs/site/estrutura-html.md` (seção
"Viagens e Eventos").

## Estado atual (sessão 38 — 18/09/2026)

**Implementado nesta sessão:** reordenar despesas no "Mapa Demonstrativo de Despesa" (Detalhe de
Prestação de Contas) sem precisar excluir e recadastrar. Botões ⬆️/⬇️ em cada linha
(`moverDespesa(prestacaoId, idx, direcao)`, perto de `excluirDespesa()`) trocam a posição de duas
despesas no array `despesas[]` e regravam o array inteiro no Firestore, mesmo padrão já usado por
`salvarDespesa()`/`excluirDespesa()`. Não precisou de campo de ordem novo nem migração — a posição
no array já era (e continua sendo) a ordem exibida na tabela e no PDF exportado. ⬆️ desabilitado na
primeira linha, ⬇️ na última; sem `confirm()` por ser ação reversível de baixo risco. Testado no
navegador (servidor estático, `userRole='admin'` simulado + `db.collection` stubado pra não gravar
de verdade): swap de linhas reflete na tabela e no payload enviado ao Firestore, clique fora dos
limites (subir na 1ª linha / descer na última) não dispara gravação, e os botões desabilitados
recalculam certo depois de cada swap. Ver `docs/site/estrutura-html.md` (seção "Prestação de
Contas").

**Ajuste ainda nesta sessão:** reordenada a ordem fixa de exibição dos 4 slots do modal "Anexos"
por despesa (`_renderCorpoModalAnexos()`) a pedido da usuária — de Recibo/Comprovação de
mercado/Justificativa/Atesto para **Justificativa/Comprovação de mercado/Recibo/Atesto**. Só
reordenação dos blocos no template (Fotos e Outros documentos continuam depois, inalterados) —
os 4 continuam os mesmos campos (`recibo_url`, `comprovacao_mercado`, `justificativa_url`,
`atesto_url`), sem mudança de schema. Testado no navegador confirmando a nova ordem dos rótulos
no DOM do modal.

**Ajuste ainda nesta sessão:** rótulo do slot de justificativa encurtado de "Justificativa da
despesa" para só "Justificativa", com um texto explicativo menor logo abaixo do título ("Para
cada aquisição/contratação de serviços por adiantamento, contendo o registro da verificação da
existência do bem em estoque ou de contrato vigente."). Novo parâmetro opcional `descricao` em
`_slotAnexoSimples(campo, label, url, descricao)` — renderiza um `<span class="pc-anexo-slot-desc">`
dentro de um novo wrapper `<div class="pc-anexo-slot-titulo">` (flex-column) junto do rótulo, sem
afetar os outros 3 slots (chamados sem o 4º argumento). CSS novo junto de `.pc-anexo-slot-label`
(`index.html:1169`). Testado no navegador — texto aparece menor e acinzentado abaixo do título,
layout do slot continua alinhado com os demais.

**Ajuste ainda nesta sessão:** removido o `<select id="pc-mercado-tipo">` (Pesquisa de mercado /
Justificativa de ausência) do slot "Comprovação de mercado" — a usuária considerou desnecessário
ter uma seleção pra isso. Virou o mesmo padrão de título + texto pequeno do slot de Justificativa
("ou, na impossibilidade, justificativa da ausência de pesquisa."), usando a mesma estrutura
`pc-anexo-slot-titulo`/`pc-anexo-slot-desc` (só que escrita manualmente aqui, não via
`_slotAnexoSimples()`, porque esse slot tem upload próprio — `_uploadComprovacaoMercado()`, campo
`comprovacao_mercado: {tipo, url}` em vez de `{campo: url}`). O campo `tipo` nunca era lido em
nenhum outro lugar (nem no PDF, nem em `_contarAnexosPreenchidos()`) — removido de
`_uploadComprovacaoMercado()`, que agora grava só `comprovacao_mercado: { url }`. Registros antigos
que já tinham `tipo` gravado continuam com o campo no Firestore (não foi feita limpeza), só deixa
de ser gravado em novos uploads. Testado no navegador: slot renderiza sem o select, e um upload
simulado (Storage stubado) grava `comprovacao_mercado: { url }` sem erro.

**Ajuste ainda nesta sessão:** rótulo do slot renomeado de "Comprovação de mercado" para "Pesquisa
de mercado" (só o texto exibido — campo `comprovacao_mercado`, nomes de função
`_uploadComprovacaoMercado()`/`comprovacao-mercado-` do caminho no Storage continuam iguais).

**Ajuste ainda nesta sessão:** texto explicativo menor adicionado no slot "Recibo / Nota Fiscal"
("Sem rasuras e em nome da Unidade Gestora que fora concedido." — texto ajustado pela usuária
depois de uma 1ª versão mais longa, removendo a parte sobre atesto por servidor), mesmo padrão do
slot de Justificativa (4º argumento `descricao` de `_slotAnexoSimples()`). A parte removida
("por servidor que não o tomador") virou o texto explicativo do slot "Atesto" em vez de ficar no
Recibo/NF — mesmo mecanismo.

**Ajuste ainda nesta sessão:** nova biblioteca de "📚 Modelos de Documentos" (título encurtado
depois, sem o sufixo "(Justificativa/Atesto)") na página inicial de Prestação de Contas
(`#pc-lista-view`, card logo abaixo da lista de Prontos
Pagamentos) — a usuária queria manter modelos .docx de referência por categoria/serviço (ex: PJ →
lavagem de carro, passagem de lancha; Consumo → água mineral; PF → roçagem), com um modelo de
Justificativa **e** um de Atesto por serviço, sem precisar excluir/recriar pra mudar a lista. Doc
único `secoes/prestacao_contas_modelos` com 3 arrays (uma por categoria, mesmas chaves de
`PC_CATEGORIA_LABELS`) — mesmo padrão de config de seção única já usado em `secoes/plantao_info`
(`_plantaoCarregarInfo()`/`_plantaoSalvarInfo()`), carregado em `_pcCarregarModelos()` (chamado
dentro de `renderPrestacoesContas()`) e renderizado em `_renderModelosPrestacaoContas()`. Cada
serviço é `{servico, justificativa_url, justificativa_nome, atesto_url, atesto_nome}` — os dois
slots de arquivo são independentes (subir um não afeta o outro). Funções novas:
`pcAdicionarServicoModelo(categoria)` (prompt pro nome, mesmo padrão de `adicionarOutroDocumento()`),
`pcRemoverServicoModelo(categoria, idx)` (confirm + splice, mesmo padrão de `excluirDespesa()` —
não apaga arquivo já enviado do Storage) e `pcUploadModeloArquivo(categoria, idx, tipo, file)`
(reusa `_uploadParaStorage()`). Arquivos vão para
`prestacoes-contas/_modelos/{categoria}/{idx}-{tipo}-{timestamp}.ext` — cai dentro do path
`prestacoes-contas/{allPaths=**}` já admin-only em `storage.rules`, e o doc fica em `secoes/{id}`
(escrita admin-only, leitura de qualquer autenticado — mesmo nível de `plantao_info`/`adote_info`,
que também não são dados sensíveis) — nenhuma regra do Firestore/Storage precisou de redeploy.
Não mexe nos slots de Anexos por despesa já existentes (Justificativa/Atesto de cada despesa
continuam independentes da biblioteca de modelos — é só consulta/download de referência). Testado
no navegador com `db`/Storage stubados: card renderiza as 3 categorias vazias, "+ Novo serviço"
adiciona, upload marca só o slot certo como "✅ Anexado" (o outro continua "⚠️ Pendente"), e
remover serviço funciona com confirmação. Ver `docs/site/estrutura-html.md` (seção "Prestação de
Contas").

**Ajuste ainda nesta sessão:** dois modelos gerais adicionados no topo do card "Modelos de
Documentos", **fora** das categorias/serviços — "📝 Modelo de Memorando" e "📑 Modelo de Pesquisa
de Mercado" (aceita `.docx` **ou** `.xlsx`, diferente dos demais slots que só aceitam Word).
Decisão tomada via pergunta direta à usuária: Memorando não varia por serviço (é documento do
processo como um todo, igual ao "Memorando de encaminhamento" de `_renderDocumentosProcesso()`),
e Pesquisa de mercado também foi pedida como modelo único geral, não por serviço. Campos novos no
mesmo doc `secoes/prestacao_contas_modelos`: `memorando_url`/`memorando_nome`/
`pesquisa_mercado_url`/`pesquisa_mercado_nome` (irmãos dos 3 arrays de categoria, não dentro
deles). Nova função `pcUploadModeloGeral(campo, file)` (`campo` é `'memorando'` ou
`'pesquisa_mercado'`) e `_pcModeloGeralSlotHtml()` (reaproveita o CSS `.pc-anexo-slot` do modal de
Anexos por despesa, em vez do `.pc-modelo-slot` novo dos slots por serviço). Arquivos em
`prestacoes-contas/_modelos/_gerais/{campo}-{timestamp}.ext` — mesmo path-prefix admin-only, sem
redeploy. Testado no navegador: upload de Memorando marca só aquele slot como "✅ Anexado",
Pesquisa de Mercado continua "⚠️ Pendente" independente, e o `accept` do input inclui os 4 tipos
MIME de Excel além dos 2 de Word.

**Ajuste ainda nesta sessão:** modelo de Recibo adicionado, um por categoria (Consumo, Pessoa
Jurídica, Pessoa Física) — diferente de Memorando/Pesquisa de Mercado (gerais, um só no total) e
diferente de Justificativa/Atesto (por serviço individual dentro da categoria): o Recibo é
**por categoria**, aparece uma vez no topo de cada bloco (`_pcModeloReciboSlotHtml(categoria)`,
antes da lista de serviços daquela categoria). Dados em `_pcModelos.recibo` — objeto
`{pessoa_juridica: {url, nome}, consumo: {...}, pessoa_fisica: {...}}`, campo `recibo` no mesmo
doc `secoes/prestacao_contas_modelos`. Nova função `pcUploadModeloRecibo(categoria, file)` — sobe
o arquivo (só `.docx`, mesmo `PC_ACCEPT_DOCX`), clona `_pcModelos.recibo` inteiro (as 3
categorias) antes de mutar a chave da categoria alvo e salva o objeto `recibo` inteiro de volta
(mesmo cuidado de clonar-antes-de-mutar já usado em `despesas`/arrays de serviço). Path no Storage:
`prestacoes-contas/_modelos/{categoria}/recibo-{timestamp}.ext`. Testado no navegador: upload do
recibo de "Consumo" marca só aquela categoria como "✅ Anexado", "Pessoa Jurídica" continua
"⚠️ Pendente" — confirma que as 3 categorias são independentes.

## Estado atual (sessão 40 — 22/09/2026)

**Implementado nesta sessão:** visualização inline dos anexos no modal "Anexos" por despesa da
Prestação de Contas — a usuária queria ver o conteúdo do arquivo sem abrir nova guia, parecido com
anexo de e-mail. Modal alargado (`#modal-anexos-overlay` até 1200px) em duas colunas: lista de
anexos à esquerda, painel de visualização fixo à direita (`.pc-anexos-preview`). Clicar em "👁️
Visualizar" num slot (Justificativa/Pesquisa de mercado/Recibo/Atesto), numa foto da grade ou num
"outro documento" mostra o arquivo no painel (PDF em `<iframe>`, imagem em `<img>`, detectado pela
extensão da URL) com botão "⬇️ Baixar" (`fetch`+`blob`+`<a download>`, força download de verdade
mesmo em URL de outra origem) e "Abrir em nova guia" como *fallback*. O que fica selecionado é uma
chave (`_anexoPreviewCampo`, ex. `'recibo_url'`/`'foto:2'`), nunca a URL/nome literal — o painel
resolve o valor atual do Firestore a cada render, então continua certo depois de um upload
re-renderizar o modal (`_visualizarAnexoCampo()`/`_resolverPreviewAnexo()`/`_painelPreviewHtml()`
em `index.html`). Escopo combinado com a usuária: só esse modal — "Documentos do Processo" e
"Modelos de Documentos" continuam com "Abrir" (nova guia). Testado no navegador (servidor
estático, `userRole='admin'` + `db`/`storage` stubados): preview de PDF e imagem, download
disparando com nome sanitizado, painel atualizando sozinho após substituir um anexo que estava
sendo visualizado, reset do preview ao remover foto/documento com índice deslocado, e layout
empilhado em coluna única no celular (375px). Ver `docs/site/estrutura-html.md` (seção "Prestação
de Contas").

**Ajuste ainda nesta sessão:** proporção das duas colunas do modal de Anexos alterada a pedido da
usuária — lista de anexos reduzida para ~75% da largura original (`.pc-anexos-lista { flex: 3 }`),
dando mais espaço ao painel de visualização (`.pc-anexos-preview { flex: 5 }`), que era 50/50.

**Implementado ainda nesta sessão:** botão "🧷 Baixar anexos em 1 PDF" no modal de Anexos —
junta Justificativa + Pesquisa de mercado + Recibo/NF + Atesto num único PDF, nessa ordem fixa,
pulando qualquer um que não tenha anexo (`_baixarAnexosMerge()`, `_ANEXOS_ORDEM_MERGE` em
`index.html`). Precisou de uma biblioteca nova, **pdf-lib** (CDN, junto dos scripts de jsPDF) —
diferente do jsPDF já usado no site (só cria PDF novo a partir de texto/tabela), o pdf-lib copia
as páginas de um PDF já existente mantendo o conteúdo original e embute imagem como página nova,
o que permite juntar de verdade os arquivos que a usuária já anexou (não gera um PDF novo com o
conteúdo reescrito). Reaproveita `_resolverPreviewAnexo()` (já existente do preview inline) pra
resolver cada um dos 4 campos na ordem certa. Falha em 1 anexo (rede, arquivo corrompido) não
aborta o merge inteiro — só avisa em toast qual ficou de fora; só cancela de vez se nenhum dos 4
entrar no PDF final. Testado no navegador com PDFs/imagem reais gerados na hora (jsPDF + canvas
pra simular arquivo real, sem depender de rede): merge de 3 dos 4 anexos (sem Pesquisa de
mercado, replicando o caso mostrado pela usuária) gerando PDF de 4 páginas na ordem certa, caso
sem nenhum anexo (toast, sem gerar arquivo) e caso de 1 URL inválida (PDF sai só com os outros 2,
toast nomeia o que faltou). Ver `docs/site/estrutura-html.md` (seção "Prestação de Contas").

**Bug real encontrado e corrigido ainda nesta sessão:** a usuária testou o botão "Baixar anexos em
1 PDF" em produção e deu erro pros 3 anexos de uma vez ("Não foi possível juntar nenhum dos
anexos"), mesmo com a pré-visualização funcionando normalmente. Causa: o bucket do Storage
(`polo-medio-as.firebasestorage.app`) não tinha **CORS** configurado — `<img>`/`<iframe>`
carregam a URL de download normalmente (navegação de recurso, sem checagem de CORS), mas
`fetch()` em JS (usado tanto no "Baixar" individual quanto no merge) precisa que o bucket libere
explicitamente a origem do site pra JS conseguir ler a resposta. Confirmado lendo a config do
bucket (`bucket.cors` vinha `[]`) via `google-cloud-storage` com o
`firebase-service-account.json` já usado nos scripts de automação do repo. Corrigido aplicando
CORS pro bucket autorizando `https://lumabandeira.github.io` (produção) + `localhost:8123`/
`localhost:8765` (testes locais), método `GET`. Não é uma mudança de código — é config do bucket
no Google Cloud, não fica em nenhum arquivo do repositório (ao contrário de `storage.rules`).
Validado com um `fetch()` real no navegador contra um PDF de produção já existente (retornou
200 com o PDF de ~144KB, sem erro de CORS). Ver `docs/firebase.md` (seção "CORS do bucket").

**Implementado ainda nesta sessão:** arrastar e soltar arquivo (drag & drop) em todos os pontos de
upload do modal de Anexos (Justificativa/Pesquisa de mercado/Recibo/Atesto/Fotos/Outros
documentos), além do botão "Enviar" de sempre. 3 funções genéricas
(`_anexoDragOver`/`_anexoDragLeave`/`_anexoDrop(event, tipo, ref)` em `index.html`) que só
disparam a função de upload já existente certa conforme `tipo` — nenhuma função de upload mudou.
Texto "📥 ou arraste o arquivo aqui" em cada ponto pra avisar que dá pra soltar ali. Bug pego e
corrigido ainda durante o teste: o aviso de "só o 1º arquivo foi usado" (quando se solta mais de 1
arquivo num slot de arquivo único) inicialmente era sobrescrito na hora pelo toast "Enviando
arquivo..." da própria função de upload, porque os dois `mostrarToast()` rodavam no mesmo trecho
síncrono antes do 1º `await` — corrigido adiando esse aviso pra depois que a promise do upload
resolve. Rede de segurança contra `drop` fora de qualquer dropzone (que faria o navegador abrir o
arquivo numa aba, perdendo o modal): `preventDefault()` no container do modal, sem afetar as
dropzones específicas (que usam `stopPropagation()`). Testado no navegador com eventos
`drop`/`dragover`/`dragleave` sintéticos (`DataTransfer`/`File`, já que automação de navegador não
arrasta arquivo real do SO). Ver `docs/site/estrutura-html.md` (seção "Prestação de Contas").

**Ajuste estético ainda nesta sessão:** o bloco "Pendente"/"Enviar" (ou "Anexado"/"Visualizar"/
"Substituir") de cada slot de Anexos aparecia ora ao lado do título, ora embaixo dele, dependendo
do tamanho do texto do título — inconsistente entre os 4 slots. Causa: `.pc-anexo-slot-titulo`
([index.html:1169](polo-medio-amazonas/index.html:1169)) não tinha `flex-basis` definido dentro do
`.pc-anexo-slot` (flex com `wrap`), então o navegador só quebrava linha quando o título "sobrava"
espaço suficiente — dependia da largura real do texto. Corrigido com `flex: 1 0 100%` no título
(força ele a sempre ocupar a linha inteira sozinho, empurrando status+botões pra linha de baixo,
sempre juntos por causa do `justify-content: space-between` já existente no `.pc-anexo-slot`).
`.pc-anexo-slot-acoes` ganhou `flex-wrap: wrap; justify-content: flex-end` de segurança pros casos
com 2 botões (Visualizar + Substituir) em telas bem estreitas. Testado visualmente em duas larguras
diferentes de coluna — layout consistente nos 4 slots em ambas.

**Removido ainda nesta sessão:** bloco "📁 Documentos do Processo" (Memorando de encaminhamento,
Termo de Devolução, Comprovante de Devolução) do Detalhe de Prestação de Contas — a usuária disse
que nunca vai usar. Removidos `_renderDocumentosProcesso()`, `uploadDocumentoProcesso()` e o
container estático `#pc-detalhe-processo`; `_renderDetalhePrestacao()` não chama mais nada disso.
Só a UI saiu — os campos `memorando_url`/`termo_devolucao_url`/`comprovante_devolucao_url` de
`prestacoes_contas/{id}` continuam existindo no schema (zerados ao criar prestação nova em
`salvarPrestacao()`) e registros antigos que já tinham algum preenchido não foram limpos, só
deixaram de ser exibidos/editáveis — mesmo padrão de "só oculta, não migra" já usado antes (sessão
39, Recibo por categoria). Cuidado pra não confundir com `_pcModelos.memorando_url`/
`pesquisa_mercado_url` (campos de mesmo nome só na parte, mas de outra seção — biblioteca "Modelos
de Documentos" — que não foi tocada). Testado no navegador: Detalhe renderiza sem erro e sem
nenhum rastro de "Documentos do Processo" (confirmado via busca por texto na página, não só no
código). Ver `docs/site/estrutura-html.md` (seção "Prestação de Contas").

## Estado atual (sessão 39 — 21/09/2026)

**Implementado nesta sessão:** ajuste na biblioteca de "📚 Modelos de Documentos" (sessão 38) — o
slot "🧾 Modelo de Recibo" por categoria (adicionado na sessão anterior em Consumo, Pessoa
Jurídica **e** Pessoa Física) passou a aparecer **só em Pessoa Física**, a pedido da usuária.
Mudança de uma linha em `_renderModelosPrestacaoContas()`: a chamada de
`_pcModeloReciboSlotHtml(categoria)` agora é condicional a `categoria === 'pessoa_fisica'`. Os
campos `recibo.consumo`/`recibo.pessoa_juridica` continuam existindo no doc
`secoes/prestacao_contas_modelos` caso já tivessem sido preenchidos (nenhuma limpeza de dados foi
necessária — nenhum arquivo real havia sido enviado ainda nessas duas categorias), só deixaram de
ser exibidos/editáveis pela UI. Testado no navegador: card renderiza só 1 "Modelo de Recibo" na
página inteira, dentro do bloco de Pessoa Física. Ver `docs/site/estrutura-html.md` (seção
"Prestação de Contas").

## Estado atual (sessão 37 — 09/09/2026)

**Implementado nesta sessão:** destaque em vermelho da linha "Aplicação" nos cards e no Detalhe
de Prestação de Contas quando o prazo final de aplicação já venceu. Novo helper
`_pcAplicacaoVencida(p)` — `true` quando `p.data_fim_aplicacao` (`YYYY-MM-DD`) < hoje **e**
`p.status !== 'concluido'` (num pronto pagamento concluído o vencimento é esperado, não é alerta).
Quando `true`, a linha ganha a classe `.pc-aplic-vencida` (label + valor em `#ef4444`) e o sufixo
`⚠ prazo encerrado`, tanto em `_renderListaPrestacoesCards()` quanto no `.pc-info-grid` de
`_renderDetalhePrestacao()`. CSS novo junto de `.pc-card-linha` (perto de `index.html:1141`). Só
exibição — não entra no PDF nem no Firestore. Testado no navegador (servidor estático) montando o
markup exato dos dois pontos: classe aplicada, as 3 cores viram vermelho e a tag aparece só no
caso vencido-e-aberto; helper confere `true` só para vencido+aberto (não concluído, não futuro,
não sem data). Ver `docs/site/estrutura-html.md` (seção "Prestação de Contas").

## Estado atual (sessão 36 — 24/08/2026)

**Implementado nesta sessão:** 4 campos opcionais de "Unidade Gestora Concedente" (Órgão/CNPJ,
Banco, Agência, Conta) no modal "Novo/Editar Pronto Pagamento" (`prestacoes_contas/{id}`),
pré-preenchidos com os dados fixos da DPE/AM (constante `PC_UG_CONCEDENTE_PADRAO`) mas editáveis.
Também exibidos (somente leitura) no bloco de informações gerais do Detalhe — ajuste pedido
ainda na mesma sessão, depois de inicialmente restringir ao formulário. Ainda não entram no PDF.

Também removido o campo redundante "Valor Recebido" do formulário — tudo padronizado para
`valor_concedido` único (form, cards, Detalhe, PDF, cálculo de saldo), com fallback
`_pcValorConcedido(p)` para os registros antigos que só têm `valor_recebido` gravado. Os dados bancários (Banco/Agência/Conta) da Unidade Gestora Concedente saíram da exibição do
Detalhe (só "Órgão/CNPJ" continua ali) mas seguem no cadastro. E tirada a linha "Data do
Recebimento" do cabeçalho do PDF exportado (segue no formulário e no Detalhe). Ver
`docs/historico-sessoes.md` (sessão 36) e `docs/site/estrutura-html.md`/`docs/firebase.md` para
o detalhamento completo.

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

**Ajuste (mesmo dia):** usuária pediu pra tirar o campo "Número da Portaria" do formulário de
Viagens, deixando só o link — a tabela deve sempre mostrar o rótulo extraído automaticamente da
URL. Removido `portaria_numero` de Viagens (HTML do form, `_viagensAbrirForm()`,
`_viagensSalvarEvento()`); `_viagensPortariaHtml(ev)` simplificada pra sempre usar
`_rotuloEdicaoDiario(ev.portaria_url)`, sem override manual — diferente de Plantão, que manteve
o campo de override por decisão anterior da usuária. Testado: campo some do form, tabela mostra
"📄 Edição NNNN" corretamente.

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
- **Bugfix pendente:** escape de HTML no campo "Editar link" do topo do Plantão
  (`_plantaoCarregarInfo()`, `linkEl.innerHTML = ...` em `index.html`, perto de
  `index.html:9057-9064`) — `nome` e `url` de `secoes/plantao_info` entram direto no HTML sem
  `esc()`/`_escAttr()`, mais grave que o bug de aspas no `href` já corrigido na sessão 35 (aqui
  dá pra injetar tag inteira, não só quebrar o atributo). Bug antigo, não introduzido na sessão
  35 — só notado ao corrigir os outros links de portaria do Plantão.
- **Bugfix pendente:** o mesmo bug de duplicação por clique-prematuro no seed do Plantão (corrigido
  na sessão 35 — ver `plantaoCarregouUmaVez` / revalidação direta no Firestore em
  `_plantaoImportarSeed()`) também existe em Viagens e Eventos: `_viagensImportarSeed(n)`
  (`index.html:9911-9932`) e o botão de seed em `renderViagensEventos()` só checam
  `_viagensEventos[n].length` (estado em memória), sem confirmar com uma leitura real do
  Firestore antes de gravar — mesma janela de corrida que causou a duplicação real no Plantão.
  Ainda não corrigido.

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
