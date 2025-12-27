"""
Tax calculator service - Australian tax system
Migrated from original tax_calculator.py
"""
from decimal import Decimal
from typing import Dict, List
import logging

from database import execute_async

logger = logging.getLogger(__name__)

# Australian tax brackets for 2023-2024
TAX_BRACKETS_2023_2024 = [
    {"min": 0, "max": 18200, "rate": 0.0, "base": 0},
    {"min": 18201, "max": 45000, "rate": 0.19, "base": 0},
    {"min": 45001, "max": 120000, "rate": 0.325, "base": 5092},
    {"min": 120001, "max": 180000, "rate": 0.37, "base": 29467},
    {"min": 180001, "max": float('inf'), "rate": 0.45, "base": 51667}
]

MEDICARE_LEVY_RATE = 0.02  # 2%

def calculate_income_tax(taxable_income: Decimal) -> Decimal:
    """Calculate income tax based on Australian tax brackets"""
    income = float(taxable_income)
    
    for bracket in TAX_BRACKETS_2023_2024:
        if bracket["min"] <= income <= bracket["max"]:
            base_tax = Decimal(str(bracket["base"]))
            rate = Decimal(str(bracket["rate"]))
            excess = taxable_income - Decimal(str(bracket["min"]))
            tax = base_tax + (excess * rate)
            return tax.quantize(Decimal('0.01'))
    
    return Decimal("0")

def calculate_medicare_levy(taxable_income: Decimal) -> Decimal:
    """Calculate Medicare levy (2% of taxable income)"""
    levy = taxable_income * Decimal(str(MEDICARE_LEVY_RATE))
    return levy.quantize(Decimal('0.01'))

async def calculate_tax(
    user_id: int,
    financial_year: str,
    gross_income: Decimal,
    deductions: Decimal = Decimal("0")
) -> Dict:
    """
    Calculate comprehensive tax information
    """
    # Calculate taxable income
    taxable_income = gross_income - deductions
    if taxable_income < 0:
        taxable_income = Decimal("0")
    
    # Calculate components
    tax_payable = calculate_income_tax(taxable_income)
    medicare_levy = calculate_medicare_levy(taxable_income)
    total_tax = tax_payable + medicare_levy
    net_income = gross_income - total_tax
    
    # Calculate effective tax rate
    effective_rate = 0.0
    if gross_income > 0:
        effective_rate = float((total_tax / gross_income) * 100)
    
    result = {
        "financial_year": financial_year,
        "gross_income": gross_income,
        "taxable_income": taxable_income,
        "tax_payable": tax_payable,
        "medicare_levy": medicare_levy,
        "total_tax": total_tax,
        "net_income": net_income,
        "effective_tax_rate": round(effective_rate, 2)
    }
    
    # Save to database
    try:
        query = """
            INSERT INTO tax_calculations 
            (user_id, financial_year, gross_income, taxable_income, tax_payable, medicare_levy, total_tax, net_income)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """
        await execute_async(
            query,
            user_id,
            financial_year,
            gross_income,
            taxable_income,
            tax_payable,
            medicare_levy,
            total_tax,
            net_income
        )
    except Exception as e:
        logger.error(f"Failed to save tax calculation: {e}")
    
    return result

async def get_user_tax_history(user_id: int, limit: int = 10) -> List[Dict]:
    """Get user's tax calculation history"""
    query = """
        SELECT id, financial_year, gross_income, total_tax, net_income, calculated_at
        FROM tax_calculations
        WHERE user_id = $1
        ORDER BY calculated_at DESC
        LIMIT $2
    """
    results = await execute_async(query, user_id, limit, fetch_all=True)
    return [dict(row) for row in results]

def get_tax_brackets_info() -> List[Dict]:
    """Get tax bracket information"""
    return [
        {
            "range": f"${int(bracket['min']):,} - ${int(bracket['max']):,}" if bracket['max'] != float('inf') else f"${int(bracket['min']):,}+",
            "rate": f"{bracket['rate'] * 100}%",
            "base_tax": f"${bracket['base']:,.2f}"
        }
        for bracket in TAX_BRACKETS_2023_2024
    ]
