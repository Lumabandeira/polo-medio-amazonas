# Categorias do Diário Oficial — Polo Médio Amazonas

Este arquivo documenta as regras de classificação de portarias e atos do Diário Oficial da DPE/AM para uso no site do Polo Médio Amazonas. **Deve ser incluído no prompt sempre que o Sonnet for usado para analisar novas edições do Diário Oficial.**

---

## Regra geral de inclusão

Só inclua um ato se ele **afeta diretamente o Polo Médio Amazonas** — seus defensores, servidores, defensorias (1ª a 12ª DP), escala de plantão ou coordenação. Atos que mencionam o Polo Médio apenas de passagem (ex: tabela de colidência que lista vários polos) podem ser incluídos com categoria `polo_medio` apenas se o conteúdo relevante for transcrito.

**Atos sobre outros polos** (Juruá, Alto Solimões, Purus, Madeira, etc.) **não devem ser incluídos**, mesmo que envolvam defensores conhecidos. Veja a regra crítica sobre `coordenacao` abaixo.

---

## Categorias disponíveis

Cada ato pode ter **uma ou mais** categorias. A ordem sugerida é da mais específica para a mais geral.

---

### `designacoes`
**O que é:** designação cumulativa de defensor(a) para uma das 12 Defensorias Públicas do Polo Médio Amazonas (1ª a 12ª DP).

**Inclui:**
- Portarias que designam defensor para atuar na Xª Defensoria Pública do Polo Médio Amazonas por período determinado
- Portarias que tornam sem efeito (cessam) designações anteriores para essas DPs e nomeiam substituto
- Retificações de designações para as DPs 1–12

**Não inclui:**
- Designações para plantão (usar `plantao`)
- Designação de Coordenador do Polo (usar `coordenacao`)
- Deslocamentos para municípios (usar `comarca`)

**Exemplos:**
- "DESIGNAR Elaine Maria Sousa Frota para atuar na 2ª Defensoria Pública do Polo Médio Amazonas, nos dias 07, 08 e 09 de janeiro de 2026"
- "CESSAR OS EFEITOS da designação de Mariana Silva Paixão na 9ª Defensoria Pública do Polo Médio Amazonas; DESIGNAR Eliaquim Antunes de Souza Santos para atuar na 9ª DP"
- "Retifica designação na 2ª DP Polo Médio: Bruna Farias até 25/01 e Daniel Bettanin a partir de 26/01"

---

### `plantao`
**O que é:** escala de plantão (Cível, Criminal/Custódia) do Polo Médio Amazonas, incluindo alterações e substituições na escala.

**Inclui:**
- Portaria que estabelece a escala de plantão trimestral do interior para o Polo Médio Amazonas
- Portarias de alteração (1ª, 2ª, 3ª... alteração) da escala de plantão quando afetam o Polo Médio
- Substituições de defensores ou servidores na escala de plantão do Polo Médio
- Tabela de colidência entre polos (quem substitui o Polo Médio em caso de impedimento)
- Escalas de assessoria vinculadas ao plantão do Polo Médio

**Não inclui:**
- Designações para as DPs 1–12 fora do contexto de plantão (usar `designacoes`)

**Exemplos:**
- "Escala de plantão 1º trimestre/2026 — Polo Médio Amazonas: Plantão Cível e de Família: 01) Elton Dariva Staub..."
- "3ª Alteração da Escala de Plantão: substitui Fábio Bastos por Luma Karolyne no Polo Médio Amazonas (semana 08)"
- "Define colidência: Polo Rio Negro-Solimões atua como substituto automático do Polo Médio Amazonas"

---

### `coordenacao`
**O que é:** designação, cessação ou substituição do **Coordenador do Polo Médio Amazonas** (FGD-6 / Coordenadoria do Interior).

**REGRA CRÍTICA:** use esta categoria **somente quando o ato se referir ao Polo Médio Amazonas**. Designações de coordenador para o Polo do Juruá, Alto Solimões, Purus, Madeira, Rio Negro-Solimões, Baixo Amazonas, Coari, Maués ou qualquer outro polo **não devem ser incluídas no banco de dados** — e nunca devem receber a categoria `coordenacao`.

