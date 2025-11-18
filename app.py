import streamlit as st
import pandas as pd
from PIL import Image
import numpy as np
import io

PASSWORD = "derma2025"
pw=st.text_input("Enter password:",type="password")
if pw!=PASSWORD:
    st.stop()

st.title("Derma Studio – AI Skin Analyzer")

df=pd.read_csv("products.csv")

st.header("🤖 AI-Powered Skin Analysis")

uploaded=st.camera_input("Take a photo")

def fake_ai_model(img):
    # placeholder demo model
    return {
        "skin_type":"Combination",
        "concerns":["Acne","Texture Issues","Dullness"],
        "score":0.87
    }

analysis=None

if uploaded:
    img=Image.open(uploaded)
    st.image(img,caption="Your Photo",use_column_width=True)
    analysis=fake_ai_model(img)
    st.success(f"Detected Skin Type: **{analysis['skin_type']}** (AI Confidence: {analysis['score']*100:.1f}%)")
    st.write("Detected Concerns:",", ".join(analysis["concerns"]))

st.header("Manual Override")
skin_type=st.selectbox("Skin type",["Oily","Dry","Combination","Sensitive","Normal"])
concerns=st.multiselect("Concerns",["Acne","Pigmentation","Dullness","Redness","Texture Issues","Large Pores","Fine Lines"])

final_skin=analysis["skin_type"] if analysis else skin_type
final_conc=analysis["concerns"] if analysis else concerns

st.subheader("Personalized Products")
filtered=df[df["SkinType"].str.contains(final_skin,case=False)]
st.write(filtered)

st.info("AI model currently runs in demo mode. Real ML model can be integrated easily.")
