# Firebase — Configuração e Estrutura

## Projeto

- **Project ID:** `polo-medio-as`
- **Console:** https://console.firebase.google.com/project/polo-medio-as
- **Serviços ativos:** Firebase Auth + Firestore

---

## Autenticação (Firebase Auth)

- Login por e-mail/senha
- 47 usuários: 5 admins + 42 viewers
- **Admins cadastrados:** `bandeira.lkp@gmail.com` (Luma) · `fabiobastos@defensoria.am.def.br` (Fábio Bastos) · `eniojunior@defensoria.am.def.br` (Ênio Jorge Lima Barbalho Junior) · `miguelfilho@defensoria.am.def.br` (Miguel Eduardo de Azevedo Martins Filho)

### Como adicionar novos usuários

Firebase Console → Authentication → Adicionar usuário → copiar UID → Firestore → coleção `usuarios` → novo documento com o UID → campos `role` ("admin" ou "viewer") e `nome`.

### Fluxo de login no site

1. Página carrega → overlay de login cobre tudo
2. Usuário digita e-mail + senha → Firebase Auth valida
3. Site lê `role` em `usuarios/{uid}`
4. Admin: badge "ADMIN" + botões ✏️ Editar visíveis
5. Viewer: site normal sem botões de edição

---

## Estrutura do Firestore

### `usuarios/{uid}`
```
role: "admin" | "viewer"
nome: "..."
```

### `secoes/{id}` — conteúdo editável das seções

| doc | campos |
|-----|--------|
| `regra_alternancia` | `html`, `atualizado_por`, `atualizado_em` |
| `ferias_folgas` | `html`, `atualizado_por`, `atualizado_em` |
| `atribuicoes_resolucao` | `url`, `nome`, `atualizado_por`, `atualizado_em` |
| `atribuicoes_celulas` | `celulas` (mapa `"N_campo": { html, cellStyle }`), `atualizado_por`, `atualizado_em` |
| `adote_info` | `html` (cabeçalho), `atualizado_por`, `atualizado_em` |
| `adote_celulas` | `celulas` (mapa `"ROW_COL": { html, cellStyle }`), `atualizado_por`, `atualizado_em` |
| `adote_expandir` | `html`, `atualizado_por`, `atualizado_em` |
| `plantao_info` | `nome`, `url` (link da portaria, opcional), `atualizado_por`, `atualizado_em` — se vazio, cai no texto padrão `PLANTAO_INFO_PADRAO` no `index.html` |

### `viagens_tabela1_admin/{id}` — Eventos e Próximas Viagens Previstas
```
data_inicio:    "YYYY-MM-DD"
data_fim:       "YYYY-MM-DD"   ← igual a data_inicio quando é um evento de 1 dia só
membro:         "Eliaquim e Natália"
motivo:         "Atendimentos presenciais e sessões do Tribunal do Júri em Urucurituba"
criado_por:     "email@..."
criado_em:      timestamp
atualizado_por: "email@..."
atualizado_em:  timestamp
```

### `viagens_tabela2_admin/{id}` — Viagens Trimestrais
```
local:          "Urucurituba"   ← um dos 6 municípios do Polo, ou texto livre (opção "Outro" no form)
data_inicio:    "YYYY-MM-DD"
data_fim:       "YYYY-MM-DD"
motivo:         "..."
membro:         "..."
criado_por / criado_em / atualizado_por / atualizado_em: idem acima
```

Ambas coleções alimentam o Calendário e a Lista da seção "🧳 Viagens e Eventos" a partir da
mesma fonte — ver `docs/site/estrutura-html.md`. Regra do Firestore: `allow write: if
isAdmin()` (leitura já coberta pela regra genérica de qualquer coleção).

### `titulares_admin/{dpKey}` — histórico de titulares por DP
```
historico_titulares: [
  { defensor: "icaro", inicio: "2026-01-01", fim: null,
    portaria_entrada: "...", do_entrada: "https://...",
    portaria_saida: null, do_saida: null }
]
atualizado_por: "email@..."
atualizado_em: timestamp
```
- `fim: null` = titular ativo
- `fim: ''` = entrada histórica em branco (ainda não preenchida)
- `fim: 'YYYY-MM-DD'` = histórico com data
- **Lacuna (nenhuma entrada cobrindo uma data, ex: última entrada com `fim` preenchido e
  nada cadastrado depois) = DP vaga a partir dali.** `getTitularForDPOnDay()` retorna `null`
  nesse caso (corrigido na sessão 31 — antes retornava `undefined` e caía num fallback
  estático que reexibia o titular "natural" antigo da DP, mesmo já ex-membro).

