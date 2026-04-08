# Regras de Ausências (Férias, Folgas e Licenças)

## Limites

- **Máximo de 2 defensores ausentes simultaneamente**
- **Mínimo de 3 defensores ativos** deve ser mantido sempre
- Distribuição máxima ideal: 12 DPs ÷ 3 defensores = 4 DPs por defensor

## Tipos de Ausência

| Símbolo | Tipo | Classe CSS | Descrição |
|---------|------|-----------|-----------|
| 🔵 | Férias | `tipo-ferias` | Período de férias regulares |
| 🟡 | Folga | `tipo-folga` | Folga programada |
| 🟢 | Licença Especial | `tipo-licenca` | Licença especial (com processo SEI) |
| — | Não informado | `tipo-folga` | Tipo não identificável pelo diário |

---

## ⚠️ HABILIDADE CRÍTICA: Leitura de Diário Oficial para Atualizar a Tabela Completa

### Contexto

Os diários oficiais da DPE/AM publicam **portarias de designação** de substitutos. Essas portarias mencionam apenas o **substituto** (quem cobre) e a **DP**, mas **nunca mencionam explicitamente quem está ausente**. O defensor ausente deve ser inferido.

---

### INSUMOS OBRIGATÓRIOS ANTES DE COMEÇAR

Antes de executar qualquer passo, você **precisa ter em mãos**:

| # | Insumo | Por que é necessário |
|---|--------|---------------------|
| 1 | **PDF do diário oficial** (link ou arquivo) | Fonte das portarias a analisar |
| 2 | **Lista atual da Tabela Completa** (ver formato abaixo) | Sem ela, é impossível saber se uma entrada já existe (Passo 5) |
| 3 | **`docs/defensorias/lista-completa.md`** | Para identificar o defensor ausente (Passo 3) |

> ⛔ **Se a Lista atual da Tabela Completa não for fornecida, NÃO execute a análise.** Responda: *"Preciso receber o conteúdo atual da Tabela Completa para verificar duplicatas. Por favor, forneça-o antes de continuar."*

#### Como fornecer a Tabela Completa ao Sonnet

Não é necessário passar o HTML do site. Basta colar o conteúdo do arquivo:

> **`Tabela de Férias e Folgas.md`**

Esse arquivo `.md` já contém todas as entradas existentes em formato de tabela legível (Período | Defensor | Tipo | Defensoria | Substituto | Processo), e é exatamente o que o Sonnet precisa para executar o Passo 5. Cole o conteúdo completo do arquivo antes de pedir a análise do diário.

---

### PASSO A PASSO OBRIGATÓRIO

#### PASSO 1 — Filtrar somente portarias do Polo Médio Amazonas

O diário contém portarias de vários polos (Baixo Amazonas, Juruá, Médio Solimões, Capital etc.). **Ignorar tudo que não seja "Polo do Médio Amazonas".**

Como identificar: procurar no texto das portarias a expressão **"Polo do Médio Amazonas"** ou **"Polo Médio Amazonas"**.

Exemplos de texto **relevante**:
> "para atuar na 5ª Defensoria Pública do **Polo do Médio Amazonas**"

Exemplos de texto **ignorar**:
> "para atuar na 5ª Defensoria Pública do Polo do Baixo Amazonas"
> "para atuar na 3ª Defensoria Pública do Polo do Juruá"
> "para atuar na 25ª Defensoria Pública de 1ª Instância Criminal" ← Capital, ignorar

---

#### PASSO 2 — Extrair os dados de cada item da portaria

Para cada inciso (I, II, III…) de uma portaria relevante, extrair:

| Campo | Onde encontrar no texto |
|-------|------------------------|
| **Substituto** | Nome após "DESIGNAR, cumulativamente, o/a Defensor(a) Público(a) [Nome]" |
| **DP** | Número após "para atuar na Xª Defensoria Pública do Polo do Médio Amazonas" |
| **Período** | Após "no período de [data] a [data]" ou "nos dias [lista]" |
| **Processo SEI** | No "CONSIDERANDO o teor do processo SEI n." ou "SGI n." |
| **Link do Diário** | URL do PDF do diário utilizado |

