from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import wikipedia
import random
import re

# Configure o idioma para português
wikipedia.set_lang("pt")

app = FastAPI(
    title="IA Coach App API",
    description="API para auxiliar nos estudos com consulta à Wikipedia.",
    version="1.2.0"
)

# API Key 
API_KEY = "893247589749805674895t980453760894537"

# Função para verificar a API Key
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="API Key inválida")

# Models
class EnsinarRequest(BaseModel):
    topico: str

# Função para tornar o texto mais amigável
def humanize_text(summary):
    # Interações iniciais
    interactions = [
        "Ótima pergunta! ",
        "Vamos explorar esse tópico interessante! ",
        "Deixe-me compartilhar alguns detalhes fascinantes: ",
        "Prepare-se para uma jornada de conhecimento! "
    ]
    
    # Adicionar uma interação inicial
    interaction = random.choice(interactions)
    
    # Simplificar o texto
    def simplify_text(text):
        # Dividir o texto em parágrafos
        paragraphs = text.split('\n')
        
        # Selecionar os dois primeiros parágrafos
        if len(paragraphs) > 2:
            text = '\n'.join(paragraphs[:2])
        
        # Remover referências e notas
        text = re.sub(r'\[.*?\]', '', text)
        
        # Limitar o tamanho
        if len(text) > 700:
            text = text[:700] + "..."
        
        return text
    
    simplified_summary = simplify_text(summary)
    
    return interaction + simplified_summary

# Endpoint para buscar resumo na Wikipedia
@app.get("/buscar/{termo}", dependencies=[Depends(verify_api_key)])
def buscar_wikipedia(termo: str):
    """
    Busca um termo na Wikipedia, processa o texto e retorna uma versão amigável.
    """
    try:
        # Tenta encontrar a página
        pagina = wikipedia.page(termo)
        
        # Usa o sumário da página
        texto_humanizado = humanize_text(pagina.summary)
        
        return {
            "titulo": pagina.title, 
            "resumo": texto_humanizado
        }
    except wikipedia.exceptions.DisambiguationError as e:
        # Se houver múltiplas possibilidades, retorna a primeira
        if e.options:
            try:
                pagina = wikipedia.page(e.options[0])
                texto_humanizado = humanize_text(pagina.summary)
                return {
                    "titulo": pagina.title, 
                    "resumo": texto_humanizado
                }
            except:
                raise HTTPException(status_code=404, detail="Tópico não encontrado após desambiguação")
        raise HTTPException(status_code=404, detail="Múltiplas possibilidades encontradas")
    except wikipedia.exceptions.PageError:
        raise HTTPException(status_code=404, detail="Tópico não encontrado na Wikipedia")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# Endpoint expandido para ensinar sobre um tópico
@app.post("/ensinar", dependencies=[Depends(verify_api_key)])
def ensinar(request: EnsinarRequest):
    """
    Retorna um conteúdo educativo sobre o tópico solicitado.
    """
    try:
        # Tenta encontrar a página
        pagina = wikipedia.page(request.topico)
        
        # Usa o sumário da página
        texto_humanizado = humanize_text(pagina.summary)
        
        return {
            "titulo": pagina.title, 
            "resumo": texto_humanizado
        }
    except wikipedia.exceptions.DisambiguationError as e:
        # Se houver múltiplas possibilidades, retorna a primeira
        if e.options:
            try:
                pagina = wikipedia.page(e.options[0])
                texto_humanizado = humanize_text(pagina.summary)
                return {
                    "titulo": pagina.title, 
                    "resumo": texto_humanizado
                }
            except:
                raise HTTPException(status_code=404, detail="Tópico não encontrado após desambiguação")
        raise HTTPException(status_code=404, detail="Múltiplas possibilidades encontradas")
    except wikipedia.exceptions.PageError:
        raise HTTPException(status_code=404, detail="Tópico não encontrado na Wikipedia")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
