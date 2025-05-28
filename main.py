from fastapi import FastAPI, HTTPException, Depends, status, Request, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, Dict, List, Annotated
import sqlite3
import uuid
import hashlib
import datetime
import os
import json
import wikipedia
import random
import re

# Configurar idioma da Wikipedia para português
wikipedia.set_lang("pt")

# API Key original (apenas para endpoints administrativos se necessário)
API_KEY = "893247589749805674895t980453760894537"

app = FastAPI(
    title="IA Coach API",
    description="API para autenticação e serviços educacionais do IA Coach",
    version="1.0.0"
)

# Configurar CORS para permitir conexões do app iOS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar banco de dados
def get_db_connection():
    conn = sqlite3.connect('iacoach.db')
    conn.row_factory = sqlite3.Row
    return conn

# Inicializar o banco de dados
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Criar tabela de usuários se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        grade TEXT,
        age INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Criar tabela de sessões se não existir
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        user_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Inicializar o banco de dados quando o servidor é iniciado
init_db()

# Modelos para as requisições
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    grade: Optional[str] = None
    age: Optional[int] = None
    
    @field_validator('password')
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError('A senha deve ter pelo menos 6 caracteres')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class EnsinarRequest(BaseModel):
    topico: str

# Função para fazer hash da senha
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Middleware de autenticação - SIMPLIFICADO
async def get_current_user(request: Request):
    # Primeiro verificar se há um Authorization header com Bearer token
    authorization = request.headers.get("authorization")
    session_id = None
    
    if authorization and authorization.startswith("Bearer "):
        session_id = authorization.replace("Bearer ", "")
    else:
        # Se não há header, verificar cookie
        session_id = request.cookies.get("session_id")
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Buscar sessão
        cursor.execute("""
            SELECT u.id, u.email, u.name, u.grade, u.age
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_id = ?
        """, (session_id,))
        
        user_row = cursor.fetchone()
        
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sessão inválida ou expirada",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return dict(user_row)
    
    finally:
        conn.close()

# Função para tornar o texto mais amigável e humanizado
def humanize_text(summary: str) -> str:
    # Interações iniciais para criar empatia
    interacoes = [
        "Ótima pergunta! ",
        "Vamos explorar esse tópico juntos! ",
        "Deixe-me compartilhar alguns detalhes interessantes: ",
        "Que legal! Vou te contar mais sobre isso: "
    ]
    
    # Seleciona uma interação inicial aleatória
    interacao_inicial = random.choice(interacoes)
    
    # Função para simplificar o texto:
    def simplificar_texto(texto: str) -> str:
        # Divide o texto em parágrafos
        paragrafos = texto.split('\n')
        
        # Pega os dois primeiros parágrafos (ou um, se houver apenas um)
        if len(paragrafos) >= 2:
            texto_simplificado = '\n\n'.join(paragrafos[:2])
        else:
            texto_simplificado = paragrafos[0]
        
        # Remove referências, notas e caracteres indesejados
        texto_simplificado = re.sub(r'\[.*?\]', '', texto_simplificado)
        
        # Limita o tamanho do texto para garantir clareza (700 caracteres, por exemplo)
        if len(texto_simplificado) > 700:
            texto_simplificado = texto_simplificado[:700].rstrip() + "..."
        
        return texto_simplificado.strip()
    
    resumo_simplificado = simplificar_texto(summary)
    
    # Retorna o texto final unindo a interação e o resumo simplificado
    return interacao_inicial + resumo_simplificado

# ENDPOINTS DE AUTENTICAÇÃO (sem API key)
@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister):
    """Registra um novo usuário no sistema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar se o email já existe
        cursor.execute("SELECT id FROM users WHERE email = ?", (user_data.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este e-mail já está cadastrado"
            )
        
        # Hash da senha antes de salvar
        hashed_password = hash_password(user_data.password)
        
        # Inserir o novo usuário
        cursor.execute(
            "INSERT INTO users (email, password, name, grade, age) VALUES (?, ?, ?, ?, ?)",
            (user_data.email, hashed_password, user_data.name, user_data.grade, user_data.age)
        )
        
        conn.commit()
        return {"message": "Usuário registrado com sucesso"}
    
    finally:
        conn.close()

@app.post("/login")
async def login_user(user_data: UserLogin, response: Response):
    """Autenticação de usuário"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Hash da senha para comparação
        hashed_password = hash_password(user_data.password)
        
        # Buscar usuário
        cursor.execute(
            "SELECT id, email, name, grade, age FROM users WHERE email = ? AND password = ?",
            (user_data.email, hashed_password)
        )
        
        user_row = cursor.fetchone()
        
        if not user_row:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos"
            )
        
        # Gerar ID de sessão
        session_id = str(uuid.uuid4())
        
        # Salvar sessão
        cursor.execute(
            "INSERT INTO sessions (session_id, user_id) VALUES (?, ?)",
            (session_id, user_row['id'])
        )
        
        conn.commit()
        
        # Converter o resultado para um dicionário
        user = dict(user_row)
        
        # Definir cookie de sessão
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=7 * 24 * 60 * 60,  # 7 dias
            samesite="lax"
        )
        
        return {
            "session_id": session_id,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "grade": user["grade"],
                "age": user["age"]
            }
        }
    
    finally:
        conn.close()