---

#### PASSO 3 — Identificar o defensor ausente (CRÍTICO)

O diário **NÃO informa** quem está ausente. Para descobrir:

1. Pegar o número da DP (ex: "5ª DP")
2. Consultar `docs/defensorias/lista-completa.md`
3. Encontrar o **Defensor Titular** daquela DP

**Tabela de referência rápida:**

| DP | Defensor Titular (ausente) |
|----|--------------------------|
| 1ª DP | Ícaro Oliveira Avelar Costa |
| 2ª DP | José Antônio Pereira da Silva |
| 3ª DP | Ícaro Oliveira Avelar Costa |
| 4ª DP | Eliaquim Antunes de Souza |
| 5ª DP | Elton Dariva Staub |
| 6ª DP | Elaine Maria Sousa Frota |
| 7ª DP | Elaine Maria Sousa Frota |
| 8ª DP | José Antônio Pereira da Silva |
| 9ª DP | Eliaquim Antunes de Souza |
| 10ª DP | José Antônio Pereira da Silva |
| 11ª DP | Ícaro Oliveira Avelar Costa |
| 12ª DP | Elton Dariva Staub |

> ⚠️ **Atenção:** Se o substituto for o próprio titular da DP, algo está errado — revisar a leitura da portaria.

---

#### PASSO 4 — Determinar o tipo de ausência

O diário **raramente informa** se é férias, folga ou licença. Regras (em ordem de prioridade):

1. Se o processo SEI/SGI já constar na Tabela Completa com um tipo → usar o mesmo tipo
2. Se a portaria mencionar "licença" no "CONSIDERANDO" → usar `🟢 Licença Especial`
3. Se houver outra linha na Tabela Completa com **mesmo defensor + mesma DP** e período adjacente ou contíguo → herdar o tipo dessa linha
4. Se não houver informação suficiente → usar **`🟡 Não informado`** com classe `tipo-folga`

> **Nunca inventar o tipo.** Usar "Não informado" somente quando as regras 1–3 não se aplicarem.

---

#### PASSO 5 — Verificar se o período já existe e decidir a ação

> ⚠️ Este passo só é possível se a Lista atual da Tabela Completa foi fornecida (ver "Insumos Obrigatórios"). Se não foi, interrompa e solicite antes de continuar.

Procurar na lista fornecida uma entrada com **os três critérios abaixo simultaneamente**:

1. Mesmo **defensor ausente**
2. Mesma **DP**
3. Período **idêntico ou sobreposto**

> ### 🚫 REGRA ABSOLUTA — NUNCA USE O TIPO COMO CRITÉRIO DE COMPARAÇÃO
>
> O campo **tipo** (🔵 Férias / 🟡 Folga / 🟢 Licença Especial / 🟡 Não informado) **NUNCA deve ser comparado** para decidir se uma entrada já existe ou não.
>
> **Motivo:** o diário quase nunca informa o tipo. Ao ler um diário, o Sonnet quase sempre atribuirá "Não informado". Se o tipo fosse usado como critério, ele encontraria uma entrada `🔵 Férias` na tabela, concluiria que é "diferente" de "Não informado", e criaria uma linha duplicada errada.
>
> **Exemplo concreto (ERRADO × CERTO):**
> - Tabela tem: `23-30/01 | Elton Dariva | 🔵 Férias | 5ª DP | Elaine Maria`
> - Diário designa: Elaine Maria para 5ª DP, período 23-30/01
> - ❌ ERRADO: "O tipo do diário seria 🟡 Não informado, que é diferente de 🔵 Férias → CRIAR"
> - ✅ CERTO: "Mesmo defensor + mesma DP + mesmo período → IGNORAR (o tipo é irrelevante)"
>
> **Regra simples:** compare apenas **defensor ausente + DP + período**. O tipo é invisível para fins de comparação.

