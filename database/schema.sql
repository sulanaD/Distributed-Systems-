-- PostgreSQL Schema for Australian Tax Calculator System
-- Run this file to set up the database:
-- 1. Create database: createdb taxdb
-- 2. Run schema: psql -d taxdb -f schema.sql

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS tax_calculations;
DROP TABLE IF EXISTS users;

-- Users table for authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

-- Index for faster queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_tax_calculations_user_id ON tax_calculations(user_id);

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
