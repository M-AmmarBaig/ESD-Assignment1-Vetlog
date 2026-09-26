from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt as jose_jwt
from sqlalchemy.orm import Session

from app.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.database import Users, get_session
from app.schemas import AuthResponse, LoginRequest, UserRegisterRequest
from app.logger import logger

security_scheme = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["auth"])


def create_jwt(user: Users) -> str:
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
    }
    return jose_jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_session),
) -> Users:
    token = credentials.credentials
    try:
        payload = jose_jwt.decode(
            token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM]
        )
        user_id = int(payload.get("sub"))
    except Exception:
        logger.warning("Authentication failed: Invalid or expired JWT token")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        logger.warning(f"Authentication failed: Token valid but user_id {user_id} not found in DB")
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_session)):
    client_ip = request.client.host if request.client else "unknown"
    user = db.query(Users).filter(Users.username == payload.username).first()
    if not user or not bcrypt.checkpw(
        payload.password.encode("utf-8"), user.password.encode("utf-8")
    ):
        logger.warning(f"SECURITY ALERT: Failed login attempt for username '{payload.username}' from IP {client_ip}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    logger.info(f"Successful login for user '{payload.username}' from IP {client_ip}")
    return AuthResponse(
        token=create_jwt(user),
        user_id=user.id,
        username=user.username,
        display_name=user.display_name,
    )


@router.post("/register")
def register(payload: UserRegisterRequest, request: Request, db: Session = Depends(get_session)):
    client_ip = request.client.host if request.client else "unknown"
    user_exists = db.query(Users).filter(Users.username == payload.username).first()
    if user_exists:
        logger.warning(f"Registration failed: Username '{payload.username}' already exists. Attempt from IP {client_ip}")
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = bcrypt.hashpw(payload.password.encode("utf-8"), bcrypt.gensalt())
    new_user = Users(
        username=payload.username,
        display_name=payload.display_name,
        password=hashed_password.decode(),
    )
    db.add(new_user)
    db.commit()
    
    logger.info(f"New user registered: '{payload.username}' from IP {client_ip}")
    return AuthResponse(
        token=create_jwt(new_user),
        user_id=new_user.id,
        username=payload.username,
        display_name=payload.display_name,
    )
