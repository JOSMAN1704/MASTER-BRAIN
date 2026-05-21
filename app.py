import streamlit as st
import os
import google.generativeai as genai

# =====================================================================
# 1. CONFIGURACIÓN INICIAL DE LA IA (VERSIÓN ESTABLE)
# =====================================================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Falta la configuración de GEMINI_API_KEY en los Secrets de Streamlit.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Usamos el modelo puro de producción, sin herramientas que fuercen la API beta
modelo_ia = genai.GenerativeModel(
    model_name="gemini-1.5-flash"
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
    
  # Nuevas instrucciones limpias para la IA
    prompt_maestro = f"""
    Eres el Cerebro Maestro del Proyecto ERP, una IA experta diseñada para apoyar al equipo de desarrollo y liderazgo.
    
    Tu objetivo es responder de manera analítica, clara y directa la duda del usuario utilizando la siguiente fuente de información interna:
    
    CONTEXTO INTERNO (Minutas de reuniones de Fathom y reportes cargados):
    {contexto_fathom}
    
    PREGUNTA DEL USUARIO:
    {pregunta_usuario}
    
    REGLAS DE RESPUESTA:
    1. Sé muy profesional y enfócate en dar soluciones claras orientadas a la optimización del ERP.
    2. Si la respuesta no se encuentra en el contexto interno, utiliza tu propio conocimiento general y técnico sobre Odoo ERP para guiar al usuario de la mejor manera posible.
    """
    
    # 3. Procesamos con la IA
    with st.spinner("El Cerebro está analizando los archivos e investigando en la web... 🌐"):
        try:
            respuesta = modelo_ia.generate_content(prompt_maestro)
            st.write("### 🤖 Respuesta del Cerebro Maestro:")
            st.write(respuesta.text)
        except Exception as e:
            st.error(f"Hubo un error al procesar la información con Gemini: {e}")
