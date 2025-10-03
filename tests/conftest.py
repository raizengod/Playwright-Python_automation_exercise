# nombra el archivo: Ve a la ubicación de tu archivo y colcoar el nombre a conftest.py
# La convención de conftest.py le indica a Pytest que este archivo contiene fixtures que deben estar disponibles 
# para los tests en ese directorio y sus subdirectorios.
import pytest
import time
from playwright.sync_api import Page, expect, Playwright, sync_playwright, APIRequestContext
from datetime import datetime
import os
from typing import Generator
import logging
from src.utils.config import load_settings, ensure_directories_exist
from src.utils.logger import setup_logger
from src.pages.base_page import BasePage
from src.locators.locator_obstaculoPantalla import ObstaculosLocators

# 1. Aseguramos que los directorios existan (incluyendo 'log')
ensure_directories_exist() 

# 2. Configuramos el logger con el nombre definido en logger.py
# El nombre es 'playwright_automation' por defecto en logger.py
ROOT_LOGGER = setup_logger(name='playwright_automation',
                           console_level=logging.INFO, 
                           file_level=logging.DEBUG)
ROOT_LOGGER.info("Logger y directorios inicializados para la sesión de pruebas.")

# Función para generar IDs legibles
def generar_ids_browser(param):
    """
    Genera un ID descriptivo para cada combinación de navegador y dispositivo.
    """
    browser = param['browser']
    device = param['device']
    resolution = param['resolution']

    if device:
        return f"{browser}-{device}"
    else:
        return f"{browser}-{resolution['width']}x{resolution['height']}"

# --- Fixture de Configuración Centralizada ---
@pytest.fixture(scope="session")
def config_data():
    """Carga y proporciona el diccionario de configuración de ambiente."""
    ROOT_LOGGER.info("Cargando variables de entorno mediante load_settings().")
    return load_settings() 

# --- Fixture de API Context ---
@pytest.fixture(scope="session")
def api_context(config_data) -> Generator[APIRequestContext, None, None]:
    """Inicializa y configura el APIRequestContext de Playwright."""
    
    base_api_url = config_data.get("API_URL")
    api_timeout = config_data.get("API_TIMEOUT")
    
    if not base_api_url:
        ROOT_LOGGER.critical("La variable 'API_URL' no está definida en la configuración.")
        raise ValueError("API_URL no está configurada para el APIRequestContext.")

    ROOT_LOGGER.info(f"Inicializando API Context para URL: {base_api_url}")
    
    playwright = sync_playwright().start()

    context = playwright.request.new_context(
        base_url=base_api_url,
        timeout=api_timeout
    )

    yield context
    
    ROOT_LOGGER.info("Cerrando/disponiendo del API Context.")
    context.dispose()
    playwright.stop()
    
