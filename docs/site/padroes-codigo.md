# Padrões de Código

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
        <!-- DP do Grupo A (itacoatiara) -->
        <tr>
            <td class="itacoatiara">1ª DP (Família)</td>
            <td class="itacoatiara">Ícaro</td>  <!-- Seg -->
            <td class="itacoatiara">Ícaro</td>  <!-- Ter -->
            <td class="itacoatiara">Ícaro</td>  <!-- Qua -->
            <td>Ícaro</td>  <!-- Sáb — SEM classe -->
            <td>Ícaro</td>  <!-- Dom — SEM classe -->
        </tr>

        <!-- DP do Grupo A (silves) -->
        <tr>
            <td class="silves">12ª DP (Silves)</td>
            <td class="silves">Elton Dariva</td>
            <td class="silves">Elton Dariva</td>
            <td class="silves">Elton Dariva</td>
            <td>Elton Dariva</td>  <!-- Sáb — SEM classe -->
            <td>Elton Dariva</td>  <!-- Dom — SEM classe -->
        </tr>

        <!-- DP sem destaque (Grupo B na semana do Grupo A) -->
        <tr>
            <td>2ª DP (Família)</td>
            <td>José Antônio</td>
            <!-- ... -->
        </tr>
    </tbody>
</table>
```

**Regras:**
- Classes `itacoatiara` ou `silves` vão na célula do nome da DP **e** em todas as células de dias úteis
- Sábados e domingos **nunca** recebem classe de destaque
- O formato das datas no `<th>` é `DD/MM`

## Legenda das Tabelas (HTML padrão)

```html
<p style="margin: 0 0 15px 0; font-weight: 600; color: var(--text-primary); font-size: 1.1em;">
    <strong>Legenda:</strong>
</p>
<div style="display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 25px;">
    <div style="flex: 1; min-width: 280px; padding: 15px; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-left: 4px solid #f59e0b; border-radius: 8px;">
        <p style="margin: 0; font-weight: 600; color: #92400e;">
            <span style="display: inline-block; width: 20px; height: 20px; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-left: 3px solid #f59e0b; border-radius: 3px; vertical-align: middle; margin-right: 8px;"></span>
            As linhas destacadas em amarelo representam as Defensorias responsáveis pelos atendimentos da sede de Itacoatiara.
        </p>
    </div>
    <div style="flex: 1; min-width: 280px; padding: 15px; background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-left: 4px solid #3b82f6; border-radius: 8px;">
        <p style="margin: 0; font-weight: 600; color: #1e40af;">
            <span style="display: inline-block; width: 20px; height: 20px; background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%); border-left: 3px solid #3b82f6; border-radius: 3px; vertical-align: middle; margin-right: 8px;"></span>
            As linhas destacadas em azul representam as Defensorias responsáveis pelos atendimentos da UDI de Silves.
        </p>
    </div>
</div>
```

## Convenções de Nomenclatura

### Abreviações dos Defensores nas Tabelas

| Defensor | Abreviação |
|----------|------------|
| José Antônio Pereira da Silva | José Antônio |
| Ícaro Oliveira Avelar Costa | Ícaro ou Ícaro Avelar |
| Eliaquim Antunes de Souza | Eliaquim |
| Elton Dariva Staub | Elton Dariva |
| Elaine Maria Sousa Frota | Elaine Maria |

### Formato de Datas

| Contexto | Formato | Exemplo |
|----------|---------|---------|
| Cabeçalho de tabela HTML | DD/MM | 10/01 |
| JavaScript `new Date` | `new Date(year, month-1, day)` | mês é 0-indexed |
| Markdown | DD/MM/AAAA | 10/01/2026 |
