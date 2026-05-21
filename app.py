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

def obtener_credenciales():
    client_config = {
        "web": {
            "client_id": CLIENT_ID,
            "project_id": "cerebro-maestro-drive",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": CLIENT_SECRET,
            "redirect_uris": ["https://cerebro-master-erp.streamlit.app/"]
        }
    }
    
    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    st.write("### 🔗 Autorización necesaria")
    st.write("Haz clic en el enlace de abajo, inicia sesión y copia el código que te dará Google:")
    st.write(auth_url)
    
    auth_code = st.text_input("Pega aquí el código de autorización que te dio Google:")
    
    if auth_code:
        flow.fetch_token(code=auth_code)
        st.session_state.credentials = flow.credentials
        st.success("¡Autenticación exitosa!")
        st.rerun()

# 3. AUTENTICACIÓN DIRECTA (Sin botones que desaparecen)
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def obtener_credenciales():
    client_config = {
        "web": {
            "client_id": CLIENT_ID,
            "project_id": "cerebro-maestro-drive",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": CLIENT_SECRET,
            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
        }
    }
    
    flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)
    auth_url, _ = flow.authorization_url(prompt='consent')
    
    st.write("### 🔗 Paso 1: Autorización")
    st.markdown(f"[Haz clic aquí para autorizar el acceso a tu Drive]({auth_url})")
    
    auth_code = st.text_input("Paso 2: Pega aquí el código que te dio Google después de autorizar:")
    
    if auth_code:
        flow.fetch_token(code=auth_code)
        st.session_state.credentials = flow.credentials
        st.success("¡Autenticación exitosa! Ya puedes usar el Cerebro Maestro.")
        st.rerun()

# Lógica de inicio
if 'credentials' not in st.session_state:
    obtener_credenciales()
    st.stop() # Esto detiene la app hasta que se autentique
else:
    drive_service = build('drive', 'v3', credentials=st.session_state.credentials)
    # Aquí iría el resto de tu código de chat...

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
