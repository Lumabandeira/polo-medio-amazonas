# Automação do Diário Oficial

## Projeto 1 — Afastamentos de Titulares (`verificar-diario-oficial.py`)

**Objetivo:** detectar afastamentos dos defensores titulares do polo e gravar em `afastamentos_admin` no Firestore.

**Quando roda:** diariamente às **06:00 de Manaus** (10:00 UTC) via `.github/workflows/verificar-diario.yml`.

**API key:** `ANTHROPIC_API_KEY` (limite mensal: $2,00)

**Modelo:** `claude-sonnet-4-5-20251001`

### Fluxo

1. Scrape da página pública do Diário Oficial da DPE/AM
2. Comparação com `automacao_config/estado_diario` no Firestore (+ arquivo local `.estado-diario.json` em cache do Actions como acelerador)
3. Para cada edição nova: baixa PDF → extrai texto com `pdfplumber`
4. **Pré-filtro por termos-gatilho** — busca `"Polo (do) Médio Amazonas"` + primeiro+segundo nome de cada titular vigente. Se nenhum termo aparece, pula (custo zero). Carregados dinamicamente de `designacoes-2026.json` + `titulares_admin` via `inicializar_defensores_e_termos()`.
5. Extrai janelas de ±1500 chars em volta de cada menção → envia ao Claude com prompt JSON
6. Claude retorna 3 arrays: `afastamentos`, `cessacoes`, `designacoes_cumulativas`
7. Grava em Firestore:
   - `afastamentos_admin` via `salvar_afastamentos_firestore()`
   - `remocoes_admin` (cessações) via `salvar_cessacoes_firestore()`
   - `designacoes_cumulativas_admin` via `salvar_designacoes_cumulativas_firestore()`
8. Atualiza `automacao_config/estado_diario` via `save_state()`

### Dedup

- **Afastamentos:** por `(defensor, data_inicio, data_fim, tipo)`
- **Cessações:** por `(tipo, portaria_cessada)`
- **Designações cumulativas:** por `(defensor_abrev, dp_designada, data_inicio)`

### Mapeamento de substitutos

- Nome bate com titular do polo → `substituto: "abrev"`, `substituto_nome_externo: ""`
- Não bate → `substituto: "_outro"`, `substituto_nome_externo: "Nome completo"`

### Persistência de estado (corrigido na sessão 24)

O estado (`ultima_edicao`) é salvo em dois lugares:
- **Arquivo local** `docs/.estado-diario.json` — cacheado no GitHub Actions (expira após 7 dias)
- **Firestore** `automacao_config/estado_diario` — backup permanente, usado quando o cache expira

### Sinos no site

| Coleção | Sino | Cor do painel |
|---------|------|--------------|
| `afastamentos_admin` (automação) | `#btn-sino` | Azul |
| `remocoes_admin` | `#btn-sino-remocao` | Âmbar |
| `designacoes_cumulativas_admin` | `#btn-sino-designacao` | Verde |

### Secrets necessários (GitHub)

| Secret | Obrigatório | Uso |
|--------|------------|-----|
| `ANTHROPIC_API_KEY` | ✅ | Chamadas ao Claude |
| `FIREBASE_SERVICE_ACCOUNT` | ✅ | Escrita no Firestore |
| `SMTP_REMETENTE` | ⬜ | E-mail de resumo |
| `SMTP_SENHA_APP` | ⬜ | E-mail de resumo |
| `SMTP_DESTINATARIO` | ⬜ | E-mail de resumo |

### Rodar localmente

```bash
py -m pip install firebase-admin requests pdfplumber beautifulsoup4 anthropic
set ANTHROPIC_API_KEY=sk-ant-...
py verificar-diario-oficial.py
```
Requer `firebase-service-account.json` na raiz (gitignored).

---

## Projeto 2 — Diário Completo (`verificar-diario-completo.py`)

**Objetivo:** detectar **todas** as portarias relevantes ao polo (defensores, servidores, cidades) e atualizar `docs/diario-oficial-completo-2026.json`.

**Quando roda:** diariamente às **04:00 de Manaus** (08:00 UTC) via `.github/workflows/verificar-diario-completo.yml`.

**API key:** `ANTHROPIC_API_KEY_COMPLETO` (limite mensal: $5,00) — separado do Projeto 1 para rastrear custos independentemente.

**Não precisa de `FIREBASE_SERVICE_ACCOUNT`** — sem escrita no Firestore.

### Termos-gatilho (mais amplos que o Projeto 1)

1. `"Polo\s+(?:do\s+)?Médio\s+Amazonas"`
2. Cidades: Itacoatiara, São Sebastião do Uatumã, Itapiranga, Urucurituba, Urucará, Silves
3. Servidores (primeiro+segundo nome): Luma Karolyne, Fábio Bastos, Natália Cristina, Arnoud Lucas, Larice Bruce
4. Titulares vigentes (carregados do JSON)

