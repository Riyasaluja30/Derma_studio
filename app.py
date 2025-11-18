import streamlit as st
import pandas as pd
from PIL import Image

PASSWORD = "yourpassword"   # <<< SET YOUR PASSWORD HERE

# ----------------------------
# PASSWORD PROTECTION
# ----------------------------
pw = st.text_input("Enter password:", type="password")
if pw != PASSWORD:
    st.stop()

st.title("Derma Studio – AI Skin Analyzer + Routine Generator")

# ----------------------------
# LOAD PRODUCT DATA
# ----------------------------
df = pd.read_csv("products.csv")

# ----------------------------
# FAKE AI (placeholder)
# ----------------------------
def fake_ai_model(img):
    return {
        "skin_type": "Combination",
        "concerns": ["Acne", "Texture Issues"],
        "score": 0.87
    }

# ----------------------------
# IMAGE INPUT
# ----------------------------
st.header("📸 Upload / Capture Image")
uploaded = st.camera_input("Take a photo")

analysis = None

if uploaded:
    img = Image.open(uploaded)
    st.image(img, caption="Your Photo", use_column_width=True)

    analysis = fake_ai_model(img)
    st.success(
        f"AI Skin Type: **{analysis['skin_type']}** "
        f"(Confidence: {analysis['score']*100:.1f}%)"
    )
    st.write("AI-detected Concerns:", ", ".join(analysis["concerns"]))

# ----------------------------
# MANUAL OVERRIDE
# ----------------------------
st.header("⚙️ Manual Override (Optional)")

skin_type = st.selectbox("Skin Type", ["Oily", "Dry", "Combination", "Sensitive", "Normal"])
concerns = st.multiselect(
    "Concerns",
    ["Acne", "Pigmentation", "Dullness", "Redness", "Texture Issues", "Large Pores", "Fine Lines"]
)

final_skin = analysis["skin_type"] if analysis else skin_type
final_conc = analysis["concerns"] if analysis else concerns

# ----------------------------
# BUDGET INPUT
# ----------------------------
st.header("💰 Enter Total Budget")
budget = st.number_input("Total Budget (₹)", min_value=0, value=1500)

# ----------------------------
# ROUTINE GENERATOR
# ----------------------------

def generate_routine(skin, conc, budget):
    categories = ["Cleanser", "Toner", "Serum", "Moisturizer", "Sunscreen", "Exfoliant"]

    routine = {}
    total_cost = 0

    for cat in categories:
        # Filter matching products
        c = df[
            (df["Category"].str.contains(cat, case=False)) &
            (df["SkinType"].str.contains(skin, case=False))
        ]

        if conc:
            c = c[c["Concern"].apply(lambda x: any(cn in x for cn in conc))]

        if c.empty:
            routine[cat] = None
            continue

        # Select cheapest product first to fit in budget
        c = c.sort_values("Price")

        for _, row in c.iterrows():
            if total_cost + row["Price"] <= budget:
                routine[cat] = row
                total_cost += row["Price"]
                break
        else:
            routine[cat] = None

    return routine, total_cost


if st.button("Generate Routine"):
    routine, spent = generate_routine(final_skin, final_conc, budget)

    st.subheader("🧴 Your Personalized Routine")
    st.write(f"**Skin Type:** {final_skin}")
    st.write(f"**Concerns:** {', '.join(final_conc)}")
    st.write(f"**Budget:** ₹{budget}")
    st.write(f"**Total Used:** ₹{spent}")

    for cat, product in routine.items():
        st.markdown("---")
        st.write(f"### {cat}")
        if product is None:
            st.warning("No product available in budget for this category.")
        else:
            st.success(product["ProductName"])
            st.write(f"Price: ₹{product['Price']}")
            st.write(f"Concern: {product['Concern']}")