---

##### Como decidir entre COMPLETAR e SOBRESCREVER

Encontrou uma linha com mesmo defensor ausente + mesma DP + período idêntico ou sobreposto? Faça apenas uma pergunta:

> **O campo Substituto na linha da tabela está vazio (em branco, `-`, ou `—`)?**
> - **Sim, está vazio** → **COMPLETAR** (preencher o substituto em branco)
> - **Não, já tem um nome preenchido** → **SOBRESCREVER** (substituir pelo nome do diário)

Nunca use SOBRESCREVER para uma linha que já tem o substituto correto. Nunca use COMPLETAR para uma linha que já tem um nome diferente.

---

#### ⚠️ VERIFICAR COBERTURA — Passo obrigatório sempre que o período não coincidir exatamente

**Execute esta verificação em todos os casos em que o período do diário não coincidir exatamente com uma única linha da tabela.** Isso inclui: quando nenhuma linha é encontrada, quando o período do diário é maior ou menor que o de uma linha encontrada, e quando o diário agrupa dias que a tabela divide em linhas separadas.

> ⛔ **NUNCA vá direto para CRIAR ou SOBRESCREVER sem antes executar VERIFICAR COBERTURA.** A ausência de uma linha com período idêntico não significa que os dias estão descobertos — eles podem estar cobertos por múltiplas linhas menores.

**Como executar:**

1. Reúna todas as linhas da tabela com **mesmo defensor ausente + mesma DP**
2. Liste todos os dias do período informado pelo diário
3. Para cada dia, localize qual linha candidata cobre esse dia (cujo período contém a data)
4. Classifique a ação para cada grupo de dias consecutivos conforme a tabela:

| Situação de cada dia | Ação |
|----------------------|------|
| Coberto por linha com **mesmo substituto** do diário | **→ IGNORAR** esses dias |
| Coberto por linha com substituto **vazio** | **→ COMPLETAR** aquela linha |
| Coberto por linha com substituto **diferente** (ambos preenchidos) | **→ SOBRESCREVER** aquela linha |
| **Não coberto** por nenhuma linha | **→ CRIAR** nova linha para esses dias |

5. Se a ação recair sobre apenas **parte** de uma linha existente (o diário cobre menos dias do que a linha), aplicar **DIVIDIR** antes de COMPLETAR ou SOBRESCREVER — ver explicação abaixo.

> ⚠️ Linhas com tipos diferentes (🟡 Folga e 🔵 Férias) ainda contam como cobertura. O tipo **nunca** é critério de comparação.

---

**Exemplo 1 — Diário agrupa dias que a tabela divide em linhas separadas:**
- Diário informa: Eliaquim substitui Elton na 5ª DP de **20 a 22/01**
- Tabela tem: `20/01 | Elton | 🟡 Folga | 5ª DP | Eliaquim` e `21-22/01 | Elton | 🔵 Férias | 5ª DP | Eliaquim`
- Verificação: dia 20 → coberto (mesmo substituto); dias 21-22 → cobertos (mesmo substituto)
- Resultado: **IGNORAR** — todos os dias já estão cobertos

**Exemplo 2 — Período do diário ultrapassa o fim de uma linha:**
- Diário informa: Elton substitui Eliaquim na 4ª DP de **31/01 a 05/02**
- Tabela tem: `26/01-04/02 | Eliaquim | 🔵 Férias | 4ª DP | Elton` e `05/02 | Eliaquim | 🟡 Folga | 4ª DP | (vazio)`
- Verificação: dias 31/01–04/02 → cobertos com mesmo substituto → IGNORAR; dia 05/02 → coberto com substituto vazio → COMPLETAR
- Resultado: **COMPLETAR** apenas a linha `05/02` (não alterar a linha `26/01-04/02`)

---

Com base no resultado, seguir a tabela-resumo:

