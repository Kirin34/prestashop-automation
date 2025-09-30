#!/usr/bin/env python3
"""
Script SOLO per upload immagini - Non modifica i prodotti!
Cerca i prodotti per reference e carica le immagini da data/assets/
"""

import sys
import logging
import csv
from pathlib import Path
from datetime import datetime
import time

# Setup del path
sys.path.append(str(Path(__file__).parent))

from config.config import Config
from src.api_client import PrestaShopAPI

# Configurazione logging
def setup_logging():
    """Configura il sistema di logging"""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    log_file = Config.LOG_DIR / f"upload_images_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return log_file

class ImageUploader:
    """Gestore upload SOLO immagini"""
    
    def __init__(self, api_client):
        self.api = api_client
        self.assets_dir = Config.ASSETS_DIR
        self.stats = {
            'products_processed': 0,
            'products_skipped': 0,
            'images_uploaded': 0,
            'images_failed': 0,
            'products_not_found': 0
        }
        
        # Estensioni immagini valide
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        
        logging.info(f"📁 Cartella immagini: {self.assets_dir.absolute()}")
    
    def find_product_images(self, reference: str):
        """Trova tutte le immagini per un prodotto"""
        product_folder = self.assets_dir / reference
        
        if not product_folder.exists():
            return []
        
        # Trova tutte le immagini nella cartella
        images = []
        for file in product_folder.iterdir():
            if file.is_file() and file.suffix.lower() in self.image_extensions:
                images.append(file)
        
        # Ordina per nome (controllo ordine)
        images.sort(key=lambda x: x.name.lower())
        
        return images
    
    def upload_images_for_product(self, reference: str, replace_existing: bool = True):
        """Upload immagini per un singolo prodotto"""
        
        print(f"\n{'='*60}")
        print(f"📦 Prodotto: {reference}")
        
        # Step 1: Cerca se il prodotto esiste su PrestaShop
        product_id = self.api.search_by_reference(reference)
        
        if not product_id:
            print(f"   ❌ Prodotto non trovato su PrestaShop")
            self.stats['products_not_found'] += 1
            return False
        
        print(f"   ✅ Trovato su PrestaShop (ID: {product_id})")
        
        # Step 2: Trova le immagini nella cartella assets
        images = self.find_product_images(reference)
        
        if not images:
            print(f"   ⚠️  Nessuna immagine trovata in: data/assets/{reference}/")
            self.stats['products_skipped'] += 1
            return False
        
        print(f"   📸 Trovate {len(images)} immagini da caricare:")
        for img in images:
            size_kb = img.stat().st_size / 1024
            print(f"      - {img.name} ({size_kb:.0f} KB)")
        
        # Step 3: Elimina immagini esistenti se richiesto
        if replace_existing:
            deleted = self.api.delete_product_images(product_id)
            if deleted > 0:
                print(f"   🗑️  Eliminate {deleted} immagini esistenti")
        
        # Step 4: Carica le nuove immagini
        uploaded = 0
        for position, image_path in enumerate(images, 1):
            print(f"   📤 Caricamento {position}/{len(images)}: {image_path.name}...")
            
            if self.api.upload_image_from_path(product_id, str(image_path), position):
                uploaded += 1
                self.stats['images_uploaded'] += 1
                print(f"      ✅ OK")
            else:
                self.stats['images_failed'] += 1
                print(f"      ❌ Fallito")
            
            # Piccola pausa tra un'immagine e l'altra
            if position < len(images):
                time.sleep(0.2)
        
        if uploaded > 0:
            print(f"   ✅ COMPLETATO: {uploaded}/{len(images)} immagini caricate")
            self.stats['products_processed'] += 1
            return True
        else:
            print(f"   ❌ ERRORE: Nessuna immagine caricata")
            return False
    
    def process_csv(self, csv_path: str, delay: float = 0.5):
        """Processa un CSV caricando SOLO le immagini"""
        
        if not Path(csv_path).exists():
            logging.error(f"File non trovato: {csv_path}")
            return self.stats
        
        print(f"\n📂 File CSV: {csv_path}")
        print(f"⏱️  Pausa tra prodotti: {delay} secondi")
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file, delimiter=';')
                rows = list(reader)
                total = len(rows)
                
                print(f"📊 Trovati {total} prodotti nel CSV")
                
                for index, row in enumerate(rows, 1):
                    reference = row.get('reference', '').strip()
                    
                    if not reference:
                        print(f"\n[{index}/{total}] ⚠️  Reference mancante, skip")
                        continue
                    
                    print(f"\n[{index}/{total}]")
                    self.upload_images_for_product(reference)
                    
                    # Pausa tra un prodotto e l'altro
                    if index < total:
                        time.sleep(delay)
                
        except Exception as e:
            logging.error(f"Errore lettura CSV: {e}")
        
        return self.stats
    
    def process_single_product(self, reference: str):
        """Processa un singolo prodotto per reference"""
        print(f"\n🎯 Upload immagini per prodotto singolo: {reference}")
        self.upload_images_for_product(reference)
        return self.stats
    
    def process_all_assets_folders(self, delay: float = 0.5):
        """Processa TUTTE le cartelle in assets (senza CSV)"""
        
        print(f"\n📁 Elaborazione di TUTTE le cartelle in: {self.assets_dir}")
        
        # Trova tutte le cartelle in assets
        folders = [f for f in self.assets_dir.iterdir() if f.is_dir()]
        
        if not folders:
            print("⚠️  Nessuna cartella trovata in assets/")
            return self.stats
        
        print(f"📊 Trovate {len(folders)} cartelle prodotto")
        
        for index, folder in enumerate(folders, 1):
            reference = folder.name
            print(f"\n[{index}/{len(folders)}]")
            self.upload_images_for_product(reference)
            
            # Pausa tra un prodotto e l'altro
            if index < len(folders):
                time.sleep(delay)
        
        return self.stats