@pytest.fixture(
    scope="function",
    params=[
            # Resoluciones de escritorio
            #{"browser": "chromium", "resolution": {"width": 1920, "height": 1080}, "device": None},
            #{"browser": "firefox", "resolution": {"width": 1920, "height": 1080}, "device": None},
            {"browser": "webkit", "resolution": {"width": 1920, "height": 1080}, "device": None},
            # Emulación de dispositivos móviles
            #{"browser": "chromium", "device": "iPhone 12", "resolution": None},
            {"browser": "webkit", "device": "Pixel 5", "resolution": None},
            {"browser": "webkit", "device": "iPhone 12", "resolution": None}
    ],
    ids=generar_ids_browser # <--- Usar la función para generar IDs
)
def playwright_page(playwright: Playwright, request, config_data: dict) -> Generator[Page, None, None]:
    """
    Fixture principal (scope="function") para inicializar y configurar los recursos de automatización de Playwright.

    Esta fixture:
    1. Lanza el navegador (Chromium, Firefox o Webkit) en modo no-headless.
    2. Crea un contexto de navegación, aplicando emulación de dispositivo o configuración de viewport/resolución.
    3. Configura la grabación de video y el rastreo (tracing) para recopilar evidencia.
    4. Proporciona la instancia 'Page' al test que la solicita (yield).
    5. Garantiza la limpieza (cierre de navegador/contexto) y el manejo de excepciones en caso de fallo.
    6. Renombra y guarda el archivo de video y el archivo de rastreo con nombres descriptivos (incluyendo el nombre del test).

    Args:
        playwright (Playwright): Instancia inyectada de Playwright proporcionada por pytest-playwright.
        request (pytest.FixtureRequest): Objeto de solicitud de Pytest, utilizado para acceder a los parámetros
                                         de la prueba y el nombre del nodo (request.node.name).
        config_data (dict): Diccionario de configuración inyectado por el fixture 'config_data'.

    Yields:
        Generator[Page, None, None]: Una instancia de la página de Playwright ('page') lista para ser utilizada en el test.
    """
    # -------------------
    # 1. Preparación inicial
    # -------------------
    param = request.param
    browser_type = param["browser"]
    resolution = param["resolution"]
    device_name = param["device"]

    browser_instance = None
    context = None
    page = None

    try:
        # -------------------
        # 2. Lanzamiento del Navegador
        # -------------------
        ROOT_LOGGER.info(f"Intentando lanzar el navegador: {browser_type}")
        
        # Lanza el tipo de navegador especificado con slow_mo (para visibilidad)
        if browser_type == "chromium":
            browser_instance = playwright.chromium.launch(headless=False, slow_mo=500)
        elif browser_type == "firefox":
            browser_instance = playwright.firefox.launch(headless=False, slow_mo=500)
        elif browser_type == "webkit":
            browser_instance = playwright.webkit.launch(headless=False, slow_mo=500)
        else:
            # Manejo explícito de un tipo de navegador no compatible (falla el setup)
            error_msg = f"El tipo de navegador '{browser_type}' no es compatible o no está definido."
            ROOT_LOGGER.error(f"❌ ERROR de configuración en fixture playwright_page: {error_msg}")
            raise ValueError(error_msg)
            
        ROOT_LOGGER.info(f"Navegador {browser_type} iniciado correctamente.")

        # -------------------
        # 3. Configuración y Creación del Contexto (Video y Viewport/Emulación)
        # -------------------
        context_options = {
            "record_video_dir": config_data['VIDEO_DIR'],
            # Se usa una resolución estándar para el video, que puede ser sobreescrita por la emulación de dispositivo
            "record_video_size": {"width": 1920, "height": 1080} 
        }

        if device_name:
            # Aplica emulación de dispositivo (e.g., iPhone 12)
            device = playwright.devices[device_name]
            context = browser_instance.new_context(**device, **context_options)
            ROOT_LOGGER.info(f"Contexto creado con emulación de dispositivo: {device_name}.")
        elif resolution:
            # Aplica configuración de resolución de escritorio
            context = browser_instance.new_context(viewport=resolution, **context_options)
            ROOT_LOGGER.info(f"Contexto creado con resolución: {resolution['width']}x{resolution['height']}.")
        else:
            # Contexto por defecto, solo con opciones de video
            context = browser_instance.new_context(**context_options)
            ROOT_LOGGER.info("Contexto creado con opciones de video por defecto.")

        # 4. Creación de la página (El objeto de interacción primario)
        page = context.new_page()
        ROOT_LOGGER.info("Página inicial creada.")

        # -------------------
        # 5. Configuración de Tracing
        # -------------------
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        trace_name_suffix = ""
        # Lógica para construir un sufijo descriptivo
        if device_name:
            trace_name_suffix = device_name.replace(" ", "_").replace("(", "").replace(")", "")
        elif resolution:
            trace_name_suffix = f"{resolution['width']}x{resolution['height']}"

        # Obtener el nombre base del test (excluyendo el parámetro '[browser-device]')
        test_name = request.node.name.split('[')[0] 
        trace_file_name = f"traceview_{current_time}_{browser_type}_{trace_name_suffix}_{test_name}.zip"
        trace_path = os.path.join(config_data['TRACEVIEW_DIR'], trace_file_name)

        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        ROOT_LOGGER.info(f"Inicio de Tracing. Archivo: {trace_file_name}")

        # La prueba se ejecuta aquí
        yield page
        
    except Exception as e:
        # -------------------
        # 6. Manejo de Excepciones Críticas (Fase de Setup)
        # -------------------
        # Captura cualquier error de Playwright o configuración durante el setup.
        ROOT_LOGGER.critical(
            f"❌ FALLO CRÍTICO en la inicialización de Playwright. Error: {e.__class__.__name__} - {e}", 
            exc_info=True
        )
        raise # Re-lanza la excepción para garantizar que Pytest falle la prueba inmediatamente.

    finally:
        # -------------------
        # 7. Fase de Limpieza (Teardown)
        # -------------------
        ROOT_LOGGER.info("Iniciando fase de limpieza (Teardown) de Playwright.")
        
        # Detener Tracing y cerrar Contexto
        if context:
            try:
                ROOT_LOGGER.info(f"Deteniendo tracing y guardando en: {trace_path}")
                context.tracing.stop(path=trace_path)
                context.close()
                ROOT_LOGGER.info("Contexto de Playwright cerrado.")
            except Exception as e:
                ROOT_LOGGER.error(f"❌ Error al detener el tracing o cerrar el contexto: {e}", exc_info=True)
                
        # Cerrar Instancia del Navegador
        if browser_instance:
            try:
                browser_instance.close()
                ROOT_LOGGER.info("Instancia del navegador cerrada.")
            except Exception as e:
                ROOT_LOGGER.error(f"❌ Error al cerrar la instancia del navegador: {e}", exc_info=True)
        
        # Renombrar Archivo de Video (si existe)
        if page and page.video:
            try:
                video_path = page.video.path()
                # Mejorar el nombre del video con el timestamp y el nombre del test
                new_video_name = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}_{request.node.name}.webm" 
                new_video_path = os.path.join(config_data['VIDEO_DIR'], new_video_name)
                
                os.rename(video_path, new_video_path)
                ROOT_LOGGER.info(f"✅ Video guardado correctamente como: {new_video_path}")
            except Exception as e:
                # El error al renombrar el video no interrumpe el teardown, solo se registra.
                ROOT_LOGGER.error(f"❌ Error al renombrar el archivo de video. Detalles: {e}", exc_info=True)
                
