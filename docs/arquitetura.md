# Arquitetura e Decisões de Design

## Decisões já tomadas (não reverter sem motivo forte)

- **Arquivo único `index.html`** — sem build, sem framework. Publicado diretamente no GitHub Pages.
- **JSONs locais como base** — `docs/afastamentos-2026.json` e `docs/designacoes-2026.json` são a fundação. Firestore adiciona por cima em memória.
- **Firestore como fonte de verdade para edições** — todos os eventos do JSON foram promovidos ao Firestore via UI em 18/04/2026. Registros JSON sem override continuam visíveis (merge em memória).
- **Sem migração de hospedagem** — continua no GitHub Pages.
- **`syncFromSheets()` removida definitivamente.**
- **Nomes de defensores em campo texto livre** — para acomodar defensores externos ou futuros.
- **Edição de titulares não retroage** — resolução por data (`getTitularForDPOnDay`) garante que tabelas passadas não são afetadas por mudanças futuras.
- **Formulário de afastamento em duas fases** — (1) cadastrar ausência; (2) registrar substituto + portaria quando o diário sair.
- **Registros base do JSON promovíveis** — campo `json_base_id` no Firestore vincula ao JSON; registro JSON é suprimido após promoção.
- **Toggle "Editar" removido** — botões admin sempre visíveis após login (sessão 17).

## Descartado

- **Coleção `defensores_admin` no Firestore** — ex-membros livres já detectados via `orphanExMembros`; não justifica a complexidade.
- **Restauração de scroll via `sessionStorage`** — removida na sessão 18. A restauração de *seção* (`pma-secao`) permanece.
- **Tarefa agendada local do Windows** (`VerificarDiarioOficialDPE`) — substituída pelo GitHub Actions. Permanece `Disabled`.

## Padrão: cache localStorage (3 camadas)

Usado para eliminar flash de dados estáticos ao abrir seções que carregam do Firestore.

**Camadas (ordem de prioridade):**
1. **Memória** (`_xyzCache`) — navegação interna, sem rede
2. **localStorage** (`pma-xyz`) — F5 / recarga, síncrono, sem flash
3. **Firestore** — sempre consultado para manter cache atualizado

**Template da função carregar:**
```javascript
async function _xyzCarregarCelulas() {
    if (_xyzCache) { _xyzAplicarCelulas(_xyzCache); }
    else {
        try {
            const ls = localStorage.getItem('pma-xyz');
            if (ls) { _xyzCache = JSON.parse(ls); _xyzAplicarCelulas(_xyzCache); }
        } catch(e) {}
    }
    try {
        const doc = await db.collection('secoes').doc('xyz').get();
        if (!doc.exists) return;
        const { celulas } = doc.data();
        _xyzCache = celulas;
        localStorage.setItem('pma-xyz', JSON.stringify(celulas));
        _xyzAplicarCelulas(celulas);
    } catch(e) { console.warn('Erro ao carregar células:', e); }
}
```

**Na função salvar**, adicionar após gravar no Firestore:
```javascript
_xyzCache = celulas;
localStorage.setItem('pma-xyz', JSON.stringify(celulas));
```

**Atenção — cache desatualizado após remoção de linhas:** se o array estático diminuir, o cache antigo vai sobrescrever células erradas. Ver `_adoteCacheDesatualizado(celulas)` como referência.

**Seções com cache aplicado:**

| Seção | Chave localStorage | Firestore |
|-------|-------------------|----------|
| Regra de Alternância | `pma-regra-alternancia` | `secoes/regra_alternancia` |
| Férias/Folgas/Licenças | `pma-ferias-folgas` | `secoes/ferias_folgas` |
| Atribuições — células | `pma-atr-celulas` | `secoes/atribuicoes_celulas` |
| Adote — células | `pma-adote-celulas` | `secoes/adote_celulas` |
| Adote — expandir | `pma-adote-expandir` | `secoes/adote_expandir` |
| Afastamentos (docs brutos) | `pma-afastamentos-fs` | `afastamentos_admin` |
| Férias Equipe (docs brutos) | `pma-equipe-fs` | `afastamentos_equipe` |
| Última seção visitada | `pma-secao` | — |

## Arquitetura do Calendário Interativo