| Situação encontrada | Ação |
|---------------------|------|
| Período do diário coincide exatamente com linha + mesmo substituto | **→ IGNORAR** |
| Período do diário coincide exatamente com linha + substituto vazio | **→ COMPLETAR** |
| Período do diário coincide exatamente com linha + substituto diferente | **→ SOBRESCREVER** |
| Qualquer outra situação (sem correspondência exata) | **→ VERIFICAR COBERTURA** (ver acima) |

---

##### Como Dividir uma linha (sub-caso de VERIFICAR COBERTURA)

Ocorre quando o período do diário cobre **apenas parte** de uma linha existente (o diário começa ou termina no meio do período de uma linha). A linha existente precisa ser dividida em dois trechos:

| Trecho | O que fazer |
|--------|------------|
| **Parte coberta** pelo diário | Ajustar o período + COMPLETAR ou SOBRESCREVER conforme o caso |
| **Parte não coberta** | Criar nova linha com o trecho restante, mantendo os dados originais (inclusive substituto vazio se for o caso) |

**Exemplo:**
- Tabela tem: `22/01-03/02 | José Antônio | 🔵 Férias | 8ª DP | (vazio)`
- Diário designa: Ícaro para 8ª DP de **22/01 a 30/01**

Resultado após a divisão:
```
22/01-30/01 | José Antônio | 🔵 Férias | 8ª DP Itapiranga | Ícaro Oliveira Avelar Costa  ← COMPLETAR
31/01-03/02 | José Antônio | 🔵 Férias | 8ª DP Itapiranga | (vazio)                      ← manter como estava
```

> ⚠️ Ao dividir, **nunca alterar o tipo** da linha original. Ambos os trechos herdam o tipo da linha que foi dividida.

---

##### Como Completar uma linha existente (substituto vazio)

Localizar a linha `<tr>` no `index.html` e preencher **apenas os campos que estão vazios** (`-` ou sem conteúdo):

| Campo | O que fazer |
|-------|------------|
| **Substituto** (5ª coluna) | Inserir o nome do substituto |
| **Diário** (6ª coluna) | Inserir o link do diário que designa o substituto |
| **Processo SEI** (7ª coluna) | Inserir o número do processo, se diferente do já existente |
| **Tipo, Período, Defensor, DP** | **Não alterar** — manter o que já está |

> ⚠️ Se o campo já tem valor (mesmo que diferente do diário), não é um caso de COMPLETAR — é SOBRESCREVER (ver abaixo).

---

##### Como Sobrescrever uma linha existente

Localizar a linha `<tr>` exata no `index.html` e substituí-la integralmente pela versão corrigida.

Os campos que podem mudar ao sobrescrever:

| Campo | O que atualizar |
|-------|----------------|
| **Substituto** (5ª coluna `<td>`) | Novo nome do substituto |
| **Tipo** (3ª coluna `<td>`) | Classe CSS e emoji, se o novo diário esclarecer o tipo |
| **Diário** (6ª coluna `<td>`) | Link do diário mais recente (que faz a correção) |
| **Processo SEI** (7ª coluna `<td>`) | Número do processo do novo diário |
| **Período** (1ª coluna `<td>`) | Ajustar se o período também mudou |

> ⚠️ **Nunca criar uma linha duplicada** quando a intenção é corrigir uma existente. A Tabela Completa deve ter no máximo uma linha por combinação defensor ausente + DP + período.

---

##### Exemplo de Sobrescrita

**Situação:** A tabela já tem esta linha:
```html
<tr><td>20-30/01</td><td><strong>Elton Dariva</strong></td><td><span class="tipo-badge tipo-folga">🟡 Não informado</span></td><td>5ª DP Criminal</td><td>Eliaquim Antunes de Souza</td><td>-</td><td>SGI 2500800</td></tr>
```

**Novo diário informa:** Elaine Maria substitui Elton na 5ª DP de 23 a 30/01 (período parcialmente diferente).

