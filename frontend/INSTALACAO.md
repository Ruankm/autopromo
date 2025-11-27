# Frontend - Instruções de Instalação

## ⚠️ **PRÉ-REQUISITO: Instalar Node.js**

Você precisa instalar o Node.js primeiro para usar `npm`.

### **Opção 1: Instalador Oficial (Recomendado)**

1. Baixe o Node.js LTS: https://nodejs.org/
2. Execute o instalador (.msi)
3. Reinicie o terminal
4. Verifique:
   ```bash
   node --version  # Deve mostrar v20.x.x ou superior
   npm --version   # Deve mostrar 10.x.x ou superior
   ```

### **Opção 2: Via Winget (Windows 11)**

```bash
winget install OpenJS.NodeJS.LTS
```

---

## 🚀 **Após Instalar Node.js**

```bash
cd frontend
npm install
npm run dev
```

O frontend estará em: `http://localhost:3000`

---

## 🔧 **Variáveis de Ambiente**

Crie `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## ✅ **Verificar se Backend está Configurado para CORS**

O backend já foi atualizado para permitir `http://localhost:3000`.

Certifique-se de que `backend/main.py` tem:
```python
allow_origins=["http://localhost:3000", ...],
```
