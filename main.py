from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import wikipedia
import random
import re

# Configure o idioma para português
wikipedia.set_lang("pt")

app = FastAPI(
    title="IA Coach App API",
    description="API para auxiliar nos estudos com consulta à Wikipedia de forma amigável.",
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

# Endpoint para buscar resumo na Wikipedia
@app.get("/buscar/{termo}", dependencies=[Depends(verify_api_key)])
def buscar_wikipedia(termo: str):
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

# Endpoint expandido para ensinar sobre um tópico
@app.post("/ensinar", dependencies=[Depends(verify_api_key)])
def ensinar(request: EnsinarRequest):
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
