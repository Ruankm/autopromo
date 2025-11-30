# 🚀 Git - Comandos Úteis e Boas Práticas

## ✅ Git Inicializado!

Seu projeto agora está sob controle de versão. Commit inicial criado com sucesso!

---

## 📚 Comandos Git Essenciais

### Ver status do repositório:
```bash
git status
```

### Adicionar mudanças:
```bash
# Adicionar todos os arquivos modificados
git add .

# Adicionar arquivo específico
git add arquivo.py
```

### Fazer commit:
```bash
git commit -m "Descrição clara das mudanças"
```

### Ver histórico:
```bash
git log --oneline --graph --decorate --all
```

### Criar branch para nova feature:
```bash
git checkout -b feature/nome-da-feature
```

### Voltar para main:
```bash
git checkout master
```

### Desfazer mudanças **NÃO** commitadas:
```bash
# Arquivo específico
git checkout -- arquivo.py

# Todos os arquivos
git checkout .
```

### Desfazer último commit (mantendo mudanças):
```bash
git reset --soft HEAD~1
```

---

## 🔐 Arquivos Protegidos (não vão para Git)

Já configurado no `.gitignore`:
- ✅ Senhas e chaves (`.env`, `.env.local`, `.env.evolution`)
- ✅ Node modules (`frontend/node_modules/`)
- ✅ Python venv (`backend/.venv/`)
- ✅ Evolution API volumes (`evolution_instances/`, `evolution_store/`)
- ✅ Banco de dados local
- ✅ Logs
- ✅ Brain da Antigravity (`.gemini/`)

---

## 🌟 Workflow Recomendado

### 1. Antes de começar a trabalhar:
```bash
git status  # Ver se há mudanças pendentes
```

### 2. Ao terminar uma feature:
```bash
git add .
git commit -m "feat: descrição da feature"
```

### 3. Tipos de commit (convenção):
- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Documentação
- `refactor:` - Refatoração de código
- `test:` - Testes
- `chore:` - Tarefas gerais

### Exemplos:
```bash
git commit -m "feat: adiciona endpoint de desconexão WhatsApp"
git commit -m "fix: corrige erro 403 na Evolution API"
git commit -m "docs: atualiza README com instruções Git"
```

---

## 🔄 Conectar com GitHub/GitLab (Opcional)

### 1. Criar repositório no GitHub

### 2. Conectar e enviar:
```bash
git remote add origin https://github.com/seu-usuario/autopromo.git
git push -u origin master
```

---

## ⚠️ IMPORTANTE

**NÃO COMMITE:**
- Senhas ou tokens no código
- `.env` ou qualquer arquivo com credenciais
- Volumes Docker
- Node modules
- Python venv

Tudo já está protegido no `.gitignore`! ✅

---

## 📦 Estado Atual

**Commit Inicial:**
- ✅ 119 arquivos incluídos
- ✅ Backend completo (FastAPI + Evolution API)
- ✅ Frontend completo (Next.js)
- ✅ Docker configs
- ✅ Documentação

**Branch:** `master`  
**Último commit:** "Initial commit: AutoPromo - WhatsApp integration complete with Evolution API"

---

## 🎯 Próximos Passos

1. **Teste o WhatsApp** - Tente conectar novamente (instância antiga deletada)
2. **Faça commits frequentes** - Cada feature = 1 commit
3. **Use branches** - Para features grandes
4. **Backup remoto** - Configure GitHub/GitLab quando quiser

**Happy coding! 🚀**