@app.post("/logout")
async def logout_user(request: Request, response: Response):
    """Encerra a sessão do usuário"""
    session_id = request.cookies.get("session_id")
    
    if session_id:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Remover sessão
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
        finally:
            conn.close()
        
        # Remover cookie
        response.delete_cookie(key="session_id")
    
    return {"message": "Logout realizado com sucesso"}

# ENDPOINTS PROTEGIDOS (apenas autenticação de usuário)
@app.get("/buscar/{termo}")
async def buscar_wikipedia(
    termo: str, 
    current_user: dict = Depends(get_current_user)
):
    """
    Busca um termo na Wikipedia, processa o texto e retorna uma versão amigável e humanizada.
    Requer autenticação do usuário.
    """
    try:
        # Tenta encontrar a página
        pagina = wikipedia.page(termo)
        
        # Usa o sumário da página e humaniza o texto
        texto_humanizado = humanize_text(pagina.summary)
        
        return {
            "titulo": pagina.title, 
            "resumo": texto_humanizado,
            "usuario": current_user["name"]
        }
    except wikipedia.exceptions.DisambiguationError as e:
        # Se houver múltiplas possibilidades, tenta a primeira opção
        if e.options:
            try:
                pagina = wikipedia.page(e.options[0])
                texto_humanizado = humanize_text(pagina.summary)
                return {
                    "titulo": pagina.title, 
                    "resumo": texto_humanizado,
                    "usuario": current_user["name"]
                }
            except Exception:
                raise HTTPException(status_code=404, detail="Tópico não encontrado após desambiguação")
        raise HTTPException(status_code=404, detail="Múltiplas possibilidades encontradas")
    except wikipedia.exceptions.PageError:
        raise HTTPException(status_code=404, detail="Tópico não encontrado na Wikipedia")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/ensinar")
async def ensinar(
    request: EnsinarRequest, 
    current_user: dict = Depends(get_current_user)
):
    """
    Retorna um conteúdo educativo e humanizado sobre o tópico solicitado.
    Requer autenticação do usuário.
    """
    try:
        # Tenta encontrar a página na Wikipedia
        pagina = wikipedia.page(request.topico)
        
        # Processa e humaniza o sumário
        texto_humanizado = humanize_text(pagina.summary)
        
        return {
            "titulo": pagina.title, 
            "resumo": texto_humanizado,
            "usuario": current_user["name"]
        }
    except wikipedia.exceptions.DisambiguationError as e:
        # Se houver múltiplas opções, tenta a primeira
        if e.options:
            try:
                pagina = wikipedia.page(e.options[0])
                texto_humanizado = humanize_text(pagina.summary)
                return {
                    "titulo": pagina.title, 
                    "resumo": texto_humanizado,
                    "usuario": current_user["name"]
                }
            except Exception:
                raise HTTPException(status_code=404, detail="Tópico não encontrado após desambiguação")
        raise HTTPException(status_code=404, detail="Múltiplas possibilidades encontradas")
    except wikipedia.exceptions.PageError:
        raise HTTPException(status_code=404, detail="Tópico não encontrado na Wikipedia")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Retorna informações do usuário autenticado
    """
    return {
        "user": {
            "id": current_user["id"],
            "email": current_user["email"],
            "name": current_user["name"],
            "grade": current_user["grade"],
            "age": current_user["age"]
        }
    }

# ENDPOINTS PÚBLICOS (sem autenticação)
@app.get("/")
async def root():
    return {"message": "IA Coach API está funcionando!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.datetime.now().isoformat(),
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
