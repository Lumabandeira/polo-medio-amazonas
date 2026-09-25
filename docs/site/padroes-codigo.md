# Padrões de Código

> Atualizado em 14/06/2026

## Estrutura HTML das Tabelas de Designações Semanais

```html
<h4>Designações - 07 a 11 de Janeiro de 2026</h4>
<table>
    <thead>
        <tr>
            <th>DP</th>
            <th>07/01</th>
            <th>08/01</th>
            <th>09/01</th>
            <th>10/01</th>  <!-- Sábado -->
            <th>11/01</th>  <!-- Domingo -->
        </tr>
    </thead>
    <tbody>
        <!-- DP do Grupo A -->
        <tr>
            <td class="itacoatiara">1ª DP (Família)</td>
            <td class="itacoatiara">Ênio</td>  <!-- Seg -->
            <td class="itacoatiara">Ênio</td>  <!-- Ter -->
            <td class="itacoatiara">Ênio</td>  <!-- Qua -->
            <td>Ênio</td>  <!-- Sáb — SEM classe -->
            <td>Ênio</td>  <!-- Dom — SEM classe -->
        </tr>

        <!-- DP do Grupo B (na semana do Grupo A, sem destaque) -->
        <tr>
            <td>2ª DP (Família)</td>
            <td>Thays</td>
            <!-- ... -->
        </tr>
    </tbody>
</table>
```

**Regras:**
- Classes `itacoatiara` ou `silves` vão na célula do nome da DP **e** em todas as células de dias úteis
- Sábados e domingos **nunca** recebem classe de destaque
- O formato das datas no `<th>` é `DD/MM`
- DPs 7–12 estão vagas — exibir "—" nas células

## Abreviações dos Defensores nas Tabelas

| Defensor | Abreviação |
|----------|------------|
| Ênio Jorge Lima Barbalho Junior | Ênio |
| Thays Lidianne Campos de Azevedo Pereira | Thays |
| Ícaro Oliveira Avelar Costa | Ícaro |
| Eliaquim Antunes de Souza Santos | Eliaquim |
| Emilly Bianca Ferreira dos Santos | Emilly |
| Miguel Eduardo de Azevedo Martins Filho | Miguel |

## Formato de Datas

| Contexto | Formato | Exemplo |
|----------|---------|---------|
| Cabeçalho de tabela HTML | DD/MM | 10/01 |
| JavaScript / Firestore | YYYY-MM-DD | 2026-01-10 |
| Exibição no site | DD/MM/YYYY | 10/01/2026 |
| JavaScript `new Date` | `new Date(year, month-1, day)` | mês é 0-indexed |

## Chaves JSON dos Defensores

| Defensor | Chave JSON | Status |
|----------|-----------|--------|
| Ênio Jorge Lima Barbalho Junior | `enio` | ativo |
| Thays Lidianne Campos de Azevedo Pereira | `thays` | ativo |
| Ícaro Oliveira Avelar Costa | `icaro` | ativo |
| Eliaquim Antunes de Souza Santos | `eliaquim` | ativo |
| Emilly Bianca Ferreira dos Santos | `emilly` | ativo |
| Miguel Eduardo de Azevedo Martins Filho | `miguel` | ativo |
| José Antônio Pereira da Silva | `jose-antonio` | ex-membro |
| Elton Dariva Staub | `elton` | ex-membro |
| Elaine Maria Sousa Frota | `elaine` | ex-membro |

## Padrão de DPs vagas no JavaScript

DPs vagas são representadas pela chave `"dpN-vaga"` (ex: `"dp7-vaga"`). A função `_atualizarNomesVaga()` gera automaticamente o label `"7ª DP (vaga)"` para exibição. Badges de vaga são ordenados por último no calendário.

## CSS: `.form-group` como item de grid (`.form-grid`) — `min-width: 0`

`.form-group { display:flex; flex-direction:column; min-width:0; }` (`index.html`, perto de
`index.html:3027`) — o `min-width: 0` é necessário porque `.form-group` também é item de um
`.form-grid` (`display:grid; grid-template-columns: repeat(4, 1fr)`) em todos os modais de
formulário do site. Por padrão, um item de grid tem `min-width: auto`, que impede a coluna de
encolher abaixo do **conteúdo mínimo** de qualquer campo nela — inclusive um `<select>`, cujo
conteúdo mínimo no Chrome é a largura da opção mais longa da lista (não a opção selecionada). Um
`<select>` com uma opção bem longa numa coluna estreita força essa coluna (e, por tabela, a grade
inteira) a crescer além do espaço disponível, vazando os campos que ocupam a linha inteira
(`grid-column: 1 / -1`, ex.: `#fd-descricao` em "Nova Despesa") para fora do modal — bug real
encontrado na sessão 43 com o campo "Tipo de Comprovante" (opção "Cupom de máquina registradora").
`min-width: 0` no item de grid remove essa trava, deixando o conteúdo encolher/cortar em vez de
estourar o container. Ao criar um novo modal de formulário com `<select>`/campo de texto longo
dentro de `.form-grid`, esse comportamento já está coberto — não precisa de ajuste por modal.