### `defensores_admin/{defKey}` — override de status ativo/ex-membro
```
ativo:          false   ← ou true (reativação de quem já era ativo=false no JSON base)
atualizado_por: "email@..."
atualizado_em:  timestamp
```
- `defKey` é a mesma chave usada em `jsonDesignacoes.defensores` (ex: `icaro`). Só se aplica a
  defensores já cadastrados nesse dicionário — não afeta titulares "livres" (texto digitado direto
  em `titulares_admin`), que já viram ex-membro automaticamente quando perdem a última DP ativa.
- **Armadilha do campo "Nome do defensor" no modal Titulares por DP:** o texto digitado só vira a
  chave (`eliaquim`, etc.) se bater **exatamente** (case-insensitive) com `defensores[k].nome` ou
  `nome_curto` do `docs/designacoes-2026.json` já carregado no navegador (`_resolverDefensor()` em
  `index.html`). Se o texto não bater — nome digitado com erro de grafia, ou o navegador ainda com
  o JSON antigo em cache no momento do salvamento — o valor é gravado como **texto livre** no
  Firestore. O card resultante perde o seletor 🟢 Membro / ⚪ Ex-membro (vira "titular livre",
  `isOrphan: true` em `index.html`), mesmo mostrando o nome certo. Sintoma: card sem a caixinha de
  status ao lado do nome. Correção: reabrir "Titulares por DP" na(s) DP(s) afetada(s) e reescrever
  o nome exatamente igual ao do dicionário (com o navegador já com o JSON atualizado em cache).
- Documento só existe quando um admin altera o status pelo site (dropdown 🟢 Membro / ⚪ Ex-membro na
  seção Defensores Públicos). Ausência do doc = usa o campo `ativo` do JSON estático como padrão.
- Marcar como ex-membro **não** remove o defensor de nenhuma DP — isso continua sendo feito
  separadamente em `titulares_admin` (seção "Titulares por DP").

