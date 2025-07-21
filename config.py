import os

class Config:
    # Configurações gerais
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Configurações da Wikipedia
    WIKIPEDIA_LANGUAGE = os.getenv('WIKIPEDIA_LANGUAGE', 'pt')
    MAX_SEARCH_RESULTS = int(os.getenv('MAX_SEARCH_RESULTS', 10))
    MAX_SUMMARY_SENTENCES = int(os.getenv('MAX_SUMMARY_SENTENCES', 8))
    
    # Configurações de rate limiting (para implementar futuramente)
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))