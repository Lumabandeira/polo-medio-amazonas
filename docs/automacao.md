# Automação do Diário Oficial

## Projeto 1 — removido (sessão 50, 15/10/2026)

O antigo `verificar-diario-oficial.py` (workflow `verificar-diario.yml`, 06:00 Manaus) lia o DO,
gravava afastamentos em `afastamentos_admin` e avisos em `remocoes_admin` e
`designacoes_cumulativas_admin` (campo `origem: "automacao-diario-oficial"`), exibidos nos 3
sinos da barra de abas de Designações. Removido a pedido da usuária: os sinos não eram usados
(decisão anterior das sessões 26/30: pouco confiáveis). Script, workflow, `criar-tarefa-agendada.ps1`,
sinos, painéis e funções JS saíram; **os dados no Firestore foram preservados** (os 2
afastamentos gravados pela automação continuam no calendário como qualquer outro). Afastamentos,
remoções e designações agora são cadastrados só à mão; o Projeto 2 continua mostrando as
portarias no Diário Oficial do site. Secret `FIREBASE_SERVICE_ACCOUNT` ficou sem uso no GitHub;
`ANTHROPIC_API_KEY` continua (fallback do Projeto 2).

---

## Projeto 2 — Diário Completo (`verificar-diario-completo.py`)

**Objetivo:** detectar **todas** as portarias relevantes ao polo (defensores, servidores, cidades) e atualizar `docs/diario-oficial-completo-2026.json`.

**Quando roda:** diariamente às **04:00 de Manaus** (08:00 UTC) via `.github/workflows/verificar-diario-completo.yml`.

**API key:** `ANTHROPIC_API_KEY_COMPLETO` (limite mensal: $5,00) (cai em `ANTHROPIC_API_KEY` se a dedicada não existir).

**Não precisa de `FIREBASE_SERVICE_ACCOUNT`** — sem escrita no Firestore.

### Termos-gatilho

1. `"Polo\s+(?:do\s+)?Médio\s+Amazonas"`
2. Cidades: Itacoatiara, São Sebastião do Uatumã, Itapiranga, Urucurituba, Urucará, Silves
3. Servidores (primeiro+segundo nome): Luma Karolyne, Fábio Bastos, Natália Cristina, Arnoud Lucas, Larice Bruce
4. Titulares vigentes (carregados de `designacoes-2026.json` — entrada sem `fim`; Projeto 2 **não** lê `titulares_admin`, então o JSON precisa estar atualizado). Nomes aceitam com e sem acento, inclusive maiúsculas (`_palavra_sem_acento_regex()`: Ênio/Enio/ENIO)

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

### Filtro pós-Claude: viagens fora do polo (sessão 44)

O pré-filtro casa pelo **nome** de qualquer titular vigente, e o Haiku acabava incluindo
portarias em que um integrante do polo só aparece viajando para trabalhar **em outro polo**.
Caso real: Edição 2739 (25/09/2026), Portarias 1744 e 1746/2026-GDPG — deslocamento/transporte
da Thays (titular da 2ª DP, mas designada cumulativamente no Polo Rio Negro-Solimões até 30/09)
no trecho Manacapuru/Novo Airão, ainda marcadas com a categoria `comarca` sem nenhuma cidade do
polo no texto. Correção em duas camadas:

1. **Prompt:** instrui a não incluir atos de deslocamento/transporte/diárias para fora do polo
   e a usar `comarca` só com uma das 6 cidades do polo.
2. **`filtrar_portarias_fora_do_polo()`** (determinístico, roda sobre a resposta do Claude antes
   de gravar no JSON): descarta a portaria quando o texto (número + trechos + resumo) é de
   logística de viagem (`deslocamento`/`transporte`/`diárias`), **não** cita "Polo Médio
   Amazonas" nem cidade do polo e **não** é ato de lotação (designação, substituição, férias,
   afastamento, remoção, licença, folga, plantão — esses continuam entrando mesmo com destino em
   outro polo, porque mudam quem atende aqui). Também tira `comarca` quando nenhuma cidade do polo
   aparece.
3. **Citação obrigatória (sessão 44, 2º ajuste):** a portaria só entra se o texto exato
   (número + trechos — o `resumo` não conta, porque o Claude às vezes inventa ligação com o
   polo) casar com algum termo-gatilho: nome do polo, cidade do polo, servidor ou titular
   vigente. O prompt exige que os trechos tragam a frase/linha de anexo que faz essa citação.

   **Exceções (atos de interesse geral, `TERMOS_RELEVANCIA_GERAL`, definidas pela usuária):**
   nomeação/exoneração de Defensor(a)/Subdefensor(a) Público(a) Geral; designação/delegação de
   Ordenador(a) de Despesas; atos do ciclo inteiro do "Adote uma Comarca"; qualquer ato do
   "Expandir Presença"; escala de substituição entre polos; resolução trimestral de metas e
   critérios de elegibilidade do CSDPEAM (meritocracia — sessão 50, caso real: Resolução
   40/2026-CSDPEAM, Edição 2742, que o prompt antigo ignorava por não ser portaria nem citar o
   polo; vai com a categoria `meta_trimestral`, filtro "🎯 Meritocracia" no site). Também entram
   como termo-gatilho no pré-filtro e no prompt.
   `termos_integrantes_na_data(data)` acrescenta quem era titular na data da edição (ex.: Elton
   até 02/05/2026) — usado no fluxo diário e na revisão do histórico.

   **Limpeza do histórico com essas regras (28/09/2026):** 52 portarias removidas do JSON depois de
   conferência da usuária em 4 lotes (outra sessão do mesmo dia já tinha tirado 23 só de outros polos).

