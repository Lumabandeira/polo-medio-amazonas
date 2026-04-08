# Estrutura do Site (index.html)

## Arquivo Único

Existe apenas **um** `index.html` na raiz do projeto. Nunca criar cópias. Para publicar no GitHub Pages, usar este mesmo arquivo.

## Abas do Site

O site possui 5 abas com os seguintes IDs:

| ID | Nome da Aba | Conteúdo |
|----|-------------|----------|
| `#calendario` | Calendário Visual | Calendário mensal com badges de ausência por defensor |
| `#tabela-completa` | Tabela Completa | Tabela HTML estática com todas as ausências de 2026, organizada por mês |
| `#detalhes` | Detalhes de Afastamentos | Tabela individual por defensor, filtrável |
| `#defensorias` | Defensorias | Informações das 12 DPs |
| `#designacoes-periodo` | Designações Semanais | Tabelas semanais com defensor por DP por dia |

## Fontes de Dados no JavaScript

O JavaScript do site possui dois objetos principais:

| Objeto | Finalidade |
|--------|-----------|
| `afastamentos` | Alimenta o calendário visual (aba Calendário). Estrutura: `{ ano: { mes: { dia: ['nome_curto'] } } }` |
| `detalhesAfastamentosRaw` | Alimenta a aba "Detalhes de Afastamentos". Array de objetos por mês. |

**Importante:** A aba "Tabela Completa" é uma tabela HTML **estática** — não é gerada pelo JavaScript. Precisa ser atualizada manualmente.

## Estrutura das Seções de Designações Semanais

Cada mês tem uma seção `<h3>` dentro de `#designacoes-periodo`. Cada semana tem:
1. Um `<h4>` com o título do período (ex: "Designações - 07 a 11 de Janeiro de 2026")
2. Uma `<table>` com as 12 DPs e os dias da semana

O título do `<h4>` é usado pela função `validateAlternation()` para ordenar as tabelas cronologicamente.

## Nomes Curtos dos Defensores (usados no objeto `afastamentos`)

| Nome completo | Nome curto no JS |
|---------------|-----------------|
| José Antônio Pereira da Silva | `jose` |
| Ícaro Oliveira Avelar Costa | `icaro` |
| Eliaquim Antunes de Souza | `eliaquim` |
| Elton Dariva Staub | `elton` |
| Elaine Maria Sousa Frota | `elaine` |
