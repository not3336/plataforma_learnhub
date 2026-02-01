from fastapi import APIRouter, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Optional
import shutil
import os
import uuid

from .. import models, database, auth_utils

router = APIRouter(prefix="/course", tags=["Course"])

# Configuração de Templates e Arquivos
templates = Jinja2Templates(directory="app/templates")
VIDEO_DIR = "app/static/videos"
THUMBNAIL_DIR = "app/static/thumbnails"

def recalculate_course_progress(course_id: int, db: Session):
    """
    Função auxiliar para recalcular o progresso de TODOS os alunos matriculados
    sempre que o número total de aulas muda (adição ou exclusão).
    """
    # 1. Conta o novo total de aulas
    total_lessons = db.query(models.Lesson).filter(models.Lesson.course_id == course_id).count()
    
    # 2. Busca todas as matrículas deste curso
    enrollments = db.query(models.Enrollment).filter(models.Enrollment.course_id == course_id).all()
    
    # 3. Para cada aluno matriculado, recalcula
    for enrollment in enrollments:
        if total_lessons == 0:
            enrollment.progress = 0.0
            enrollment.completed = False
        else:
            # Conta quantas esse aluno específico já fez
            completed_count = db.query(models.LessonProgress).join(models.Lesson).filter(
                models.LessonProgress.user_id == enrollment.student_id,
                models.LessonProgress.is_completed == True,
                models.Lesson.course_id == course_id
            ).count()
            
            # Atualiza porcentagem
            new_percentage = (completed_count / total_lessons) * 100
            enrollment.progress = round(new_percentage, 1)
            
            # Se a porcentagem caiu para menos de 100, remove o status de concluído
            enrollment.completed = (new_percentage >= 100)
            
    db.commit()

@router.post("/create")
async def create_course(
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category_id: int = Form(...),
    thumbnail_file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(auth_utils.get_current_instructor),
    db: Session = Depends(database.get_db)
): 
    thumbnail_path = None
    if thumbnail_file and thumbnail_file.filename:
        ext = os.path.splitext(thumbnail_file.filename)[1]
        unique_thumb_name = f"{uuid.uuid4()}{ext}"
        
        file_path = os.path.join(THUMBNAIL_DIR, unique_thumb_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(thumbnail_file.file, buffer)
            
        thumbnail_path = f"/static/thumbnails/{unique_thumb_name}"
        
    new_course = models.Course(
        title=title, 
        description=description, 
        price=price, 
        category_id=category_id, 
        thumbnail=thumbnail_path, 
        instructor_id=current_user['id'])
    
    db.add(new_course)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@router.get("/{course_id}")
def gerenciar_curso(
    request: Request, 
    course_id: int, 
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_instructor)
):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    
    if not course:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Curso não encontrado"})

    categories = db.query(models.Category).all()
    # VERIFICAÇÃO DE PROPRIEDADE (Dono do Curso)
    # Se não for Admin E o ID do dono for diferente do usuário logado -> Bloqueia
    if current_user['role'] != 'admin' and course.instructor_id != current_user['id']:
        return RedirectResponse(url="/?error=Você não tem permissão para editar este curso", status_code=303)

    return templates.TemplateResponse("course_details.html", {
        "request": request, 
        "course": course,
        "categories": categories,
        "user": current_user
    })

