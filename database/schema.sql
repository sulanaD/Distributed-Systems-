-- PostgreSQL Schema for Distributed Banking System
-- Combines Tax Calculator with Banking Features
-- Run this file to set up the database:
-- 1. Create database: createdb bankingdb
-- 2. Run schema: psql -d bankingdb -f schema.sql

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS tax_calculations;
DROP TABLE IF EXISTS users;

-- Users table for authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accounts table for banking
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    account_number VARCHAR(20) UNIQUE NOT NULL,
    account_type VARCHAR(20) DEFAULT 'savings' CHECK (account_type IN ('savings', 'checking')),
    balance DECIMAL(15, 2) DEFAULT 0.00 CHECK (balance >= 0),
    currency VARCHAR(3) DEFAULT 'AUD',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transactions table for transfer history
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(36) UNIQUE NOT NULL,
    from_account_id INTEGER REFERENCES accounts(id),
    to_account_id INTEGER REFERENCES accounts(id),
    amount DECIMAL(15, 2) NOT NULL CHECK (amount > 0),
    fee DECIMAL(10, 2) DEFAULT 0.00,
    total_amount DECIMAL(15, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'reversed')),
    description TEXT,
    idempotency_key VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit log for tracking all operations
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tax calculations history table
CREATE TABLE tax_calculations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    financial_year VARCHAR(10) NOT NULL,
    gross_income DECIMAL(12, 2) NOT NULL,
    taxable_income DECIMAL(12, 2) NOT NULL,
    tax_payable DECIMAL(12, 2) NOT NULL,
    medicare_levy DECIMAL(12, 2) NOT NULL,
    total_tax DECIMAL(12, 2) NOT NULL,
    net_income DECIMAL(12, 2) NOT NULL,
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for faster queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_accounts_user_id ON accounts(user_id);
CREATE INDEX idx_accounts_account_number ON accounts(account_number);
CREATE INDEX idx_accounts_is_active ON accounts(is_active);
CREATE INDEX idx_transactions_transaction_id ON transactions(transaction_id);
CREATE INDEX idx_transactions_from_account ON transactions(from_account_id);
CREATE INDEX idx_transactions_to_account ON transactions(to_account_id);
CREATE INDEX idx_transactions_idempotency_key ON transactions(idempotency_key);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX idx_tax_calculations_user_id ON tax_calculations(user_id);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to auto-update updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_accounts_updated_at
    BEFORE UPDATE ON accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default test users with accounts
INSERT INTO users (email, password_hash, first_name, last_name) VALUES
('alice@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIKMW2QwVe', 'Alice', 'Johnson'),
('bob@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIKMW2QwVe', 'Bob', 'Smith');

INSERT INTO accounts (user_id, account_number, account_type, balance) VALUES
(1, 'ACC1000000001', 'savings', 10000.00),
(1, 'ACC1000000002', 'checking', 5000.00),
(2, 'ACC2000000001', 'savings', 15000.00),
(2, 'ACC2000000002', 'checking', 8000.00);

-- Comments for documentation
COMMENT ON TABLE users IS 'User accounts for authentication and profile management';
COMMENT ON TABLE accounts IS 'Bank accounts linked to users';
COMMENT ON TABLE transactions IS 'Transaction history for all transfers';
COMMENT ON TABLE audit_log IS 'Audit trail for all system operations';
COMMENT ON TABLE tax_calculations IS 'Historical tax calculations for users';
COMMENT ON COLUMN transactions.idempotency_key IS 'Unique key to prevent duplicate transactions';
