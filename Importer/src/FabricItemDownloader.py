import requests
import time
import base64
import zipfile
import io
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from msal import PublicClientApplication
import logging

# Configurar encoding UTF-8 para evitar errores con emojis en Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Setup logging
logger = logging.getLogger("src.FabricItemDownloader")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class FabricItemDownloader:
  
    """
    Clase para descargar items de Microsoft Fabric usando la API REST.
    
    Soporta la descarga de:
    - Reportes (PBIR)
    - Modelos semánticos (PBISM)
    - Workspaces
    
    Características:
    - Autenticación con MSAL y cache de tokens
    - Opción para usar token externo ya autenticado
    - Descarga de definiciones con extracción de archivos base64
    - Organización automática en carpetas por workspace y nombre de item
    - Soporte para operaciones asíncronas con polling
    """
    
    TOKEN_CACHE_FILE = "fabric_token_cache.json"
    DEFAULT_SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]
    
    def __init__(self, client_id="04b07795-8ddb-461a-bbee-02f9e1bf7b46", 
                 tenant_id="common", 
                 token_cache_file=None,
                 access_token=None,
                 scopes=None):
        """
        Inicializa el descargador de items de Fabric.
        
        Args:
            client_id: ID del cliente de Azure AD
            tenant_id: ID del tenant (default: "common")
            token_cache_file: Archivo para guardar el cache de tokens (default: fabric_token_cache.json)
            access_token: Token de acceso ya obtenido (opcional, si se proporciona, no autentica)
            scopes: Lista de scopes para autenticación (default: Power BI API)
        """
        self.config = {
            "client_id": client_id,
            "tenant_id": tenant_id,
            "scopes": scopes or self.DEFAULT_SCOPES,
            "authority": f"https://login.microsoftonline.com/{tenant_id}"
        }
        self.token_cache_file = token_cache_file or self.TOKEN_CACHE_FILE
        self.access_token = access_token  # Puede ser None o un token ya obtenido
        self._external_token = access_token is not None  # Flag para saber si es token externo
    
    def set_access_token(self, access_token: str):
        """
        Establece un token de acceso externo.
        
        Args:
            access_token: Token de acceso ya autenticado
        """
        self.access_token = access_token
        self._external_token = True
        logger.info("✅ Token externo establecido")
    
    def load_token_from_file(self):
        """Carga el token del archivo si existe y no ha expirado"""
        if not os.path.exists(self.token_cache_file):
            return None
        
        try:
            with open(self.token_cache_file, 'r') as f:
                data = json.load(f)
                expires_at = datetime.fromisoformat(data['expires_at'])
                
                # Asegurar que expires_at sea timezone-aware
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                
                # Asegurar que ambos datetime sean timezone-aware para comparar
                now_utc = datetime.now(timezone.utc)
                
                # Si el token expira en menos de 1 minuto, considerarlo expirado
                if expires_at > now_utc + timedelta(minutes=1):
                    logger.info("✅ Token reutilizado del archivo")
                    return data['access_token']
                else:
                    logger.info("⏱️ Token expirado, necesario renovar")
                    return None
        except Exception as e:
            logger.error(f"❌ Error cargando token: {e}")
            return None
    
    def save_token_to_file(self, access_token):
        """Guarda el token en un archivo con su fecha de expiración"""
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        data = {
            'access_token': access_token,
            'expires_at': expires_at.isoformat(),
            'saved_at': datetime.now(timezone.utc).isoformat()
        }
        
        with open(self.token_cache_file, 'w') as f:
            json.dump(data, f)
        logger.info(f"💾 Token guardado hasta {expires_at}")
    
    
    def authenticate(self, callback=None) -> bool:
        """
        Autentica usando device code flow.
        Si ya hay un token externo establecido, no hace nada.
        
        Args:
            callback: Función opcional para mostrar el código de dispositivo
        
        Returns:
            bool: True si la autenticación fue exitosa
        """
        try:
            # Si ya hay token externo, no autenticar
            if self._external_token and self.access_token:
                logger.info("Usando token externo ya establecido")
                return True
            
            # Intentar cargar token del cache
            cached_token = self.load_token_from_file()
            if cached_token:
                self.access_token = cached_token
                logger.info("Authenticated using local cached token")
                return True
            
            # Device code flow
            logger.info("🔐 Autenticando con device code flow...")
            
            app = PublicClientApplication(
                self.config["client_id"],
                authority=self.config["authority"]
            )
            
            flow = app.initiate_device_flow(scopes=self.config["scopes"])
            if "user_code" not in flow:
                raise ValueError(f"Failed to create device flow: {flow.get('error_description')}")
            
            # Mostrar código de dispositivo
            message = flow["message"]
            if callback:
                callback(message)
            else:
                print(message, flush=True)
                logger.info(message)
            
            result = app.acquire_token_by_device_flow(flow)
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.save_token_to_file(self.access_token)
                logger.info("Authentication successful")
                return True
            else:
                logger.error(f"Authentication failed: {result.get('error_description')}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def get_access_token(self):
        """Obtiene el token actual, autentica si es necesario"""
        if self.access_token:
            return self.access_token
        
        # Si no hay token, intentar autenticar
        if self.authenticate():
            return self.access_token
        
        return None
    
    def list_workspaces(self):
        """
        Lista todos los workspaces disponibles para el usuario.
        
        Returns:
            Lista de workspaces con sus IDs y nombres
        """
        if not self.access_token:
            self.access_token = self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"\n🏢 Listando workspaces disponibles...")
        list_url = f"https://api.fabric.microsoft.com/v1/workspaces"
        response = requests.get(list_url, headers=headers)
        
        if response.status_code == 200:
            workspaces = response.json().get('value', [])
            logger.info(f"✅ Se encontraron {len(workspaces)} workspaces:")
            for i, ws in enumerate(workspaces, 1):
                logger.info(f"  {i}. {ws.get('displayName')} -> ID: {ws.get('id')}")
            return workspaces
        else:
            logger.error(f"❌ Error listando workspaces: {response.status_code}")
            logger.error(response.text)
            return []
    
    def get_workspace_info(self, workspace_id):
        """
        Obtiene información del workspace y ajusta campos de capacidad según reglas de negocio.
        
        Args:
            workspace_id: ID del workspace de Fabric
            
        Returns:
            Diccionario con información del workspace
        """
        if not self.access_token:
            self.access_token = self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        workspace_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}"
        response = requests.get(workspace_url, headers=headers)
        
        if response.status_code == 200:
            ws = response.json()
            # Normalizar campos de capacidad
            capacity_id = ws.get("capacityId")
            capacity_sku = ws.get("capacitySku")
            # isOnDedicatedCapacity: True solo si ambos capacityId y capacitySku no son nulos
            ws["isOnDedicatedCapacity"] = bool(capacity_id and capacity_sku)
            # Si capacityId existe pero capacitySku es None, type pasa a 'ppu'
            if capacity_id and not capacity_sku:
                ws_type = ws.get("type", "workspace")
                if ws_type == "workspace":
                    ws["type"] = "ppu"
            return ws
        elif response.status_code == 404:
            logger.error(f"❌ Workspace no encontrado: {workspace_id}")
            logger.error(f"   Verifica que el ID sea correcto y que tengas permisos de acceso")
            return {"displayName": workspace_id}
        else:
            logger.warning(f"⚠️ Error {response.status_code} obteniendo info del workspace")
            return {"displayName": workspace_id}
    
    def list_reports(self, workspace_id):
        """
        Lista todos los reportes disponibles en un workspace.
        
        Args:
            workspace_id: ID del workspace de Fabric
            
        Returns:
            Lista de reportes con sus IDs y nombres
        """
        if not self.access_token:
            self.access_token = self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"\n📋 Listando reportes en workspace {workspace_id}...")
        list_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/reports"
        response = requests.get(list_url, headers=headers)
        
        if response.status_code == 200:
            reports = response.json().get('value', [])
            logger.info(f"✅ Se encontraron {len(reports)} reportes:")
            return reports
        else:
            logger.error(f"❌ Error listando reportes: {response.status_code}")
            if response.status_code == 404:
                logger.error("   El workspace no existe o no tienes permisos para acceder")
            logger.error(response.text)
            return []
    
    def list_semantic_models(self, workspace_id):
        """
        Lista todos los modelos semánticos disponibles en un workspace.
        
        Args:
            workspace_id: ID del workspace de Fabric
            
        Returns:
            Lista de modelos semánticos con sus IDs y nombres
        """
        if not self.access_token:
            self.access_token = self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        logger.info(f"\n📊 Listando modelos semánticos en workspace {workspace_id}...")
        list_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/semanticModels"
        response = requests.get(list_url, headers=headers)
        
        if response.status_code == 200:
            models = response.json().get('value', [])
            logger.info(f"✅ Se encontraron {len(models)} modelos semánticos:")
            for i, model in enumerate(models, 1):
                logger.info(f"  {i}. {model.get('displayName')} -> ID: {model.get('id')}")
            return models
        else:
            logger.error(f"❌ Error listando modelos semánticos: {response.status_code}")
            logger.error(response.text)
            return []
    
    def download_pbix(self, workspace_id, report_id, report_name, output_folder="data", workspace_name=None):
        """
        Descarga un archivo PBIX de un reporte clásico de Power BI usando ExportToFile.
        
        Args:
            workspace_id: ID del workspace
            report_id: ID del reporte
            report_name: Nombre del reporte
            output_folder: Carpeta base para guardar (default: "data")
            workspace_name: Nombre del workspace (opcional)
            
        Returns:
            True si la descarga fue exitosa, False en caso contrario
        """
        if not self.access_token:
            self.access_token = self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        logger.info(f"\n📦 Descargando PBIX (reporte clásico)...")
        logger.info(f"   Nota: Requiere permisos de Contributor con Build en el reporte")
        # Intentar con el endpoint directo de descarga (requiere permisos de Owner/Build)
        download_url = f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/reports/{report_id}/Export"
        
        response = requests.get(download_url, headers=headers, stream=True)
        
        if response.status_code == 200:
            # Guardar directamente el archivo
            if workspace_name:
                safe_workspace_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in workspace_name.strip())
            else:
                safe_workspace_name = workspace_id
            
            safe_report_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in report_name.strip())
            target_folder = os.path.join(output_folder, safe_workspace_name, safe_report_name)
            os.makedirs(target_folder, exist_ok=True)
            
            # Guardar el archivo PBIX
            pbix_path = os.path.join(target_folder, f"{safe_report_name}.pbix")
            
            with open(pbix_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = os.path.getsize(pbix_path)
            logger.info(f"✅ PBIX descargado: {pbix_path} ({file_size:,} bytes)")
            return True
        else:
            logger.error(f"❌ Error descargando PBIX: {response.status_code}")
            logger.error(response.text)
            if response.status_code in [401, 403]:
                logger.warning("   ⚠️ No tienes permisos suficientes para descargar este reporte")
                logger.warning("   ℹ️ Se requieren permisos de Owner o Contributor con capacidad de Build")
            return False
    
    def download(self, workspace_id, report_id, output_folder="data"):
        """
        Descarga un reporte de Fabric y guarda sus archivos.
        Detecta automáticamente si es un reporte PBIR (nuevo) o clásico (PBIX).
        
        Args:
            workspace_id: ID del workspace de Fabric
            report_id: ID del reporte a descargar
            output_folder: Carpeta base para guardar los archivos (default: "data")
                          Los archivos se guardarán en: {output_folder}/{workspace_name}/{report_name}/
            
        Returns:
            True si la descarga fue exitosa, False en caso contrario
        """
        # Obtener token si no existe
        if not self.access_token:
            self.access_token = self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Obtener información del workspace
        workspace_info = self.get_workspace_info(workspace_id)
        workspace_name = workspace_info.get('displayName', workspace_id)
        
        # Listar reportes disponibles
        reports = self.list_reports(workspace_id)
        
        if not reports:
            print("❌ No se encontraron reportes en el workspace")
            return False
        
        # Encontrar el reporte específico o usar el primero
        current_report = None
        if report_id:
            current_report = next((r for r in reports if r.get('id') == report_id), None)
        
        if not current_report:
            current_report = reports[0]
            report_id = current_report.get('id')
            print(f"\n✅ Usando reporte: {current_report.get('displayName')} ({report_id})")
        
        report_name = current_report.get('displayName', report_id)
        
        # Crear la estructura de carpetas: data/{workspace_name}/{report_name}/
        safe_workspace_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in workspace_name.strip())
        safe_report_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in report_name.strip())
        target_folder = os.path.join(output_folder, safe_workspace_name, safe_report_name)
        
        # Crear la carpeta de destino
        os.makedirs(target_folder, exist_ok=True)
        logger.info(f"📁 Guardando en: {target_folder}")
        
        # Construir URL de definición para reporte
        definition_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/reports/{report_id}/getDefinition"
        
        # Intentar descargar como PBIR (nuevo formato)
        success = self._download_definition(definition_url, headers, target_folder, workspace_id, report_id, report_name, workspace_name, output_folder)
        
        return success
    
    def _download_definition(self, definition_url, headers, target_folder, workspace_id=None, item_id=None, item_name=None, workspace_name=None, output_folder="data"):
        """
        Método privado para manejar la descarga de definiciones (común para reportes y modelos).
        Si falla con 404, intenta descargar como PBIX (reporte clásico).
        
        Args:
            definition_url: URL del endpoint de getDefinition
            headers: Headers HTTP con autenticación
            target_folder: Carpeta donde guardar los archivos
            workspace_id: ID del workspace (opcional, para fallback a PBIX)
            item_id: ID del item/reporte (opcional, para fallback a PBIX)
            item_name: Nombre del item (opcional, para fallback a PBIX)
            workspace_name: Nombre del workspace (opcional, para fallback a PBIX)
            output_folder: Carpeta base (opcional, para fallback a PBIX)
            
        Returns:
            True si la descarga fue exitosa, False en caso contrario
        """
        logger.info(f"\n📥 Descargando definición...")
        
        # POST para iniciar la operación
        response = requests.post(definition_url, headers=headers)
        
        if response.status_code != 202:
            logger.error(f"❌ Error iniciando descarga: {response.status_code}")
            logger.error(response.text)
            if response.status_code in [401, 403]:
                logger.warning("\n⚠️ No tienes permisos para acceder a este reporte vía API de Fabric")
                logger.warning("   Posibles razones:")
                logger.warning("   - El reporte requiere permisos especiales de Fabric (no solo Power BI)")
                logger.warning("   - Necesitas rol de Admin o Member con permisos extendidos")
                logger.warning("   - El reporte puede tener configuración de seguridad adicional")
                if workspace_id and item_id and item_name and 'reports' in definition_url:
                    logger.info("\n💡 Intentando método alternativo de descarga...")
                    return self.download_pbix(workspace_id, item_id, item_name, output_folder, workspace_name)
            elif response.status_code == 404 and workspace_id and item_id and item_name:
                logger.info("\n💡 Detectado reporte clásico (no PBIR)")
                logger.info("   Intentando descargar como archivo PBIX...")
                return self.download_pbix(workspace_id, item_id, item_name, output_folder, workspace_name)
            return False
        
        # Obtener la URL de la operación desde el header Location
        operation_url = response.headers.get('Location')
        operation_id = response.headers.get('x-ms-operation-id')
        
        logger.info(f"📊 Operation ID: {operation_id}")
        logger.info(f"📊 Operation URL: {operation_url}")
        if not operation_url:
            logger.error("❌ No se pudo obtener la URL de la operación")
            return False
        
        # Polling: Esperar a que la operación se complete
        max_attempts = 30
        definition_data = None
        
        for attempt in range(max_attempts):
            time.sleep(2)
            
            status_response = requests.get(operation_url, headers=headers)
            status_data = status_response.json()
            
            status = status_data.get('status')
            logger.info(f"Intento {attempt + 1}: Estado = {status}")
            
            if status == 'Succeeded':
                logger.info("✅ Operación completada")
                break
            elif status == 'Failed':
                logger.error(f"❌ Error: {status_data.get('error')}")
                return False
        
        # Obtener el resultado final
        final_response = requests.get(operation_url, headers=headers)
        
        if final_response.status_code == 200:
            operation_result = final_response.json()
            result_url: str | None = final_response.headers.get('Location')
            logger.info(f"📊 Result URL: {result_url}")
            if result_url:
                result_response = requests.get(result_url, headers=headers)
                if result_response.status_code == 200:
                    definition_data = result_response.json()
                    logger.info(f"📊 Resultado descargado exitosamente")
                else:
                    logger.error(f"❌ Error descargando resultado: {result_response.text}")
                    return False
            else:
                logger.warning("⚠️ No se encontró URL de resultado en el header Location")
                return False
        else:
            logger.error(f"📊 Error obteniendo resultado: {final_response.text}")
            return False
        if definition_data:
            parts = definition_data.get('definition', {}).get('parts', [])
            if not parts:
                logger.warning("⚠️ No se encontraron partes en la definición")
                return False
            for part in parts:
                path = part.get('path')
                payload = part.get('payload')
                payload_type = part.get('payloadType')
                if payload_type == 'InlineBase64':
                    full_path = os.path.join(target_folder, path)
                    dir_path = os.path.dirname(full_path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    content = base64.b64decode(payload)
                    with open(full_path, 'wb') as f:
                        f.write(content)
                    logger.info(f"📥 Descargado: {full_path}")
            logger.info(f"\n✅ Descarga completada exitosamente")
            return True
        return False
    
    def download_semantic_model(self, workspace_id, semantic_model_id, output_folder="data"):
        """
        Descarga un modelo semántico de Fabric y guarda sus archivos.
        
        Args:
            workspace_id: ID del workspace de Fabric
            semantic_model_id: ID del modelo semántico a descargar
            output_folder: Carpeta base para guardar los archivos (default: "data")
                          Los archivos se guardarán en: {output_folder}/{workspace_name}/{model_name}/
            
        Returns:
            True si la descarga fue exitosa, False en caso contrario
        """
        # Obtener token si no existe
        if not self.access_token:
            self.access_token = self.get_access_token()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Obtener información del workspace
        workspace_info = self.get_workspace_info(workspace_id)
        workspace_name = workspace_info.get('displayName', workspace_id)
        
        # Listar modelos semánticos disponibles
        models = self.list_semantic_models(workspace_id)
        
        if not models:
            print("❌ No se encontraron modelos semánticos en el workspace")
            return False
        
        # Encontrar el modelo específico o usar el primero
        current_model = None
        if semantic_model_id:
            current_model = next((m for m in models if m.get('id') == semantic_model_id), None)
        
        if not current_model:
            current_model = models[0]
            semantic_model_id = current_model.get('id')
            print(f"\n✅ Usando modelo semántico: {current_model.get('displayName')} ({semantic_model_id})")
        
        model_name = current_model.get('displayName', semantic_model_id)
        
        # Crear la estructura de carpetas: data/{workspace_name}/{model_name}/
        safe_workspace_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in workspace_name.strip())
        safe_model_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in model_name.strip())
        target_folder = os.path.join(output_folder, safe_workspace_name, safe_model_name)
        
        # Crear la carpeta de destino
        os.makedirs(target_folder, exist_ok=True)
        logger.info(f"📁 Guardando en: {target_folder}")
        
        # Construir URL de definición para modelo semántico
        definition_url = f"https://api.fabric.microsoft.com/v1/workspaces/{workspace_id}/semanticModels/{semantic_model_id}/getDefinition"
        
        # Usar método común para descargar
        return self._download_definition(definition_url, headers, target_folder)
