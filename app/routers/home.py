from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models, database, auth_utils

router = APIRouter()

# Configuração de Templates e Arquivos
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def dashboard(
    request: Request, 
    category_id: int = None,
    q: str = None,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_user_optional)
):
    # ==========================================
    # CENÁRIO 1: USUÁRIO NÃO LOGADO (Landing Page)
    # ==========================================
    if not current_user:
        # Pega alguns cursos aleatórios para mostrar na vitrine (opcional)
        featured_courses = db.query(models.Course).limit(3).all()
        return templates.TemplateResponse("landing.html", {
            "request": request,
            "featured_courses": featured_courses
        })

    # ==========================================
    # CENÁRIO 2: USUÁRIO LOGADO (Dashboard)
    # ==========================================
    
    # 1. Buscar Cursos Matriculados (Meu Aprendizado)
    my_enrollments = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == current_user['id']
    ).all()

    enrolled_course_ids = [e.course_id for e in my_enrollments]

    # 2. Buscar Cursos Criados (Se for Instrutor)
    created_courses = []
    if current_user['role'] in ['instrutor', 'admin']:
        created_courses = db.query(models.Course).filter(
            models.Course.instructor_id == current_user['id']
        ).all()

    # 3. Buscar Catálogo (Recomendações / Busca)
    query = db.query(models.Course)
    if category_id:
        query = query.filter(models.Course.category_id == category_id)
    if q:
        search_term = f"%{q}%"
        query = query.filter(or_(
            models.Course.title.ilike(search_term), 
            models.Course.description.ilike(search_term)
        ))
    
    catalog_courses = query.all()

    all_categories = db.query(models.Category).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "user": current_user,
        "user_role": current_user['role'],
        
        # Dados
        "my_enrollments": my_enrollments,
        "created_courses": created_courses,
        "catalog_courses": catalog_courses,
        "categories": all_categories,
        "enrolled_course_ids": enrolled_course_ids,
        
        # Filtros
        "selected_category": category_id,
        "search_query": q,
    })