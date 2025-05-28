from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import datetime
import os
import wikipedia
import random
import re

# Configurar idioma da Wikipedia para português
wikipedia.set_lang("pt")

# API Key original
API_KEY = "893247589749805674895t980453760894537"

app = FastAPI(
    title="IA Coach API",
    description="API para serviços educacionais do IA Coach",
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

# Modelos para as requisições
class EnsinarRequest(BaseModel):
    topico: str

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

# ENDPOINTS PÚBLICOS (sem autenticação)
@app.get("/buscar/{termo}")
async def buscar_wikipedia(termo: str):
    """
    Busca um termo na Wikipedia, processa o texto e retorna uma versão amigável e humanizada.
    """
    try:
        # Tenta encontrar a página
        pagina = wikipedia.page(termo)
        
        # Usa o sumário da página e humaniza o texto
        texto_humanizado = humanize_text(pagina.summary)
        
        return {
            "titulo": pagina.title, 
            "resumo": texto_humanizado
        }
    except wikipedia.exceptions.DisambiguationError as e:
        # Se houver múltiplas possibilidades, tenta a primeira opção
        if e.options:
            try:
                pagina = wikipedia.page(e.options[0])
                texto_humanizado = humanize_text(pagina.summary)
                return {
                    "titulo": pagina.title, 
                    "resumo": texto_humanizado
                }
            except Exception:
                raise HTTPException(status_code=404, detail="Tópico não encontrado após desambiguação")
        raise HTTPException(status_code=404, detail="Múltiplas possibilidades encontradas")
    except wikipedia.exceptions.PageError:
        raise HTTPException(status_code=404, detail="Tópico não encontrado na Wikipedia")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.post("/ensinar")
async def ensinar(request: EnsinarRequest):
    """
    Retorna um conteúdo educativo e humanizado sobre o tópico solicitado.
    """
    try:
        # Tenta encontrar a página na Wikipedia
        pagina = wikipedia.page(request.topico)
        
        # Processa e humaniza o sumário
        texto_humanizado = humanize_text(pagina.summary)
        
        return {
            "titulo": pagina.title, 
            "resumo": texto_humanizado
        }
    except wikipedia.exceptions.DisambiguationError as e:
        # Se houver múltiplas opções, tenta a primeira
        if e.options:
            try:
                pagina = wikipedia.page(e.options[0])
                texto_humanizado = humanize_text(pagina.summary)
                return {
                    "titulo": pagina.title, 
                    "resumo": texto_humanizado
                }
            except Exception:
                raise HTTPException(status_code=404, detail="Tópico não encontrado após desambiguação")
        raise HTTPException(status_code=404, detail="Múltiplas possibilidades encontradas")
    except wikipedia.exceptions.PageError:
        raise HTTPException(status_code=404, detail="Tópico não encontrado na Wikipedia")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@app.get("/")
async def root():
    return {"message": "IA Coach API está funcionando!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
