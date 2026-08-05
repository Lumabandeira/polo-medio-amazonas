# Estrutura do Site (index.html)

> Atualizado em 14/06/2026 — reflete sessões 1–24

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
| 📋 Designações | `#designacoes` | `showSection('designacoes')` |
| ⛱️ Férias Equipe | `#equipe` | `showSection('equipe')` |
| 🏘️ Adote | `#adote` | `showSection('adote')` |
| 🚨 Plantão | `#plantao` | `showSection('plantao')` → `renderPlantao()` |
| 📰 Diário Oficial | `#diario` | `showSection('diario')` |
| 💰 Prestação de Contas | `#prestacao-contas` | `showSection('prestacao-contas')` — **admin-only**, botão fica `display:none` para viewers |

## Abas dentro da seção Designações (`#designacoes`)

| ID da aba | Nome | Função de render |
|-----------|------|-----------------|
| `defensorias` | 📋 Defensorias | `renderDefensorias()` |
| `designacoes-semanais` | 📅 Designações semanais | `renderDesignacoes()` |
| `calendario` | 📅 Calendário | `renderCalendar()` |
| `lista-substituicoes` | 📋 Lista de Substituições | `renderListaSubstituicoes()` |
| `detalhes` | 📊 Resumo de Afastamentos | `renderDetalhesAfastamentos()` |

> ⚠️ A aba "Tabela Completa" foi **removida** em sessão anterior. O Calendário Visual é a aba principal de ausências.

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
| `detalhesAfastamentos[ano][mes][dia]` | JSON + Firestore mesclados | modal de detalhes |
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

**Decisão da sessão 26:** sem IA e sem automação de PDF. As automações
existentes (sinos de notificação de afastamentos/remoções/designações
cumulativas) não têm se mostrado confiáveis na prática, então o cadastro de
Plantão é 100% manual, com duas vias:

- **Um período por vez** — botão "➕ Novo período" → modal (`abrirFormPlantao`,
  `salvarPlantaoFirestore`) idêntico em espírito ao modal de Férias Equipe.
- **Vários de uma vez** — botão "📋 Importar CSV" → cola texto (uma linha por
  período, `data_inicio;data_fim;defensor;assessoria`, aceita `;`, Tab ou `,`
  como separador) → `_plantaoParseCSV()` faz o parsing 100% local (sem rede,
  sem IA) → pré-visualização com linhas ok/erro → confirma e grava em lote.
- **Migração inicial**: `PLANTAO_SEED_2026` guarda os 13 períodos extraídos da
  Portaria nº 764/2026-GSPG/DPE/AM; um botão "⬇️ Importar dados iniciais"
  aparece só enquanto `plantao_admin` está vazia e grava esse seed uma única vez.

Cache local: `pma-plantao-fs` (docs brutos de `plantao_admin`, mesmo padrão de
`pma-equipe-fs`).

## Prestação de Contas (`#prestacao-contas`, admin-only)

Seção inteira restrita a admin: o botão da landing (`#btn-prestacao-contas`) nasce com `display:none`
e só é revelado em `_aplicarModoEdicao()`. `showSection('prestacao-contas')` também expulsa
qualquer usuário não-admin de volta para `atribuicoes` como segunda camada de proteção.

- **Lista** (`#pc-lista-view`): cards agrupados por tomador, um card por "pronto pagamento" (adiantamento).
  Cada tomador pode ter no máximo **2 prontos pagamentos com `status: "aberto"` simultâneos**,
  em categorias diferentes entre si (`consumo` | `pessoa_juridica` | `pessoa_fisica`) — regra
  aplicada em `_validarCategoriaDisponivel()` antes de salvar ou reabrir.
- **Detalhe** (`#pc-detalhe-view`): réplica do "Mapa Demonstrativo de Despesa" (planilha em papel
  usada pela Defensoria) — tabela de despesas com totais calculados automaticamente (valor das
  despesas, saldo remanescente), mais os 3 documentos do processo como um todo (Memorando,
  Termo de Devolução, Comprovante de Devolução).
- **Anexos por despesa**: modal com 5 slots fixos (Recibo/NF, Comprovação de mercado — pesquisa
  *ou* justificativa de ausência, Justificativa da despesa, Atesto, Fotos) + lista livre de
  "Outros documentos". Upload vai para Firebase Storage em `prestacoes-contas/{prestacaoId}/...`;
  a URL de download fica salva no array `despesas[]` do documento Firestore.
- Ver `docs/firebase.md` para o schema completo de `prestacoes_contas/{id}` e as regras de
  segurança (mais restritas que o padrão do site: leitura **e** escrita admin-only, por causa de
  CPF/dados bancários nos comprovantes de devolução).
- **Exportar em PDF**: botão "📄 Baixar Mapa (PDF)" no cabeçalho do detalhe, função `baixarMapaPDF()`.
  Usa jsPDF + jsPDF-AutoTable (CDN, `jspdf.umd.min.js` + `jspdf.plugin.autotable.min.js`) para gerar
  uma página A4 paisagem replicando o layout em papel: bloco de cabeçalho, barra "COMPROVANTE DE
  DESPESA" desenhada manualmente acima da tabela (em vez de `colSpan`/`rowSpan` no `head` do
  AutoTable), tabela de despesas e rodapé de totais. Validado com PDF real baixado e aberto no
  Chrome (fornecedor com nome longo quebrando em 3 linhas, valores corretos, sem sobreposição).
  Nota: durante o desenvolvimento, a ferramenta de inspeção de PDF usada para conferir o layout
  mostrou um artefato de renderização que não existe no arquivo real — se for depurar isso de novo,
  confie no PDF baixado de verdade, não na pré-visualização.

## Cache localStorage (elimina flash de dados)

| Chave | Conteúdo |
|-------|---------|
| `pma-regra-alternancia` | HTML da seção Regra de Alternância |
| `pma-ferias-folgas` | HTML da seção Férias/Folgas/Licenças |
| `pma-atr-celulas` | células JSON de Atribuições |
| `pma-adote-celulas` | células JSON de Adote |
| `pma-adote-expandir` | HTML do bloco Expandir |
| `pma-plantao-fs` | docs brutos de `plantao_admin` |
| `pma-afastamentos-fs` | docs brutos de `afastamentos_admin` |
| `pma-equipe-fs` | docs brutos de `afastamentos_equipe` |
| `pma-secao` | última seção visitada (restaura na recarga) |