**Ação:** O período 20-30/01 precisa ser dividido:
- 20-22/01 → Eliaquim (linha existente, ajustar período)
- 23-30/01 → Elaine Maria (linha nova)

**Resultado após a edição:**
```html
<tr><td>20-22/01</td><td><strong>Elton Dariva</strong></td><td><span class="tipo-badge tipo-folga">🟡 Não informado</span></td><td>5ª DP Criminal</td><td>Eliaquim Antunes de Souza</td><td>-</td><td>SGI 2500800</td></tr>
<tr><td>23-30/01</td><td><strong>Elton Dariva</strong></td><td><span class="tipo-badge tipo-folga">🟡 Não informado</span></td><td>5ª DP Criminal</td><td>Elaine Maria Sousa Frota</td><td><a href="URL_DIARIO" target="_blank">Edição 2572 - 14/01/2026</a></td><td>26.0.000000008-5</td></tr>
```

---

#### PASSO 6 — Criar a nova linha HTML na Tabela Completa

Localizar no `index.html` a seção da Tabela Completa (buscar por `Tabela Completa de Férias e Folgas`). Inserir dentro do `<tbody>` correspondente ao período.

**Modelo HTML de uma linha:**

```html
<tr>
  <td>DD/MM-DD/MM</td>
  <td><strong>Nome do Defensor Ausente</strong></td>
  <td><span class="tipo-badge tipo-ferias">🔵 Férias</span></td>
  <td>Xª DP NomeDaDP</td>
  <td>Nome do Substituto</td>
  <td><a href="URL_DO_DIARIO" target="_blank">Edição XXXX - DD/MM/AAAA</a></td>
  <td>26.0.000000XXX-X</td>
</tr>
```

**Substituições de tipo:**

| Tipo | Classe CSS | Emoji + Texto |
|------|-----------|---------------|
| Férias | `tipo-ferias` | `🔵 Férias` |
| Folga | `tipo-folga` | `🟡 Folga` |
| Licença Especial | `tipo-licenca` | `🟢 Licença Especial` |
| Não informado | `tipo-folga` | `🟡 Não informado` |

**Formato do período:**
- Um dia: `20/01`
- Vários dias seguidos: `20-22/01`
- Cruzando meses: `31/01-03/02`

---

#### PASSO 7 — Repetir para cada item (I, II, III…)

Cada inciso da portaria = uma verificação completa do Passo 5 + ação correspondente (criar ou sobrescrever).

**Exemplo:** Portaria com 4 incisos → verificar os 4 separadamente; cada um pode resultar em criar, sobrescrever ou ignorar.

---

### Exemplo Completo — Portaria nº 18/2026

**Texto do diário:**
> I - DESIGNAR, cumulativamente, Eliaquim Antunes de Souza Santos para atuar na **5ª Defensoria Pública do Polo do Médio Amazonas**, no período de **20 a 22 de janeiro de 2026**;
> II - DESIGNAR, cumulativamente, Elaine Maria Sousa Frota para atuar na **5ª Defensoria Pública do Polo do Médio Amazonas**, no período de **23 a 30 de janeiro de 2026**;
> III - DESIGNAR, cumulativamente, Eliaquim Antunes de Souza Santos para atuar na **12ª Defensoria Pública do Polo do Médio Amazonas**, no período de **20 a 22 de janeiro de 2026**;
> IV - DESIGNAR, cumulativamente, Elaine Maria Sousa Frota para atuar na **12ª Defensoria Pública do Polo do Médio Amazonas**, no período de **23 a 30 de janeiro de 2026**;
> SEI n. 26.0.000000008-5

**Aplicando o passo a passo:**

| Inciso | Substituto | DP | Período | Ausente (lista-completa.md) |
|--------|-----------|-----|---------|---------------------------|
| I | Eliaquim | 5ª DP | 20-22/01 | Elton Dariva Staub |
| II | Elaine Maria | 5ª DP | 23-30/01 | Elton Dariva Staub |
| III | Eliaquim | 12ª DP | 20-22/01 | Elton Dariva Staub |
| IV | Elaine Maria | 12ª DP | 23-30/01 | Elton Dariva Staub |

