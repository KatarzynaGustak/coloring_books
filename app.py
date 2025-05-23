
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
#env = dotenv_values(".env")

def get_openai_clients():
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

 # OpenAI API key protection
# if not st.session_state.get("openai_api_key"):
#      if "OPENAI_API_KEY" in env: 
#         st.session_state["openai_api_key"] = env["OPENAI_API_KEY"]
#      else: 
#          st.info("Add your OpenAI API key to be able to use this application") 
#          st.session_state["openai_api_key"] = st.text_input("Key API", type="password")        
#          if st.session_state["openai_api_key"]: 
#              st.rerun()
# if not st.session_state.get("openai_api_key"):
#      st.stop()



# #połaczenie z instruktorem
instructor_openai_client = instructor.from_openai(get_openai_clients()) 

#łączenie z BMaC
buy_me_a_coffee_url = st.secrets["buy_me_a_coffee"]["url"]

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
def generate_image(prompt: str, session_name: str):
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

st.header("🎨 Color Your Creative Pattern")
st.image("image.png",  use_container_width=True)

st.write("---")
st.markdown("Welcome to the Coloring Page Generator App." )  
st.markdown("**Pick Your Perfect Coloring Theme!**  Immerse yourself in a relaxing painting experience!"
        " You can add a description for a more detailed effect or let your imagination be guided by AI.") 
st.markdown("Coloring Fun for Everyone! 🖌️")
st.write("---")

#wybór motywu
motyw = st.selectbox(
    "Choose a Coloring Page Theme:",
    ("Landscape", "Plants" ,"Animals" ,"Fantasy" ,"Fruits" ,"Vegetables" ,"Mandalas", "Architecture", "Underwater World", "Space", "Fairy Tales")
)
opis = st.text_input("Provide a short description of your future coloring page (optional):", "")

#wybór ilosci kolorowanek
ilosc = st.select_slider(
     "Choose the number of coloring pages to generate:",
     options=[1, 2, 3, 4, 5,6,7,8,9,10], 
     value=1
 )

session_name = st.text_input("Save the coloring page under the name-example: Coloring_Page_" + motyw)
if st.button(":ok: Generate Coloring Page"):
    with st.spinner("Creating your coloring page! Please hold on..."):
        input_data = ColoringBookInput(motyw=motyw, opis=opis)
        prompts = generate_prompts(input_data)
        
        # Generowanie i wyświetlanie obrazów
        for i, prompt in enumerate(prompts.prompts[:ilosc]): 
            image_url = generate_image(prompt, session_name) 
            image_data = requests.get(image_url).content
            image_io = io.BytesIO(image_data)
            
            #wyświetlenie kolorowanki
            st.image(image_io, caption=f"🎨 Coloring_Page_{i+1}", use_container_width=True)
            st.download_button(
                label=":arrow_down: Download the Coloring Page",
                data=image_data,
                file_name=f"{session_name}_{i+1}.png",
                mime="image/png"
            )
    
    if st.success("✅ Your coloring pages are ready! Enjoy coloring!"):
        st.balloons()

       
       
   # Historia sesji, pasek boczny
with st.sidebar:
    st.subheader("📂 Your Saved Coloring Pages")
    selected_session=None
    if st.session_state["generated_images"]:
        selected_session = st.selectbox("📂 Select from Your Saved Coloring Pages.", list(st.session_state["generated_images"].keys()))

    if selected_session:
        
        for i, url in enumerate(st.session_state["generated_images"][selected_session]):
            st.image(url, caption=f"🎨 Coloring_Page_{i+1}", use_container_width=True)

            # Przycisk pobrania dla wczytanych obrazów
            image_data = requests.get(url).content
            st.download_button(
                label=":arrow_down: Download the Coloring Page",
                data=image_data,
                file_name=f"{selected_session}_{i+1}.png",
                mime="image/png",
                key=f"download_sidebar_{selected_session}_{i}"
            )
    else:
        st.info("No coloring pages saved")
    
with st.sidebar:
    st.markdown(f"""
<a href="{buy_me_a_coffee_url}" target="_blank">
    <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px; width: 217px;">
</a>
""", unsafe_allow_html=True)

    


st.markdown("---")

st.markdown("🎨 Color Your Creative Pattern -- Create and color unique AI-generated patterns!")