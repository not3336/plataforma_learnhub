from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
import os

from . import models, database
from .routers import course, auth, admin, home


# Criação das tabelas (se não existirem)
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

@app.exception_handler(HTTPException)
async def auth_exception_handler(request: Request, exc: HTTPException):
    # Se o erro for 401 (Login necessário), redireciona para /login
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        return RedirectResponse(url="/login?error=Faça login para continuar", status_code=303)
    
    # Para outros erros, retorna o erro padrão ou trata conforme necessário
    return exc

# Garante que a pasta static existe para evitar erros
os.makedirs("app/static/videos", exist_ok=True)
os.makedirs("app/static/css", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


app.include_router(home.router)
app.include_router(course.router)
app.include_router(auth.router)
app.include_router(admin.router)