@router.post("/{course_id}/edit")
async def update_course(
    course_id: int,
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category_id: int = Form(...),
    thumbnail_file: Optional[UploadFile] = File(None),
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_instructor)
):
    # Busca e Verifica
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course: return RedirectResponse(url="/", status_code=303)
    
    if current_user['role'] != 'admin' and course.instructor_id != current_user['id']:
        raise HTTPException(status_code=403, detail="Sem permissão")

    # Atualiza Campos de Texto
    course.title = title
    course.description = description
    course.price = price
    course.category_id = category_id
    
    # Atualiza Thumbnail (se enviada uma nova)
    if thumbnail_file and thumbnail_file.filename:
        # Salva a nova
        ext = os.path.splitext(thumbnail_file.filename)[1]
        unique_name = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join(THUMBNAIL_DIR, unique_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(thumbnail_file.file, buffer)
            
        course.thumbnail = f"/static/thumbnails/{unique_name}"

    db.commit()
    return RedirectResponse(url=f"/course/{course_id}?success=Curso atualizado", status_code=303)

@router.post("/{course_id}/enroll")
async def enroll_student(
    course_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    # 1. Verifica se o curso existe
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        return RedirectResponse(url="/", status_code=303)

    # 2. Verifica se já está matriculado (Evita duplicidade)
    existing_enrollment = db.query(models.Enrollment).filter(
        models.Enrollment.student_id == current_user['id'],
        models.Enrollment.course_id == course_id
    ).first()

    if not existing_enrollment:
        # 3. Cria a matrícula
        new_enrollment = models.Enrollment(
            student_id=current_user['id'],
            course_id=course_id,
            progress=0.0
        )
        db.add(new_enrollment)
        db.commit()

    # 4. Redireciona direto para o Player
    return RedirectResponse(url=f"/course/watch/{course_id}", status_code=303)

@router.post("/{course_id}/add-lesson")
async def add_lesson(
    course_id: int,
    title: str = Form(...),
    description: str = Form(None),
    video_file: UploadFile = File(...),
    current_user: dict = Depends(auth_utils.get_current_instructor),
    db: Session = Depends(database.get_db)
):
    course = db.query(models.Course).filter(models.Course.id == course_id and models.Course.instructor_id == current_user['id']).first()
    if not course:
        return RedirectResponse(url="/", status_code=303)
    # Lógica de salvar arquivo
    course_dir = f"{VIDEO_DIR}/course_{course_id}"
    os.makedirs(course_dir, exist_ok=True)
    
    file_extension = os.path.splitext(video_file.filename)[1]
    
    # 2. Gera um nome único (ex: a4e2-45b1-9988.mp4)
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # 3. Caminho físico para salvar
    file_path_on_disk = os.path.join(course_dir, unique_filename)
    
    with open(file_path_on_disk, "wb") as buffer:
        shutil.copyfileobj(video_file.file, buffer)
    
    web_path = f"/static/videos/course_{course_id}/{unique_filename}"
    
    new_lesson = models.Lesson(title=title, description=description, video_path=web_path, course_id=course_id)
    db.add(new_lesson)
    db.commit()
    #RECALCULAR PROGRESSO DA TURMA ---
    recalculate_course_progress(course_id, db)
    
    return RedirectResponse(url=f"/course/{course_id}", status_code=303)

@router.post("/lesson/{lesson_id}/edit")
async def update_lesson(
    lesson_id: int,
    title: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_instructor)
):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson: return RedirectResponse(url="/", status_code=303)
    
    # Verifica permissão via curso
    course = lesson.course
    if current_user['role'] != 'admin' and course.instructor_id != current_user['id']:
        raise HTTPException(status_code=403, detail="Sem permissão")

    # Atualiza
    lesson.title = title
    lesson.description = description
    
    db.commit()
    return RedirectResponse(url=f"/course/{course.id}?success=Aula atualizada", status_code=303)

@router.post("/lesson/{lesson_id}/delete")
async def delete_lesson(
    lesson_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_instructor)
):
    # 1. Buscar a aula
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    
    if not lesson:
        return RedirectResponse(url="/", status_code=303)
    
    # 2. Buscar o curso para verificar permissão
    course = db.query(models.Course).filter(models.Course.id == lesson.course_id).first()
    
    # 3. Verificação de Segurança (Dono ou Admin)
    if current_user['role'] != 'admin' and course.instructor_id != current_user['id']:
        raise HTTPException(status_code=403, detail="Sem permissão para excluir esta aula")

    # 4. Apagar o Arquivo Físico (Vídeo)
    # O caminho no banco é algo como "/static/videos/..." (URL)
    # Precisamos converter para caminho do sistema: "app/static/videos/..."
    
    try:
        # Remove a primeira barra "/" para juntar corretamente com "app"
        relative_path = lesson.video_path.lstrip("/") 
        file_path_on_disk = os.path.join("app", relative_path)
        
        if os.path.exists(file_path_on_disk):
            os.remove(file_path_on_disk)
    except Exception as e:
        print(f"Erro ao deletar arquivo: {e}") 
        # Continuamos a execução para deletar do banco mesmo se o arquivo falhar

    # 5. Apagar do Banco de Dados
    db.delete(lesson)
    db.commit()
    #RECALCULAR PROGRESSO DA TURMA ---
    recalculate_course_progress(course.id, db)
    # Redireciona de volta para a gestão do curso
    return RedirectResponse(url=f"/course/{course.id}", status_code=303)

