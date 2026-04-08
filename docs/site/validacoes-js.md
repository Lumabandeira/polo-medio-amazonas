# Funções JavaScript de Validação

Todas as funções são executadas automaticamente quando a página carrega (`window.onload`).

## `getDayOfWeek(year, month, day)`

Calcula o dia da semana de uma data.

- **Retorna:** 0 = Domingo, 1 = Segunda, 2 = Terça, 3 = Quarta, 4 = Quinta, 5 = Sexta, 6 = Sábado
- **Uso:** Internamente pelas funções de validação e pode ser chamada no console para verificar datas

```javascript
getDayOfWeek(2026, 1, 10) // → 6 (Sábado)
getDayOfWeek(2026, 1, 12) // → 1 (Segunda)
```

## `validateWeekendHighlights()`

Remove automaticamente classes de destaque de sábados e domingos.

**O que faz:**
1. Identifica todas as tabelas na aba "Designações semanais"
2. Lê os cabeçalhos para identificar colunas de datas (formato DD/MM)
3. Calcula o dia da semana de cada data
4. Remove classes `itacoatiara` e `silves` de sábados (6) e domingos (0)

**Execução:** Automática ao carregar a página (com delay de 100ms após `renderCalendar()`).

## `validateAlternation()`

Valida a alternância semanal entre Grupo A e Grupo B.

**O que faz:**
1. Extrai datas dos títulos `<h4>` de cada tabela
2. Ordena as tabelas **cronologicamente** (não pela ordem no HTML)
3. Para cada tabela verifica:
   - Se TODAS as DPs do Grupo A estão destacadas (ou TODAS do Grupo B)
   - Se NENHUMA DP do grupo oposto está destacada
   - Se a semana alternou corretamente em relação à semana anterior
4. Reporta erros no console do navegador com o nome do período

**Como usar para debug:**
1. Abrir o site no navegador
2. Pressionar F12 → aba Console
3. Os erros indicam o período problemático (ex: "Designações - 12 a 18 de Janeiro")

**Execução:** Automática ao carregar a página.

## Inicialização (`window.onload`)

```javascript
window.onload = function() {
    renderCalendar();
    setTimeout(validateWeekendHighlights, 100);
};
```

`validateAlternation()` também é chamada automaticamente neste bloco.
