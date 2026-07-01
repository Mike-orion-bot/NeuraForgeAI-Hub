from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime

import models
import schemas
import auth
from database import engine, get_db

# Crear las tablas en la base de datos si no existen
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Módulo de Inscripción & Autenticación",
    description="API portable para registro y login de usuarios, lista para desplegar en la nube.",
    version="1.0.0"
)

# Configuración de CORS para permitir peticiones desde cualquier origen (Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar el esquema de autenticación por Token portador (Bearer)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Obtiene el usuario actual validando el Token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token de acceso",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = auth.decode_access_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


@app.get("/", tags=["General"])
def read_root():
    """Endpoint de bienvenida del API."""
    return {
        "mensaje": "¡Bienvenido al Módulo de Inscripción y Autenticación!",
        "documentacion": "/docs",
        "redoc": "/redoc",
        "estado": "activo"
    }


@app.get("/health", tags=["General"])
def health_check():
    """Endpoint de salud (Health check) para balanceadores de carga y Render/Docker."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, tags=["Autenticación"])
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registra un nuevo usuario en la base de datos."""
    # Verificar si el usuario ya existe por email o por username
    db_user_by_email = db.query(models.User).filter(models.User.email == user_in.email).first()
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya está registrado"
        )

    db_user_by_username = db.query(models.User).filter(models.User.username == user_in.username).first()
    if db_user_by_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado"
        )

    # Crear el nuevo usuario con contraseña encriptada
    hashed_pass = auth.get_password_hash(user_in.password)
    new_user = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_pass
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post("/login", response_model=schemas.Token, tags=["Autenticación"])
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Autentica a un usuario y retorna un Token JWT de acceso."""
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generar el Token JWT
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.UserResponse, tags=["Usuarios"])
def get_user_profile(current_user: models.User = Depends(get_current_user)):
    """Obtiene el perfil del usuario autenticado."""
    return current_user
