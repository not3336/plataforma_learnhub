def test_edit_course(professor_token, db):
    from app.models import Category, Course, User
    
    # 1. Setup: Pegar o ID do professor criado na fixture
    # O professor_token cria um user com email 'prof@teste.com'
    prof = db.query(User).filter(User.email == "prof@teste.com").first()
    
    cat = Category(name="Backend")
    db.add(cat)
    db.commit()
    
    # 2. Criar um curso original
    course = Course(
        title="Curso Antigo",
        description="Descricao Antiga",
        price=50.0,
        category_id=cat.id,
        instructor_id=prof.id
    )
    db.add(course)
    db.commit()
    
    # 3. Ação: Professor edita o curso
    response = professor_token.post(
        f"/course/{course.id}/edit",
        data={
            "title": "Curso Novo 2.0",
            "description": "Nova descrição atualizada",
            "price": 100.0,
            "category_id": cat.id
        },
        follow_redirects=False
    )
    
    # 4. Validação
    assert response.status_code == 303 # Redirecionou
    
    db.refresh(course)
    assert course.title == "Curso Novo 2.0"
    assert course.price == 100.0

def test_edit_lesson(professor_token, db):
    from app.models import Category, Course, User, Lesson
    
    # Setup
    prof = db.query(User).filter(User.email == "prof@teste.com").first()
    cat = Category(name="Frontend")
    db.add(cat)
    db.commit()
    
    course = Course(title="Curso Web", description="...", price=0, category_id=cat.id, instructor_id=prof.id)
    db.add(course)
    db.commit()
    
    lesson = Lesson(title="Aula Errada", video_path="/vid.mp4", course_id=course.id)
    db.add(lesson)
    db.commit()
    
    # Ação: Editar a aula
    response = professor_token.post(
        f"/course/lesson/{lesson.id}/edit",
        data={
            "title": "Aula Corrigida",
            "description": "Descrição adicionada"
        },
        follow_redirects=False
    )
    
    # Validação
    assert response.status_code == 303
    
    db.refresh(lesson)
    assert lesson.title == "Aula Corrigida"
    assert lesson.description == "Descrição adicionada"

def test_aluno_cannot_edit_course(aluno_token, db):
    """Garante que aluno não edita curso alheio"""
    from app.models import Category, Course, User
    
    # Cria um professor (dono do curso)
    prof = User(name="Outro Prof", email="outro@prof.com", hashed_password="x", role="instrutor")
    cat = Category(name="Security")
    db.add(prof)
    db.add(cat)
    db.commit()
    
    course = Course(title="Curso Protegido", description="...", price=100, category_id=cat.id, instructor_id=prof.id)
    db.add(course)
    db.commit()
    
    # Aluno tenta editar
    response = aluno_token.post(
        f"/course/{course.id}/edit",
        data={"title": "Hacked", "description": "...", "price": 0, "category_id": cat.id}
    )
    
    # Deve ser proibido (403) ou redirecionado se tratado
    assert response.status_code in [403, 401]
    
    db.refresh(course)
    assert course.title == "Curso Protegido" # Não mudou