# app.py - Derma Studio (Performance-optimized)
import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io, base64, requests, pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# ---------- Page config ----------
st.set_page_config(page_title="Derma Studio", layout="wide", initial_sidebar_state="expanded")

# ---------- Minimal theme (keeps app light) ----------
st.markdown("""
<style>
body { background:#F5F5F5; color:#333; }
.card{background:#fff;border-radius:10px;padding:12px;margin-bottom:10px;box-shadow:0 1px 6px rgba(0,0,0,0.05);}
.small{font-size:0.9rem;color:#555;}
</style>
""", unsafe_allow_html=True)

# ---------- Helpers & performance ----------
@st.cache_data
def load_products_default():
    # small product DB (expand later or load CSV)
    # keep compact fields for fast filtering
    return [
        {"id":"M001","Brand":"Bioderma","Name":"Sensibio H2O","Category":"Micellar","Skin Type":"Sensitive","Concern":"Makeup Removal"},
        {"id":"C007","Brand":"Bioderma","Name":"Sebium Gel Moussant","Category":"Cleanser","Skin Type":"Oily","Concern":"Oil Control"},
        {"id":"C010","Brand":"CeraVe","Name":"Foaming Cleanser","Category":"Cleanser","Skin Type":"Oily","Concern":"Acne"},
        {"id":"S014","Brand":"The Ordinary","Name":"Niacinamide 10% + Zinc","Category":"Serum","Skin Type":"All","Concern":"Pores/Acne"},
        {"id":"MO025","Brand":"Neutrogena","Name":"Hydro Boost","Category":"Moisturizer","Skin Type":"Dry","Concern":"Hydration"},
        {"id":"SS007","Brand":"EltaMD","Name":"UV Clear SPF46","Category":"Sunscreen","Skin Type":"All","Concern":"UV Protection"},
        # ... (you can replace with the big CSV; this default is to keep app fast)
    ]

def enhance_image_fast(img: Image.Image, max_size=800, sharp=1.4, quality=80):
    """ Resize + autocontrast + sharpen — faster and smaller file size """
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((max_size, max_size))
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Sharpness(img).enhance(sharp)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    return Image.open(buffer)

def image_to_b64(img: Image.Image):
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# Generic mock / pluggable API call (kept async-free)
def call_skin_api_mock(base64_str):
    # Very fast mock response — replace with real API in Settings
    return {"hydration":70,"acne_score":25,"spots_score":15,"pigmentation_score":35,"notes":"Demo analysis"}

# Fast tolerant parser
def parse_api_response(resp):
    # ensure numeric-ish outputs
    def conv(x):
        try:
            return float(x)
        except:
            return None
    return {
        "hydration": conv(resp.get("hydration")),
        "acne": conv(resp.get("acne_score") or resp.get("acne")),
        "spots": conv(resp.get("spots_score") or resp.get("spots")),
        "pigmentation": conv(resp.get("pigmentation_score") or resp.get("pigmentation")),
        "notes": resp.get("notes","")
    }

# Routine generator: maps analysis -> AM/PM + product picks (fast, rule-based)
@st.cache_data
def generate_routine_from_analysis(analysis: dict, skin_type: str, products: list):
    """
    analysis: dict with hydration, acne, spots, pigmentation (0-100)
    skin_type: 'Oily'|'Dry'|'Combination'|'Sensitive'|'Normal'
    products: product list to pick suggestions from
    """
    am = []
    pm = []
    suggestions = []

    # Basic rules
    hydration = analysis.get("hydration") or 50
    acne = analysis.get("acne") or 0
    pigmentation = analysis.get("pigmentation") or 0

    # AM routine baseline
    am = ["Cleanser", "Hydrating / Toner", "Serum (targeted)", "Moisturizer", "Sunscreen"]
    pm = ["Cleanser", "Toner (gentle)", "Treatment Serum", "Moisturizer / Night"]

    # Adjust based on concerns
    if acne > 30:
        # prioritize BHA/Salicylic and oil-control
        pm.insert(1, "BHA / Salicylic Serum")
        suggestions += [p for p in products if "Acne" in p.get("Concern","") or p.get("Category","").lower()=="serum"]
    if pigmentation > 30:
        suggestions += [p for p in products if "Pigment" in p.get("Name","") or "Pigment" in p.get("Concern","")]
        # add brightening serum
        am.insert(2, "Vitamin C / Brightening Serum")
        pm.insert(2, "AHA/BHA (2x week)")
    if hydration < 40:
        am.insert(1, "Hydrating Serum (HA)")
        pm.append("Overnight Hydrating Mask / Rich Moisturizer")
        suggestions += [p for p in products if p.get("Category","").lower()=="moisturizer"]

    # deduplicate suggestions preserving order and limit to 6
    seen = set(); final_suggestions = []
    for s in suggestions:
        key = s.get("id") or s.get("Name")
        if key and key not in seen:
            final_suggestions.append(s)
            seen.add(key)
        if len(final_suggestions) >= 6:
            break

    return {"am": am, "pm": pm, "suggestions": final_suggestions}

