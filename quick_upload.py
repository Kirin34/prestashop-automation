#!/usr/bin/env python3
"""
Upload veloce immagini - versione senza menu
Uso: python quick_images.py [csv_file | --all | reference]
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from config.config import Config
from src.api_client import PrestaShopAPI
from upload_images_only import ImageUploader
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def main():
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python quick_images.py file.csv      # Upload da CSV")
        print("  python quick_images.py --all         # Upload tutte le cartelle")
        print("  python quick_images.py PROD001       # Upload singolo prodotto")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    # Configurazione e connessione
    if not Config.validate():
        print("❌ Configurazione non valida!")
        sys.exit(1)
    
    api = PrestaShopAPI(Config.PRESTASHOP_API_URL, Config.PRESTASHOP_API_KEY)
    if not api.test_connection():
        print("❌ Connessione fallita!")
        sys.exit(1)
    
    uploader = ImageUploader(api)
    
    # Determina cosa fare
    if arg == '--all':
        print("📸 Upload TUTTE le cartelle in assets/")
        stats = uploader.process_all_assets_folders(Config.UPLOAD_DELAY)
        
    elif arg.endswith('.csv'):
        csv_path = Path(arg)
        if not csv_path.exists():
            csv_path = Config.INPUT_DIR / arg
        
        if not csv_path.exists():
            print(f"❌ File non trovato: {arg}")
            sys.exit(1)
        
        print(f"📸 Upload immagini da CSV: {csv_path.name}")
        stats = uploader.process_csv(str(csv_path), Config.UPLOAD_DELAY)
        
    else:
        # Assume sia un reference
        print(f"📸 Upload immagini per: {arg}")
        stats = uploader.process_single_product(arg)
    
    # Report
    print(f"\n{'='*50}")
    print(f"✅ Prodotti: {stats['products_processed']}")
    print(f"📸 Immagini: {stats['images_uploaded']}")
    print(f"❌ Errori: {stats['images_failed']}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()