A mesma regra foi aplicada ao histórico do JSON: 11 portarias de viagem fora do polo removidas
(edições 2643, 2657, 2660, 2666, 2684, 2716 e 2739) e `comarca` retirada das que não citavam
cidade do polo.

**Outros polos (sessão 44, 3º ajuste):** a Portaria 1733/2026-GDPG (Edição 2737, GT das
comarcas satélite) tinha entrado como "Polo Médio" porque o texto do PDF misturou uma tabela de
nomes com o inciso de outra portaria ("Polo do Médio Lucena Solimões") e o Claude confundiu
Médio Solimões com o nosso polo. A citação obrigatória (item 3) já a descarta; o prompt passou a
listar os outros polos (Médio Solimões, Médio Madeira, Baixo Amazonas…) e a pedir para não juntar
incisos de portarias vizinhas. Histórico: removidas mais 23 portarias só de outros polos (lista
conferida pela usuária), incluindo 571 e 779 (Pedro Henrique no Médio Solimões antes de vir para
o polo) — essas duas passariam pelo filtro atual, porque o nome dele hoje é termo-gatilho.

### Categorias só da lista (sessão 50)

`normalizar_categorias()`, chamada em `filtrar_portarias_fora_do_polo()`, tira acento/maiúsculas
("estágio" → `estagio`) e descarta qualquer categoria fora de `CATEGORIAS_VALIDAS` (com log).
Motivo: a IA inventou "estágio" na Portaria 426/2026 (Edição 2658), que virou botão de filtro sem
rótulo no site. Além disso, `estagio` e `residencia_juridica` são garantidas pelo texto
(número + trechos + resumo), mesmo que a IA esqueça: `_RE_CAT_RESIDENCIA` ("Residência Jurídica",
"Residente Jurídico") tem prioridade; `_RE_CAT_ESTAGIO` casa estágio/estagiário mas não
"estágio probatório" (e não casa "Presidente"). **Ao criar categoria nova, atualizar os três lugares:** `CATEGORIAS_VALIDAS`, a
lista do prompt e `CAT_LABELS` + `.cat-<nome>` no `index.html` (e `docs/diario-oficial-categorias.md`).

### Escala de plantão do Polo → CSV (sessão 44)

`extrair_escala_plantao_polo(pdf_bytes, data_pub)` lê, **sem Claude** (determinístico, custo
zero), a tabela da escala de plantão do interior (colunas = semanas `"09) 24/08 a 30/08"`, às
vezes com ano; cada polo = linhas Cível e de Família / Criminal e de Custódia / Assessoria) e
grava as semanas do Polo Médio Amazonas em `plantao_polo` da edição:
`[{data_inicio, data_fim, defensor, assessoria}]` (ISO; defensor = Plantão Cível e de Família,
com "(F)" preservado). Roda em toda edição processada; se achar escala, cria/atualiza a entrada
da edição mesmo sem portaria detectada pelo Claude. O site mostra como CSV
`DD/MM/AAAA;DD/MM/AAAA;defensor;assessoria` com botão "📋 Copiar CSV" (Plantão → Importar CSV).
Acima do CSV, a portaria da escala: `extrair_portaria_escala_plantao()` (também sem Claude) grava
em `plantao_polo_portaria` = `{numero, texto}` — o cabeçalho "PORTARIA Nº …" (maiúsculas, início
de linha; não as portarias citadas nos CONSIDERANDOs) e o 1º inciso do RESOLVE, aceitando
"ESTABELECER a escala de plantão … do interior …" ou "ALTERAR a Portaria … nos seguintes termos"
seguido de "Plantão do Polo …". Lê a página inteira e, se não achar, coluna por coluna (o
extract_text() mistura as 2 colunas em algumas edições). Motivo: o resumo do Claude na Edição
2739 inventou o número (1747, inexistente no PDF — a certa é 1011; corrigida à mão no JSON).

Armadilhas do PDF tratadas (todas vistas em edições reais): bloco do polo quebrando de página
(estado carregado entre tabelas); nome do polo ausente na 1ª coluna quando o bloco cai no fim da
página (deduzido pela ordem fixa dos polos — quem vem depois de "Polo do Madeira" etc.); linha
do topo da página seguinte sem borda superior, que o pdfplumber deixa fora da tabela
(`_linha_orfa_acima()`, remonta pelas colunas da tabela a partir das palavras); nome quebrado
em 2 linhas; colunas extras vazias (`_valores_semanas()`); linha Cível extraída antes do
cabeçalho de semanas; colunas estreitas que partem palavras no meio sem hífen ("Eliaqui|m",
"Amazo|nas", "28/0|9" — Edição 2739), remendadas em `_texto_celula()` quando a junção forma
palavra conhecida do vocabulário tirado do próprio JSON do DO + designações
(`_vocabulario_nomes()`). Validado nas edições 2644, 2660, 2686, 2714, 2731 e 2739 (backfill já feito) —
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
| `verificar-diario-completo.py` | Projeto 2 — todas portarias → JSON |
| `backfill-calendario-do-estruturado.py` | Backfill histórico do DO |
| `limpar-backfill.py` | Limpeza de registros duplicados/fragmentados |
| `.github/workflows/verificar-diario-completo.yml` | Workflow do Projeto 2 (04:00 Manaus) |
| `docs/.estado-diario-completo.json` | Estado do Projeto 2 (gitignored, cache do Actions) |
| `docs/diario-oficial-completo-2026.json` | Saída do Projeto 2 (commitado) |
