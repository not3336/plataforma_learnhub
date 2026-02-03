def test_get_user_profile(aluno_token, db):
    # Ação: Aluno comenta
    response = aluno_token.get(
        f"/profile",
    )
    
    assert response.status_code == 200

def test_edit_user_profile(client, db):
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

    client.post(
        "/login",
        data={"email": "aluno@teste.com", "password": password},
        follow_redirects=False
    )

    new_cpf = '07385566375'
    response = client.post(
        f'/profile',
        data={
            'name': 'Aluno',
            'cpf': new_cpf
        }
    )
    db.refresh(user)
    assert response.status_code == 200
    assert user.cpf == new_cpf
    assert user.name == 'Aluno'