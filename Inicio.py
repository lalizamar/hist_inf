import os
import streamlit as st
import base64
from openai import OpenAI
import openai
from PIL import Image
import numpy as np
from streamlit_drawable_canvas import st_canvas
from io import BytesIO

# --- 0. Inicialización de Estado de Sesión ---
if 'story_thread' not in st.session_state:
    st.session_state.story_thread = ""
if 'api_key_valid' not in st.session_state:
    st.session_state.api_key_valid = False
if 'drawing_analyzed' not in st.session_state:
    st.session_state.drawing_analyzed = False
if 'base64_image' not in st.session_state:
    st.session_state.base64_image = ""

# --- 1. CSS para la Estética "Etérea/Mística" ---
def inject_dream_weaver_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Spectral:wght@400;700&family=Pacifico&display=swap');
            
            /* Colores Base: Sueños de Lavanda */
            :root {
                --color-text-dark: #3A015E;  /* Violeta Profundo */
                --color-background: #F0F8FF; /* Azul Claro Etéreo */
                --color-primary: #D7A9E3;    /* Lavanda Mística */
                --color-accent: #FFEB3B;     /* Dorado de Hadas */
                --color-shadow: rgba(58, 1, 94, 0.4);
            }

            /* Fondo General (Gradiante de Sueño) */
            .stApp {
                background: linear-gradient(135deg, var(--color-background) 0%, var(--color-primary) 100%);
                color: var(--color-text-dark);
                font-family: 'Spectral', serif; 
            }
            
            /* Títulos y Encabezados (Estilo Mágico) */
            h1, h2, h3, h4 {
                font-family: 'Pacifico', cursive; /* Fuente Cursiva Whimsical */
                color: var(--color-text-dark);
                text-shadow: 2px 2px 5px var(--color-primary);
                text-align: center;
            }
            
            /* Input de API Key (Caja de Secretos) */
            .stTextInput label {
                font-family: 'Spectral', serif;
                color: var(--color-text-dark);
            }

            /* Botones (Gema Brillante) */
            .stButton > button {
                background-color: var(--color-accent);
                color: var(--color-text-dark);
                border: 2px solid var(--color-text-dark);
                border-radius: 15px;
                padding: 10px 20px;
                box-shadow: 0 4px 10px var(--color-shadow), 0 0 15px var(--color-accent);
                transition: all 0.3s;
                font-family: 'Spectral', serif;
                font-weight: bold;
            }
            .stButton > button:hover {
                background-color: #FFC107;
                transform: scale(1.05);
            }

            /* Contenedor de Historia (Papiro Iluminado) */
            .stMarkdown, .stAlert, .stInfo {
                border-radius: 15px;
                border: 3px solid var(--color-primary);
                background-color: #FFFFFFD0; /* Blanco semi-transparente */
                padding: 20px;
                box-shadow: 0 5px 15px var(--color-shadow);
            }
            
            /* Barra lateral (Portal de Sueños) */
            .css-1d3s3aw, .st-emotion-cache-1d3s3aw { 
                background-color: var(--color-primary); 
                border-right: 5px dashed var(--color-text-dark);
            }

            /* Estilo del Canvas (El Telar) */
            .main .block-container .st-emotion-cache-1ft911z, 
            .main .block-container .st-emotion-cache-1cpxdwv {
                border: 5px solid var(--color-text-dark); 
                box-shadow: 0 8px 15px var(--color-shadow);
                padding: 0;
                border-radius: 20px; 
            }
        </style>
    """, unsafe_allow_html=True)

# --- 2. Funciones de Ayuda ---

def image_to_base64(image):
    """Convierte un objeto PIL Image a una cadena Base64 (formato PNG)."""
    buffered = BytesIO()
    image.save(buffered, format="PNG") 
    encoded_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return encoded_image

def call_openai_vision(client, base64_image):
    """Llama a la API de OpenAI Vision para describir la imagen."""
    vision_prompt = "Describe el objeto principal o la escena dibujada en este boceto. Limítate solo a describir lo que es, por ejemplo: 'un dragón volando' o 'un árbol con una puerta'."
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": vision_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}",
                    },
                },
            ],
        }
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=100,
    )
    return response.choices[0].message.content if response.choices else "un misterio indescifrable"

def call_openai_story_weaver(client, story_thread, new_element_description):
    """Llama a la API de OpenAI para tejer la historia."""
    if not story_thread:
        # Primer fragmento
        story_prompt = f"Comienza una historia de fantasía breve y atractiva. El elemento central del primer capítulo debe ser: '{new_element_description}'. Termina el capítulo con un gancho que invite a un nuevo elemento."
    else:
        # Fragmentos subsiguientes
        story_prompt = f"Continuemos la historia. El capítulo anterior terminó así: '{story_thread}'. El nuevo elemento introducido en el telar es: '{new_element_description}'. Escribe el siguiente capítulo de la historia, integrando este nuevo elemento y terminando con un gancho para un nuevo dibujo."

    messages = [{"role": "user", "content": story_prompt}]
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=500,
    )
    return response.choices[0].message.content if response.choices else "El Telar se ha enredado, intenta de nuevo."

# --- 3. Configuración de Streamlit y UI ---
st.set_page_config(page_title='El Telar del Tejedor de Sueños', page_icon='✨')
inject_dream_weaver_css() 
st.title('✨ El Telar del Tejedor de Sueños 🧶')

with st.sidebar:
    st.subheader("📚 Guía del Tejedor:")
    st.markdown("""
        **1. 🗝️ Llave:** Ingresa tu clave de OpenAI.
        **2. ✍️ Dibuja:** Traza un objeto, criatura o lugar en el Telar.
        **3. 📜 Teje:** Presiona 'Analizar Hilo' para que el Oráculo revele el sueño.
        **4. 🔁 Continúa:** Presiona 'Tejer el Siguiente Hilo' para que el Telar cree el siguiente capítulo de la historia.
    """)
    st.divider()
    # Control de ancho de trazo en el sidebar
    stroke_width = st.slider('Grosor de la Tinta de Sueños', 1, 30, 5) 

# --- Panel de API Key ---
ke = st.text_input('🔑 Llave del Telar (OpenAI API Key)')
os.environ['OPENAI_API_KEY'] = ke
api_key = os.environ['OPENAI_API_KEY']
client = OpenAI(api_key=api_key)

# --- Contenedor de la Historia ---
st.subheader("📖 El Hilo de la Historia")
if st.session_state.story_thread:
    st.markdown(st.session_state.story_thread)
else:
    st.info("La historia está esperando ser tejida. ¡Dibuja tu primer elemento!")

st.divider()

# --- Canvas de Dibujo (El Telar) ---
st.subheader("✍️ Dibuja el Siguiente Elemento en el Telar")

drawing_mode = "freedraw"
stroke_color = "#3A015E"  # Tinta Violeta
bg_color = '#FFFFFF' 

canvas_result = st_canvas(
    fill_color="rgba(255, 165, 0, 0.0)", 
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    height=300,
    width=400,
    drawing_mode=drawing_mode,
    key="canvas",
)

# --- Botón para analizar el dibujo (Siempre visible) ---
analyze_button = st.button("🔮 Analizar Hilo de Sueño", type="primary")

# --- Lógica de Llamada a la API ---
if analyze_button:
    if not api_key:
        st.error("Por favor, ingresa la Llave del Telar (API key) antes de analizar el sueño.")
    elif canvas_result.image_data is None:
        st.warning("Por favor, dibuja tu elemento en el Telar.")
    else:
        # Verificar dibujo
        input_numpy_array = np.array(canvas_result.image_data)
        non_transparent_pixels = (input_numpy_array[:, :, 3] > 0).sum()
        
        if non_transparent_pixels < 50:
            st.warning("El hilo del sueño es muy débil. Dibuja algo más claro.")
            
        else:
            with st.spinner("⏳ El Oráculo de la Visión está revelando el objeto..."):
                
                # 1. Preparar la imagen
                input_image = Image.fromarray(input_numpy_array.astype('uint8'), 'RGBA')
                base64_image = image_to_base64(input_image)
                st.session_state.base64_image = base64_image

                # 2. Llamar a la Visión para describir
                try:
                    element_description = call_openai_vision(client, base64_image)
                    st.session_state.drawing_analyzed = True
                    st.info(f"✨ El Oráculo revela: '{element_description}'")
                    st.session_state.current_element_description = element_description
                except openai.APIError as e:
                    st.error(f"Error en el Oráculo (API de OpenAI): {e.status_code}. Por favor, verifica tu clave.")
                except Exception as e:
                    st.error(f"Ocurrió un error inesperado: {e}")

# --- Botón para tejer la historia (Visible después del análisis) ---
if st.session_state.drawing_analyzed and st.session_state.current_element_description:
    
    # Este botón solo llama a la generación de texto
    if st.button("🪄 Tejer el Siguiente Hilo (Crear Capítulo)", type="secondary"):
        
        # Usamos la descripción guardada en el estado de sesión
        element_description = st.session_state.current_element_description
        
        with st.spinner("🌌 Tejiendo la narrativa mágica..."):
            
            # 3. Llamar al Tejedor de Historias
            try:
                new_chapter = call_openai_story_weaver(client, st.session_state.story_thread, element_description)
                
                # 4. Actualizar el Hilo de la Historia
                # Agregar el nuevo capítulo, separado por un título de capítulo
                chapter_number = st.session_state.story_thread.count('### Capítulo') + 1
                new_story_thread = st.session_state.story_thread
                
                if new_story_thread:
                    new_story_thread += "\n\n---\n\n"
                
                new_story_thread += f"### Capítulo {chapter_number}: El Elemento de la {element_description.capitalize().split()[0]}"
                new_story_thread += "\n\n" + new_chapter
                
                st.session_state.story_thread = new_story_thread
                st.session_state.drawing_analyzed = False # Resetear para forzar un nuevo dibujo
                st.session_state.current_element_description = ""
                st.rerun() # Forzar la actualización para mostrar la nueva historia
                
            except openai.APIError as e:
                st.error(f"Error en el Telar de Historias (API de OpenAI): {e.status_code}. Por favor, verifica tu clave.")
            except Exception as e:
                st.error(f"Ocurrió un error inesperado: {e}")
