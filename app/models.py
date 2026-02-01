from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relationship, backref
from .database import Base

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    
    # Chaves Estrangeiras
    student_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    
    # Dados do Progresso
    progress = Column(Float, default=0.0) # Porcentagem (0 a 100)
    enrolled_at = Column(DateTime, default=func.now())
    completed = Column(Boolean, default=False) # Se já terminou o curso
    
    # Relacionamentos
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    is_completed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=func.now())

    # Relacionamentos
    user = relationship("User", back_populates="lesson_progress")
    lesson = relationship("Lesson", back_populates="user_progress")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # Roles: 'admin', 'professor', 'aluno'
    role = Column(String, default="aluno")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    # Relacionamentos
    courses_created = relationship("Course", back_populates="instructor")
    comments = relationship("Comment", back_populates="user")

    enrollments = relationship("Enrollment", back_populates="student")
    lesson_progress = relationship("LessonProgress", back_populates="user")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # Relacionamento: Uma categoria tem vários cursos
    courses = relationship("Course", back_populates="category")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    price = Column(Float)
    thumbnail = Column(String, nullable=True) # Caminho da imagem de capa
    created_at = Column(DateTime, default=func.now())
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category", back_populates="courses")    

    # Vínculo com o Professor (User)
    instructor_id = Column(Integer, ForeignKey("users.id"))
    instructor = relationship("User", back_populates="courses_created")

    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")

    enrollments = relationship("Enrollment", back_populates="course")

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    video_path = Column(String) # Caminho do arquivo salvo localmente
    description = Column(Text, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    order = Column(Integer, default=0) # Para ordenar as aulas (Aula 1, Aula 2...)

    course = relationship("Course", back_populates="lessons")
    comments = relationship("Comment", back_populates="lesson", cascade="all, delete-orphan")
    user_progress = relationship("LessonProgress", back_populates="lesson")

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # NOVO: Referência ao próprio comentário (Auto-relacionamento)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True)

    # Relacionamentos
    lesson = relationship("Lesson", back_populates="comments")
    user = relationship("User", back_populates="comments")
    
    # Esta linha mágica cria a lista de respostas dentro de um comentário
    replies = relationship("Comment", 
        backref=backref('parent', remote_side=[id]),
        cascade="all, delete-orphan"
    )