@router.get("/watch/{course_id}")
def assistir_curso(
    request: Request, 
    course_id: int, 
    lesson_id: int = None,
    current_user: dict = Depends(auth_utils.get_current_user),
    db: Session = Depends(database.get_db)
):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        return templates.TemplateResponse("index.html", {"request": request, "error": "Curso não encontrado"})

    # Lógica para definir qual aula tocar
    current_lesson = None
    if lesson_id:
        # Tenta achar a aula solicitada
        current_lesson = next((l for l in course.lessons if l.id == lesson_id), None)
    
    # Se não pediu aula específica (ou não achou), toca a primeira
    if not current_lesson and course.lessons:
        current_lesson = course.lessons[0]

    completed_lessons = db.query(models.LessonProgress.lesson_id).filter(
        models.LessonProgress.user_id == current_user['id'],
        models.LessonProgress.is_completed == True
    ).all()
    completed_ids = [c[0] for c in completed_lessons]

    return templates.TemplateResponse("player.html", {
        "request": request,
        "course": course,
        "current_lesson": current_lesson,
        "user": current_user,
        "completed_ids": completed_ids
    })

@router.post("/lesson/{lesson_id}/complete")
async def complete_lesson_progress(
    lesson_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    # 1. Verificar se a aula existe
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        return {"error": "Aula não encontrada"}
    course_id = lesson.course_id
    # 2. Registrar/Atualizar o progresso da aula
    progress_entry = db.query(models.LessonProgress).filter(
        models.LessonProgress.user_id == current_user['id'],
        models.LessonProgress.lesson_id == lesson_id
    ).first()

    if not progress_entry:
        progress_entry = models.LessonProgress(
            user_id=current_user['id'],
            lesson_id=lesson_id,
            is_completed=True
        )
        db.add(progress_entry)
    else:
        progress_entry.is_completed = True
    
    db.commit()

    recalculate_course_progress(course_id, db)

    return {"status": "success"}

@router.post("/lesson/{lesson_id}/comment")
async def post_comment(
    lesson_id: int,
    content: str = Form(...),
    current_user: dict = Depends(auth_utils.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Busca a aula para saber qual é o curso (para redirecionar de volta)
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    
    if not lesson:
        return {"status": "error", "message": "Aula não encontrada"}

    new_comment = models.Comment(
        content=content,
        user_id=current_user['id'],
        lesson_id=lesson_id,
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    is_instructor = False
    if lesson.course and lesson.course.instructor_id == current_user['id']:
        is_instructor = True

    return {
        "status": "success",
        "id": new_comment.id,
        "content": new_comment.content,
        "user_name": current_user['name'],
        "user_initial": current_user['name'][0],
        "created_at": new_comment.created_at.strftime('%d/%m/%Y às %H:%M'),
        "is_instructor": is_instructor
    }

@router.post("/comment/{comment_id}/reply")
async def reply_comment(
    comment_id: int,
    content: str = Form(...),
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_user)
):
    # Verifica se o comentário pai existe
    parent_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    
    if not parent_comment:
        return {"status": "error", "message": "Comentário original não encontrado"}    
    # Cria a resposta
    new_reply = models.Comment(
        content=content,
        user_id=current_user['id'],
        lesson_id=parent_comment.lesson_id, # Pertence à mesma aula
        parent_id=comment_id # <--- Vínculo com o pai
    )
    
    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)

    is_instructor = False
    if parent_comment.lesson.course and parent_comment.lesson.course.instructor_id == current_user['id']:
        is_instructor = True
    
    # Redireciona para a aula correta
    return {
        "status": "success",
        "id": new_reply.id,
        "content": new_reply.content,
        "user_name": current_user['name'],
        "user_initial": current_user['name'][0],
        "created_at": new_reply.created_at.strftime('%d/%m/%Y às %H:%M'),
        "is_instructor": is_instructor,
        "parent_id": comment_id
    }

@router.delete("/comment/{comment_id}")
async def delete_comment(
    comment_id: int,
    db: Session = Depends(database.get_db),
    current_user: dict = Depends(auth_utils.get_current_instructor)
):
    # 1. Busca o comentário
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    
    if not comment:
        return {"status": "error", "message": "Comentário não encontrado"}
    
    # 2. Verifica se quem está tentando apagar é o instrutor do curso
    # Navegamos: Comentário -> Aula -> Curso -> Instrutor
    course = comment.lesson.course
    if course.instructor_id != current_user['id']:
        return {"status": "error", "message": "Permissão negada. Apenas o instrutor pode excluir."}
    
    # 3. Deleta o comentário
    # Nota: Se o banco estiver configurado com cascade, as respostas (replies)
    # serão apagadas automaticamente.
    db.delete(comment)
    db.commit()
    
    return {"status": "success", "message": "Comentário excluído"}
