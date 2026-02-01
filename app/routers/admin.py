from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .. import models, database, auth_utils

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/users")
async def list_users(
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_admin)
):
    # Busca todos os usuários ordenados por ID
    users = db.query(models.User).order_by(models.User.id).all()
    
    return templates.TemplateResponse("admin_users.html", {
        "request": request,
        "users": users,
        "user": current_user
    })

#Alterar Role (Permissão)
@router.post("/users/{user_id}/change-role")
async def change_role(
    user_id: int,
    new_role: str = Form(...),
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_admin)
):
    # Proteção: Admin não pode alterar seu próprio papel para não se trancar fora
    if user_id == current_user['id']:
        return RedirectResponse(url="/admin/users?error=Você não pode alterar sua própria permissão", status_code=303)

    user_to_edit = db.query(models.User).filter(models.User.id == user_id).first()
    
    if user_to_edit:
        user_to_edit.role = new_role
        db.commit()
    
    return RedirectResponse(url="/admin/users?success=Permissão atualizada com sucesso", status_code=303)

@router.get("/categories")
async def manage_categories(
    request: Request,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_admin)
):
    categories = db.query(models.Category).all()
    return templates.TemplateResponse("admin_categories.html", {
        "request": request, 
        "categories": categories,
        "user": current_user
    })

@router.post("/categories/create")
async def create_category(
    name: str = Form(...),
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_admin)
):
    # Evitar duplicatas
    exists = db.query(models.Category).filter(models.Category.name == name).first()
    if not exists:
        new_cat = models.Category(name=name)
        db.add(new_cat)
        db.commit()
        
    return RedirectResponse(url="/admin/categories", status_code=303)