**Inclui:**
- Portaria que designa defensor como Coordenador do Polo Médio Amazonas (FGD-6)
- Portaria que cessa a FGD-6 de um coordenador do Polo Médio e designa substituto (interinamente ou por período determinado)
- Portaria que cessa a FGD-6 sem nomear substituto imediato

**Exemplos (incluir):**
- "DESIGNAR Ícaro Oliveira Avelar Costa como Coordenador do Polo do Médio Amazonas, atribuindo-lhe a FGD-6 (Coordenadoria do Interior)"
- "CESSAR OS EFEITOS da FGD-6 de Ícaro Costa; DESIGNAR Eliaquim Antunes de Souza Santos como Coordenador do Polo Médio Amazonas de 19 a 22/02/2026"

**Exemplos (NÃO incluir):**
- "DESIGNAR Vinicius Cepil Coelho como Coordenador do Polo do Juruá" → **descartar, não é Polo Médio**
- "CESSAR designação de Murilo Rodrigues Breda como Coordenador do Polo do Alto Solimões" → **descartar**

---

### `nomeacao_diretoria`
**O que é:** nomeações, exonerações e delegações de cargos de direção e gestão da DPE/AM que têm impacto indireto no Polo Médio Amazonas (ex: mudança de Subdefensor Público Geral que assina as portarias do polo, nomeação de Diretor-Geral).

**Inclui:**
- Nomeação/exoneração do Defensor Público Geral ou Subdefensores Públicos Gerais
- Nomeação/exoneração de Diretores DPE com competência sobre o interior
- Delegação de competências ao Subdefensor que passa a assinar designações do polo
- Nomeação de defensor do Polo Médio para cargo de Diretor Adjunto na sede

**Não inclui:**
- Designação de Coordenador de Polo → usar `coordenacao`
- Portarias de coordenadoria acadêmica ou outras coordenadorias sem relação com o Polo Médio

**Exemplos:**
- "Nomeia Helom Cesar da Silva Nunes como 1º Subdefensor Público Geral do Estado a partir de 02/03/2026"
- "Nomeia Eliaquim Antunes de Souza Santos como Diretor Adjunto DPE-4 a partir de 16/03/2026"
- "Delega a Helom Cesar funções de gestão de membros e polos do interior"

---

### `substituicao`
**O que é:** atos que tornam sem efeito designações anteriores e as substituem, ou retificações que alteram quem atua em determinada posição.

**Use em conjunto com** `designacoes`, `coordenacao` ou `plantao` — raramente sozinha.

**Exemplos:**
- "TORNAR SEM EFEITO o inciso VII da Portaria 923/2025 quanto à designação de Daniel Bettanin para a 2ª DP; DESIGNAR Elaine Frota no lugar"
- "Retifica designação na 2ª DP Polo Médio"

---

### `comarca`
**O que é:** deslocamentos autorizados para municípios do interior, inspeções carcerárias, visitas a comarcas, criação de postos de atendimento avançado (PAV).

**Exemplos:**
- "Autoriza deslocamento de Ícaro Avelar Costa a Silves (01 a 06/02/2026) para atendimentos presenciais"
- "Autoriza deslocamento de José Antônio e Larice Bruce a Urucará/Itacoatiara, 02-05/03/2026"
- "Autoriza deslocamento a Urucará para tratar criação de Posto de Atendimento Avançado (PAV)"

---

### `servidor`
**O que é:** atos que envolvem servidores (não defensores) vinculados ao Polo Médio Amazonas — assessores defensoriais, técnicos, estagiários.

**Use em conjunto com outras categorias** (ex: `plantao` + `servidor` quando a escala inclui servidores).

**Exemplos:**
- "Designa servidor Rafael Pereira de Freitas para assessorar 4ª e 9ª DP do Polo Médio Amazonas"
- "Prorroga por 1 mês designação de Deborah Lavareda para assessorar remotamente o Polo Médio"

---

