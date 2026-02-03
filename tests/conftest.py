import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.main import app

# URL do banco de dados de teste (em memória)
# check_same_thread=False é necessário para SQLite em memória rodar com FastAPI/Pytest
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool, # Mantém os dados na memória entre conexões da mesma sessão
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    """
    Cria um banco de dados novo para cada teste e o destrói no final.
    """
    # Cria as tabelas
    Base.metadata.create_all(bind=engine)
    
    # Cria a sessão
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Remove as tabelas após o teste
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    """
    Cliente de teste que usa o banco de dados override.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass # A sessão é fechada na fixture 'db'

    app.dependency_overrides[get_db] = override_get_db
    
    # TestClient para requisições síncronas (FastAPI suporta isso bem para testes)
    with TestClient(app) as c:
        yield c
    
    # Limpa overrides
    app.dependency_overrides.clear()

@pytest.fixture
def aluno_token(client, db):
    """
    Cria um aluno e retorna o header de autenticação (cookie ou bearer).
    Como o login retorna cookie, vamos usar o client com cookie jar persistente ou extrair.
    O TestClient gerencia cookies automaticamente se usarmos a mesma instância.
    Mas para facilitar requests autenticados explicitamente, vamos retornar os headers.
    """
    from app.models import User
    from app.auth_utils import get_password_hash
    
    # Cria usuário direto no DB para ser rápido
    password = "alunopass"
    user = User(
        name="Aluno Teste",
        email="aluno@teste.com",
        hashed_password=get_password_hash(password),
        role="aluno"
    )
    db.add(user)
    db.commit()
    
    # Loga para pegar o cookie
    client.post(
        "/login",
        data={"email": "aluno@teste.com", "password": password},
        follow_redirects=False
    )
    return client # O client agora tem o cookie na sessão

@pytest.fixture
def professor_token(client, db):
    """
    Cria um professor e retorna o client autenticado.
    """
    from app.models import User
    from app.auth_utils import get_password_hash
    
    password = "profpass"
    user = User(
        name="Prof Teste",
        email="prof@teste.com",
        hashed_password=get_password_hash(password),
        role="instrutor" # auth_utils espera 'instrutor', não 'professor'
    )
    db.add(user)
    db.commit()
    
    client.post(
        "/login",
        data={"email": "prof@teste.com", "password": password},
        follow_redirects=False
    )
    return client
