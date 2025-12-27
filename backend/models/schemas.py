"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from decimal import Decimal

# Auth Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    is_active: bool
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Account Models
class AccountCreate(BaseModel):
    account_type: str = Field(default="savings", pattern="^(savings|checking)$")
    initial_balance: Decimal = Field(default=Decimal("0.00"), ge=0)

class AccountResponse(BaseModel):
    id: int
    user_id: int
    account_number: str
    account_type: str
    balance: Decimal
    currency: str
    is_active: bool
    created_at: datetime
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }

# Transfer Models
class TransferRequest(BaseModel):
    from_account_number: str
    to_account_number: str
    amount: Decimal = Field(..., gt=0, le=1000000)
    description: Optional[str] = None
    idempotency_key: Optional[str] = None

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        if v > 1000000:
            raise ValueError('Amount exceeds maximum allowed')
        # Ensure 2 decimal places
        return round(v, 2)

class TransferResponse(BaseModel):
    transaction_id: str
    from_account_number: str
    to_account_number: str
    amount: Decimal
    fee: Decimal
    total_amount: Decimal
    status: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }

class BalanceResponse(BaseModel):
    account_number: str
    balance: Decimal
    currency: str
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

# Tax Calculator Models
class TaxCalculationRequest(BaseModel):
    financial_year: str = Field(..., pattern="^\d{4}-\d{4}$")
    gross_income: Decimal = Field(..., gt=0)
    deductions: Optional[Decimal] = Field(default=Decimal("0"), ge=0)

    @validator('financial_year')
    def validate_financial_year(cls, v):
        years = v.split('-')
        if len(years) != 2:
            raise ValueError('Financial year must be in format YYYY-YYYY')
        start_year = int(years[0])
        end_year = int(years[1])
        if end_year != start_year + 1:
            raise ValueError('Financial year must be consecutive years')
        return v

class TaxCalculationResponse(BaseModel):
    financial_year: str
    gross_income: Decimal
    taxable_income: Decimal
    tax_payable: Decimal
    medicare_levy: Decimal
    total_tax: Decimal
    net_income: Decimal
    effective_tax_rate: float
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

class TaxCalculationHistory(BaseModel):
    id: int
    financial_year: str
    gross_income: Decimal
    total_tax: Decimal
    net_income: Decimal
    calculated_at: datetime
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }

# Error Response
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