def main():
    """Funzione principale"""
    print("\n" + "="*60)
    print("📸 UPLOAD SOLO IMMAGINI - PRESTASHOP")
    print("="*60)
    print("⚠️  ATTENZIONE: Questo script NON modifica i dati prodotto!")
    print("   Carica SOLO le immagini da data/assets/")
    print("="*60)
    
    # Configurazione
    if not Config.validate():
        print("❌ Configurazione non valida!")
        return False
    
    # Setup logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    # Connessione API
    print("\n🔌 Connessione alle API...")
    api = PrestaShopAPI(Config.API_URL, Config.API_KEY)
    
    if not api.test_connection():
        print("❌ Impossibile connettersi alle API!")
        return False
    
    print("✅ Connesso a PrestaShop!")
    
    # Menu opzioni
    print("\n" + "="*60)
    print("SCEGLI MODALITÀ:")
    print("="*60)
    print("1. Upload da file CSV (solo prodotti nel CSV)")
    print("2. Upload TUTTE le cartelle in assets/")
    print("3. Upload singolo prodotto (inserisci reference)")
    print("="*60)
    
    choice = input("\n▶️  Scelta (1/2/3): ").strip()
    
    uploader = ImageUploader(api)
    stats = None
    
    if choice == '1':
        # Modalità CSV
        csv_files = list(Config.INPUT_DIR.glob('*.csv'))
        
        if not csv_files:
            print(f"❌ Nessun CSV trovato in {Config.INPUT_DIR}")
            return False
        
        print(f"\n📁 File CSV disponibili:")
        for i, csv_file in enumerate(csv_files, 1):
            print(f"{i}. {csv_file.name}")
        
        if len(csv_files) == 1:
            csv_choice = 0
        else:
            csv_choice = int(input(f"\n▶️  Quale file? (1-{len(csv_files)}): ")) - 1
        
        csv_file = csv_files[csv_choice]
        
        # Chiedi conferma
        response = input(f"\n▶️  Caricare immagini per i prodotti in {csv_file.name}? (s/n): ")
        if response.lower() == 's':
            stats = uploader.process_csv(str(csv_file), Config.UPLOAD_DELAY)
    
    elif choice == '2':
        # Modalità tutte le cartelle
        folders = list(Config.ASSETS_DIR.iterdir())
        folder_count = len([f for f in folders if f.is_dir()])
        
        print(f"\n📁 Trovate {folder_count} cartelle in assets/")
        response = input(f"▶️  Caricare immagini per TUTTI i prodotti? (s/n): ")
        
        if response.lower() == 's':
            stats = uploader.process_all_assets_folders(Config.UPLOAD_DELAY)
    
    elif choice == '3':
        # Modalità singolo prodotto
        reference = input("\n▶️  Inserisci il reference del prodotto: ").strip()
        
        if reference:
            # Verifica che esista la cartella
            folder = Config.ASSETS_DIR / reference
            if not folder.exists():
                print(f"❌ Cartella non trovata: {folder}")
                create = input("▶️  Vuoi crearla? (s/n): ")
                if create.lower() == 's':
                    folder.mkdir(exist_ok=True)
                    print(f"✅ Cartella creata. Aggiungi le immagini e riprova.")
                return False
            
            stats = uploader.process_single_product(reference)
    
    else:
        print("❌ Scelta non valida")
        return False
    
    # Report finale
    if stats:
        print("\n" + "="*60)
        print("📊 REPORT FINALE")
        print("="*60)
        print(f"✅ Prodotti processati: {stats['products_processed']}")
        print(f"📸 Immagini caricate: {stats['images_uploaded']}")
        print(f"⚠️  Prodotti saltati: {stats['products_skipped']}")
        print(f"❌ Prodotti non trovati: {stats['products_not_found']}")
        print(f"❌ Immagini fallite: {stats['images_failed']}")
        print(f"📝 Log salvato in: {log_file}")
        print("="*60)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Upload interrotto dall'utente")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Errore inaspettato: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)