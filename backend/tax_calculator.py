"""
Australian Tax Calculator - 2024-2025 Financial Year
Based on ATO tax brackets for Australian residents
"""

# Australian Tax Brackets 2024-2025 (for residents)
TAX_BRACKETS_2024_25 = [
    (18200, 0, 0),           # 0 - $18,200: Nil
    (45000, 0.16, 0),        # $18,201 - $45,000: 16c for each $1 over $18,200
    (135000, 0.30, 4288),    # $45,001 - $135,000: $4,288 plus 30c for each $1 over $45,000
    (190000, 0.37, 31288),   # $135,001 - $190,000: $31,288 plus 37c for each $1 over $135,000
    (float('inf'), 0.45, 51638)  # $190,001+: $51,638 plus 45c for each $1 over $190,000
]

# Medicare Levy rate
MEDICARE_LEVY_RATE = 0.02
MEDICARE_LEVY_THRESHOLD = 26000  # Approximate threshold for full levy

def calculate_income_tax(taxable_income: float) -> float:
    """
    Calculate income tax based on Australian tax brackets for 2024-2025
    """
    if taxable_income <= 0:
        return 0.0
    
    tax = 0.0
    previous_threshold = 0
    
    for threshold, rate, base_tax in TAX_BRACKETS_2024_25:
        if taxable_income <= threshold:
            if previous_threshold == 0:
                # First bracket (tax-free threshold)
                tax = 0
            else:
                tax = base_tax + (taxable_income - previous_threshold) * rate
            break
        previous_threshold = threshold
    
    return round(tax, 2)

def calculate_medicare_levy(taxable_income: float) -> float:
    """
    Calculate Medicare Levy (2% of taxable income)
    Simplified calculation - actual has shade-in thresholds
    """
    if taxable_income <= MEDICARE_LEVY_THRESHOLD:
        return 0.0
    
    return round(taxable_income * MEDICARE_LEVY_RATE, 2)

def calculate_tax(gross_income: float, deductions: float = 0) -> dict:
    """
    Calculate complete tax breakdown for Australian resident
    
    Args:
        gross_income: Total income before deductions
        deductions: Work-related deductions
    
    Returns:
        Dictionary with full tax breakdown
    """
    taxable_income = max(0, gross_income - deductions)
    
    income_tax = calculate_income_tax(taxable_income)
    medicare_levy = calculate_medicare_levy(taxable_income)
    total_tax = income_tax + medicare_levy
    net_income = gross_income - total_tax
    
    # Calculate effective tax rate
    effective_rate = (total_tax / gross_income * 100) if gross_income > 0 else 0
    
    return {
        'gross_income': round(gross_income, 2),
        'deductions': round(deductions, 2),
        'taxable_income': round(taxable_income, 2),
        'income_tax': round(income_tax, 2),
        'medicare_levy': round(medicare_levy, 2),
        'total_tax': round(total_tax, 2),
        'net_income': round(net_income, 2),
        'effective_tax_rate': round(effective_rate, 2),
        'financial_year': '2024-2025'
    }

def get_tax_brackets_info() -> list:
    """Return tax bracket information for display"""
    return [
        {'min': 0, 'max': 18200, 'rate': '0%', 'description': 'Tax-free threshold'},
        {'min': 18201, 'max': 45000, 'rate': '16%', 'description': '16c for each $1 over $18,200'},
        {'min': 45001, 'max': 135000, 'rate': '30%', 'description': '$4,288 plus 30c for each $1 over $45,000'},
        {'min': 135001, 'max': 190000, 'rate': '37%', 'description': '$31,288 plus 37c for each $1 over $135,000'},
        {'min': 190001, 'max': None, 'rate': '45%', 'description': '$51,638 plus 45c for each $1 over $190,000'}
    ]
