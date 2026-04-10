# Polo Médio Amazonas 2026 — Guia de Contexto para IA

## O que é este projeto

Site HTML responsivo (`index.html`) para gerenciar designações semanais e ausências dos Defensores Públicos do Polo Médio Amazonas em 2026. Tecnologias: HTML5, CSS3, JavaScript vanilla. Publicado via GitHub Pages em https://lumabandeira.github.io/polo-medio-amazonas/

- **5 defensores ativos**, **12 Defensorias Públicas**
- Regra central: alternância semanal obrigatória entre **Grupo A** e **Grupo B**

---

## Firebase (autenticação e banco de dados)

O site usa **Firebase** para login e edição de conteúdo. Console: https://console.firebase.google.com/project/polo-medio-as

### Serviços ativos
- **Firebase Auth** — login por e-mail/senha. 40 usuários (3 admins + 37 viewers).
- **Firestore** — banco de dados em tempo real. Projeto: `polo-medio-as`

### Estrutura do Firestore
```
usuarios/{uid}
  role: "admin" | "viewer"
  nome: "..."

secoes/regra_alternancia
  html: "..."           ← conteúdo editável da seção Regra de Alternância
  atualizado_por: "..."
  atualizado_em: timestamp

secoes/ferias_folgas
  html: "..."           ← conteúdo editável da seção Férias/Folgas/Licenças
  atualizado_por: "..."
  atualizado_em: timestamp

afastamentos_admin/{id}   ← afastamentos adicionados pelo admin via calendário
  defensor: "elton"       ← chave do defensor (mesmo padrão dos JSONs)
  tipo: "ferias" | "folga" | "licenca_especial"
  data_inicio: "2026-04-15"
  data_fim: "2026-04-20"
  portaria_numero: "Portaria nº 123/2026-GSPG/DPE/AM"
  portaria_url: "https://..."   ← link do PDF do Diário Oficial
  portaria_sei: "26.0.000..."
  designacoes: [{ dp: "5", substituto: "eliaquim" }, ...]
  criado_por: "email@..."
  criado_em: timestamp
  atualizado_por: "email@..."
  atualizado_em: timestamp
```

> **Nota:** Os dados dos JSONs locais (`docs/afastamentos-2026.json` e `docs/designacoes-2026.json`) continuam sendo a base. A coleção `afastamentos_admin` contém apenas os registros adicionados/editados pelo admin via interface. Os dois são mesclados em memória ao carregar a página.

### Regras de segurança do Firestore
- Leitura: apenas usuários autenticados
- Escrita: apenas usuários com `role == "admin"`

### Como funciona o login no site
1. Página carrega → overlay de login cobre tudo
2. Usuário digita e-mail + senha → Firebase Auth valida
3. Site lê `role` no Firestore (`usuarios/{uid}`)
4. Admin: vê badge "ADMIN" + botões ✏️ Editar nas seções
5. Viewer: vê o site normalmente sem botões de edição

### Seções editáveis (admin)
- **Regra de Alternância** (`#regra_alternancia-html`) — edição inline com contentEditable
- **Férias/Folgas/Licenças** (`#ferias_folgas-html`) — edição inline com contentEditable
- Edições salvas em `secoes/{id}` no Firestore e carregadas a cada login

### Funções JS do Firebase no index.html
- `fazerLogin()` — autentica com Firebase Auth
- `fazerLogout()` — encerra sessão
- `carregarConteudoFirestore()` — carrega conteúdo editável do Firestore
- `iniciarEdicao(secaoId)` — ativa contentEditable na seção
- `salvarSecao(secaoId)` — salva HTML no Firestore
- `cancelarEdicao(secaoId)` — restaura conteúdo original
- `mostrarToast(msg)` — exibe notificação temporária

### Para adicionar novos usuários
Firebase Console → Authentication → Adicionar usuário → copiar UID → Firestore → coleção `usuarios` → novo documento com o UID → campos `role` e `nome`

---

## Mapa de Tarefas → Arquivos a Ler

Antes de qualquer alteração, leia **apenas** os arquivos listados para a tarefa. Não leia o projeto todo.

### Adicionar férias / folga / licença
1. `docs/regras/ausencias.md` — limites, tipos e interpretação de textos
2. `docs/escalas/ferias-folgas-2026.md` — tabela mestra de ausências
3. `docs/defensores/[nome-do-defensor].md` — dados do defensor afetado
4. `docs/site/processo-atualizacao.md` — ordem obrigatória de atualização do site

### Criar ou atualizar tabela semanal de designações
1. `docs/regras/alternancia.md` — regra de Grupo A/B + checklist
2. `docs/regras/destaques-cores.md` — classes CSS e regra de fins de semana
3. `docs/site/padroes-codigo.md` — estrutura HTML das tabelas
4. `docs/escalas/ferias-folgas-2026.md` — quem está ausente no período