### Extração de texto — tabelas (sessão 44)

O DO é diagramado em 2 colunas e `page.extract_text()` do pdfplumber **mistura as colunas de
uma tabela com a coluna de texto ao lado**, picotando frases ("Polo do / Médio Médio /
Amazonas"). Com isso nem o termo-gatilho casa nem o Claude entende a linha. Caso real: Edição
2734 (18/09/2026), Anexo I da Portaria 1708/2026-GDPG (7º Concurso de Remoção) — a remoção de
Pedro Henrique Pereira Paiva para a 6ª DP do Polo não foi detectada, e a do Miguel saiu com
origem/destino invertidos. Correção: `extract_pdf_text()` (nos **dois** projetos) acrescenta ao
texto de cada página as tabelas via `page.extract_tables()` (`_tabelas_da_pagina()`), uma linha
por registro com células separadas por ` | `, entre `[TABELA — pág. N]` e `[FIM DA TABELA]`. O
prompt do Projeto 2 explica esse formato ao Claude (cada linha que envolva o polo, respeitando
origem → destino; em caso de conflito, confiar na tabela).

### Escala de plantão do Polo → CSV (sessão 44)

`extrair_escala_plantao_polo(pdf_bytes, data_pub)` lê, **sem Claude** (determinístico, custo
zero), a tabela da escala de plantão do interior (colunas = semanas `"09) 24/08 a 30/08"`, às
vezes com ano; cada polo = linhas Cível e de Família / Criminal e de Custódia / Assessoria) e
grava as semanas do Polo Médio Amazonas em `plantao_polo` da edição:
`[{data_inicio, data_fim, defensor, assessoria}]` (ISO; defensor = Plantão Cível e de Família,
com "(F)" preservado). Roda em toda edição processada; se achar escala, cria/atualiza a entrada
da edição mesmo sem portaria detectada pelo Claude. O site mostra como CSV
`DD/MM/AAAA;DD/MM/AAAA;defensor;assessoria` com botão "📋 Copiar CSV" (Plantão → Importar CSV).

Armadilhas do PDF tratadas (todas vistas em edições reais): bloco do polo quebrando de página
(estado carregado entre tabelas); nome do polo ausente na 1ª coluna quando o bloco cai no fim da
página (deduzido pela ordem fixa dos polos — quem vem depois de "Polo do Madeira" etc.); linha
do topo da página seguinte sem borda superior, que o pdfplumber deixa fora da tabela
(`_linha_orfa_acima()`, remonta pelas colunas da tabela a partir das palavras); nome quebrado
em 2 linhas; colunas extras vazias (`_valores_semanas()`); linha Cível extraída antes do
cabeçalho de semanas. Validado nas edições 2644, 2660, 2686, 2714 e 2731 (backfill já feito) —
a 2686 bate 100% com o seed da Portaria 764 (`PLANTAO_SEED_2026`).

### Saída

`docs/diario-oficial-completo-2026.json` — lido diretamente pelo site via `fetch()`. Commitado automaticamente pelo workflow quando há portarias novas.

### Estado

`docs/.estado-diario-completo.json` — cache independente no Actions.

---

## Backfill histórico (`backfill-calendario-do-estruturado.py`)

Script para popular retroativamente o Firestore a partir de `docs/diario-oficial-completo-2026.json`.

**Executado em:** 17–18/04/2026. **Resultado:** 8 registros genuínos no Firestore.

**Quando reexecutar:** sempre que `diario-oficial-completo-2026.json` for atualizado com edições antigas. O script é idempotente.

**Uso:**
```bash
py backfill-calendario-do-estruturado.py           # dry-run
py backfill-calendario-do-estruturado.py --commit  # grava no Firestore
py limpar-backfill.py --commit                     # limpa fragmentações após o backfill
```

**Limitação conhecida:** revogações detectadas são removidas do plano em memória antes de gravar — não são aplicadas retroativamente a registros já no Firestore. Revisar manualmente se necessário.

---

## Arquivos-chave

| Arquivo | Descrição |
|---------|----------|
| `verificar-diario-oficial.py` | Projeto 1 — afastamentos → Firestore |
| `verificar-diario-completo.py` | Projeto 2 — todas portarias → JSON |
| `backfill-calendario-do-estruturado.py` | Backfill histórico do DO |
| `limpar-backfill.py` | Limpeza de registros duplicados/fragmentados |
| `.github/workflows/verificar-diario.yml` | Workflow do Projeto 1 (06:00 Manaus) |
| `.github/workflows/verificar-diario-completo.yml` | Workflow do Projeto 2 (04:00 Manaus) |
| `docs/.estado-diario.json` | Estado do Projeto 1 (gitignored, cache do Actions) |
| `docs/.estado-diario-completo.json` | Estado do Projeto 2 (gitignored, cache do Actions) |
| `docs/diario-oficial-completo-2026.json` | Saída do Projeto 2 (commitado) |