# ---------- Session defaults ----------
if "products" not in st.session_state:
    # load default DB (fast)
    st.session_state.products = load_products_default()

if "page" not in st.session_state:
    st.session_state.page = "Home"

# Simple navigation handler (no rerun)
def navigate(to):
    st.session_state.page = to

# ---------- Layout: header ----------
st.markdown("<div class='card'><h2>Derma Studio</h2><p class='small'>Fast mobile-first skin consultation</p></div>", unsafe_allow_html=True)

# ---------- Top quick nav ----------
col1, col2, col3, col4 = st.columns(4)
if col1.button("Consultation"):
    navigate("Consultation")
if col2.button("Skin Analysis"):
    navigate("Skin Analysis")
if col3.button("Products"):
    navigate("Products")
if col4.button("Routine"):
    navigate("Routine")

# ---------- Render pages (lightweight) ----------
page = st.session_state.page

# ---------- Consultation ----------
if page == "Consultation":
    st.markdown("<div class='card'><h3>Consultation</h3></div>", unsafe_allow_html=True)
    with st.form("consult"):
        name = st.text_input("Name")
        age = st.number_input("Age", 1, 120, 26)
        skin_type = st.selectbox("Skin type", ["Normal","Dry","Oily","Combination","Sensitive"])
        concerns = st.text_area("Concerns")
        if st.form_submit_button("Save"):
            st.session_state.setdefault("clients", []).append({
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "name": name, "age": age, "skin_type": skin_type, "concerns": concerns,
                "created_at": datetime.now().isoformat()
            })
            st.success("Saved")

    # quick list
    clients = st.session_state.get("clients", [])
    if clients:
        for c in clients[-6:][::-1]:
            st.write(f"- **{c['name']}** — {c['age']}y • {c['skin_type']} — {c['concerns']}")

# ---------- Products (fast table) ----------
elif page == "Products":
    st.markdown("<div class='card'><h3>Products (sample)</h3></div>", unsafe_allow_html=True)
    df = pd.DataFrame(st.session_state.products)
    st.dataframe(df[["id","Brand","Name","Category","Skin Type","Concern"]], use_container_width=True)

# ---------- Routine page ----------
elif page == "Routine":
    st.markdown("<div class='card'><h3>Routine Templates</h3></div>", unsafe_allow_html=True)
    st.write("Choose or generate routine after skin analysis.")
    if st.button("Back to Home"):
        navigate("Home")

