# Polo Médio Amazonas - Designações e Calendário 2026

Site web para visualização das designações dos Defensores Públicos e calendário de afastamentos do Polo Médio Amazonas em 2026.

> **⚠️ IMPORTANTE:** Use o arquivo `index.html` da **raiz do projeto** para publicação. Não é necessário manter cópias duplicadas - isso evita inconsistências.

## 🚀 Como Publicar no GitHub Pages

### Passo 1: Criar um Repositório no GitHub

1. Acesse [GitHub.com](https://github.com) e faça login
2. Clique no botão **"+"** no canto superior direito → **"New repository"**
3. Preencha:
   - **Repository name:** `polo-medio-amazonas-2026` (ou outro nome de sua escolha)
   - **Description:** "Designações dos Defensores Públicos e Calendário de Afastamentos 2026"
   - **Visibilidade:** Público ou Privado (sua escolha)
   - **NÃO marque** "Add a README file" (já temos um)
4. Clique em **"Create repository"**

### Passo 2: Fazer Upload dos Arquivos

**⚠️ IMPORTANTE:** Use o arquivo `index.html` da **raiz do projeto**, não é necessário manter cópias duplicadas.

#### Opção A: Pelo Site do GitHub (Mais Fácil)

1. No repositório criado, clique em **"uploading an existing file"**
2. Arraste o arquivo `index.html` da **raiz do projeto** para a área de upload
3. Role até o final da página e clique em **"Commit changes"**

#### Opção B: Usando Git (Mais Profissional)

Se você tem Git instalado no computador:

```bash
# Navegue até a raiz do projeto
cd "DOCUMENTOS/0. Fiscal de contrato e Cordenação/0. Assessoria da Coordenação/0. Designações Semanais das DPs em 2026"

# Inicialize o repositório Git
git init

# Adicione o arquivo principal
git add index.html

# Faça o commit
git commit -m "Adiciona site do Polo Médio Amazonas"

# Adicione o repositório remoto (substitua SEU-USUARIO pelo seu usuário do GitHub)
git remote add origin https://github.com/SEU-USUARIO/polo-medio-amazonas-2026.git

# Envie os arquivos
git branch -M main
git push -u origin main
```

### Passo 3: Ativar o GitHub Pages

1. No repositório do GitHub, vá em **Settings** (Configurações)
2. No menu lateral esquerdo, clique em **Pages**
3. Em **Source**, selecione:
   - **Branch:** `main` (ou `master`)
   - **Folder:** `/ (root)`
4. Clique em **Save**

### Passo 4: Acessar o Site

Após alguns minutos, seu site estará disponível em:
```
https://SEU-USUARIO.github.io/polo-medio-amazonas-2026/
```

(Substitua `SEU-USUARIO` pelo seu nome de usuário do GitHub e `polo-medio-amazonas-2026` pelo nome do repositório que você criou)

## 📝 Atualizando o Site

Sempre que precisar atualizar as informações do site:

### Método 1: Pelo Site do GitHub (Mais Simples) ⭐ RECOMENDADO

1. Acesse seu repositório no GitHub (ex: `https://github.com/SEU-USUARIO/polo-medio-amazonas-2026`)
2. Clique no arquivo `index.html`
3. Clique no ícone de **lápis** (✏️) no canto superior direito para editar
4. **OU** clique no botão **"..."** (três pontos) → **"Delete file"** para deletar o arquivo antigo
5. Depois clique em **"Add file"** → **"Upload files"**
6. Arraste o arquivo `index.html` da **raiz do projeto** do seu computador
7. Role até o final da página
8. Em **"Commit changes"**, escreva uma mensagem como: "Atualiza site com melhorias de responsividade"
9. Clique em **"Commit changes"** (ou **"Commit new file"**)
10. Aguarde 1-2 minutos e o site será atualizado automaticamente!

### Método 2: Usando Git (Para Quem Já Usa)

Se você já tem o repositório clonado no seu computador:

```bash
# Navegue até a raiz do projeto
cd "DOCUMENTOS/0. Fiscal de contrato e Cordenação/0. Assessoria da Coordenação/0. Designações Semanais das DPs em 2026"

# Adicione as mudanças
git add index.html

# Faça o commit
git commit -m "Atualiza site com melhorias de responsividade"

# Envie para o GitHub
git push origin main
```

### ⏱️ Tempo de Atualização

- O GitHub Pages geralmente atualiza o site em **1-5 minutos**
- Se não atualizar, tente limpar o cache do navegador (Ctrl+F5 ou Cmd+Shift+R)
- Você pode verificar o status da publicação em: **Settings → Pages**

## 🔒 Privacidade

- **Repositório Público:** Qualquer pessoa com o link pode acessar o site
- **Repositório Privado:** Apenas pessoas com acesso ao repositório podem ver o site (mas o GitHub Pages ainda funciona)

## 📱 Funcionalidades do Site

- ✅ Visualização das designações dos defensores
- ✅ Calendário interativo com navegação por mês
- ✅ Visualização visual dos períodos de afastamento
- ✅ Design responsivo (funciona em celular e computador)
- ✅ Funciona completamente offline após carregar

## 🆘 Precisa de Ajuda?

Se tiver dúvidas sobre como usar o GitHub Pages, consulte a [documentação oficial](https://docs.github.com/en/pages).
