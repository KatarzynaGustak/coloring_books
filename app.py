
#importy bibliotek
import streamlit as st
from dotenv import dotenv_values
from openai import OpenAI
import instructor
from pydantic import BaseModel
import requests
from typing import List, Optional
import io
import os


#łączenie z kluczem OpenAi API 
env = dotenv_values(".env")

def get_openai_clients():
    return OpenAI(api_key=st.session_state["openai_api_key"])

# OpenAI API key protection
if not st.session_state.get("openai_api_key"):
    if "OPENAI_API_KEY" in env: 
        st.session_state["openai_api_key"] = env["OPENAI_API_KEY"]
    else: 
        st.info("Dodaj swój klucz API OpenAI aby móc korzystać z tej aplikacji") 
        st.session_state["openai_api_key"] = st.text_input("Klucz API", type="password")        
        if st.session_state["openai_api_key"]: 
            st.rerun()
if not st.session_state.get("openai_api_key"):
    st.stop()

#połaczenie z instruktorem
instructor_openai_client = instructor.from_openai(get_openai_clients()) 

#zapisywanie wygenerowanej kolorowanki
if "generated_images" not in st.session_state:
    st.session_state["generated_images"] = {}

#określenie struktury promtów
class ColoringBookInput(BaseModel):
    motyw:str
    opis:Optional[str] = None
class ColoringBookPrompts(BaseModel):
    prompts: List[str] #lista promptów do generowania obrazów


#funkcja de generowania opisów kolorowanek na podstawie motywu i opisu
def generate_prompts(input_data:ColoringBookInput)-> ColoringBookPrompts:
    input_text = f"Wygeneruj 5 krótkich promptów do stworzenia kolorowanki antystresowej o motywie '{input_data.motyw}'"
    if input_data.opis:
        input_text += f" z uwzględnieniem opisu: '{input_data.opis}'"
    input_text += ". Prompty mają być kreatywne i zwięzłe. Zwróć odpowiedź jako strukturalna lista stringów."
    #łaczenie z modelem openai
    response = instructor_openai_client.chat.completions.create(
         model="gpt-4o",
         response_model=ColoringBookPrompts,
         messages=[
            {"role": "system", "content": "Jesteś kreatywnym asystentem do generowania pomysłów na kolorowanki antystresowe dla dzieci i dorosłych."},
            {"role": "user", "content": input_text}
            
        ],
    )
    return response 

#funkcja do generowania i pobierania kolorowanek
def generate_image(prompt: str, session_name:str):
    response = instructor_openai_client.images.generate(
        model="dall-e-3",
        prompt=f"Line art style coloring book page: {prompt}",
        size="1024x1024",
        quality="standard",
        n=1,
)
    image_url = response.data[0].url
#zapisywanie kolorowanek do sessopn state
    if session_name not in st.session_state["generated_images"] or not isinstance(st.session_state["generated_images"][session_name], list):
        st.session_state["generated_images"] [session_name]= []
    st.session_state["generated_images"][session_name].append(image_url)
    
    return image_url
    

#strona głowna aplikacji

st.header("Pokoloruj Twój Kreatywny Wzór")
st.image("image.png",  use_container_width=True)

st.write("---")
st.markdown("Witaj w aplikacji do generowania kolorowanek." )  
st.markdown("**Wybierz motyw kolorowanki,**  jaką chcesz dziś pokolorować i zanurz się w odprężającym malowaniu!"
        " Możesz dodać opis dla dokładniejszego efektu lub poddać się _wyobraźni AI_.") 
st.markdown("Kolorowanki dla dzieci i dorosłych.")
st.write("---")

#wybór motywu
motyw = st.selectbox(
    "Wybierz motyw kolorowanki",
    ("Krajobraz", "Rośliny","Zwierzęta", "Fantastyka", "Owoce", "Warzywa", "Mandale","Architektura", "Morski świat", "Kosmos", "Bajki")
)
opis = st.text_input("Podaj krótki opis przyszłej kolorowanki (opcionalnie):", "")

#wybór ilosci kolorowanek
ilosc = st.select_slider(
     "Wybierz liczbę kolorowanek do wygenerowania:",
     options=[1, 2, 3, 4, 5,6,7,8,9,10], 
     value=1
 )

session_name = st.text_input("Zapisz kolorownkę pod nazwą:", "Kolorowanka_"+ motyw)
if st.button(":ok: Generuj kolorowankę"):
    with st.spinner("Twoja kolorowanka tworzy się! Proszę czekać..."):
        input_data = ColoringBookInput(motyw=motyw, opis=opis)
        prompts = generate_prompts(input_data)
        
        # Generowanie i wyświetlanie obrazów
        for i, prompt in enumerate(prompts.prompts[:ilosc]): 
            image_url = generate_image(prompt, session_name) 
            image_data = requests.get(image_url).content
            image_io = io.BytesIO(image_data)
            
            #wyświetlenie kolorowanki
            st.image(image_io, caption=f"🎨 Kolorowanka {i+1}", use_container_width=True)
            st.download_button(
                label=":arrow_down: Pobierz kolorowankę",
                data=image_data,
                file_name=f"{session_name}_{i+1}.png",
                mime="image/png"
            )
    
    if st.success("Twoje kolorowanki są gotowe! Miłej zabawy!"):
        st.balloons()

       
       
   # Historia sesji, pasek boczny
with st.sidebar:
    st.subheader("Zapisane kolorowanki")
    selected_session=None
    if st.session_state["generated_images"]:
        selected_session = st.selectbox("📂 Wybierz zapisaną kolorowankę", list(st.session_state["generated_images"].keys()))

    if selected_session:
        
        for i, url in enumerate(st.session_state["generated_images"][selected_session]):
            st.image(url, caption=f"🎨 Kolorowanka {i+1}", use_container_width=True)

            # Przycisk pobrania dla wczytanych obrazów
            image_data = requests.get(url).content
            st.download_button(
                label=":arrow_down: Pobierz kolorowankę",
                data=image_data,
                file_name=f"{selected_session}_{i+1}.png",
                mime="image/png",
                key=f"download_sidebar_{selected_session}_{i}"
            )
    else:
        st.info("Brak zapisanych kolorowanek.")