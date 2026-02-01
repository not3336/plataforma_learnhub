from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import timedelta

from .. import models, database, auth_utils

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "auth_login.html")

@router.get("/register")
def register_page(request: Request):
    return templates.TemplateResponse(request, "auth_register.html")


@router.post("/register")
async def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    # Verifica se email já existe
    user_exists = db.query(models.User).filter(models.User.email == email).first()
    if user_exists:
        return RedirectResponse(url="/register?error=Email já cadastrado", status_code=303)
    
    # Cria usuário (Padrão: Aluno)
    hashed_password = auth_utils.get_password_hash(password)
    new_user = models.User(
        name=name,
        email=email,
        hashed_password=hashed_password,
        role="aluno" 
    )
    db.add(new_user)
    db.commit()
    
    return RedirectResponse(url="/login?success=Conta criada", status_code=303)

@router.post("/login")
async def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(database.get_db)
):
    user = db.query(models.User).filter(models.User.email == email).first()
    
    # Validação
    if not user or not auth_utils.verify_password(password, user.hashed_password):
        return RedirectResponse(url="/login?error=Credenciais inválidas", status_code=303)
    
    # Gerar Token
    access_token_expires = timedelta(minutes=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_utils.create_access_token(
        data={"sub": user.email, "role": user.role, "name": user.name, "id": user.id},
        expires_delta=access_token_expires
    )
    
    # Criar Cookie e Redirecionar
    redirect = RedirectResponse(url="/", status_code=303)
    
    # httponly=True impede que JavaScript leia o cookie (Segurança contra XSS)
    redirect.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    
    return redirect

@router.get("/logout")
def logout(response: Response):
    redirect = RedirectResponse(url="/login", status_code=303)
    redirect.delete_cookie("access_token")
    return redirect