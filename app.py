# app.py - Derma Studio (FINAL — FIXED NAVIGATION)
import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io, base64, requests, pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# =====================================================
#  PAGE CONFIG + NUDE THEME
# =====================================================
st.set_page_config(page_title="Derma Studio", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
body { background-color: #F5F5F5; color: #333333; }
header, .reportview-container .main footer {visibility: hidden;}
.stApp { padding-top: 0rem; }
.card { background: #FFFFFF; border-radius: 12px; padding: 14px; 
        box-shadow: 0 1px 6px rgba(0,0,0,0.06); margin-bottom:12px; }
.small { font-size:0.9rem; color:#555; }
.link-btn {
    width: 100%; 
    background:#D9B89C;
    color:#333; 
    border:none;
    padding:10px;
    border-radius:8px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
#  HELPERS
# =====================================================
def enhance_image(img: Image.Image, sharpness=1.8, max_size=1400):
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((max_size, max_size))
    img = ImageOps.autocontrast(img)
    enhancer = ImageEnhance.Sharpness(img)
    return enhancer.enhance(sharpness)

def image_to_b64(img: Image.Image):
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return base64.b64encode(buf.getvalue()).decode()

def call_skin_api(b64, cfg):
    try:
        if cfg.get("mode") == "bearer_json":
            headers = {"Authorization": f"Bearer {cfg.get('bearer_token','')}",
                       "Content-Type":"application/json"}
            payload = {"image_base64": b64}
            r = requests.post(cfg.get("endpoint",""), headers=headers, json=payload, timeout=30)
            return r.status_code, r.json()

        elif cfg.get("mode") == "formdata_facepp":
            img_bytes = base64.b64decode(b64)
            files = {"image_file": ("image.jpg", img_bytes, "image/jpeg")}
            data = {"api_key": cfg.get("api_key",""), "api_secret": cfg.get("api_secret","")}
            r = requests.post(cfg.get("endpoint",""), data=data, files=files, timeout=30)
            return r.status_code, r.json()

        # Mock response
        return 200, {
            "hydration": 78,
            "acne_score": 22,
            "spots_score": 14,
            "pigmentation_score": 35,
            "notes": "Mock mode active (no real API)."
        }
    except Exception as e:
        return 500, {"error": str(e)}

# =====================================================
#  SESSION STATE
# =====================================================
if "clients" not in st.session_state:
    st.session_state.clients = []

if "products" not in st.session_state:
    st.session_state.products = []  # You will load CSV separately

if "api_config" not in st.session_state:
    st.session_state.api_config = {"mode":"mock"}

# =====================================================
#  SIDEBAR NAVIGATION (FIXED)
# =====================================================
st.sidebar.title("Derma Studio")

def go(page):
    st.session_state.forced_page = page
    st.experimental_rerun()

pages = [
    "Home","Consultation","Products & Budget",
    "Routine Tracker","Skin Analysis","Export Data","Settings"
]

if "forced_page" in st.session_state:
    _ = st.sidebar.radio("Navigate", pages, index=0)
    page = st.session_state.forced_page
else:
    page = st.sidebar.radio("Navigate", pages)

# =====================================================
#  HOME (FIXED BUTTON NAVIGATION)
# =====================================================
if page == "Home":

    st.markdown("<div class='card'><h2>Derma Studio</h2><p class='small'>Mobile-first skin consultation assistant.</p></div>", unsafe_allow_html=True)

    st.markdown("<div class='card'><h4>Quick Links</h4></div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.button("📋 Consultation", on_click=go, args=("Consultation",))
    with c2:
        st.button("📷 Skin Analysis", on_click=go, args=("Skin Analysis",))
    with c3:
        st.button("🧴 Products", on_click=go, args=("Products & Budget",))
    with c4:
        st.button("✅ Routine", on_click=go, args=("Routine Tracker",))

    st.markdown("<div class='small'>Tap a tile to navigate. Works on iPhone Safari.</div>", unsafe_allow_html=True)

# =====================================================
#  CONSULTATION
# =====================================================
elif page == "Consultation":
    st.markdown("<div class='card'><h3>New Consultation</h3></div>", unsafe_allow_html=True)

    with st.form("consult_form", clear_on_submit=True):
        name = st.text_input("Client name")
        age = st.number_input("Age", 1, 120, 26)
        skin_type = st.selectbox("Skin Type", ["Normal","Dry","Oily","Combination","Sensitive"])
        concerns = st.text_area("Concerns")
        notes = st.text_area("Notes (optional)")

        if st.form_submit_button("Save client"):
            st.session_state.clients.append({
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "name": name,
                "age": age,
                "skin_type": skin_type,
                "concerns": concerns,
                "notes": notes,
                "created_at": datetime.now().isoformat()
            })
            st.success("Client saved")

    st.markdown("<div class='card'><h4>Saved Clients</h4></div>", unsafe_allow_html=True)
    for c in st.session_state.clients[::-1]:
        st.markdown(
            f"<div class='card'><b>{c['name']}</b> — {c['age']}y • {c['skin_type']}<br>"
            f"<span class='small'>{c['concerns']}</span></div>",
            unsafe_allow_html=True
        )

# =====================================================
#  PRODUCTS & BUDGET
# =====================================================
elif page == "Products & Budget":

    st.markdown("<div class='card'><h3>Products & Budget</h3></div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1,1,2])

    f_skin = c1.selectbox("Skin type", ["All","Normal","Dry","Oily","Combination","Sensitive"])
    f_concern = c2.text_input("Filter concern")

    selected = []
    for p in st.session_state.products:
        if f_skin != "All" and p["Skin Type"] != f_skin:
            continue
        if f_concern and f_concern.lower() not in p["Concern"].lower():
            continue
        key = f"sel_{p['Name']}"
        if st.checkbox(f"{p['Brand']} — {p['Name']} (₹{p['Price']})", key=key):
            selected.append(p)

    total = sum(x["Price"] for x in selected)
    st.markdown(f"<div class='card'><b>Total Budget: ₹{total}</b></div>", unsafe_allow_html=True)

# =====================================================
#  ROUTINE TRACKER
# =====================================================
elif page == "Routine Tracker":

    st.markdown("<div class='card'><h3>Routine Tracker</h3></div>", unsafe_allow_html=True)

    routines = {
        "Oily": ["Cleanser","Toner","BHA/Serum","Moisturizer","Sunscreen"],
        "Dry": ["Gentle Cleanser","Hydrating Serum","Moisturizer","Sunscreen"],
        "Combination": ["Cleanser","Toner","Serum","Moisturizer","Sunscreen"]
    }

    stype = st.selectbox("Template", ["Custom"] + list(routines.keys()))

    if stype == "Custom":
        steps = st.text_area("Steps (comma separated)",
                             "Cleanser, Serum, Moisturizer, Sunscreen").split(",")
        steps = [s.strip() for s in steps if s.strip()]
    else:
        steps = routines[stype]

    if "routine_state" not in st.session_state:
        st.session_state.routine_state = {s: False for s in steps}

    st.markdown("<div class='card'><h4>Today's Routine</h4></div>", unsafe_allow_html=True)

    done = 0
    for step in steps:
        check = st.checkbox(step, value=st.session_state.routine_state.get(step, False))
        st.session_state.routine_state[step] = check
        if check:
            done += 1

    st.progress(done / len(steps))
    st.write(f"{done} / {len(steps)} steps completed")

# =====================================================
#  HIGH RES SKIN ANALYSIS
# =====================================================
elif page == "Skin Analysis":

    st.markdown("<div class='card'><h3>Skin Analysis</h3><p class='small'>Use high-res camera → Download → Upload → Analyze.</p></div>", unsafe_allow_html=True)

    # High-res camera HTML/JS
    camera_html = r"""
    <div style='text-align:center'>
      <video id="v" autoplay playsinline style="width:100%;max-width:520px;border-radius:10px;background:#000;"></video>
      <div style="margin-top:8px;">
        <button id="start" style="background:#D9B89C;padding:10px;border-radius:8px;border:none;">Start camera</button>
        <button id="cap" style="background:#D9B89C;padding:10px;border-radius:8px;border:none;margin-left:6px;">Capture</button>
      </div>
      <div id="dl" style="margin-top:8px;"></div>
      <canvas id="c" style="display:none;"></canvas>
    </div>

    <script>
    const v = document.getElementById('v');
    const s = document.getElementById('start');
    const b = document.getElementById('cap');
    const dl = document.getElementById('dl');
    const c = document.getElementById('c');

    let stream = null;
    s.onclick = async function(){
        dl.innerHTML = "Requesting camera...";
        try {
           stream = await navigator.mediaDevices.getUserMedia({
               video:{facingMode:'environment', width:{ideal:1920}, height:{ideal:1080}}
           });
           v.srcObject = stream;
           dl.innerHTML = "Camera started";
        } catch(e){ dl.innerHTML = "Camera failed: "+e.message }
    };

    b.onclick = function(){
        if(!stream){ dl.innerHTML = "Start camera first"; return; }
        c.width = v.videoWidth; c.height = v.videoHeight;
        c.getContext('2d').drawImage(v,0,0,c.width,c.height);
        let url = c.toDataURL('image/jpeg',0.95);
        let link = document.createElement('a');
        link.href = url;
        link.download = 'derma_capture.jpg';
        link.innerText = 'Download image';
        link.style.padding='8px'; link.style.background='#D9B89C';
        link.style.borderRadius='8px'; link.style.color='#333';
        dl.innerHTML = ''; dl.appendChild(link);
    };
    </script>
    """

    components.html(camera_html, height=420)

    st.markdown("<div class='small'>Upload the downloaded image below:</div>", unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload photo", type=["jpg","jpeg","png"])
    cam_fallback = st.camera_input("Or use phone camera (lower quality)")
    analyze = st.button("Analyze")

    chosen = uploaded if uploaded else cam_fallback

    if analyze:
        if not chosen:
            st.error("Upload or capture an image.")
        else:
            img = Image.open(io.BytesIO(chosen.getvalue()))
            img = enhance_image(img)

            st.image(img, caption="Enhanced Image", use_column_width=True)

            b64 = image_to_b64(img)
            cfg = st.session_state.api_config
            status, resp = call_skin_api(b64, cfg)

            if status != 200:
                st.error(resp)
            else:
                st.markdown("<div class='card'><h4>Analysis Result</h4></div>", unsafe_allow_html=True)

                h = resp.get("hydration")
                a = resp.get("acne_score")
                sp = resp.get("spots_score")
                pig = resp.get("pigmentation_score")

                cols = st.columns(4)
                cols[0].metric("Hydration", h)
                cols[1].metric("Acne (low better)", a)
                cols[2].metric("Spots (low better)", sp)
                cols[3].metric("Pigmentation", pig)

                if resp.get("notes"):
                    st.info(resp["notes"])

# =====================================================
#  EXPORT DATA
# =====================================================
elif page == "Export Data":
    st.markdown("<div class='card'><h3>Export Data</h3></div>", unsafe_allow_html=True)

    dfc = pd.DataFrame(st.session_state.clients)
    if not dfc.empty:
        st.dataframe(dfc)
        st.download_button("Download Clients CSV", dfc.to_csv(index=False), "clients.csv")
    else:
        st.info("No clients yet.")

    dfp = pd.DataFrame(st.session_state.products)
    st.dataframe(dfp)
    st.download_button("Download Product CSV", dfp.to_csv(index=False), "products.csv")

# =====================================================
#  SETTINGS
# =====================================================
elif page == "Settings":

    st.markdown("<div class='card'><h3>Settings</h3></div>", unsafe_allow_html=True)

    mode = st.selectbox("API Mode", ["mock","bearer_json","formdata_facepp"])

    if mode == "bearer_json":
        ep = st.text_input("Endpoint")
        tok = st.text_input("Bearer Token")
        if st.button("Save"):
            st.session_state.api_config = {"mode":"bearer_json","endpoint":ep,"bearer_token":tok}
            st.success("Saved")

    elif mode == "formdata_facepp":
        ep = st.text_input("Endpoint")
        k = st.text_input("API Key")
        s = st.text_input("API Secret")
        if st.button("Save"):
            st.session_state.api_config = {"mode":"formdata_facepp","endpoint":ep,"api_key":k,"api_secret":s}
            st.success("Saved")
    else:
        st.session_state.api_config = {"mode":"mock"}
        st.info("Mock mode active")