# --- Fixture principal de la arquitectura ---
@pytest.fixture(scope="function")
def base_page(playwright_page: Page, config_data: dict) -> Generator[BasePage, None, None]: # <- Añadir config_data
    """
    Fixture que proporciona una instancia inicializada de BasePage
    con la página de Playwright, lista para ser usada por los tests.
    """
    
    # 1. Inicializa BasePage, inyectando Page, config_data y el logger
    base_page_instance = BasePage(
        page=playwright_page, 
        config_data=config_data, 
        logger=ROOT_LOGGER # Inyecta la instancia del logger
    ) 
    
    # 2. Usa el logger para informar
    ROOT_LOGGER.info("Instancia de BasePage creada y lista para la prueba.")
    
    yield base_page_instance
    
    # 3. Teardown
    ROOT_LOGGER.info("Finalizando la instancia de BasePage.")

# --- Ejemplo de nuevos fixtures de pre-condición ---
@pytest.fixture
def set_up_Home(base_page: BasePage, config_data: dict) -> BasePage:
    """
    Fixture de pre-condición para las pruebas en la página de inicio.
    
    Este fixture garantiza que la página esté en un estado conocido y limpio
    antes de que cada test de la página de inicio comience. Realiza las siguientes acciones:
    
    1. Navega a la URL base de la aplicación.
    2. Valida que la URL actual coincida con la URL base esperada.
    3. Cierra cualquier obstáculo o popup (como banners de cookies o anuncios) que
       puedan interferir con la ejecución del test.
    4. Valida que el título de la página sea el correcto.

    Args:
        base_page (BasePage): Una instancia de la clase BasePage, que se espera
                              sea proporcionada por otro fixture de nivel superior
                              (como el fixture `page` de Playwright).

    Returns:
        BasePage: La instancia de BasePage ya inicializada y configurada, lista para
                  ser utilizada por el test para realizar las validaciones o acciones.
    """
    # 1. Navega a la URL base y toma una captura de pantalla inicial.
    base_page.navigation.ir_a_url(config_data['BASE_URL_UI'], "inicio_test", config_data['SCREENSHOT_DIR'])
    
    # 2. Valida que la URL actual sea la de la página de inicio.
    base_page.navigation.validar_url_actual(config_data['BASE_URL_UI'])
    
    # 3. Intenta cerrar cualquier obstáculo que pueda aparecer.
    #    Esto asegura que los elementos principales de la página no estén cubiertos.
    base_page.element.manejar_obstaculos_en_pagina(ObstaculosLocators.LISTA_DE_OBSTACULOS)
    
    # 4. Valida que el título de la web sea el esperado, confirmando que la página cargó correctamente.
    base_page.navigation.validar_titulo_de_web("Buggy Cars Rating", "validar_titulo_de_web", config_data['SCREENSHOT_DIR'])
    
    # Retorna la instancia de BasePage para que el test pueda comenzar sus acciones.
    return base_page

@pytest.fixture
def set_up_Registrar(base_page: BasePage, config_data: dict):
    """
    Fixture que prepara el entorno de la prueba para escenarios de registro.
    
    Este fixture realiza los siguientes pasos de pre-condición:
    1. Navega a la URL base de la aplicación.
    2. Hace clic en el botón 'Register' para ir a la página de registro.
    3. Valida que la URL actual sea la esperada para la página de registro.
    4. Maneja cualquier obstáculo o popup que pueda aparecer en la página.
    5. Valida que el título de la página sea el correcto.

    Args:
        base_page (BasePage): Una instancia de la clase BasePage proporcionada por
                              un fixture de nivel superior (precondición necesaria).

    Returns:
        BasePage: La instancia de BasePage ya inicializada y lista para interactuar
                  con la página de registro.
    """
    # 1. Navega a la URL base de la aplicación.
    base_page.navigation.ir_a_url(config_data['BASE_URL_UI'], "Inicio_test_registro", config_data['SCREENSHOT_DIR'])
    
    # 2. Hace clic en el botón 'Register' para ir a la página de registro.
    #    Se utiliza el localizador desde la instancia de HomeLocatorsPage.
    base_page.element.hacer_clic_en_elemento(base_page.home.botonRegistrarse, "Clic_botonRegistrarse", config_data['SCREENSHOT_DIR'])
    
    # 3. Valida que la URL actual sea la de la página de registro.
    base_page.navigation.validar_url_actual(config_data['REGISTRAR_URL'])
    
    # 4. Maneja cualquier obstáculo en la página (popups, banners, etc.).
    base_page.element.manejar_obstaculos_en_pagina(ObstaculosLocators.LISTA_DE_OBSTACULOS)
    
    # 5. Valida que el título de la página sea el correcto para asegurar que la navegación fue exitosa.
    base_page.navigation.validar_titulo_de_web("Buggy Cars Rating", "validar_titulo_de_web_registro", config_data['SCREENSHOT_DIR'])
    
    # Retorna la instancia de BasePage para que los tests puedan utilizarla.
    return base_page