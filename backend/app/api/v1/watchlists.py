"""
Watchlist API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db import models
from app.db.schemas import WatchlistCreate, WatchlistResponse
from app.api.v1.auth import get_current_user

router = APIRouter()


@router.get("", response_model=List[WatchlistResponse])
async def get_watchlist(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user watchlist"""
    watchlist = db.query(models.Watchlist).filter(
        models.Watchlist.user_id == current_user.id
    ).all()
    
    return watchlist


@router.post("", response_model=WatchlistResponse)
async def add_to_watchlist(
    watchlist_data: WatchlistCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add stock to watchlist"""
    # Check if already in watchlist
    existing = db.query(models.Watchlist).filter(
        models.Watchlist.user_id == current_user.id,
        models.Watchlist.symbol == watchlist_data.symbol.upper()
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Stock already in watchlist"
        )
    
    db_watchlist = models.Watchlist(
        user_id=current_user.id,
        symbol=watchlist_data.symbol.upper(),
        exchange=watchlist_data.exchange,
        target_price=watchlist_data.target_price,
        notes=watchlist_data.notes
    )
    
    db.add(db_watchlist)
    db.commit()
    db.refresh(db_watchlist)
    
    return db_watchlist


@router.delete("/{watchlist_id}")
async def remove_from_watchlist(
    watchlist_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove stock from watchlist"""
    watchlist_item = db.query(models.Watchlist).filter(
        models.Watchlist.id == watchlist_id,
        models.Watchlist.user_id == current_user.id
    ).first()
    
    if not watchlist_item:
        raise HTTPException(
            status_code=404,
            detail="Watchlist item not found"
        )
    
    db.delete(watchlist_item)
    db.commit()
    
    return {"message": "Removed from watchlist"}


@router.delete("/symbol/{symbol}")
async def remove_from_watchlist_by_symbol(
    symbol: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove stock from watchlist by symbol"""
    watchlist_item = db.query(models.Watchlist).filter(
        models.Watchlist.symbol == symbol.upper(),
        models.Watchlist.user_id == current_user.id
    ).first()
    
    if not watchlist_item:
        raise HTTPException(
            status_code=404,
            detail="Stock not found in watchlist"
        )
    
    db.delete(watchlist_item)
    db.commit()
    
    return {"message": "Removed from watchlist"}

