from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Request, HTTPException, status

# CONFIGURAÇÕES DE SEGURANÇA
# Em produção, isso ficaria no .env
SECRET_KEY = "segredo_super_secreto_do_mvp_trocar_em_producao"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # Sessão dura 1 hora

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
    
async def get_current_user_optional(request: Request):
    """
    Tenta pegar o usuário do cookie. Se não estiver logado, retorna None.
    Usado para páginas públicas (Dashboard) que mudam se você estiver logado.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    try:
        # O token vem como "Bearer eyJhbGci..."
        scheme, _, param = token.partition(" ")
        payload = decode_access_token(param)
        if payload is None:
            return None
        return payload # Retorna o dict com {'sub': email, 'role': role, 'name': name}
    except Exception:
        return None

async def get_current_user(request: Request):
    """
    Obriga o usuário a estar logado. Se não estiver, lança erro 401.
    Usado para rotas como 'Assistir Aula' ou 'Comentar'.
    """
    user = await get_current_user_optional(request)
    if not user:
        # Redireciona para login se tentar acessar sem token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Faça login para acessar esta página",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_instructor(request: Request):
    """
    Bloqueia o acesso se não for instrutor ou admin.
    """
    user = await get_current_user_optional(request)
    if not user:
         # Redirecionamento deve ser tratado na rota ou via Exception Handler
         # Para simplicidade aqui, lançamos erro, mas o ideal é redirecionar
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login necessário")
    
    if user['role'] not in ['instrutor', 'admin']:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a instrutores")
    
    return user

async def get_current_admin(request: Request):
    """
    Bloqueia acesso se o usuário não for estritamente ADMIN.
    """
    user = await get_current_user(request) # Já verifica se está logado
    
    if user['role'] != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acesso restrito a administradores"
        )
    return user