"""
Authentication router for FemCare AI.
Handles user registration, login, and profile management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app import models, schemas
from app.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_user
)
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    """
    # Check if email already exists
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = models.User(
        email=user_data.email,
        name=user_data.name,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create initial health streaks
    streak_types = ["logging", "exercise", "sleep", "hydration"]
    for streak_type in streak_types:
        streak = models.HealthStreak(user_id=new_user.id, streak_type=streak_type)
        db.add(streak)
    
    # Award first achievement
    achievement = models.Achievement(
        user_id=new_user.id,
        achievement_type="first_log",
        title="Welcome to FemCare AI! 🌟",
        description="You've taken the first step towards better health tracking.",
        icon="🌟"
    )
    db.add(achievement)
    db.commit()
    
    return new_user


@router.post("/login", response_model=schemas.Token)
async def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """
    Login and get an access token.
    """
    # Find user
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/profile", response_model=schemas.UserResponse)
async def get_profile(current_user: models.User = Depends(get_current_user)):
    """
    Get the current user's profile.
    """
    return current_user


@router.put("/profile", response_model=schemas.UserResponse)
async def update_profile(
    update_data: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's profile.
    """
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_dict.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    # Check for "full profile" achievement
    profile_complete = all([
        current_user.date_of_birth,
        current_user.weight,
        current_user.height
    ])
    
    if profile_complete:
        existing_achievement = db.query(models.Achievement).filter(
            models.Achievement.user_id == current_user.id,
            models.Achievement.achievement_type == "full_profile"
        ).first()
        
        if not existing_achievement:
            achievement = models.Achievement(
                user_id=current_user.id,
                achievement_type="full_profile",
                title="Profile Complete ✅",
                description="You've filled out all your profile information!",
                icon="✅"
            )
            db.add(achievement)
            db.commit()
    
    return current_user


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete the current user's account and all associated data.
    """
    db.delete(current_user)
    db.commit()
    return None
