import os
import dotenv
import logging

# Obtiene la ruta absoluta del directorio donde se encuentra este archivo config.py
# Esto resultará en algo como '.../src/utils'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Navega un nivel arriba para llegar a la raíz de tu paquete principal 'practice'
# CURRENT_DIR = '.../src/utils'
# os.path.dirname(CURRENT_DIR) = '.../src'
PROJECT_ROOT = os.path.dirname(CURRENT_DIR) 

# --- Agregando la lógica de manejo de ambientes ---
# 1. Define la ruta a la carpeta de entornos
ENVIRONMENTS_DIR = os.path.join(PROJECT_ROOT, "environments")

# --- Rutas de Almacenamiento de Evidencias ---

# Directorio base donde se guardarán todas las evidencias.
# Construye la ruta absoluta para que apunte a '.../src/reporting'
EVIDENCE_BASE_DIR = os.path.join(PROJECT_ROOT, "reporting")

# Ruta para videos.
# Se creará '.../src/reporting/video'
VIDEO_DIR = os.path.join(EVIDENCE_BASE_DIR, "video")

# Ruta para traceview.
# Se creará '.../src/reporting/traceview'
TRACEVIEW_DIR = os.path.join(EVIDENCE_BASE_DIR, "traceview")

# Ruta para capturas de pantalla.
# Se creará '.../src/reporting/imagen'
SCREENSHOT_DIR = os.path.join(EVIDENCE_BASE_DIR, "imagen")

# Ruta para logger.
# Se creará '.../src/reporting/log'
LOGGER_DIR = os.path.join(EVIDENCE_BASE_DIR, "log")

# --- Nueva ruta para archivos fuente ---
# Se creará '.../.../src/test/archivos_data_escritura'
SOURCE_FILES_DIR_DATA_WRITE = os.path.join(PROJECT_ROOT, "test", "files", "files_data_write")

# Se creará '.../.../src/test/archivos_data_fuente'
SOURCE_FILES_DIR_DATA_SOURCE = os.path.join(PROJECT_ROOT, "test", "files", "files_data_source")

# Se creará '.../.../src/test/archivos_upload'
SOURCE_FILES_DIR_UPLOAD = os.path.join(PROJECT_ROOT, "test", "files", "files_upload")

# Se creará '.../.../src/test/archivos_download'
SOURCE_FILES_DIR_DOWNLOAD = os.path.join(PROJECT_ROOT, "test", "files", "files_download")

# Función para asegurar que los directorios existan
def ensure_directories_exist():
    """
    Crea los directorios necesarios si no existen.
    """
    # 1. Creamos directorios
    os.makedirs(VIDEO_DIR, exist_ok=True)
    os.makedirs(TRACEVIEW_DIR, exist_ok=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(LOGGER_DIR, exist_ok=True) # Directorio para logs
    os.makedirs(SOURCE_FILES_DIR_DATA_WRITE, exist_ok=True)
    os.makedirs(SOURCE_FILES_DIR_DATA_SOURCE, exist_ok=True)
    os.makedirs(SOURCE_FILES_DIR_UPLOAD, exist_ok=True)
    os.makedirs(SOURCE_FILES_DIR_DOWNLOAD, exist_ok=True)
    
    # 2. Registramos el mensaje de confirmación
    # logging.getLogger() sin nombre trae el logger raíz, que será configurado en conftest.
    logger = logging.getLogger() 
    logger.info("Directorios de evidencia y datos verificados/creados.")
    
def load_settings(env_name=os.getenv("ENVIRONMENT", "qa")):
    """
    Carga el archivo .env del ambiente y devuelve TODA la configuración 
    necesaria en un diccionario.
    """
    # 1. Define y carga el archivo .env
    dotenv_file = os.path.join(ENVIRONMENTS_DIR, f"{env_name}.env")
    
    if os.path.exists(dotenv_file):
        dotenv.load_dotenv(dotenv_file)
    else:
        # Usamos logging.warning en lugar del print original
        logger = logging.getLogger() 
        logger.warning(f"No se encontró el archivo de entorno '{dotenv_file}'. Usando variables de entorno del sistema.")

    # 2. Devolución de la Configuración Centralizada
    # Leemos las variables usando os.getenv, ahora que ya están cargadas
    return {
        # --- Configuración de URLs (Crítico para fixtures) ---
        "ENVIRONMENT": env_name,
        "BASE_URL_UI": os.getenv("BASE_URL"),
        "API_URL": os.getenv("API_URL"),  # URL Crítica para la Fixture de API
        "DASHBOARD_URL": os.getenv("DASHBOARD_URL"),
        "MAKE_URL": os.getenv("MAKE_URL"),
        "POPULAR_URL": os.getenv("POPULAR_URL"),
        "OVERALL_URL": os.getenv("OVERALL_URL"),
        "REGISTRAR_URL": os.getenv("REGISTRAR_URL"),
        
        # --- Configuración de Timeouts/Opciones ---
        "TIMEOUT_IMPLICIT": int(os.getenv("TIMEOUT_IMPLICIT", 5000)),
        "API_TIMEOUT": int(os.getenv("API_TIMEOUT", 15000)),
        
        # --- Rutas de Evidencia ---
        "EVIDENCE_BASE_DIR": EVIDENCE_BASE_DIR,
        "LOGGER_DIR": LOGGER_DIR,
        "VIDEO_DIR": VIDEO_DIR,
        "TRACEVIEW_DIR": TRACEVIEW_DIR,
        "SCREENSHOT_DIR": SCREENSHOT_DIR,
        # Puedes añadir aquí las demás rutas si son necesarias en las pruebas
        
        # --- Rutas de Datos ---
        "DATA_WRITE_DIR": SOURCE_FILES_DIR_DATA_WRITE,
        "DATA_SOURCE_DIR": SOURCE_FILES_DIR_DATA_SOURCE,
        "UPLOAD_DIR": SOURCE_FILES_DIR_UPLOAD,
        "DOWNLOAD_DIR": SOURCE_FILES_DIR_DOWNLOAD,
    }