**HTML gerado (4 linhas):**

```html
<tr><td>20-22/01</td><td><strong>Elton Dariva</strong></td><td><span class="tipo-badge tipo-folga">🟡 Não informado</span></td><td>5ª DP Criminal</td><td>Eliaquim Antunes de Souza</td><td><a href="URL_DIARIO" target="_blank">Edição 2572 - 14/01/2026</a></td><td>26.0.000000008-5</td></tr>
<tr><td>23-30/01</td><td><strong>Elton Dariva</strong></td><td><span class="tipo-badge tipo-folga">🟡 Não informado</span></td><td>5ª DP Criminal</td><td>Elaine Maria Sousa Frota</td><td><a href="URL_DIARIO" target="_blank">Edição 2572 - 14/01/2026</a></td><td>26.0.000000008-5</td></tr>
<tr><td>20-22/01</td><td><strong>Elton Dariva</strong></td><td><span class="tipo-badge tipo-folga">🟡 Não informado</span></td><td>12ª DP Silves</td><td>Eliaquim Antunes de Souza</td><td><a href="URL_DIARIO" target="_blank">Edição 2572 - 14/01/2026</a></td><td>26.0.000000008-5</td></tr>
<tr><td>23-30/01</td><td><strong>Elton Dariva</strong></td><td><span class="tipo-badge tipo-folga">🟡 Não informado</span></td><td>12ª DP Silves</td><td>Elaine Maria Sousa Frota</td><td><a href="URL_DIARIO" target="_blank">Edição 2572 - 14/01/2026</a></td><td>26.0.000000008-5</td></tr>
```

> **Nota:** Neste caso, como o Sonnet não sabe se é férias, folga ou licença, usa "Não informado". Se você souber o tipo correto (por contexto ou outro documento), pode corrigir depois.

---

### Casos Especiais

#### Substituto não é do Polo Médio Amazonas

Se o substituto designado não constar na lista dos 5 defensores do polo (José Antônio, Ícaro, Eliaquim, Elton Dariva, Elaine Maria), é um **defensor externo da capital**. Processar normalmente — colocar o nome completo como aparece no diário.

#### Portaria menciona "cessar efeitos" de designação anterior

Ignorar para fins de nova linha. Significa que uma substituição anterior foi encerrada. Não cria linha nova.

#### Portaria de diárias (deslocamento)

Ignorar. Portarias de autorização de deslocamento e pagamento de diárias **não criam linhas** na Tabela Completa — são apenas autorização de viagem, não ausências.

#### Mesmo defensor ausente, mesma DP, substitutos diferentes em sub-períodos

Isso é uma **substituição escalonada** — criar uma linha para cada sub-período. Ver seção "Substituições Escalonadas" abaixo. Se uma dessas linhas já existir na tabela com substituto diferente, aplicar a lógica de **sobrescrita** do Passo 5.

---

## Substituições Escalonadas

Ocorre quando um defensor ausente tem substitutos diferentes em sub-períodos.

**Exemplo — Elton Dariva (20-30/01):**
- 20/01: Eliaquim substitui (folga)
- 21-22/01: Eliaquim substitui (férias)
- 23-30/01: Elaine Maria substitui (férias)

Cada sub-período é uma linha separada na Tabela Completa.

---

## Formatos Comuns de Texto no Diário

**Formato formal (DESIGNAR):**
> "DESIGNAR, cumulativamente, o Defensor Público [Nome] para atuar na [DP], no período de [data] a [data]"

**Formato lista direta (menos comum):**
> "2ª Defensoria Pública do Polo do Médio Amazonas: Elton Dariva Staub (31 de janeiro a 03 de fevereiro);"

**Importante:** "Cumulativamente" significa que o substituto acumula DPs além das suas próprias.
