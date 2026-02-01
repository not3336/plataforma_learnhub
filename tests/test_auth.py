def test_create_user(client):
    """
    Testa se é possível criar um usuário novo.
    """
    response = client.post(
        "/register",
        data={
            "name": "Test User",
            "email": "test@example.com",
            "password": "testpassword"
        },
        follow_redirects=False # Importante para testar se houve o redirect correto
    )
    
    # Esperamos um redirecionamento 303 para /login?success...
    assert response.status_code == 303
    assert "/login" in response.headers["location"]

def test_login_user(client):
    """
    Testa o fluxo completo: Registrar -> Logar
    """
    # 1. Registrar
    client.post(
        "/register",
        data={
            "name": "Login User",
            "email": "login@example.com",
            "password": "password123"
        }
    )
    
    # 2. Logar
    response = client.post(
        "/login",
        data={
            "email": "login@example.com",
            "password": "password123"
        },
        follow_redirects=False
    )
    
    # Esperamos redirect para / (home)
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    
    # Verifica se o cookie foi setado
    assert "access_token" in response.cookies
