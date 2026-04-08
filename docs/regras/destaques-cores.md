# Regras de Cores e Destaques

## Classes CSS

### `.itacoatiara` — Amarelo

```css
background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
border-left: 3px solid #f59e0b;
color: #92400e;
```

Aplicar nas DPs responsáveis pelos atendimentos da **sede de Itacoatiara** (Grupo A ou B ativo na semana).

### `.silves` — Azul

```css
background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
border-left: 3px solid #3b82f6;
color: #1e40af;
```

Aplicar nas DPs responsáveis pelos atendimentos da **UDI de Silves** (11ª ou 12ª DP, conforme o grupo ativo).

## Onde Aplicar

1. **Célula do nome da DP** (primeira coluna `<td>`)
2. **Células dos dias úteis** (segunda a sexta-feira)
3. **NUNCA aplicar em sábados e domingos**

## Regra Crítica: Fins de Semana

**Sábados e domingos NUNCA recebem destaque**, mesmo que o dia apareça na tabela.

- ✅ Segunda a Sexta → pode ter classe `itacoatiara` ou `silves`
- ❌ Sábado e Domingo → sem classe de destaque

**Motivo:** Não há atendimentos presenciais nos fins de semana.

**Validação automática:** A função `validateWeekendHighlights()` remove automaticamente destaques de fins de semana ao carregar a página. Mas é melhor não inserir a classe desde o início.

## Como Verificar o Dia da Semana

Antes de aplicar destaques, verificar o dia da semana de cada data:

- Use `getDayOfWeek(year, month, day)` no console do navegador
  - Retorna: 0 = Domingo, 1 = Segunda, ..., 6 = Sábado
- Referência rápida Janeiro 2026:
  - 10/01 = Sábado ❌
  - 11/01 = Domingo ❌
  - 12/01 = Segunda ✅
  - 17/01 = Sábado ❌
  - 18/01 = Domingo ❌

**Nunca assuma o dia da semana sem verificar.**

## Classes Adicionais (Badges de Afastamento)

| Classe | Uso |
|--------|-----|
| `.tipo-badge` | Container genérico de badge |
| `.tipo-ferias` | Badge de férias |
| `.tipo-folga` | Badge de folga |
| `.tipo-licenca` | Badge de licença |
