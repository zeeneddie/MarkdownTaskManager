# MarQed.ai Client Portal

**Status:** Fase A - Multi-Tenant Foundation
**Start:** Week 158 (2026-01-15)

## Project Structuur

```
marqed-portal/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── models/         # SQLAlchemy models
│   │   ├── services/       # Business logic
│   │   ├── middleware/     # Tenant middleware
│   │   └── core/           # Config, security, database
│   ├── migrations/         # Alembic migrations
│   └── tests/              # Pytest tests
│
├── frontend/               # React + Refine frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Route pages
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API clients
│   │   ├── store/          # State management
│   │   └── types/          # TypeScript types
│   └── public/             # Static assets
│
└── README.md               # This file
```

## Tech Stack

### Backend
- **Framework:** FastAPI
- **ORM:** SQLAlchemy 2.0+
- **Database:** PostgreSQL with Row-Level Security
- **Auth:** JWT tokens
- **Migrations:** Alembic

### Frontend
- **Framework:** React 18+
- **Admin Framework:** Refine
- **UI Components:** shadcn/ui
- **Styling:** Tailwind CSS
- **State:** React Query + Zustand

## Multi-Tenant Architecture

### Isolation Strategy: Row-Level Security (RLS)

```
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Tenant A   │  │  Tenant B   │  │  Tenant C   │             │
│  │  (marqed)   │  │   (hci)     │  │ (fysioone)  │             │
│  ├─────────────┤  ├─────────────┤  ├─────────────┤             │
│  │ tenant_id=1 │  │ tenant_id=2 │  │ tenant_id=3 │             │
│  │ Projects    │  │ Projects    │  │ Projects    │             │
│  │ Users       │  │ Users       │  │ Users       │             │
│  │ Stories     │  │ Stories     │  │ Stories     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  RLS Policy: WHERE tenant_id = current_setting('app.tenant_id') │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Development Phases

- [x] Week 158-159: Multi-Tenant Infrastructure
- [ ] Week 160-161: Authentication & Authorization
- [ ] Week 162-163: Basic Frontend
- [ ] Week 164+: Core Features (Fase B)

---
*Part of MarQed.ai Platform - Week 158*
