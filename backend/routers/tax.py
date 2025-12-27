"""
Tax calculator router
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List

from models.schemas import TaxCalculationRequest, TaxCalculationResponse, TaxCalculationHistory
from dependencies import get_current_active_user
from services.tax_service import calculate_tax, get_user_tax_history, get_tax_brackets_info

router = APIRouter()

@router.post("/calculate", response_model=TaxCalculationResponse)
async def calculate_taxes(
    tax_data: TaxCalculationRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Calculate tax based on income"""
    try:
        result = await calculate_tax(
            user_id=current_user['id'],
            financial_year=tax_data.financial_year,
            gross_income=tax_data.gross_income,
            deductions=tax_data.deductions
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tax calculation failed: {str(e)}"
        )

@router.get("/history", response_model=List[TaxCalculationHistory])
async def get_tax_history(
    limit: int = 10,
    current_user: dict = Depends(get_current_active_user)
):
    """Get tax calculation history"""
    history = await get_user_tax_history(current_user['id'], limit)
    return history

@router.get("/brackets")
async def get_tax_brackets():
    """Get Australian tax brackets information"""
    return {
        "financial_year": "2023-2024",
        "brackets": get_tax_brackets_info(),
        "medicare_levy": "2.0%"
    }
