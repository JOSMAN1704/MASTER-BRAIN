import streamlit as st
import os
import requests
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings # <--- Ruta oficial actualizada
from langchain_core.documents import Document # <--- Añadimos esto para asegurar compatibilidad
from langchain_text_splitters import RecursiveCharacterTextSplitter

# =====================================================================
# 1. VALIDACIÓN Y CONFIGURACIÓN DE LLAVES (APIs)
# =====================================================================
if "GEMINI_API_KEY" not in st.secrets or "TAVILY_API_KEY" not in st.secrets:
    st.error("Por favor, asegúrate de configurar GEMINI_API_KEY y TAVILY_API_KEY en los Secrets de Streamlit.")
    st.stop()

# Configurar el entorno global de Google Generative AI
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
modelo_ia = genai.GenerativeModel(model_name="gemini-2.5-flash")

# Cargar API de Tavily para el motor web externo
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]

# =====================================================================
# 2. MOTOR DE BÚSQUEDA WEB INDEPENDIENTE (TAVILY)
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
            resultados += f"Fuente Web: {resultado['url']}\nContenido técnico encontrado: {resultado['content']}\n\n"
        return resultados
    except Exception:
        return "No se pudo obtener documentación adicional de la web en este momento."

# =====================================================================
# 3. PROCESAMIENTO ESTELO NOTEBOOK (GOOGLE EMBEDDINGS V004 CORREGIDO)
# =====================================================================
@st.cache_resource
def obtener_embeddings_google():
    # Forzamos a la librería a usar la API Key y el cliente correcto de AI Studio
    return GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=st.secrets["GEMINI_API_KEY"],
        task_type="retrieval_document" # Especifica a Google que es para buscar documentos
    )

def buscar_parrafos_clave_expertos(pregunta, carpeta="datos_internos"):
    if not os.path.exists(carpeta) or not os.listdir(carpeta):
        return ""
        
    documentos_texto = []
    
    try:
        archivos = os.listdir(carpeta)
        for archivo in archivos:
            if archivo.endswith('.txt') or archivo.endswith('.csv'):
                ruta = os.path.join(carpeta, archivo)
                with open(ruta, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                    # Si el archivo está vacío, lo ignoramos para evitar errores en la API
                    if contenido.strip():
                        documentos_texto.append(f"ORIGEN_ARCHIVO: {archivo}\nDATOS_REUNIÓN: " + contenido)
    except Exception as e:
        st.error(f"Error al leer los archivos de la carpeta: {e}")
        return ""
                
    if not documentos_texto:
        return ""
        
    # Segmentación estricta
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    fragmentos = text_splitter.create_documents(documentos_texto)
    
    try:
        embeddings_google = obtener_embeddings_google()
        
        # Generamos la base de conocimiento local
        base_conocimiento = FAISS.from_documents(fragmentos, embeddings_google)
        
        # Extracción de los 4 bloques más alineados
        resultados_busqueda = base_conocimiento.similarity_search(pregunta, k=4)
        
        contexto_filtrado = ""
        for doc in resultados_busqueda:
            contexto_filtrado += doc.page_content + "\n\n-----------------\n\n"
            
        return contexto_filtrado
        
    except Exception as e:
        # Si Google vuelve a rechazarlo, este bloque atrapará el error y te dirá la causa real en la pantalla
        st.warning(f"Aviso técnico: El motor de Embeddings de Google reportó un detalle de conexión: {e}. Procediendo con extracción básica...")
        
        # Plan de respaldo (Fallback): Si falla Google Embeddings por región o cuota, 
        # extraemos los párrafos que contengan palabras clave de la pregunta para no detener la app
        palabras_clave = pregunta.lower().split()
        coincidencias = []
        for frag in fragmentos:
            if any(palabra in frag.page_content.lower() for palabra in palabras_clave if len(palabra) > 3):
                coincidencias.append(frag.page_content)
                if len(coincidencias) >= 4:
                    break
        return "\n\n-----------------\n\n".join(coincidencias)

# =====================================================================
# 4. INTERFAZ DE USUARIO Y CONTROLADOR DE RESPUESTAS (STREAMLIT)
# =====================================================================
st.set_page_config(page_title="Cerebro Maestro", page_icon="🧠", layout="centered")

st.title("🧠 Cerebro Maestro - Odoo v19 & Fathom")
st.write("Entorno analítico corporativo integrado con Google Embeddings y búsqueda semántica avanzada.")

pregunta_usuario = st.text_input("¿Qué deseas auditar o consultar hoy?")

if pregunta_usuario:
    with st.spinner("Ejecutando análisis semántico en minutas y consultando documentación técnica... 🌐"):
        # 1. Extracción con el nuevo motor de embeddings de Google
        contexto_interno = buscar_parrafos_clave_expertos(pregunta_usuario)
        
        # 2. Investigación técnica paralela sobre Odoo v19
        contexto_web = buscar_en_web_odoo(pregunta_usuario)
        
        # 3. Super Prompt de nivel directivo y analítico (Formato Notebook)
        prompt_maestro = f"""
        Eres el Cerebro Maestro del Proyecto ERP, una IA experta y analítica diseñada para apoyar a directores de proyectos y desarrolladores líderes.
        Tu misión es responder la consulta del usuario de manera exhaustiva, rigurosa y altamente técnica, basándote de forma estricta en las siguientes fuentes de verdad compartidas:
        
        FUENTE A: FRAGMENTOS EXTRACTOS DE REUNIONES INTERNAS (Minutas de Fathom):
        {contexto_interno if contexto_interno else "No hay registro directo de este tema en las minutas internas proporcionadas."}
        
        FUENTE B: RECOPILACIÓN TÉCNICA EXTERNA (Buenas prácticas de Odoo v19):
        {contexto_web}
        
        PREGUNTA DEL USUARIO A RESOLVER:
        {pregunta_usuario}
        
        DIRECTRICES DE REDACCIÓN COMPORTAMIENTO NOTEBOOK:
        1. Adopta una postura analítica y basada puramente en datos y acuerdos. Evita conclusiones subjetivas o narrativas emocionales.
        2. Es OBLIGATORIO que cites el origen exacto de la información. Si usas datos de las minutas, añade al final de la oración el tag correspondiente del archivo (ejemplo: '[Fuente: Minuta_X]'). Si la información viene de la investigación técnica, añade '[Fuente: Web Odoo v19]'.
        3. Genera un contraste constructivo: si el usuario pregunta por un proceso, explica lo que se acordó internamente en la reunión frente a lo que dicta la documentación y arquitectura técnica de Odoo v19.
        """
        
        # 4. Ejecución del procesamiento analítico
        try:
            respuesta = modelo_ia.generate_content(prompt_maestro)
            st.write("### 🤖 Dictamen del Cerebro Maestro:")
            st.write(respuesta.text)
        except Exception as e:
            st.error(f"Error crítico en el motor de procesamiento de Google: {e}")
