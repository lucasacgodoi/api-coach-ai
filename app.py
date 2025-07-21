from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import wikipedia
import re
import logging
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar idioma do Wikipedia para português
wikipedia.set_lang("pt")

class StudyAssistantAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'StudyAssistant/1.0 (Educational API)'
        })
    
    def search_wikipedia(self, query, max_sentences=8):
        """Busca informações na Wikipedia"""
        try:
            # Limpar e normalizar a query
            clean_query = self.clean_query(query)
            
            # Buscar páginas relacionadas
            search_results = wikipedia.search(clean_query, results=5)
            
            if not search_results:
                return None
            
            # Tentar obter a melhor página
            for result in search_results:
                try:
                    page = wikipedia.page(result)
                    summary = wikipedia.summary(result, sentences=max_sentences)
                    
                    return {
                        'title': page.title,
                        'summary': summary,
                        'url': page.url,
                        'categories': getattr(page, 'categories', [])[:5]  # Primeiras 5 categorias
                    }
                except wikipedia.exceptions.DisambiguationError:
                    continue
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao buscar Wikipedia: {str(e)}")
            return None
    
    def clean_query(self, query):
        """Limpa e normaliza a pergunta"""
        # Remove caracteres especiais e palavras de pergunta comuns
        query = re.sub(r'^(o que é|what is|como|por que|porque|onde|quando|quem|qual)\s+', '', query.lower())
        query = re.sub(r'[^\w\s]', '', query)
        return query.strip()
    
    def format_educational_response(self, question, wikipedia_data):
        """Formata a resposta de forma educacional sem usar IA externa"""
        try:
            if not wikipedia_data:
                return self.generate_not_found_response(question)
            
            # Extrair informações principais
            title = wikipedia_data['title']
            content = wikipedia_data['summary']
            
            # Estruturar a resposta educacional
            formatted_response = self.structure_educational_content(title, content, question)
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Erro ao formatar resposta: {str(e)}")
            return "Desculpe, não foi possível processar sua pergunta adequadamente."
    
    def structure_educational_content(self, title, content, question):
        """Estrutura o conteúdo de forma educacional"""
        
        # Dividir o conteúdo em parágrafos
        paragraphs = [p.strip() for p in content.split('.') if p.strip()]
        
        # Criar estrutura educacional
        response_parts = []
        
        # Introdução baseada na pergunta
        intro = f"📚 **{title}**\n\n"
        
        # Definição principal (primeiras frases)
        if paragraphs:
            definition = paragraphs[0] + "."
            response_parts.append(f"**Definição:**\n{definition}\n")
        
        # Características principais
        if len(paragraphs) > 1:
            characteristics = []
            for i, para in enumerate(paragraphs[1:4]):  # Próximos 3 parágrafos
                if para:
                    characteristics.append(f"• {para.strip()}.")
            
            if characteristics:
                response_parts.append(f"**Características principais:**\n" + "\n".join(characteristics) + "\n")
        
        # Informações adicionais
        if len(paragraphs) > 4:
            additional_info = []
            for para in paragraphs[4:7]:  # Mais 3 parágrafos
                if para and len(para) > 20:
                    additional_info.append(f"• {para.strip()}.")
            
            if additional_info:
                response_parts.append(f"**Informações complementares:**\n" + "\n".join(additional_info) + "\n")
        
        # Montar resposta final
        final_response = intro + "\n".join(response_parts)
        
        # Adicionar conclusão educacional
        final_response += f"\n**💡 Resumo:**\nEste conceito é importante para entender {title.lower()} e suas aplicações no contexto educacional."
        
        return final_response
    
    def generate_not_found_response(self, question):
        """Gera resposta quando não encontra informações"""
        return f"""
❌ **Informação não encontrada**

Desculpe, não foi possível encontrar informações específicas sobre "{question}" na Wikipedia.

**Sugestões:**
• Tente reformular sua pergunta de forma mais específica
• Verifique a ortografia dos termos utilizados
• Use sinônimos ou termos relacionados
• Seja mais específico sobre o contexto da pergunta

**Exemplo:** Em vez de "isso", tente "fotossíntese" ou "revolução francesa"
        """

study_assistant = StudyAssistantAPI()

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se a API está funcionando"""
    return jsonify({
        'status': 'active',
        'message': 'Study Assistant API está funcionando!',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/ask', methods=['POST'])
def ask_question():
    """Endpoint principal para processar perguntas"""
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': 'Pergunta não fornecida',
                'code': 'MISSING_QUESTION'
            }), 400
        
        question = data['question'].strip()
        
        if not question:
            return jsonify({
                'success': False,
                'error': 'Pergunta não pode estar vazia',
                'code': 'EMPTY_QUESTION'
            }), 400
        
        if len(question) < 3:
            return jsonify({
                'success': False,
                'error': 'Pergunta muito curta. Use pelo menos 3 caracteres.',
                'code': 'QUESTION_TOO_SHORT'
            }), 400
        
        logger.info(f"Processando pergunta: {question}")
        
        # Buscar na Wikipedia
        wikipedia_data = study_assistant.search_wikipedia(question)
        
        # Formatar resposta educacional
        formatted_response = study_assistant.format_educational_response(question, wikipedia_data)
        
        response_data = {
            'success': True,
            'question': question,
            'answer': formatted_response,
            'timestamp': datetime.now().isoformat(),
            'source': {
                'type': 'wikipedia',
                'found': wikipedia_data is not None,
                'title': wikipedia_data['title'] if wikipedia_data else None,
                'url': wikipedia_data['url'] if wikipedia_data else None
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Erro no endpoint ask: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/search', methods=['POST'])
def search_topics():
    """Endpoint para buscar tópicos relacionados"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Query não fornecida'
            }), 400
        
        query = data['query'].strip()
        limit = data.get('limit', 10)  # Limite padrão de 10 resultados
        
        if limit > 20:
            limit = 20  # Máximo de 20 resultados
        
        # Buscar tópicos relacionados na Wikipedia
        search_results = wikipedia.search(query, results=limit)
        
        # Enriquecer resultados com informações básicas
        enriched_results = []
        for result in search_results[:5]:  # Primeiros 5 para não sobrecarregar
            try:
                summary = wikipedia.summary(result, sentences=1)
                enriched_results.append({
                    'title': result,
                    'preview': summary
                })
            except:
                enriched_results.append({
                    'title': result,
                    'preview': 'Informações disponíveis na Wikipedia'
                })
        
        return jsonify({
            'success': True,
            'query': query,
            'results_count': len(search_results),
            'topics': search_results,
            'enriched_topics': enriched_results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro no endpoint search: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro ao buscar tópicos'
        }), 500

@app.route('/categories', methods=['GET'])
def get_popular_categories():
    """Endpoint para obter categorias populares de estudo"""
    categories = [
        "Matemática", "História", "Geografia", "Biologia", "Química", 
        "Física", "Literatura", "Filosofia", "Sociologia", "Psicologia",
        "Economia", "Política", "Arte", "Música", "Tecnologia"
    ]
    
    return jsonify({
        'success': True,
        'categories': categories,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
