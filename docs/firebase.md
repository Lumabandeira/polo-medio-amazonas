# Firebase — Configuração e Estrutura

## Projeto

- **Project ID:** `polo-medio-as`
- **Console:** https://console.firebase.google.com/project/polo-medio-as
- **Serviços ativos:** Firebase Auth + Firestore

---

## Autenticação (Firebase Auth)

- Login por e-mail/senha
- 46 usuários: 5 admins + 41 viewers
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

### `defensores_admin/{defKey}` — override de status ativo/ex-membro
```
ativo:          false   ← ou true (reativação de quem já era ativo=false no JSON base)
atualizado_por: "email@..."
atualizado_em:  timestamp
```
- `defKey` é a mesma chave usada em `jsonDesignacoes.defensores` (ex: `icaro`). Só se aplica a
  defensores já cadastrados nesse dicionário — não afeta titulares "livres" (texto digitado direto
  em `titulares_admin`), que já viram ex-membro automaticamente quando perdem a última DP ativa.
- Documento só existe quando um admin altera o status pelo site (dropdown 🟢 Membro / ⚪ Ex-membro na
  seção Defensores Públicos). Ausência do doc = usa o campo `ativo` do JSON estático como padrão.
- Marcar como ex-membro **não** remove o defensor de nenhuma DP — isso continua sendo feito
  separadamente em `titulares_admin` (seção "Titulares por DP").

### `afastamentos_admin/{id}` — afastamentos de defensores
```
defensor:         "elton"
tipo:             "ferias" | "folga" | "licenca_especial" | "outro"
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
- Coleções protegidas: `usuarios`, `secoes`, `afastamentos_admin`, `titulares_admin`, `defensores_admin`, `remocoes_admin`, `designacoes_cumulativas_admin`, `afastamentos_equipe`
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
| `carregarNotificacoesAutomacao()` | Carrega as 3 coleções de notificações (try/catch independentes) |
| `get_firestore_client()` | Python — inicializa Firebase Admin SDK |
| `renderPrestacoesContas()` | Carrega `prestacoes_contas` e renderiza a lista de cards (admin-only) |
| `salvarPrestacao()` / `_validarCategoriaDisponivel()` | Cria/edita um pronto pagamento, validando o limite de 2 abertos por tomador |
| `salvarDespesa()` / `excluirDespesa()` | CRUD de linhas do Mapa Demonstrativo dentro do array `despesas[]` |
| `abrirModalAnexos()` / `_uploadSlotSimples()` / `uploadFotos()` / `adicionarOutroDocumento()` | Upload de anexos por despesa para o Firebase Storage |
| `uploadDocumentoProcesso()` | Upload dos 3 documentos do processo (Memorando, Termo/Comprovante de Devolução) |
| `baixarMapaPDF()` | Gera e baixa o Mapa Demonstrativo em PDF (jsPDF + AutoTable, ver `docs/site/estrutura-html.md`) |
