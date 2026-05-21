import streamlit as st
import os
import requests
import google.generativeai as genai

# =====================================================================
# 1. VALIDACIÓN DE LLAVES DE ACCESO (SECRETS)
# =====================================================================
if "GEMINI_API_KEY" not in st.secrets or "TAVILY_API_KEY" not in st.secrets:
    st.error("Falta configurar GEMINI_API_KEY o TAVILY_API_KEY en los Secrets de Streamlit.")
    st.stop()

# Configuración oficial de los motores de Google e Internet
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
modelo_ia = genai.GenerativeModel(model_name="gemini-2.5-flash")
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]

# =====================================================================
# 2. MOTOR DE BÚSQUEDA WEB (TAVILY)
# =====================================================================
def buscar_en_web_odoo(consulta):
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": f"Odoo v19 {consulta}",  # Forzamos la especialización en Odoo v19
        "search_depth": "advanced",
        "max_results": 3
    }
    try:
        response = requests.post(url, json=payload, timeout=10).json()
        resultados = ""
        for resultado in response.get("results", []):
            resultados += f"Fuente Web: {resultado['url']}\nContenido: {resultado['content']}\n\n"
        return resultados
    except Exception:
        return "No se pudo obtener documentación adicional de internet en este momento."

# =====================================================================
# 3. LECTURA DE REPOSITORIOS CONSOLIDADOS
# =====================================================================
def cargar_repositorios_internos(carpeta="datos_internos"):
    contexto_total = ""
    archivos_objetivo = ["Sesiones_Con_Fathom.txt", "Sesiones_Sin_Fathom.txt"]
    
    for nombre_archivo in archivos_objetivo:
        ruta = os.path.join(carpeta, nombre_archivo)
        if os.path.exists(ruta):
            with open(ruta, 'r', encoding='utf-8') as f:
                contexto_total += f"\n\n--- INICIO ARCHIVO DE ORIGEN: {nombre_archivo} ---\n"
                contexto_total += f.read()
                contexto_total += f"\n--- FIN ARCHIVO DE ORIGEN: {nombre_archivo} ---\n"
        else:
            contexto_total += f"\n[Aviso: El archivo {nombre_archivo} no se encontró en la carpeta interna]\n"
            
    return contexto_total

# =====================================================================
# 4. INTERFAZ DE USUARIO (STREAMLIT)
# =====================================================================
st.set_page_config(page_title="Cerebro Maestro", page_icon="🧠", layout="centered")

st.title("🧠 Cerebro Maestro - Odoo v19 & Fathom")
st.write("Entorno analítico de alta precisión. Respuestas cruzadas basadas en minutas internas e investigación web.")

pregunta_usuario = st.text_input("¿Qué deseas auditar o consultar hoy?")

if pregunta_usuario:
    with st.spinner("Analizando repositorios consolidados y consultando documentación técnica... 🌐"):
        
        # 1. Cargamos el texto íntegro de tus dos archivos maestros (Indestructible, sin errores de embeddings)
        base_conocimiento_interna = cargar_repositorios_internos()
        
        # 2. Buscamos en tiempo real las respuestas en internet sobre Odoo v19
        contexto_web_externo = buscar_en_web_odoo(pregunta_usuario)
        
        # 3. SUPER PROMPT ESTILO NOTEBOOK LM
        prompt_maestro = f"""
        Eres el Cerebro Maestro del Proyecto ERP, una IA experta, analítica y de nivel auditor diseñada para apoyar a directores de proyectos y desarrolladores líderes.
        Tu objetivo es resolver la consulta del usuario de manera exhaustiva, rigurosa y altamente técnica, contrastando los acuerdos de las reuniones con la documentación de Odoo v19.
        
        CONTRATO DE FUENTES INTERNAS (Tus archivos consolidados):
        \"\"\"
        {base_conocimiento_interna}
        \"\"\"
        
        DOCUMENTACIÓN TÉCNICA EXTRAÍDA DE INTERNET (Odoo v19):
        \"\"\"
        {contexto_web_externo}
        \"\"\"
        
        PREGUNTA DEL USUARIO A RESOLVER:
        {pregunta_usuario}
        
        INSTRUCCIONES ESTRICTAS DE COMPORTAMIENTO (ESTILO NOTEBOOK LM):
        1. Analiza minuciosamente el bloque de 'FUENTES INTERNAS'. Busca las sesiones delimitadas por '[INICIO_SESION]' que mencionen el tema consultado.
        2. Al redactar la respuesta, es OBLIGATORIO que cites de dónde provino cada afirmación utilizando el nombre del archivo origen entre corchetes al final de la frase (Ejemplos: '[Fuente: Sesiones_Con_Fathom.txt]' o '[Fuente: Sesiones_Sin_Fathom.txt]').
        3. Si la respuesta incluye enlaces de Fathom en el bloque analizado, muéstralos explícitamente para que el usuario pueda hacer clic e ir a la sesión.
        4. Si utilizas los datos de internet para complementar la duda sobre Odoo v19, coloca el tag '[Fuente: Web Odoo v19]'.
        5. Estructura la información con títulos limpios, listas de viñetas para acuerdos/pendientes y mantén un tono puramente corporativo, técnico y enfocado a datos, sin opiniones subjetivas.
        """
        
        # 4. Procesamiento directo con Gemini 2.5 Flash
        try:
            respuesta = modelo_ia.generate_content(prompt_maestro)
            st.write("### 🤖 Dictamen del Cerebro Maestro:")
            st.write(respuesta.text)
        except Exception as e:
            st.error(f"Error crítico en el motor de procesamiento: {e}")
