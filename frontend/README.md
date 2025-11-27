# AutoPromo Cloud - Frontend

Frontend do AutoPromo Cloud construído com Next.js 15, TypeScript, e Tailwind CSS.

## 🚀 Quick Start

```bash
# Instalar dependências
npm install

# Rodar em desenvolvimento
npm run dev

# Build de produção
npm run build
npm start
```

## 📁 Estrutura

```
frontend/
├── app/              # App Router (Next.js 15)
│   ├── layout.tsx    # Layout raiz
│   ├── page.tsx      # Landing page
│   ├── login/        # Tela de login
│   ├── register/     # Tela de cadastro
│   └── dashboard/    # Dashboard protegido
├── lib/              # Utilitários
│   └── api.ts        # Axios instance com interceptors
├── services/         # API services
│   └── auth.ts       # Autenticação
└── middleware.ts     # Proteção de rotas
```

## 🔐 Autenticação

- JWT armazenado em cookie (`autopromo_token`)
- Middleware protege rotas `/dashboard/*`
- Interceptors Axios para injeção automática do token

## 🎨 Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Linguagem**: TypeScript
- **Estilização**: Tailwind CSS + shadcn/ui
- **HTTP Client**: Axios
- **Gerenciamento de Estado**: React Hooks

## 🌐 Variáveis de Ambiente

Crie um arquivo `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 📝 TODO

- [ ] Implementar CRUD de Grupos (Fonte/Destino)
- [ ] Implementar CRUD de Tags de Afiliado
- [ ] Dashboard com estatísticas em tempo real
- [ ] Salvar configurações do usuário
