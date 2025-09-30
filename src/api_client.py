"""
Client API per comunicare con PrestaShop - VERSIONE CON IMMAGINI LOCALI
"""

import requests
import xml.etree.ElementTree as ET
import logging
import time
import os
from pathlib import Path
from typing import Optional, Dict

# Configurazione logging
logger = logging.getLogger(__name__)

class PrestaShopAPI:
    """Gestisce tutte le comunicazioni con le API di PrestaShop"""
    
    def __init__(self, api_url: str, api_key: str):
        """
        Inizializza il client API
        
        Args:
            api_url: URL base delle API (es. https://shop.com/api)
            api_key: Chiave API di PrestaShop
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.auth = (api_key, "")  # PrestaShop usa solo username, password vuota
        
    def test_connection(self) -> bool:
        """Testa se la connessione funziona"""
        try:
            response = requests.get(
                self.api_url,
                auth=self.auth,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Connessione API OK")
                return True
            else:
                logger.error(f"❌ Connessione fallita: Status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Errore connessione: {e}")
            return False
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Optional[ET.Element]:
        """
        Esegue una richiesta GET
        
        Args:
            endpoint: Endpoint API (es. 'products', 'categories')
            params: Parametri query opzionali
            
        Returns:
            Risposta XML parsata o None se errore
        """
        try:
            url = f"{self.api_url}/{endpoint}"
            response = requests.get(
                url,
                auth=self.auth,
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                return ET.fromstring(response.content)
            else:
                logger.error(f"GET {endpoint} fallito: Status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Errore GET {endpoint}: {e}")
            return None
    
    def post(self, endpoint: str, xml_data: str) -> Optional[ET.Element]:
        """
        Esegue una richiesta POST (per creare risorse)
        
        Args:
            endpoint: Endpoint API
            xml_data: Dati XML da inviare
            
        Returns:
            Risposta XML parsata o None se errore
        """
        try:
            url = f"{self.api_url}/{endpoint}"
            response = requests.post(
                url,
                auth=self.auth,
                data=xml_data,
                headers={'Content-Type': 'application/xml'},
                timeout=30
            )
            
            if response.status_code == 201:  # 201 = Created
                logger.info(f"✅ Risorsa creata su {endpoint}")
                return ET.fromstring(response.content)
            else:
                logger.error(f"POST {endpoint} fallito: Status {response.status_code}")
                logger.debug(f"Risposta: {response.text[:500]}")
                return None
                
        except Exception as e:
            logger.error(f"Errore POST {endpoint}: {e}")
            return None
    
    def put(self, endpoint: str, xml_data: str) -> bool:
        """
        Esegue una richiesta PUT (per aggiornare risorse)
        
        Args:
            endpoint: Endpoint API con ID (es. 'products/123')
            xml_data: Dati XML da inviare
            
        Returns:
            True se successo, False altrimenti
        """
        try:
            url = f"{self.api_url}/{endpoint}"
            response = requests.put(
                url,
                auth=self.auth,
                data=xml_data,
                headers={'Content-Type': 'application/xml'},
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Risorsa aggiornata: {endpoint}")
                return True
            else:
                logger.error(f"PUT {endpoint} fallito: Status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Errore PUT {endpoint}: {e}")
            return False
    
    def delete(self, endpoint: str) -> bool:
        """
        Esegue una richiesta DELETE
        
        Args:
            endpoint: Endpoint API con ID (es. 'products/123')
            
        Returns:
            True se successo, False altrimenti
        """
        try:
            url = f"{self.api_url}/{endpoint}"
            response = requests.delete(
                url,
                auth=self.auth,
                timeout=30
            )
            
            if response.status_code in [200, 204]:  # 204 = No Content
                logger.info(f"✅ Risorsa eliminata: {endpoint}")
                return True
            else:
                logger.error(f"DELETE {endpoint} fallito: Status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Errore DELETE {endpoint}: {e}")
            return False
    
    def search_by_reference(self, reference: str) -> Optional[str]:
        """
        Cerca un prodotto per reference
        
        Args:
            reference: Reference del prodotto
            
        Returns:
            ID del prodotto se trovato, None altrimenti
        """
        params = {
            'filter[reference]': reference,
            'display': 'full'
        }
        
        root = self.get('products', params)
        if root is not None:
            products = root.findall('.//product')
            if products:
                product_id = products[0].find('id').text
                logger.info(f"Prodotto trovato: {reference} (ID: {product_id})")
                return product_id
        
        logger.info(f"Prodotto non trovato: {reference}")
        return None
    
    def search_by_reference(self, reference: str) -> Optional[str]:
        """
        Cerca un prodotto per reference
        
        Args:
            reference: Reference del prodotto
            
        Returns:
            ID del prodotto se trovato, None altrimenti
        """
        params = {
            'filter[reference]': reference,
            'display': 'full'
        }
        
        root = self.get('products', params)
        if root is not None:
            products = root.findall('.//product')
            if products:
                product_id = products[0].find('id').text
                logger.info(f"Prodotto trovato: {reference} (ID: {product_id})")
                return product_id
        
        logger.info(f"Prodotto non trovato: {reference}")
        return None
    
    def upload_image_from_path(self, product_id: str, image_path: str, position: int = 1) -> bool:
        """
        Carica un'immagine per un prodotto DA FILE LOCALE
        
        Args:
            product_id: ID del prodotto
            image_path: Percorso del file immagine sul PC
            position: Posizione dell'immagine (1 = principale)
            
        Returns:
            True se successo, False altrimenti
        """
        try:
            # Verifica che il file esista
            image_path = Path(image_path.strip())
            if not image_path.exists():
                logger.error(f"❌ File immagine non trovato: {image_path}")
                return False
            
            # Verifica che sia un'immagine valida
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            if image_path.suffix.lower() not in valid_extensions:
                logger.error(f"❌ Formato immagine non valido: {image_path.suffix}")
                return False
            
            # Verifica dimensione file (max 8MB per sicurezza)
            file_size_mb = image_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 8:
                logger.warning(f"⚠️  Immagine molto grande ({file_size_mb:.1f}MB): {image_path.name}")
            
            # Leggi il file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Determina il content type
            content_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            content_type = content_types.get(image_path.suffix.lower(), 'image/jpeg')
            
            # Prepara il file per l'upload
            files = {
                'image': (image_path.name, image_data, content_type)
            }
            
            # Upload immagine
            url = f"{self.api_url}/images/products/{product_id}"
            response = requests.post(
                url,
                auth=self.auth,
                files=files,
                timeout=60
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"   🖼️  Immagine {position} caricata: {image_path.name}")
                return True
            else:
                logger.error(f"   ❌ Upload immagine fallito: Status {response.status_code}")
                logger.debug(f"   Risposta: {response.text[:200]}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Errore upload immagine {image_path}: {e}")
            return False
    
    def delete_product_images(self, product_id: str) -> int:
        """
        Elimina tutte le immagini di un prodotto
        
        Args:
            product_id: ID del prodotto
            
        Returns:
            Numero di immagini eliminate
        """
        deleted = 0
        try:
            # Ottieni lista immagini del prodotto
            response = self.get(f'images/products/{product_id}')
            if response is not None:
                images = response.findall('.//image')
                for image in images:
                    image_id = image.get('id')
                    if image_id:
                        # Elimina l'immagine
                        if self.delete(f'images/products/{product_id}/{image_id}'):
                            deleted += 1
                            logger.info(f"   🗑️  Immagine {image_id} eliminata")
            
            if deleted > 0:
                logger.info(f"   Eliminate {deleted} immagini esistenti")
                
        except Exception as e:
            logger.error(f"Errore eliminazione immagini: {e}")
        
        return deleted