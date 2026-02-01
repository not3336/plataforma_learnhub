from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models, auth_utils

# Garante que as tabelas existam antes de inserir
models.Base.metadata.create_all(bind=engine)

def create_super_user():
    db: Session = SessionLocal()
    
    try:
        # Dados do Administrador
        admin_email = "admin@learnhub.com"
        admin_pass = "admin123"
        admin_name = "Administrador do Sistema"
        
        # 1. Verifica se já existe
        user = db.query(models.User).filter(models.User.email == admin_email).first()
        
        if user:
            print(f"⚠️  O usuário {admin_email} já existe no sistema.")
            
            # Opcional: Atualizar para admin caso ele já exista como aluno
            if user.role != "admin":
                user.role = "admin"
                db.commit()
                print(f"🔄  Permissão do usuário atualizada para ADMIN.")
            
            return

        # 2. Cria o usuário com role='admin'
        print(f"🔨  Criando usuário administrador...")
        
        new_admin = models.User(
            email=admin_email,
            name=admin_name,
            hashed_password=auth_utils.get_password_hash(admin_pass),
            role="admin",  # A chave Mágica: define como admin
            is_active=True
        )
        
        db.add(new_admin)
        db.commit()
        
        print("✅  Sucesso! Usuário Admin criado.")
        print(f"📧  Email: {admin_email}")
        print(f"🔑  Senha: {admin_pass}")

    except Exception as e:
        print(f"❌  Erro ao criar usuário: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    create_super_user()