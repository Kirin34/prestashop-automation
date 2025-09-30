"""
Configurazione centralizzata per PrestaShop Automation
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Carica le variabili dal file .env
load_dotenv()

# Directory base del progetto
BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    """Tutte le configurazioni in un unico posto"""
    
    # API PrestaShop
    PRESTASHOP_API_URL = os.getenv('PRESTASHOP_API_URL', '')
    PRESTASHOP_API_KEY = os.getenv('PRESTASHOP_API_KEY', '')
    
    # Impostazioni generali
    DEFAULT_LANGUAGE_ID = int(os.getenv('DEFAULT_LANGUAGE_ID', '1'))
    UPLOAD_DELAY = float(os.getenv('UPLOAD_DELAY', '0.5'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    
    # Percorsi delle cartelle
    INPUT_DIR = BASE_DIR / 'data' / 'input'
    PROCESSED_DIR = BASE_DIR / 'data' / 'processed'
    FAILED_DIR = BASE_DIR / 'data' / 'failed'
    ASSETS_DIR = BASE_DIR / 'data' / 'assets'
    LOG_DIR = BASE_DIR / 'logs'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Verifica che la configurazione sia valida"""
        errors = []
        
        if not cls.PRESTASHOP_API_URL:
            errors.append("❌ PRESTASHOP_API_URL mancante nel file .env")
        
        if not cls.PRESTASHOP_API_KEY:
            errors.append("❌ PRESTASHOP_API_KEY mancante nel file .env")
        
        # Crea le cartelle se non esistono
        for directory in [cls.INPUT_DIR, cls.PROCESSED_DIR, cls.FAILED_DIR, cls.LOG_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
        
        if errors:
            print("\n⚠️  ERRORI DI CONFIGURAZIONE:")
            for error in errors:
                print(f"  {error}")
            print("\n📝 Controlla il file .env")
            return False
        
        return True
    
    @classmethod
    def display(cls):
        """Mostra la configurazione corrente (nascondendo dati sensibili)"""
        print("\n" + "="*50)
        print("CONFIGURAZIONE CORRENTE")
        print("="*50)
        print(f"API URL: {cls.PRESTASHOP_API_URL}")
        print(f"API Key: {cls.PRESTASHOP_API_KEY[:10]}..." if cls.PRESTASHOP_API_KEY else "API Key: NON IMPOSTATA")
        print(f"Language ID: {cls.DEFAULT_LANGUAGE_ID}")
        print(f"Upload Delay: {cls.UPLOAD_DELAY} secondi")
        print(f"Input Dir: {cls.INPUT_DIR}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print("="*50 + "\n")