import os
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt  # Jose or PyJWT. In requirements.txt we added pyjwt, let's use jwt
# Wait, PyJWT is imported as 'import jwt'. Let's use 'import jwt' for simplicity and robust compatibility.
import jwt
from passlib.context import CryptContext

# Configuración de variables de entorno con valores por defecto seguros para desarrollo
SECRET_KEY = os.getenv("SECRET_KEY", "b33f_s3cr3t_k3y_for_affiliates_and_monetization_123456789")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")) # 24 horas por defecto

# Configuración para encriptar contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Genera un hash de la contraseña."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña coincide con el hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Genera un Token JWT firmado."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica y valida un Token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
