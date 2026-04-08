# Processo de Atualização do Site

## Ordem Obrigatória — Férias / Folgas / Licenças

**SEMPRE seguir esta ordem para evitar inconsistências:**

1. **Atualizar `docs/escalas/ferias-folgas-2026.md`** — fonte de dados primária
   - Adicionar na tabela do mês correspondente
   - Campos: período, defensor, tipo, DP, substituto, processo, link

2. **Atualizar aba "Tabela Completa" no `index.html`** ⚠️ SEMPRE PRIMEIRO no site
   - Adicionar as linhas HTML na seção do mês correspondente
   - Ordenar cronologicamente dentro do mês
   - **Esta é a fonte de verdade mais visível**

3. **Atualizar objeto `detalhesAfastamentosRaw`** no JavaScript
   - Array do mês correspondente
   - Formato: `{ periodo: [dias], defensor: 'Nome', tipo: 'Tipo', defensorias: [...], substitutos: [...], processo: '...', link: '...' }`

4. **Atualizar objeto `afastamentos`** no JavaScript
   - Adicionar nome curto do defensor nos dias do período
   - Exemplo: `{ 2026: { 2: { 11: ['icaro'], 12: ['icaro', 'jose'] } } }`

5. **Atualizar aba "Detalhes de Afastamentos"** — tabela HTML individual do defensor

6. **Atualizar tabelas de "Designações semanais"** (se aplicável)
   - Aplicar substituições nas tabelas do período
   - ⚠️ Verificar se o defensor realmente está ausente no dia específico

7. **Atualizar `docs/escalas/calendario-visual-2026.md`** (se necessário)

---

## Checklist Completo

### Antes de Começar
- [ ] Identificar qual defensor está ausente
- [ ] Identificar o período exato
- [ ] Identificar o tipo (Férias/Folga/Licença Especial)
- [ ] Identificar as DPs afetadas (consultar `docs/defensorias/lista-completa.md`)
- [ ] Identificar os substitutos (se houver)

### Durante a Atualização
- [ ] Tabela Completa no `index.html` atualizada ⚠️ PRIMEIRO
- [ ] `detalhesAfastamentosRaw` atualizado
- [ ] `afastamentos` atualizado
- [ ] Tabela individual do defensor atualizada
- [ ] Designações semanais atualizadas (se aplicável)
- [ ] Verificar dia da semana antes de aplicar destaques
- [ ] Classes aplicadas apenas em dias úteis (seg-sex)
- [ ] Alternância de grupos verificada (A/B)

### Verificações Finais
- [ ] Informação aparece na aba "Tabela Completa"?
- [ ] Informação aparece no calendário visual (aba "Calendário")?
- [ ] Informação aparece na tabela individual do defensor?
- [ ] Substituições aplicadas corretamente nas Designações Semanais?
- [ ] Recarregar a página e verificar console (F12) — sem erros de alternância?
- [ ] Testar responsividade (celular/tablet)?

---

## Problema Comum: Calendário ≠ Tabela Completa

**Sintoma:** Afastamento aparece no calendário (aba Calendário) mas NÃO na Tabela Completa.

**Causa:** O calendário é gerado pelo JavaScript (`afastamentos`), que foi atualizado, mas a tabela HTML estática não foi.

**Solução:** Sempre começar pela aba "Tabela Completa" antes de atualizar o JavaScript.

---

## Publicação no GitHub Pages

Usar o mesmo `index.html` da raiz. Não é necessário nenhum arquivo adicional além do `.nojekyll` já presente em `github-pages/`.