**Fluxo de dados:**
1. `loadJSONData()` → constrói `afastamentos[ano][mes][dia]` e `detalhesAfastamentos[ano][mes][dia]`
2. `loadAfastamentosFirestore()` → mescla `afastamentos_admin` por cima (additive)
3. `reloadAfastamentosData()` → repete 1+2 sem refetch de rede

**Estrutura year-aware:** `afastamentos[ano][mes][dia]` e `detalhesAfastamentos[ano][mes][dia]`. Seletor 2026/2027 via `currentYear` e `switchYear(year)`.

**Gap filling:** dias do afastamento não cobertos por substituto mostram "ainda não definido" automaticamente via `mergeAfastamentoFirestoreRecord`.

**Validações no salvar:**
1. Defensor e datas obrigatórios
2. Fim não pode ser anterior ao início
3. Tipo "outro" exige texto
4. Por substituto: início/fim dentro do período do afastamento
5. Por DP: sem sobreposição entre substitutos

## Arquitetura da Edição de Titulares

**Fluxo de dados:**
1. `loadJSONData()` → snapshot imutável em `_jsonDesignacoesBkDefensorias`
2. `loadTitularesFirestore()` → lê `titulares_admin`, substitui `historico_titulares` em memória, re-renderiza
3. `reloadTitularesData()` → restaura snapshot e reaplicar Firestore (usado ao cancelar)

**Resolução por data:** `getTitularForDPOnDay(dpNum, mes, dia)` — intervalo inclusivo (`inicio <= date <= fim`; `fim == null` = vigente). Retorna a entrada com `inicio` mais recente entre as válidas.

**Ordenação no modal:** `fim === null` (ativo) → topo; `fim === ''` (histórico novo em branco) → final; datas preenchidas → mais recente primeiro.

**Validações:** nome obrigatório, início obrigatório, `fim >= inicio` se preenchido, máximo 1 entrada sem `fim` por DP.

## Arquitetura da Seção Atribuições

**Preservação de formatação (mecanismo chave — dupla aplicação):**
- `execCommand('foreColor')` cria `<span>` — ao apagar o texto, o span some
- Solução: ao usar cor/bold/italic/size na toolbar, estilo aplicado **também ao `<td>`** via `td.style.*`
- Novo texto digitado herda via CSS cascade
- "Limpar formatação": além de `execCommand('removeFormat')`, zera `td.style.color/backgroundColor/fontWeight/fontStyle/textDecoration/fontSize`

**Segurança contra reconstrução do DOM:** `renderAtribuicoes()` verifica se `_atrModoEdicao` ativo → chama `_atrSairModoEdicao()` antes de reconstruir innerHTML. `showLanding()` também chama `_atrSairModoEdicao()`.

**`_atrResolverDefensor(dpKey)`:** não chama `getCurrentTitular()` (local a `renderDefensorias`). Lógica duplicada inline — percorre `historico_titulares` e retorna entrada com `inicio` mais recente que cobre hoje.

## Arquitetura da Toolbar RTE

- **Elemento único** `#rich-editor-toolbar` no DOM, movido via `insertBefore` para junto do editor ativo
- `mousedown + preventDefault()` preserva seleção ao clicar na toolbar
- `_rteSaveRange()` / `_rteRestoreRange()` — salva/restaura seleção via `Range.cloneRange()`
- `_rteMountTabelaHandlers()` — **função compartilhada** entre Atribuições e Adote. Usa `_rteTargetEl` (global) como referência ao TD ativo
- `RTE_EMOJIS` — categorias: Comuns, Jurídico, Pessoas, Status, Natureza/AM
- `_ATR_FONTSIZE_PX` — mapa HTML size (1–7) → px

## Arquitetura da Detecção de Ex-membros

- **`orphanExMembros`** — defensores em `titulares_admin` (Firestore, como texto livre) sem DP ativa que não constam no dicionário `defensores` do JSON. Aparecem no accordion "Ex-membros".
- **`orphanCurrentMembros`** — defensores cadastrados via UI antes de existir no JSON; detectados por DP ativa no Firestore mas ausentes de `defensores`. Exibidos normalmente nos cards.
- **Filtro `!/^dp\d+-vaga$/i`** — impede que placeholders de DPs vagas sejam contados como defensores.
- **`getFutureTitular(dpKey)`** — detecta membros com início futuro (`inicio > today && fim === null`). Excluídos de `orphanExMembros`.
