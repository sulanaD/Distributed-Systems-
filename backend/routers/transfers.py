"""
Transfers router
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List

from models.schemas import TransferRequest, TransferResponse
from dependencies import get_current_active_user
from services.transaction_service import process_transfer, get_transaction_history

router = APIRouter()

@router.post("/", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    transfer_data: TransferRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """Process a fund transfer"""
    try:
        result = await process_transfer(
            from_account_number=transfer_data.from_account_number,
            to_account_number=transfer_data.to_account_number,
            amount=transfer_data.amount,
            user_id=current_user['id'],
            description=transfer_data.description,
            idempotency_key=transfer_data.idempotency_key
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transfer failed: {str(e)}"
        )

@router.get("/history", response_model=List[TransferResponse])
async def get_transfer_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_active_user)
):
    """Get transfer history for current user"""
    history = await get_transaction_history(current_user['id'], limit)
    return history
