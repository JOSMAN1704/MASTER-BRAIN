import streamlit as st
import google.generativeai as genai
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

# 1. CONFIGURACIÓN DE SEGURIDAD (STREAMLIT SECRETS)
# Recogemos las llaves que guardaste de forma segura en la plataforma
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]

# Configurar el motor de Gemini
genai.configure(api_key=GOOGLE_API_KEY)

st.set_page_config(page_title="Cerebro Maestro ERP", page_icon="🧠", layout="centered")
st.title("🧠 Cerebro Maestro - Proyecto ERP")
st.write("Consulta todo el historial de Fathom e investigaciones de Odoo con IA en tiempo real.")

# 2. AUTENTICACIÓN CON GOOGLE DRIVE VIA OAUTH2
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def autenticar_drive():
    # Creamos la configuración de autenticación sobre la marcha sin archivos JSON físicos
    client_config = {
        "web": {
            "client_id": CLIENT_ID,
            "project_id": "cerebro-maestro-drive",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": CLIENT_SECRET,
            "redirect_uris": ["http://localhost"]
        }
    }
    
    # Esto abrirá una ventana emergente para que firmes con tu cuenta la primera vez
    if 'credentials' not in st.session_state:
        flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
        # Usamos redirección local simulada para entornos web
        flow.redirect_uri = 'https://localhost'
        st.session_state.credentials = flow.run_local_server(port=0, open_browser=False)
    
    return build('drive', 'v3', credentials=st.session_state.credentials)

# 3. FUNCIÓN PARA LEER ARCHIVOS TXT DE LA CARPETA DE DRIVE
def obtener_contexto_drive(service):
    # NOTA: Reemplaza 'ID_DE_TU_CARPETA_AQUÍ' por el ID real de tu carpeta 00_Cerebro_Maestro
    folder_id = '16Qa47qooE2M6W4XrLYM_1-km_SINjxfx?hl=it' 
    query = f"'{folder_id}' in parents and mimeType = 'text/plain'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    
    contexto_completo = ""
    for item in items:
        file_id = item['id']
        request = service.files().get_media(fileId=file_id)
        content = request.execute().decode('utf-8')
        contexto_completo += f"\n\n--- ARCHIVO: {item['name']} ---\n{content}"
    
    return contexto_completo

# --- PUESTA EN MARCHA DEL BOTÓN DE CONEXIÓN ---
if 'drive_service' not in st.session_state:
    if st.button("Conectar con Google Drive"):
        try:
            st.session_state.drive_service = autenticar_drive()
            st.success("Conectado con éxito ✅")
            st.rerun() # Esto recarga la página para mostrar el chat
        except Exception as e:
            st.error(f"Error al conectar: {e}")
    
    drive_service = None
else:
    drive_service = st.session_state.drive_service
# -----------------------------------------------

# 4. INTERFAZ DE CHAT Y PROCESAMIENTO CON GEMINI
if drive_service:
    # Caja de texto para la duda del usuario
    user_question = st.text_input("¿De qué tienes duda hoy? (Ej. ¿Qué pendientes tiene Miguel? o ¿Cómo resuelve Odoo los lotes?)")
    
    if user_question:
        with st.spinner("El Cerebro está consultando tus carpetas y buscando en la Web..."):
            # Traer los datos de tus TXT en tiempo real
            contexto_documentos = obtener_contexto_drive(drive_service)
            
            # Configurar el modelo con Google Search Grounding activado (Búsqueda en Google)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                tools=[{"google_search_grounding": {}}] # <--- ESTO ACTIVA LA BÚSQUEDA WEB EN VIVO
            )
            
            # Construir el prompt estructurado
            prompt_maestro = f"""
            Eres el Cerebro Maestro del proyecto ERP. Tu objetivo es cruzar lo que se habló en las sesiones de Fathom de la empresa con las soluciones del mercado.
            Identifica usuarios (como Miguel Pérez, Roberto, etc.), tareas, acuerdos y diferencias entre modelo estándar y desarrollo técnico.
            
            [CONTEXTO INTERNO DE TUS ARCHIVOS DRIVE]:
            {contexto_documentos}
            
            [PREGUNTA DEL USUARIO]:
            {user_question}
            
            Responde de manera puntual y estructurada. Si la información no está en los archivos de Drive, utiliza tu herramienta de búsqueda web en vivo para complementar cómo lo resuelve Odoo.
            """
            
            response = model.generate_content(prompt_maestro)
            
            # Mostrar la respuesta en la pantalla de la App
            st.markdown("### 🧠 Respuesta de tu Cerebro Maestro:")
            st.write(response.text)
