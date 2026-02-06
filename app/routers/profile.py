from fastapi import APIRouter, Request, Form, Depends, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .. import models, database, auth_utils

router = APIRouter(prefix='/profile', tags=['Profile'])
templates = Jinja2Templates(directory="app/templates")

# 1. Rota para VISUALIZAR a página
@router.get("")
async def profile_page(
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    user_db = db.query(models.User).filter(models.User.id == current_user['id']).first()
    if not user_db:
        return RedirectResponse(url="/login", status_code=401)
    
    return templates.TemplateResponse(request, "profile.html", {
        "user": user_db,
        "active_page": "profile" # Para destacar no menu se tiver
    })

# 2. Rota para ATUALIZAR os dados
@router.post("")
async def update_profile(
    request: Request,
    name: str = Form(...),
    cpf: str = Form(None), # CPF é opcional no form, mas ideal validar
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    print(cpf)
    # Busca o usuário no banco
    user_db = db.query(models.User).filter(models.User.id == current_user['id']).first()
    
    if not user_db:
        return RedirectResponse(url="/login", status_code=401)
    

    # Lógica simples para CPF (apenas salva, mas ideal seria validar algorítmico)
    if cpf:
        exists = db.query(models.User).filter(models.User.cpf == cpf).first()
        if exists and user_db.cpf != cpf:
            return templates.TemplateResponse(request, "profile.html", {
                "user": user_db,
                "warning_msg": "CPF em uso!"
            }, status_code=409)
        user_db.cpf = cpf

    # Atualiza os dados
    user_db.name = name
    

    db.commit()
    db.refresh(user_db)
    
    # Aqui você poderia adicionar uma "Flash Message" se estivesse usando
    # Por enquanto, recarregamos a página para mostrar os dados novos
    return templates.TemplateResponse(request, "profile.html", {
        "user": user_db,
        "success_msg": "Dados atualizados com sucesso!"
    })