### `defensor`
**O que é:** categoria genérica que indica que o ato envolve pelo menos um defensor do Polo Médio Amazonas (Ícaro, José Antônio, Elton, Eliaquim, Elaine ou outros que atuem no polo).

**Use sempre que um defensor do polo for mencionado como sujeito principal do ato.** Combine com as categorias mais específicas.

---

### `polo_medio`
**O que é:** categoria base que indica que o ato menciona o Polo Médio Amazonas como unidade organizacional.

**Use em quase todos os atos incluídos.** Exceções: atos sobre defensores do polo em contexto de licença/estudo na sede (sem menção ao polo como unidade) podem ter apenas `defensor`.

---

### `projeto`
**O que é:** projetos institucionais específicos que envolvem o Polo Médio Amazonas.

**Exemplos:**
- "14º Ciclo Projeto Adote uma Comarca: designações para comarcas do Polo Médio Amazonas"
- "GT Ação 'Eu tenho pai': designa José Antônio e Luma Karolyne pelo Polo Médio"

---

## Resumo das regras de classificação

| Situação | Categorias |
|---|---|
| Designa defensor para Xª DP do Polo Médio | `designacoes` + `polo_medio` + `defensor` |
| Designa defensor para DP **sem titular** (vaga) | `designacoes` + `polo_medio` + `defensor` |
| Substitui designação numa DP | `designacoes` + `substituicao` + `polo_medio` + `defensor` |
| Defensor deixa de ser titular de uma DP (DP fica vaga) | `designacoes` + `substituicao` + `polo_medio` + `defensor` |
| Escala de plantão trimestral | `plantao` + `polo_medio` + `defensor` + `servidor` |
| Alteração da escala de plantão | `plantao` + `substituicao` + `polo_medio` + `defensor` + `servidor` |
| Designa Coordenador do **Polo Médio** | `coordenacao` + `polo_medio` + `defensor` |
| Substitui Coordenador do **Polo Médio** interinamente | `coordenacao` + `substituicao` + `polo_medio` + `defensor` |
| Coordenador de **outro polo** (Juruá, etc.) | **Não incluir** |
| Nomeação de Subdefensor Geral ou Diretor DPE | `nomeacao_diretoria` |
| Defensor do polo nomeado Diretor na sede | `nomeacao_diretoria` + `defensor` |
| Deslocamento para município | `comarca` + `defensor` (+ `servidor` se aplicável) |
| Processo seletivo de estágio para o polo | `polo_medio` + `defensor` + `comarca` (se citar município) |
| Projeto institucional com o polo | `projeto` + `polo_medio` + `defensor` |

---

## Formato do JSON de saída

Cada ato deve ser representado como:

```json
{
  "numero": "Portaria nº 7/2026-GSPG/DPE/AM",
  "sei": "25.0.000014378-5",
  "sgi": null,
  "categorias": ["polo_medio", "defensor", "designacoes"],
  "trechos": [
    "I - DESIGNAR, cumulativamente, a Defensora Pública de 3ª Classe Elaine Maria Sousa Frota para atuar na 2ª Defensoria Pública do Polo do Médio Amazonas, no período de 12 a 21 de janeiro de 2026;",
    "II - DESIGNAR, cumulativamente, o Defensor Público de 4ª Classe Ícaro Oliveira Avelar Costa para atuar na 8ª Defensoria Pública do Polo do Médio Amazonas, no período de 12 a 21 de janeiro de 2026;"
  ],
  "resumo": "Designa Elaine Frota (2ª DP) e Ícaro Costa (8ª DP) no Polo Médio Amazonas de 12 a 21/01/2026"
}
```

**Regras do resumo:**
- Máximo de 120 caracteres
- Mencionar defensores pelo sobrenome e a DP (ex: "2ª DP", "9ª DP")
- Incluir o período (datas de início e fim)
- Indicar se é cessação + nova designação

**Regras dos trechos:**
- Transcrever apenas os incisos diretamente relevantes para o Polo Médio
- Omitir incisos sobre outros polos
- Omitir considerandos e fórmulas de estilo ("CERTIFIQUE-SE, PUBLIQUE-SE E CUMPRA-SE")
- Omitir assinaturas digitais
