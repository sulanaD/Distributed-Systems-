# Distributed Banking System

A full-stack distributed banking application with **FastAPI backend**, **React frontend**, and distributed features including Redis caching, Kafka event streaming, and PostgreSQL database.

## 🚀 Features

### Banking Features
- User Authentication (JWT + bcrypt)
- Account Management (Savings/Checking)
- Fund Transfers with 6-tier fee structure
- Transaction History & Audit Logs

### Tax Calculator
- Australian tax calculation
- Medicare levy calculation
- Tax history tracking

### Distributed Systems
- **Redis Caching** (sessions, balances, idempotency)
- **Distributed Locking** (prevent race conditions)
- **Kafka Event Streaming** (transaction events)
- **Idempotency** (duplicate prevention)

## 📦 Tech Stack

**Backend**: FastAPI (Python 3.11), PostgreSQL 15, Redis 7, Apache Kafka  
**Frontend**: React 18, Vite, TailwindCSS, React Router  
**Infrastructure**: Docker, Docker Compose, Nginx

## 🚀 Quick Start

```bash
# Start all services
docker compose up -d --build

# Check status
docker compose ps

# Access the app
open http://localhost
```

**Test Accounts**:
- Email: `alice@example.com` / Password: `password`
- Email: `bob@example.com` / Password: `password`

## 📖 API Docs

Visit http://localhost:8000/docs for interactive API documentation.

## 🛑 Stop Services

```bash
docker compose down
```

For full documentation, see the detailed README files in the project.
