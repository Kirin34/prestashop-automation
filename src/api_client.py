"""
Client API per PrestaShop con gestione errori e retry
"""

import requests
import time
import logging
import xml.etree.ElementTree as ET
from typing import Optional, Dict

# Setup logger
logger = logging.getLogger(__name__)

class PrestaShopAPI:
    """Client per comunicare con le API di PrestaShop"""
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.auth = (api_key, "")  # PrestaShop usa solo la key, password vuota
        self.session = requests.Session()
        self.session.auth = self.auth
        
    def test_connection(self) -> bool:
        """Testa la connessione alle API"""
        try:
            response = self.session.get(self.api_url, timeout=10)
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
        """Esegue una richiesta GET"""
        try:
            url = f"{self.api_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return ET.fromstring(response.content)
            else:
                logger.error(f"GET {endpoint} fallito: Status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Errore GET {endpoint}: {e}")
            return None
    
    def post(self, endpoint: str, xml_data: str) -> Optional[ET.Element]:
        """Esegue una richiesta POST"""
        try:
            url = f"{self.api_url}/{endpoint}"
            headers = {'Content-Type': 'application/xml'}
            response = self.session.post(url, data=xml_data, headers=headers, timeout=30)
            
            if response.status_code == 201:  # 201 = Created
                logger.info(f"✅ POST {endpoint} riuscito")
                return ET.fromstring(response.content)
            else:
                logger.error(f"POST {endpoint} fallito: Status {response.status_code}")
                logger.debug(f"Risposta: {response.text[:500]}")
                return None
                
        except Exception as e:
            logger.error(f"Errore POST {endpoint}: {e}")
            return None
    
    def put(self, endpoint: str, xml_data: str) -> bool:
        """Esegue una richiesta PUT per aggiornamenti"""
        try:
            url = f"{self.api_url}/{endpoint}"
            headers = {'Content-Type': 'application/xml'}
            response = self.session.put(url, data=xml_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"✅ PUT {endpoint} riuscito")
                return True
            else:
                logger.error(f"PUT {endpoint} fallito: Status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Errore PUT {endpoint}: {e}")
            return False
    
    def delete(self, endpoint: str) -> bool:
        """Esegue una richiesta DELETE"""
        try:
            url = f"{self.api_url}/{endpoint}"
            response = self.session.delete(url, timeout=30)
            
            if response.status_code in [200, 204]:  # 204 = No Content
                logger.info(f"✅ DELETE {endpoint} riuscito")
                return True
            else:
                logger.error(f"DELETE {endpoint} fallito: Status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Errore DELETE {endpoint}: {e}")
            return False
    
    def search(self, resource: str, filters: Dict[str, str]) -> Optional[ET.Element]:
        """Cerca risorse con filtri"""
        params = {}
        for key, value in filters.items():
            params[f'filter[{key}]'] = value
        
        return self.get(resource, params=params)
    
    def upload_image(self, product_id: str, image_path: str) -> bool:
        """Carica un'immagine per un prodotto"""
        try:
            url = f"{self.api_url}/images/products/{product_id}"
            
            with open(image_path, 'rb') as f:
                files = {'image': ('image.jpg', f, 'image/jpeg')}
                response = self.session.post(url, files=files, timeout=60)
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Immagine caricata per prodotto {product_id}")
                return True
            else:
                logger.error(f"Upload immagine fallito: Status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Errore upload immagine: {e}")
            return False