# ---------- Skin Analysis (phone-friendly, fast path) ----------
elif page == "Skin Analysis":
    st.markdown("<div class='card'><h3>Skin Analysis</h3><p class='small'>Fast mode: Upload saved high-res photo (recommended). Camera option available but uploader is fastest on phones.</p></div>", unsafe_allow_html=True)

    # Option: low-data (uploader) vs camera (embedded)
    mode = st.radio("Capture mode", ["Uploader (fast)", "High-res camera (optional)"], index=0, horizontal=True)

    uploaded = None
    if mode == "Uploader (fast)":
        uploaded = st.file_uploader("Upload high-res photo", type=["jpg","jpeg","png"], accept_multiple_files=False)
    else:
        # small camera widget — keep minimal JS to avoid heavy reflows
        camera_html = """
        <video id="video" autoplay playsinline style="width:100%;max-width:520px;border-radius:10px;background:#000;"></video>
        <div style="margin-top:8px;">
            <button id="start" style="background:#D9B89C;padding:8px;border-radius:8px;border:none;">Start</button>
            <button id="cap" style="background:#D9B89C;padding:8px;border-radius:8px;border:none;margin-left:6px;">Capture</button>
        </div>
        <div id="dl" style="margin-top:8px;"></div>
        <canvas id="c" style="display:none;"></canvas>
        <script>
        const v=document.getElementById('video'), s=document.getElementById('start'), b=document.getElementById('cap'), dl=document.getElementById('dl'), c=document.getElementById('c');
        let stream=null;
        s.onclick=async()=>{ try { stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment',width:{ideal:1280},height:{ideal:720}}}); v.srcObject=stream; dl.innerHTML='Camera started'; }catch(e){dl.innerText='Camera error:'+e.message} };
        b.onclick=()=>{ if(!stream){dl.innerText='Start first';return;} c.width=v.videoWidth; c.height=v.videoHeight; c.getContext('2d').drawImage(v,0,0,c.width,c.height); let url=c.toDataURL('image/jpeg',0.9); let a=document.createElement('a'); a.href=url; a.download='derma.jpg'; a.innerText='Download image'; a.style.padding='8px'; a.style.background='#D9B89C'; a.style.borderRadius='8px'; a.style.color='#333'; dl.innerHTML=''; dl.appendChild(a); };
        </script>
        """
        components.html(camera_html, height=420)
        st.markdown("Capture → tap Download image → save to Photos → upload via Uploader for fastest analysis.", unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload the saved capture here", type=["jpg","jpeg","png"])

    if uploaded:
        with st.spinner("Processing image..."):
            try:
                raw = uploaded.getvalue()
                img = Image.open(io.BytesIO(raw))
                img = enhance_image_fast(img)  # faster enhancement + resize
                st.image(img, caption="Processed image", use_column_width=True)

                # convert to base64 -> call mock API (fast)
                b64 = image_to_b64(img)
                # call real API here if configured (kept mock to be fast)
                resp = call_skin_api_mock(b64)
                parsed = parse_api_response(resp)

                # display quick metrics
                cols = st.columns(4)
                cols[0].metric("Hydration", int(parsed["hydration"] or 0))
                cols[1].metric("Acne (lower better)", int(parsed["acne"] or 0))
                cols[2].metric("Spots (lower better)", int(parsed["spots"] or 0))
                cols[3].metric("Pigmentation", int(parsed["pigmentation"] or 0))
                if parsed.get("notes"):
                    st.info(parsed["notes"])

                # generate routine immediately (fast cached)
                routine = generate_routine_from_analysis(parsed, skin_type="Normal", products=st.session_state.products)
                st.markdown("### Suggested Routine (generated)")
                st.markdown("**AM:** " + " → ".join(routine["am"]))
                st.markdown("**PM:** " + " → ".join(routine["pm"]))

                if routine["suggestions"]:
                    st.markdown("**Suggested Products:**")
                    for p in routine["suggestions"]:
                        st.write(f"- {p['Brand']} — {p['Name']} ({p['Category']})")

                # save last analysis to session for quick access
                st.session_state["last_analysis"] = {"time": datetime.now().isoformat(), "metrics": parsed, "routine": routine}
            except Exception as e:
                st.error("Image processing failed: " + str(e))

    else:
        st.info("Upload or capture an image to analyze.")

# ---------- Export (fast) ----------
elif page == "Export Data":
    st.markdown("<div class='card'><h3>Export</h3></div>", unsafe_allow_html=True)
    if st.session_state.get("clients"):
        df = pd.DataFrame(st.session_state.clients)
        st.download_button("Download clients CSV", df.to_csv(index=False), "clients.csv", mime="text/csv")
    else:
        st.info("No clients saved.")
    # export product sample
    st.download_button("Download product sample CSV", pd.DataFrame(st.session_state.products).to_csv(index=False), "products.csv", mime="text/csv")

# ---------- Settings ----------
elif page == "Settings":
    st.markdown("<div class='card'><h3>Settings</h3></div>", unsafe_allow_html=True)
    st.markdown("This app runs in **fast demo mode** (mock API). Replace call_skin_api_mock with your real API for live results.")
    if st.button("Clear cached last analysis"):
        st.session_state.pop("last_analysis", None)
        st.success("Cleared")

# ---------- Footer ----------
st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
