# Firebase — Configuração e Estrutura

## Projeto

- **Project ID:** `polo-medio-as`
- **Console:** https://console.firebase.google.com/project/polo-medio-as
- **Serviços ativos:** Firebase Auth + Firestore

---

## Autenticação (Firebase Auth)

- Login por e-mail/senha
- 44 usuários: 3 admins + 41 viewers
- **Admins cadastrados:** `bandeira.lkp@gmail.com` (Luma) e `fabiobastos@defensoria.am.def.br` (Fábio Bastos)

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
- Coleções protegidas: `usuarios`, `secoes`, `afastamentos_admin`, `titulares_admin`, `remocoes_admin`, `designacoes_cumulativas_admin`, `afastamentos_equipe`

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
| `loadAfastamentosFirestore()` | Carrega `afastamentos_admin` e mescla com JSON |
| `loadEquipeFirestore()` | Carrega `afastamentos_equipe` |
| `carregarNotificacoesAutomacao()` | Carrega as 3 coleções de notificações (try/catch independentes) |
| `get_firestore_client()` | Python — inicializa Firebase Admin SDK |
