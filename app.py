import streamlit as st
import os
import google.generativeai as genai

# =====================================================================
# 1. CONFIGURACIÓN INICIAL DE LA IA
# =====================================================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Falta la configuración de GEMINI_API_KEY en los Secrets de Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Usamos la estructura nativa compatible con versiones anteriores y nuevas
modelo_ia = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=[{"google_search_retrieval": {}}] # <--- ESTE es el nombre exacto del componente en el motor de Google
)

# =====================================================================
# 2. FUNCIÓN PARA LEER ARCHIVOS AUTOMÁTICAMENTE
# =====================================================================
def leer_datos_internos():
    carpeta = 'datos_internos'
    
    # Si la carpeta no existe por alguna razón, la creamos vacía
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
        return ""
        
    archivos = os.listdir(carpeta)
    contenido_total = ""
    
    # Escaneamos y leemos cada archivo dentro de la carpeta
    for archivo in archivos:
        if archivo.endswith('.txt') or archivo.endswith('.csv'):
            ruta_completa = os.path.join(carpeta, archivo)
            with open(ruta_completa, 'r', encoding='utf-8') as f:
                contenido_total += f"--- INICIO ARCHIVO: {archivo} ---\n"
                contenido_total += f.read() + "\n"
                contenido_total += f"--- FIN ARCHIVO: {archivo} ---\n\n"
    return contenido_total

# =====================================================================
# 3. INTERFAZ DE USUARIO (STREAMLIT)
# =====================================================================
st.set_page_config(page_title="Cerebro Maestro", page_icon="🧠")

st.title("🧠 Cerebro Maestro - Proyecto ERP")
st.write("Consulta todo el historial de Fathom e investigaciones de Odoo con IA en tiempo real.")

# Cuadro de texto para las dudas
pregunta_usuario = st.text_input("¿De qué tienes duda hoy?...")

if pregunta_usuario:
    # 1. La app escanea la carpeta en este instante
    contexto_fathom = leer_datos_internos()
    
    if not contexto_fathom:
        st.warning("⚠️ Nota: No se encontraron archivos en la carpeta 'datos_internos'. La IA responderá usando solo su conocimiento y búsqueda web.")
    
    # 2. Creamos las instrucciones para Gemini
    prompt_maestro = f"""
    Eres el Cerebro Maestro del Proyecto ERP, una IA experta diseñada para apoyar al equipo de desarrollo y liderazgo.
    
    Tu objetivo es responder de manera analítica, clara y directa la duda del usuario utilizando las siguientes fuentes:
    
    1. CONTEXTO INTERNO (Minutas de reuniones de Fathom y reportes cargados):
    {contexto_fathom}
    
    2. BÚSQUEDA WEB EN TIEMPO REAL:
    Si la duda del usuario requiere detalles técnicos actualizados sobre Odoo ERP, configuraciones estándar, módulos o buenas prácticas que NO estén en el contexto interno, utiliza obligatoriamente tu herramienta de búsqueda en Google.
    
    PREGUNTA DEL USUARIO:
    {pregunta_usuario}
    
    Se muy profesional y enfócate en dar soluciones claras orientadas a la optimización del ERP.
    """
    
    # 3. Procesamos con la IA
    with st.spinner("El Cerebro está analizando los archivos e investigando en la web... 🌐"):
        try:
            respuesta = modelo_ia.generate_content(prompt_maestro)
            st.write("### 🤖 Respuesta del Cerebro Maestro:")
            st.write(respuesta.text)
        except Exception as e:
            st.error(f"Hubo un error al procesar la información con Gemini: {e}")