### Verificar quem é o defensor de uma DP
1. `docs/defensorias/lista-completa.md` — lista com defensor de cada DP

### Entender os grupos de alternância
1. `docs/defensorias/grupos-alternancia.md` — Grupo A e Grupo B (resumo rápido)
2. `docs/regras/alternancia.md` — regras detalhadas e exemplos

### Alterar estrutura ou comportamento do site (HTML/CSS/JS)
1. `docs/site/estrutura-html.md` — abas, IDs, organização geral
2. `docs/site/padroes-codigo.md` — padrões de código
3. `docs/site/validacoes-js.md` — funções JavaScript automáticas

### Consultar ausências de um defensor específico
1. `docs/defensores/[nome-do-defensor].md`

### Visão geral do calendário de ausências
1. `docs/escalas/calendario-visual-2026.md`

### Consultar designações diárias de janeiro/2026
1. `docs/escalas/designacoes-janeiro-2026.md`

---

## Estrutura de Arquivos do Projeto

```
index.html                          ← site completo (único arquivo do site)
CLAUDE.md                           ← este arquivo
docs/
├── INDEX.md                        ← índice de todos os arquivos docs/
├── defensores/
│   ├── jose-antonio.md
│   ├── icaro.md
│   ├── eliaquim.md
│   ├── elton.md
│   └── elaine.md
├── defensorias/
│   ├── lista-completa.md
│   └── grupos-alternancia.md
├── regras/
│   ├── alternancia.md
│   ├── ausencias.md
│   └── destaques-cores.md
├── escalas/
│   ├── ferias-folgas-2026.md
│   ├── calendario-visual-2026.md
│   └── designacoes-janeiro-2026.md
└── site/
    ├── estrutura-html.md
    ├── padroes-codigo.md
    ├── validacoes-js.md
    └── processo-atualizacao.md
github-pages/
├── README.md
└── .nojekyll
```

---

## Estado atual do site (atualizado em 09/04/2026)

### O que já foi implementado ✅
- **Sistema de login completo** — overlay de tela cheia, Firebase Auth, roles admin/viewer
- **Badge ADMIN** no header (visível só para admins, posicionado em top:75px left:20px)
- **Botão Sair** no header (top:60px right:20px)
- **Botão Início** no header (aparece ao entrar nas abas, some na landing)
- **Seções editáveis inline** — "Regra de Alternância" e "Férias/Folgas/Licenças" com título + conteúdo editáveis via contentEditable, salvos no Firestore
- **Coluna Diário Oficial no modal do calendário** — link clicável para o PDF ao clicar em dia com afastamento
- **Aba Tabela Completa removida** — Calendário Visual é a aba principal
- **Botões "Nova Aba" e "Sincronizar Planilha" removidos** — e todo código/CSS associado limpo
- **1 usuário admin cadastrado** — bandeira.lkp@gmail.com (role: admin, nome: Luma) no Firestore
- **Calendário interativo para admins** — admin pode adicionar/editar/remover afastamentos direto do calendário (dados salvos em `afastamentos_admin` no Firestore, mesclados com os JSONs em memória)

### O que ainda falta implementar ⏳
- **Cadastrar os outros 39 usuários** (2 admins + 37 viewers) no Firebase Auth + Firestore
- **Edição dos defensores titulares de cada DP** — atualmente vem do `docs/designacoes-2026.json`, sem interface de edição
- **Dados privados da equipe** — WhatsApp, contatos internos (estrutura no Firestore planejada mas não implementada)

### Decisões de arquitetura já tomadas
- Sem automação do Diário Oficial — admin insere links manualmente
- Sem migração de hospedagem — continua no GitHub Pages
- Dados de afastamentos e designações ainda vêm dos JSONs locais (`docs/afastamentos-2026.json` e `docs/designacoes-2026.json`) — apenas as seções de texto estático foram migradas para o Firestore
- Função `syncFromSheets()` removida definitivamente

---

## Regras Críticas (resumo rápido)

- **Arquivo único:** existe apenas um `index.html` na raiz. Nunca duplicar.
- **Alternância semanal:** Grupo A e Grupo B alternam toda semana sem exceção. Ver `docs/regras/alternancia.md`.
- **Destaques apenas em dias úteis:** nunca aplicar classes `itacoatiara` ou `silves` em sábados/domingos.
- **Máximo 2 defensores ausentes** ao mesmo tempo; mínimo 3 ativos.
- **Aba Tabela Completa foi removida** — o Calendário Visual é a aba principal de ausências.
- **Nunca editar seções do Firestore diretamente no HTML** — o conteúdo vem do Firestore e sobrescreve o HTML padrão ao carregar.
