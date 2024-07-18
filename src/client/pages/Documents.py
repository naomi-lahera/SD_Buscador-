import streamlit as st
from Search import Client

try:
    client: Client = st.session_state.client
except:
    client = Client()
    st.session_state.client = client

# Lista de textos de ejemplo
# textos = ["Texto 1", "Texto 2", "Texto 3"]
texts = client.get_docs()

# Función para mostrar cada texto con opciones de eliminar y actualizar
def mostrar_textos_con_opciones(textos):
    if not textos:
        st.warning('We have problems')
        return
    
    for i, texto in enumerate(textos):
        st.write(f"Texto {i+1}: {texto}")
        
        # Botón para eliminar el texto
        col1, col2 = st.columns([4, 1])
        with col1:
            # Entrada para actualizar el texto
            nuevo_texto = st.text_input(f"Actualizar Texto {i+1}:", value=texto, key=f"texto_{i}")
            
            # Actualizar el texto si se ha modificado
            if st.button(f"Actualizar Texto {i+1}", key=f"actualizar_{i}"):
                client.update(i, nuevo_texto)
                # textos[i] = nuevo_texto
        
        with col2:
            # Botón para eliminar el texto
            if st.button("Eliminar", key=f"eliminar_{i}"):
                client.delete(i)
                # del textos[i]
                # st.experimental_rerun()

# Mostrar los textos con opciones
mostrar_textos_con_opciones(texts)

# Opción para agregar un nuevo texto
nuevo_texto = st.text_input("Agregar nuevo texto:", value="")
if st.button("Agregar Texto"):
    # textos.append(nuevo_texto)
    # st.experimental_rerun()
    client.insert_to_leader(nuevo_texto)