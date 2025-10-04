import logging
import os
from datetime import datetime
# SE ELIMINÓ: from .config import LOGGER_DIR # No debe haber ninguna importación a config.py aquí.

def setup_logger(name='playwright_automation', console_level=logging.INFO, file_level=logging.DEBUG, log_dir=None):
    """
    Configura y devuelve una instancia de logger...
    """
    # 1. Obtener o crear una instancia del logger
    logger = logging.getLogger(name)

    # 2. Establecer el nivel mínimo
    logger.setLevel(min(console_level, file_level))

    # 3. Evitar propagación
    logger.propagate = False

    # 4. Limpiar handlers existentes
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    # 5. Definir el formato
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # 6. Configurar el handler para la consola (StreamHandler)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 7. Configurar el handler para el archivo (FileHandler)
    
    # PUNTO CLAVE: Verificamos y usamos el argumento 'log_dir'
    if log_dir is None:
        # Fallback de seguridad, pero config.py siempre debe pasarlo
        log_dir = os.getcwd() 
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file_name = f"automation_log_{timestamp}.log"
    
    # Construcción de la ruta: USA EXCLUSIVAMENTE 'log_dir' pasado como argumento.
    log_file_path = os.path.join(log_dir, log_file_name) 

    # Esto fallará si el directorio 'log_dir' no existe, por eso se crea en config.py antes de llamar a setup_logger
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

"""# --- Ejemplo de uso (opcional, para testing rápido del logger) ---
if __name__ == "__main__":
    from config import ensure_directories_exist
    ensure_directories_exist() 

    print("\n--- Probando Logger con Nivel INFO en Consola y DEBUG en Archivo ---")
    my_logger_1 = setup_logger(name='test_logger_1', console_level=logging.INFO, file_level=logging.DEBUG)
    my_logger_1.debug("DEBUG message - Should be in file, not console.")
    my_logger_1.info("INFO message - Should be in console and file.")
    my_logger_1.warning("WARNING message - Should be in console and file.")
    my_logger_1.error("ERROR message - Should be in console and file.", exc_info=True)
    my_logger_1.critical("CRITICAL message - Should be in console and file.")

    print("\n--- Probando Logger con Nivel WARNING en Consola y INFO en Archivo ---")
    my_logger_2 = setup_logger(name='test_logger_2', console_level=logging.WARNING, file_level=logging.INFO)
    my_logger_2.debug("DEBUG message 2 - Should only be in file (if file_level=DEBUG or lower).") # Won't be in this file.
    my_logger_2.info("INFO message 2 - Should be in file, not console.")
    my_logger_2.warning("WARNING message 2 - Should be in console and file.")
    my_logger_2.error("ERROR message 2 - Should be in console and file.")

    print(f"\nLogs guardados en: {LOGGER_DIR}")"""