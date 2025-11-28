# Australian Tax Calculator System

A simple web application for calculating Australian income tax based on the 2024-2025 financial year tax brackets.

## Features

- User registration and authentication (JWT-based)
- Australian tax calculation with current tax brackets
- Medicare levy calculation
- Calculation history per user
- Responsive frontend design

## Project Structure

```
tax-system/
├── backend/
│   ├── app.py              # Flask application
│   ├── auth.py             # Authentication functions
│   ├── config.py           # Configuration
│   ├── database.py         # Database connection
│   ├── tax_calculator.py   # Tax calculation logic
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment variables template
├── frontend/
│   ├── index.html          # Main HTML file
│   ├── css/style.css       # Styles
│   └── js/app.js           # Frontend JavaScript
└── database/
    └── schema.sql          # PostgreSQL schema
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Node.js (optional, for serving frontend)

### 1. Database Setup

```bash
# Create database
createdb taxdb

# Run schema
cd database
psql -d taxdb -f schema.sql
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run the server
python app.py
```

The backend will run at `http://localhost:5000`

### 3. Frontend Setup

You can serve the frontend using Python's built-in HTTP server:

```bash
cd frontend
python -m http.server 8080
```

Or open `frontend/index.html` directly in your browser.

The frontend will be available at `http://localhost:8080`

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login and get JWT token |
| GET | `/api/auth/me` | Get current user (requires auth) |

### Tax Calculation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tax/calculate` | Calculate tax (requires auth) |
| GET | `/api/tax/history` | Get calculation history (requires auth) |
| GET | `/api/tax/brackets` | Get tax bracket information (public) |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check endpoint |

## 2024-2025 Tax Brackets (Australian Residents)

| Taxable Income | Tax Rate |
|---------------|----------|
| $0 - $18,200 | Nil |
| $18,201 - $45,000 | 16c for each $1 over $18,200 |
| $45,001 - $135,000 | $4,288 plus 30c for each $1 over $45,000 |
| $135,001 - $190,000 | $31,288 plus 37c for each $1 over $135,000 |
| $190,001+ | $51,638 plus 45c for each $1 over $190,000 |

Plus Medicare Levy of 2% on taxable income.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DB_HOST | PostgreSQL host | localhost |
| DB_PORT | PostgreSQL port | 5432 |
| DB_NAME | Database name | taxdb |
| DB_USER | Database user | postgres |
| DB_PASSWORD | Database password | - |
| JWT_SECRET_KEY | Secret for JWT tokens | - |
| FLASK_DEBUG | Enable debug mode | True |

## License

MIT License
