import streamlit as st
import os
import requests
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# =====================================================================
# 1. VALIDACIÓN Y CONFIGURACIÓN DE LLAVES (APIs)
# =====================================================================
if "GEMINI_API_KEY" not in st.secrets or "TAVILY_API_KEY" not in st.secrets:
    st.error("Por favor, asegúrate de configurar GEMINI_API_KEY y TAVILY_API_KEY en los Secrets de Streamlit.")
    st.stop()

# Configurar Gemini
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
modelo_ia = genai.GenerativeModel(model_name="gemini-2.5-flash")

# Cargar API de Tavily
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]

# =====================================================================
# 2. MOTOR DE BÚSQUEDA WEB INDEPENDIENTE (TAVILY)
# =====================================================================
def buscar_en_web_odoo(consulta):
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": f"Odoo v19 {consulta}",  # Forzamos la búsqueda hacia Odoo v19
        "search_depth": "advanced",
        "max_results": 3
    }
    try:
        response = requests.post(url, json=payload, timeout=10).json()
        resultados = ""
        for resultado in response.get("results", []):
            resultados += f"Fuente: {resultado['url']}\nContenido: {resultado['content']}\n\n"
        return resultados
    except Exception:
        return "No se pudo obtener información adicional de la web en este momento."

# =====================================================================
# 3. PROCESAMIENTO INTELIGENTE DE ARCHIVOS INTERNOS (RAG - FAISS)
# =====================================================================
@st.cache_resource
def obtener_embeddings():
    # Modelo gratuito y ligero para generar los vectores de búsqueda semántica local
    return SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

def buscar_parrafos_clave(pregunta, carpeta="datos_internos"):
    if not os.path.exists(carpeta) or not os.listdir(carpeta):
        return ""
        
    documentos_texto = []
    archivos = os.listdir(carpeta)
    
    # 1. Leer todos los archivos TXT o CSV de la carpeta
    for archivo in archivos:
        if archivo.endswith('.txt') or archivo.endswith('.csv'):
            ruta = os.path.join(carpeta, archivo)
            with open(ruta, 'r', encoding='utf-8') as f:
                documentos_texto.append(f"Archivo: {archivo}\nContenido: " + f.read())
                
    if not documentos_texto:
        return ""
        
    # 2. Fragmentar el texto en pedazos pequeños (Ahorro radical de tokens)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    fragmentos = text_splitter.create_documents(documentos_texto)
    
    # 3. Crear el "Archivero Semántico" temporal en memoria
    embeddings = obtener_embeddings()
    base_conocimiento = FAISS.from_documents(fragmentos, embeddings)
    
    # 4. Extraer ÚNICAMENTE los 3 fragmentos más parecidos a la pregunta del usuario
    resultados_busqueda = base_conocimiento.similarity_search(pregunta, k=3)
    
    contexto_filtrado = ""
    for doc in resultados_busqueda:
        contexto_filtrado += doc.page_content + "\n---\n"
        
    return contexto_filtrado

# =====================================================================
# 4. INTERFAZ DE USUARIO (STREAMLIT)
# =====================================================================
st.set_page_config(page_title="Cerebro Maestro", page_icon="🧠", layout="centered")

st.title("🧠 Cerebro Maestro - Odoo v19 & Fathom")
st.write("Consulta interna optimizada con Inteligencia Artificial y Motores de Búsqueda de alta velocidad.")

pregunta_usuario = st.text_input("¿De qué tienes duda hoy? (Ej. Acuerdos con Miguel o procesos en Odoo v19)")

if pregunta_usuario:
    with st.spinner("Buscando en tus minutas de Fathom e investigando en la web... 🌐"):
        # 1. El filtro inteligente extrae solo los fragmentos relevantes (gasta poquísimos tokens)
        contexto_interno = buscar_parrafos_clave(pregunta_usuario)
        
        # 2. El motor externo busca soluciones sobre Odoo v19 en la web
        contexto_web = buscar_en_web_odoo(pregunta_usuario)
        
        # 3. Construimos el súper prompt optimizado para Gemini
        prompt_maestro = f"""
        Eres el Cerebro Maestro del Proyecto ERP, una IA analítica orientada a apoyar a líderes y desarrolladores.
        Responde la consulta del usuario combinando de manera estructurada las siguientes dos fuentes de información:
        
        1. FRAGMENTOS RELEVANTES DE REUNIONES INTERNAS (Si aplica):
        {contexto_interno if contexto_interno else "No se encontraron menciones directas en las minutas locales."}
        
        2. INVESTIGACIÓN EN LA WEB (Documentación técnica de Odoo v19):
        {contexto_web}
        
        PREGUNTA DEL USUARIO:
        {pregunta_usuario}
        
        REGLA DE REDACCIÓN: 
        Sé directo, muy profesional y enfocado en la toma de decisiones del ERP. Si encontraste datos en las minutas internas, priorízalos detallando a qué archivo corresponden.
        """
        
        # 4. Gemini procesa la información ya filtrada sin saturar la cuota
        try:
            respuesta = modelo_ia.generate_content(prompt_maestro)
            st.write("### 🤖 Respuesta del Cerebro Maestro:")
            st.write(respuesta.text)
        except Exception as e:
            st.error(f"Hubo un error al procesar el resultado con la IA: {e}")
