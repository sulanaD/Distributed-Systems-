"""
Accounts router
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List

from models.schemas import AccountCreate, AccountResponse, BalanceResponse
from dependencies import get_current_active_user
from services.account_service import (
    create_account,
    get_user_accounts,
    get_account_by_number,
    get_account_balance,
    delete_account
)

router = APIRouter()

@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_new_account(
    account_data: AccountCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new bank account"""
    account = await create_account(
        user_id=current_user['id'],
        account_type=account_data.account_type,
        initial_balance=account_data.initial_balance
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account"
        )
    
    return account

@router.get("/", response_model=List[AccountResponse])
async def list_accounts(current_user: dict = Depends(get_current_active_user)):
    """Get all accounts for current user"""
    accounts = await get_user_accounts(current_user['id'])
    return accounts

@router.get("/{account_number}", response_model=AccountResponse)
async def get_account(
    account_number: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get account details"""
    account = await get_account_by_number(account_number)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Verify ownership
    if account['user_id'] != current_user['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this account"
        )
    
    return account

@router.get("/{account_number}/balance", response_model=BalanceResponse)
async def get_balance(
    account_number: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Get account balance"""
    account = await get_account_by_number(account_number)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Verify ownership
    if account['user_id'] != current_user['id']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this account"
        )
    
    balance = await get_account_balance(account_number)
    
    return {
        "account_number": account_number,
        "balance": balance,
        "currency": account['currency']
    }

@router.delete("/{account_number}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account_endpoint(
    account_number: str,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete an account (soft delete)"""
    try:
        success = await delete_account(account_number, current_user['id'])
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete account"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
