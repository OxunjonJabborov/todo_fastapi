import security
import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as Session

from database import get_db
from enums import Roles
from models import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token yaroqsiz yoki muddati tugagan",
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user_id = int(user_id)

    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise credentials_exception from None

    user = await db.scalar(select(User).where(User.id == user_id))

    if user is None:
        raise credentials_exception
    return user


def role_checker(*allowed_roles: Roles | str):
    allowed_values = {
        role.value if isinstance(role, Roles) else role
        for role in allowed_roles
    }

    async def checker(user: User = Depends(get_current_user)):
        if user.role not in allowed_values:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ruxsat etilmagan")
        return user
    return checker
