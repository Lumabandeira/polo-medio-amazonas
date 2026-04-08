# Regras de Alternância Semanal

## Conceito

A alternância NÃO é entre pares individuais de DPs — é entre dois **grupos fixos** que alternam toda semana.

Ver definição dos grupos em `docs/defensorias/grupos-alternancia.md`.

## Padrão de Referência (Janeiro 2026)

| Semana | Período | Grupo Ativo |
|--------|---------|-------------|
| 1 | 07-11/01 | **Grupo A** |
| 2 | 12-18/01 | **Grupo B** |
| 3 | 19-25/01 | **Grupo A** |
| 4 | 26/01-01/02 | **Grupo B** |

## Exemplo Prático

**Semana 07-11/01 (Grupo A ativo):**
- ✅ 1ª DP destacada (itacoatiara)
- ❌ 2ª DP não destacada
- ✅ 3ª DP destacada (itacoatiara)
- ❌ 4ª DP não destacada
- ❌ 5ª DP não destacada
- ✅ 6ª DP destacada (itacoatiara)
- ❌ 11ª DP não destacada
- ✅ 12ª DP destacada (silves)

**Semana 12-18/01 (Grupo B ativo):**
- ❌ 1ª DP não destacada
- ✅ 2ª DP destacada (itacoatiara)
- ❌ 3ª DP não destacada
- ✅ 4ª DP destacada (itacoatiara)
- ✅ 5ª DP destacada (itacoatiara)
- ❌ 6ª DP não destacada
- ✅ 11ª DP destacada (silves)
- ❌ 12ª DP não destacada

## Checklist — Antes de Criar uma Nova Tabela

- [ ] Qual foi a última semana criada?
- [ ] Qual grupo estava ativo naquela semana? (A ou B)
- [ ] Aplicar o grupo OPOSTO na nova semana

**Se Grupo A estava ativo → nova semana = Grupo B**
**Se Grupo B estava ativo → nova semana = Grupo A**

### Verificação para Grupo A
- [ ] 1ª DP destacada com classe `itacoatiara`
- [ ] 3ª DP destacada com classe `itacoatiara`
- [ ] 6ª DP destacada com classe `itacoatiara`
- [ ] 12ª DP destacada com classe `silves`
- [ ] 2ª, 4ª, 5ª, 11ª DPs **sem** classe de destaque

### Verificação para Grupo B
- [ ] 2ª DP destacada com classe `itacoatiara`
- [ ] 4ª DP destacada com classe `itacoatiara`
- [ ] 5ª DP destacada com classe `itacoatiara`
- [ ] 11ª DP destacada com classe `silves`
- [ ] 1ª, 3ª, 6ª, 12ª DPs **sem** classe de destaque

## Por Que Erros Acontecem

1. Não verificar qual grupo estava ativo na semana anterior
2. Aplicar destaque baseado no defensor, sem considerar a regra de grupo
3. Tabelas de meses diferentes misturadas — a função `validateAlternation()` ordena cronologicamente para evitar isso

## Tabelas que Cruzam Meses

Quando uma segunda-feira cai no final de um mês:
- A tabela fica na seção do mês onde a **segunda-feira** cai
- Exemplo: semana 26/01-01/02 → seção Janeiro (porque a segunda-feira é 26/01)
- Exemplo: semana 02-08/02 → seção Fevereiro

## Validação Automática

Executar `validateAlternation()` no console do navegador (F12 → Console) após criar novas tabelas. A função reporta erros com o nome do período para facilitar a correção.
