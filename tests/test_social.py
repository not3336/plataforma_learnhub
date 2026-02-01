def test_post_comment(aluno_token, db):
    from app.models import Category, Course, User, Lesson, Comment
    
    # Setup: Criar Instrutor e Curso
    prof = User(name="Mestre", email="mestre@code.com", hashed_password="x", role="instrutor")
    cat = Category(name="Dados")
    db.add(prof)
    db.add(cat)
    db.commit()
    
    course = Course(title="SQL", description="...", price=10, category_id=cat.id, instructor_id=prof.id)
    db.add(course)
    db.commit()
    
    lesson = Lesson(title="Select", video_path="/v.mp4", course_id=course.id)
    db.add(lesson)
    db.commit()
    
    # Ação: Aluno comenta
    response = aluno_token.post(
        f"/course/lesson/{lesson.id}/comment",
        data={"content": "Não entendi o WHERE"}
    )
    
    # Validação (API retorna JSON)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["content"] == "Não entendi o WHERE"
    
    # Verifica DB
    comment = db.query(Comment).first()
    assert comment.content == "Não entendi o WHERE"
    assert comment.user.email == "aluno@teste.com"

def test_reply_comment(professor_token, db):
    from app.models import Category, Course, User, Lesson, Comment
    
    # Setup: Professor (do token) cria curso e aula
    prof = db.query(User).filter(User.email == "prof@teste.com").first()
    cat = Category(name="Web")
    db.add(cat)
    db.commit()
    
    course = Course(title="API", description="...", price=0, category_id=cat.id, instructor_id=prof.id)
    db.add(course)
    db.commit()
    
    lesson = Lesson(title="Routes", video_path="/v.mp4", course_id=course.id)
    db.add(lesson)
    db.commit()
    
    # Comentário original de um aluno qualquer
    aluno = User(name="Student", email="st@st.com", hashed_password="x")
    db.add(aluno)
    db.commit()
    
    original_comment = Comment(content="Dúvida aqui", user_id=aluno.id, lesson_id=lesson.id)
    db.add(original_comment)
    db.commit()
    
    # Ação: Professor responde
    response = professor_token.post(
        f"/course/comment/{original_comment.id}/reply",
        data={"content": "A resposta é X"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["parent_id"] == original_comment.id
    
    # DB
    reply = db.query(Comment).filter(Comment.content == "A resposta é X").first()
    assert reply.parent_id == original_comment.id

def test_delete_comment_as_instructor(professor_token, db):
    from app.models import Category, Course, User, Lesson, Comment
    
    prof = db.query(User).filter(User.email == "prof@teste.com").first()
    cat = Category(name="Git")
    db.add(cat)
    db.commit()
    course = Course(title="Git Flow", description="...", price=0, category_id=cat.id, instructor_id=prof.id)
    db.add(course)
    db.commit()
    lesson = Lesson(title="Merge", video_path="/v.mp4", course_id=course.id)
    db.add(lesson)
    db.commit()
    
    # Comentário ofensivo ou spam
    spammer = User(name="Spam", email="spam@spam.com", hashed_password="x")
    db.add(spammer)
    db.commit()
    spam_comment = Comment(content="SPAM SPAM", user_id=spammer.id, lesson_id=lesson.id)
    db.add(spam_comment)
    db.commit()
    
    # Ação: Professor deleta
    response = professor_token.delete(f"/course/comment/{spam_comment.id}")
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    
    # Verifica sumiço
    assert db.query(Comment).filter(Comment.id == spam_comment.id).first() is None

def test_student_cannot_delete_others_comment(aluno_token, db):
    from app.models import Category, Course, User, Lesson, Comment
    
    # Setup básico
    cat = Category(name="Basic")
    prof = User(name="P", email="p@p.com", hashed_password="x", role="instrutor")
    db.add(cat)
    db.add(prof)
    db.commit()
    
    course = Course(title="C", price=0, category_id=cat.id, instructor_id=prof.id)
    db.add(course)
    db.commit()
    
    lesson = Lesson(title="L", video_path="x", course_id=course.id)
    db.add(lesson)
    db.commit()
    
    # Comentário do Professor
    comment = Comment(content="Aviso importante", user_id=prof.id, lesson_id=lesson.id)
    db.add(comment)
    db.commit()
    
    # Aluno tenta deletar
    response = aluno_token.delete(f"/course/comment/{comment.id}")
    
    # Como delete_comment usa Depends(get_current_instructor), se o usuário não for instrutor,
    # o FastAPI lança HTTPException(403) antes de entrar na função.
    # O teste deve esperar 403 Forbidden.
    assert response.status_code == 403
    
    # O comentário ainda deve existir
    assert db.query(Comment).filter(Comment.id == comment.id).first() is not None