"""
Script per testare che tutto sia configurato correttamente
"""

import sys
from pathlib import Path

# Aggiungi il percorso del progetto
sys.path.append(str(Path(__file__).parent))

from config.config import Config
from src.api_client import PrestaShopAPI
import logging

# Configura il logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    print("\n🔧 TEST CONFIGURAZIONE PRESTASHOP")
    print("="*50)
    
    # Step 1: Verifica configurazione
    print("\n1️⃣ Verifica configurazione...")
    if not Config.validate():
        print("❌ Configurazione non valida. Controlla il file .env")
        return False
    
    Config.display()
    
    # Step 2: Test connessione API
    print("\n2️⃣ Test connessione API...")
    api = PrestaShopAPI(Config.PRESTASHOP_API_URL, Config.PRESTASHOP_API_KEY)
    
    if not api.test_connection():
        print("❌ Connessione API fallita")
        return False
    
    # Step 3: Test lettura prodotti
    print("\n3️⃣ Test lettura prodotti...")
    products = api.get('products', {'limit': 5})
    
    if products is not None:
        product_list = products.findall('.//product')
        print(f"✅ Trovati {len(product_list)} prodotti")
        
        # Mostra i primi prodotti
        for product in product_list[:3]:
            product_id = product.get('id')
            print(f"   - Prodotto ID: {product_id}")
    else:
        print("⚠️  Impossibile leggere i prodotti")
    
    # Step 4: Test lettura categorie
    print("\n4️⃣ Test lettura categorie...")
    categories = api.get('categories', {'limit': 5})
    
    if categories is not None:
        category_list = categories.findall('.//category')
        print(f"✅ Trovate {len(category_list)} categorie")
    else:
        print("⚠️  Impossibile leggere le categorie")
    
    print("\n" + "="*50)
    print("✅ SETUP COMPLETATO CON SUCCESSO!")
    print("="*50)
    print("\n📝 Prossimi passi:")
    print("1. Crea un file CSV in data/input/")
    print("2. Esegui lo script di upload")
    print("")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)