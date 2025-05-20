from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Profile
from app.schemas.user import ProfileResponse, ProfileUpdate

router = APIRouter()

@router.get("/me", response_model=ProfileResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Получение профиля текущего пользователя
    """
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль не найден"
        )
    return current_user.profile

@router.put("/me", response_model=ProfileResponse)
def update_current_user_profile(
    profile_update: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновление профиля текущего пользователя
    """
    # Проверка существования профиля
    if not current_user.profile:
        # Создаем профиль если его нет
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(current_user)
    
    # Обновление полей профиля
    profile = current_user.profile
    
    if profile_update.first_name is not None:
        profile.first_name = profile_update.first_name
    
    if profile_update.last_name is not None:
        profile.last_name = profile_update.last_name
    
    if profile_update.bio is not None:
        profile.bio = profile_update.bio
    
    if profile_update.avatar_url is not None:
        profile.avatar_url = profile_update.avatar_url
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return profile