### `afastamentos_admin/{id}` — afastamentos de defensores
```
defensor:         "elton"
tipo:             "ferias" | "folga" | "licenca_especial" | "trabalho_remoto" | "outro"
tipo_custom:      ""
data_inicio:      "YYYY-MM-DD"
data_fim:         "YYYY-MM-DD"
processo_tipo:    "SEI" | "SGI" | ""
processo_sei:     "25.0.000..."
portaria_numero:  "Portaria nº .../2026-GSPG/DPE/AM"
portaria_url:     "https://..."
designacoes_dp: [
  { dp: "5",
    substitutos: [
      { substituto: "eliaquim" | "_outro" | "",
        substituto_nome_externo: "",
        data_inicio: "YYYY-MM-DD",
        data_fim: "YYYY-MM-DD",
        portaria_numero: "...",
        portaria_url: "..." }
    ]
  }
]
criado_por:     "automacao@github-actions" | "email@..."
origem:         "automacao-diario-oficial"   ← só na automação
lido:           false   ← false = aparece no sino azul
precisa_revisao: true   ← quando data_fim vazia
```
> **`tipo: "trabalho_remoto"`** (exibido na UI como "💻 Trabalho em Trânsito") é especial: **não é
> ausência**. Sempre grava `designacoes_dp: []` (a UI oculta a seção "Defensorias Afetadas" para
> esse tipo) e é tratado à parte no merge dos dados no `index.html` — não entra em
> `afastamentos[ano][mes][dia]` nem aparece em "Lista de Substituições"/"Resumo de Afastamentos",
> só no Calendário (badge transparente). Ver `docs/site/estrutura-html.md` (seção "Trabalho em
> Trânsito") para o detalhamento completo.

### `afastamentos_equipe/{id}` — afastamentos dos servidores
```
nome:         "Natália"
tipo:         "ferias" | "folga" | "outro"
tipo_custom:  ""
data_inicio:  "YYYY-MM-DD"
data_fim:     "YYYY-MM-DD"
ano:          2026
criado_por:   "email@..."
criado_em:    timestamp
```

### `plantao_admin/{id}` — escala de plantão do polo (período/defensor/assessoria)
```
data_inicio:  "YYYY-MM-DD"
data_fim:     "YYYY-MM-DD"
defensor:     "Eliaquim Antunes de Souza Santos"   ← texto livre, nem sempre um dos 6 titulares
assessoria:   "Larice Bruce Pereira"                ← texto livre
lote_nome:         ""   ← opcional. Nome da leva de períodos (ex: "3º Trimestre 2026") — agrupa a tabela
portaria_numero:   ""   ← opcional. Override manual do rótulo do link (padrão: "Edição NNNN", extraído da URL)
portaria_url:      ""   ← opcional. Link da portaria própria do período (vazio = usa a geral de plantao_info)
alteracao_numero:  ""   ← opcional. Override manual do rótulo do link de alteração (idem)
alteracao_url:     ""   ← opcional. Só preenchido se este período foi alterado por portaria pontual
alteracao_obs:     ""   ← opcional. Texto curto livre — vira tooltip do badge de alteração
criado_por:   "email@..."
criado_em:    timestamp
atualizado_por / atualizado_em   ← só em edições
```
- `lote_nome`/`portaria_numero`/`portaria_url` são preenchidos pelo formulário de 1
  período **e** pelo "Importar CSV" (campos únicos aplicados a todo o lote colado).
  `alteracao_*` só pelo formulário de 1 período (exceção pontual). Ver "Plantão" em
  `docs/site/estrutura-html.md` para a lógica de agrupamento por lote
  (`_plantaoAgruparPorLote()`) e de prioridade de exibição do link
  (`_plantaoLinkPortariaHtml()`).
- Cadastro 100% manual pelo admin — sem IA, sem automação (decisão da sessão
  26, depois que as automações com sino de notificação se mostraram pouco
  confiáveis). Duas vias no site: formulário de 1 período, ou colar texto CSV
  (`data_inicio;data_fim;defensor;assessoria`) para importar vários de uma vez.
- `PLANTAO_SEED_2026` (constante em `index.html`) guarda os 13 períodos
  extraídos da Portaria nº 764/2026-GSPG/DPE/AM — importados uma única vez via
  botão que só aparece enquanto a coleção está vazia.

### `remocoes_admin/{id}` — alterações de titularidade (automação)
```
tipo:              "cessacao_designacao"   ← ausente = concurso de remoção
portaria_numero:   "Portaria nº 602/2026-GDPG/DPE/AM"
portaria_cessada:  "Portaria nº 206/2026-GSPG/DPE/AM"
portaria_url:      "https://..."
concurso:          "Concurso de Remoção nº 1/2026"
data_vigencia:     "2026-05-02"
saindo:  [{ dp: "1", defensor: "Nome completo" }]
chegando: [{ dp: "1", defensor: "Nome completo" }]
origem:   "automacao-diario-oficial"
lido:     false   ← false = aparece no sino âmbar
edicao_do: "2640"
data_publicacao: "2026-04-15"
```

### `designacoes_cumulativas_admin/{id}` — designações cumulativas sem data fim
```
defensor_nome:    "Eliaquim Antunes de Souza Santos"
defensor_abrev:   "eliaquim"
dp_designada:     "9"
data_inicio:      "2026-05-04"
portaria_numero:  "Portaria nº .../2026-..."
portaria_url:     "https://..."
processo_sei:     "..."
origem:           "automacao-diario-oficial"
lido:             false   ← false = aparece no sino verde
edicao_do:        "2650"
data_publicacao_do: "2026-05-06"
```

### `prestacoes_contas/{id}` — Prestação de Contas (prontos pagamentos, admin-only)
```
tomador:                  "Fábio Bastos de Souza"
categoria:                "consumo" | "pessoa_juridica" | "pessoa_fisica"
status:                   "aberto" | "concluido"   ← controla o limite de 2 simultâneos por tomador
processo_sei:             "26.0.000000661-0"
valor_recebido:           4000
valor_concedido:          4000
data_recebimento:         "YYYY-MM-DD"
data_inicio_aplicacao:    "YYYY-MM-DD"
data_fim_aplicacao:       "YYYY-MM-DD"
prazo_prestacao_contas:   "YYYY-MM-DD"
memorando_url:            "https://firebasestorage..." | null
termo_devolucao_url:      "https://firebasestorage..." | null
comprovante_devolucao_url:"https://firebasestorage..." | null
despesas: [
  { tipo: "Recibo" | "Nota Fiscal", numero: "1", data_emissao: "YYYY-MM-DD",
    fornecedor: "...", descricao: "...", quantidade: 1, valor_unitario: 80, valor_total: 80,
    recibo_url: "https://..." | null,
    comprovacao_mercado: { tipo: "pesquisa" | "justificativa_ausencia", url: "https://..." } | null,
    justificativa_url: "https://..." | null,
    atesto_url: "https://..." | null,
    fotos_urls: ["https://...", ...],
    outros_documentos: [{ nome: "...", url: "https://..." }]
  }
]
criado_por / atualizado_por: "email@..."
criado_em / atualizado_em:   timestamp
```
- **Regra de negócio (client-side, em `_validarCategoriaDisponivel()`):** um mesmo `tomador` pode
  ter no máximo 2 documentos com `status: "aberto"` ao mesmo tempo, e as categorias desses 2
  precisam ser diferentes entre si. Marcar como `"concluido"` libera a vaga.
- **Segurança:** diferente de todas as outras coleções (que liberam leitura a qualquer autenticado),
  `prestacoes_contas` tem leitura **e** escrita restritas a `isAdmin()` — expõe CPF e dados
  bancários via `comprovante_devolucao_url`. Ver `firestore.rules` e `storage.rules`.
- **Storage:** arquivos em `prestacoes-contas/{id}/despesas/{idx}/{campo}-{timestamp}.{ext}` e
  `prestacoes-contas/{id}/{memorando|termo_devolucao|comprovante_devolucao}-{timestamp}.{ext}`.

### `automacao_config/estado_diario` — estado da automação (Projeto 1)
```
ultima_edicao:       2680   ← número da última edição processada
edicoes_processadas: [2640, 2641, ...]
atualizado_em:       timestamp
```
> Criado na sessão 24 como backup permanente do `.estado-diario.json` (que vivia só no cache do Actions).

---

## Regras de Segurança do Firestore

- **Leitura:** apenas usuários autenticados
- **Escrita:** apenas usuários com `role == "admin"`
- Coleções protegidas: `usuarios`, `secoes`, `afastamentos_admin`, `titulares_admin`, `defensores_admin`, `remocoes_admin`, `designacoes_cumulativas_admin`, `afastamentos_equipe`, `plantao_admin`
- **Exceção:** `prestacoes_contas` tem leitura **e** escrita restritas a admin (não apenas escrita) — ver acima.

## Regras de Segurança do Storage

- Bucket `polo-medio-as.firebasestorage.app`, regras em `storage.rules`.
- `prestacoes-contas/**`: leitura e escrita restritas a `isAdmin()` (checa `usuarios/{uid}.role` via `firestore.get()`).
- Qualquer outro caminho: bloqueado por padrão (`allow read, write: if false`).

---

## Funções JS relacionadas ao Firebase

| Função | O que faz |
|--------|----------|
| `fazerLogin()` | Autentica com Firebase Auth |
| `fazerLogout()` | Encerra sessão |
| `carregarConteudoFirestore()` | Carrega seções editáveis (com cache localStorage) |
| `iniciarEdicao(secaoId)` | Ativa contentEditable + monta toolbar RTE |
| `salvarSecao(secaoId)` | Salva HTML no Firestore |
| `loadTitularesFirestore()` | Carrega `titulares_admin` e mescla com JSON base |
| `loadDefensoresAdminFirestore()` | Carrega `defensores_admin` e mescla `ativo` no dicionário `defensores` |
| `alterarStatusDefensor(selectEl)` | Grava override em `defensores_admin/{defKey}` a partir do `<select>` 🟢 Membro / ⚪ Ex-membro |
| `loadAfastamentosFirestore()` | Carrega `afastamentos_admin` e mescla com JSON |
| `loadEquipeFirestore()` | Carrega `afastamentos_equipe` |
| `loadPlantaoFirestore()` | Carrega `plantao_admin`, ordena por `data_inicio` |
| `salvarPlantaoFirestore()` / `confirmarDeletarPlantao()` | CRUD de 1 período via formulário modal |
| `_plantaoParseCSV()` / `_plantaoConfirmarImportacaoCsv()` | Importação em lote via texto CSV colado (parsing 100% local, sem IA) |
| `carregarNotificacoesAutomacao()` | Carrega as 3 coleções de notificações (try/catch independentes) |
| `get_firestore_client()` | Python — inicializa Firebase Admin SDK |
| `renderPrestacoesContas()` | Carrega `prestacoes_contas` e renderiza a lista de cards (admin-only) |
| `salvarPrestacao()` / `_validarCategoriaDisponivel()` | Cria/edita um pronto pagamento, validando o limite de 2 abertos por tomador |
| `salvarDespesa()` / `excluirDespesa()` | CRUD de linhas do Mapa Demonstrativo dentro do array `despesas[]` |
| `abrirModalAnexos()` / `_uploadSlotSimples()` / `uploadFotos()` / `adicionarOutroDocumento()` | Upload de anexos por despesa para o Firebase Storage |
| `uploadDocumentoProcesso()` | Upload dos 3 documentos do processo (Memorando, Termo/Comprovante de Devolução) |
| `baixarMapaPDF()` | Gera e baixa o Mapa Demonstrativo em PDF (jsPDF + AutoTable, ver `docs/site/estrutura-html.md`) |
