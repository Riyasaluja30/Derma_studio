# app.py - Derma Studio (final)
import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io, base64, requests, pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# ---- Page config & CSS (nude theme) ----
st.set_page_config(page_title="Derma Studio", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
body { background-color: #F5F5F5; color: #333333; }
header, .reportview-container .main footer {visibility: hidden;}
.stApp { padding-top: 0rem; }
.card { background: #FFFFFF; border-radius: 12px; padding: 14px; box-shadow: 0 1px 6px rgba(0,0,0,0.06); margin-bottom:12px; }
.big-btn > button { background-color: #D9B89C; color: #333333; border-radius:8px; height:44px; }
.small { font-size:0.9rem; color:#555; }
.center { display:flex; justify-content:center; align-items:center; }
.note { color:#666; font-size:0.9rem; margin-top:8px; }
a.link { color:#333333; text-decoration:none; background:#D9B89C; padding:8px 10px; border-radius:8px; }
</style>
""", unsafe_allow_html=True)

# ---- Helpers ----
def enhance_image(img: Image.Image, sharpness=1.8, max_size=1400):
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((max_size, max_size))
    img = ImageOps.autocontrast(img)
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(sharpness)
    return img

def image_to_b64(img: Image.Image, quality=92):
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def call_skin_api(b64, cfg):
    mode = cfg.get("mode", "mock")
    try:
        if mode == "bearer_json":
            headers = {"Authorization": f"Bearer {cfg.get('bearer_token','')}", "Content-Type":"application/json"}
            payload = {"image_base64": b64}
            r = requests.post(cfg.get("endpoint",""), headers=headers, json=payload, timeout=30)
            return r.status_code, r.json()
        elif mode == "formdata_facepp":
            img_bytes = base64.b64decode(b64)
            files = {"image_file": ("image.jpg", img_bytes, "image/jpeg")}
            data = {"api_key": cfg.get("api_key",""), "api_secret": cfg.get("api_secret","")}
            r = requests.post(cfg.get("endpoint",""), data=data, files=files, timeout=30)
            return r.status_code, r.json()
        else:
            # Mock response
            demo = {"hydration": 78, "acne_score": 18, "spots_score": 12, "pigmentation_score": 34,
                    "notes": "Demo mode: no real API connected. Replace config in Settings to enable live analysis."}
            return 200, demo
    except Exception as e:
        return 500, {"error": str(e)}

# ---- Session data (persist in session_state) ----
if "clients" not in st.session_state:
    st.session_state.clients = []
if "products" not in st.session_state:
    st.session_state.products = [
        {"Brand":"Bioderma","Name":"Sensibio H2O","Skin Type":"Sensitive","Concern":"Makeup Removal","Price":719},
        {"Brand":"Bioderma","Name":"Sensibio Lait","Skin Type":"Dry","Concern":"Dryness","Price":1634},
        {"Brand":"CeraVe","Name":"Hydrating Cleanser","Skin Type":"Normal/Combo","Concern":"Hydration","Price":999},
        {"Brand":"La Roche-Posay","Name":"Effaclar Gel","Skin Type":"Oily","Concern":"Acne","Price":1200},
        {"Brand":"Minimalist","Name":"10% Niacinamide Serum","Skin Type":"All","Concern":"Pores/Acne","Price":899},
        {"Brand":"La Roche-Posay","Name":"Hydrating Serum","Skin Type":"Dry","Concern":"Hydration","Price":1350},
        {"Brand":"CeraVe","Name":"Foaming Cleanser","Skin Type":"Oily","Concern":"Acne","Price":1150},
        {"Brand":"Minimalist","Name":"Vitamin C Serum","Skin Type":"All","Concern":"Pigmentation","Price":950},
        {"Brand":"Bioderma","Name":"Hydrabio Gel","Skin Type":"Sensitive","Concern":"Redness","Price":800},
        {"Brand":"CeraVe","Name":"Moisturizing Cream","Skin Type":"Dry","Concern":"Hydration","Price":1099},
        {"Brand":"La Roche-Posay","Name":"Toleriane Cleanser","Skin Type":"Normal/Combo","Concern":"Sensitive","Price":1250},
        {"Brand":"Minimalist","Name":"BHA Serum","Skin Type":"All","Concern":"Anti-Acne","Price":1199},
        {"Brand":"Bioderma","Name":"Sebium Gel","Skin Type":"Oily","Concern":"Oil Control","Price":899},
        {"Brand":"CeraVe","Name":"Ceramide Lotion","Skin Type":"Dry","Concern":"Dryness","Price":950},
        {"Brand":"La Roche-Posay","Name":"Pigmentclar Serum","Skin Type":"All","Concern":"Pigmentation","Price":1300},
        {"Brand":"Minimalist","Name":"Acne Spot Gel","Skin Type":"Oily","Concern":"Acne Spots","Price":799},
        {"Brand":"Bioderma","Name":"Sébium H2O","Skin Type":"Sensitive","Concern":"Makeup Removal","Price":719},
        {"Brand":"CeraVe","Name":"Hydrating Serum","Skin Type":"Normal/Combo","Concern":"Hydration","Price":999},
        {"Brand":"Minimalist","Name":"Retinol Serum","Skin Type":"All","Concern":"Anti-Aging","Price":1099},
        {"Brand":"Bioderma","Name":"Sensibio Lotion","Skin Type":"Sensitive","Concern":"Moisturizing","Price":1634},
    ]
if "api_config" not in st.session_state:
    st.session_state.api_config = {"mode":"mock"}

# ---- Sidebar navigation ----
st.sidebar.title("Derma Studio")
page = st.sidebar.radio("Navigate", ["Home","Consultation","Products & Budget","Routine Tracker","Skin Analysis","Export Data","Settings"])

# ---- Home ----
if page == "Home":
    st.markdown("<div class='card'><h2>Derma Studio</h2><p class='small'>Mobile-first skin consultation assistant.</p></div>", unsafe_allow_html=True)
    st.markdown("<div class='card'><h4>Quick Links</h4><div style='display:flex;gap:10px;flex-wrap:wrap'>"
                "<a class='link' href='#Consultation'>📋 Consultation</a>"
                "&nbsp;&nbsp;<a class='link' href='#Skin Analysis'>📷 Skin Analysis</a>"
                "&nbsp;&nbsp;<a class='link' href='#Products & Budget'>🧴 Products</a>"
                "&nbsp;&nbsp;<a class='link' href='#Routine Tracker'>✅ Routine</a>"
                "</div></div>", unsafe_allow_html=True)

# ---- Consultation ----
elif page == "Consultation":
    st.markdown("<div class='card'><h3>New Consultation</h3></div>", unsafe_allow_html=True)
    with st.form("consult_form", clear_on_submit=True):
        name = st.text_input("Client name")
        age = st.number_input("Age", min_value=1, max_value=120, value=26)
        skin_type = st.selectbox("Skin type", ["Normal","Oily","Dry","Combination","Sensitive"])
        concerns = st.text_area("Concerns (comma separated)")
        notes = st.text_area("Notes (optional)")
        if st.form_submit_button("Save client"):
            client = {"id": datetime.now().strftime("%Y%m%d%H%M%S"), "name":name, "age":age, "skin_type":skin_type, "concerns":concerns, "notes":notes, "created_at": datetime.now().isoformat()}
            st.session_state.clients.append(client)
            st.success(f"Saved client {name}")
    st.markdown("<div class='card'><h4>Saved clients</h4></div>", unsafe_allow_html=True)
    for c in st.session_state.clients[::-1]:
        st.markdown(f"<div class='card'><b>{c['name']}</b> — {c['age']}y • {c['skin_type']}<br><span class='small'>{c['concerns']}</span></div>", unsafe_allow_html=True)

# ---- Products & Budget ----
elif page == "Products & Budget":
    st.markdown("<div class='card'><h3>Products & Budget</h3></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1,2])
    f_skin = c1.selectbox("Filter skin type", ["All","Sensitive","Dry","Normal/Combo","Oily"])
    f_concern = c2.text_input("Filter concern (text)")
    c3.markdown("<div class='small'>Select products to calculate budget.</div>", unsafe_allow_html=True)
    selected = []
    for p in st.session_state.products:
        if f_skin != "All" and p["Skin Type"] != f_skin:
            continue
        if f_concern and f_concern.lower() not in p["Concern"].lower():
            continue
        key = f"prod_{p['Brand']}_{p['Name']}"
        if st.checkbox(f"{p['Brand']} — {p['Name']} (₹{p['Price']}) — {p['Skin Type']} — {p['Concern']}", key=key):
            selected.append(p)
    total = sum([x["Price"] for x in selected])
    st.markdown(f"<div class='card'><b>Total estimated budget: ₹{total}</b></div>", unsafe_allow_html=True)

# ---- Routine Tracker ----
elif page == "Routine Tracker":
    st.markdown("<div class='card'><h3>Routine Tracker</h3></div>", unsafe_allow_html=True)
    stype = st.selectbox("Choose template", ["Custom","Oily","Dry","Combination"])
    template = {
        "Oily": ["Cleanser","Toner","BHA/Serum","Moisturizer","Sunscreen"],
        "Dry": ["Gentle Cleanser","Hydrating Serum","Moisturizer","Sunscreen"],
        "Combination": ["Cleanser","Toner","Serum","Moisturizer","Sunscreen"]
    }
    if stype == "Custom":
        steps_text = st.text_area("Enter routine steps (comma separated)", value="Cleanser,Serum,Moisturizer,Sunscreen")
        steps = [s.strip() for s in steps_text.split(",") if s.strip()]
    else:
        steps = template.get(stype, [])
    if "routine_state" not in st.session_state:
        st.session_state.routine_state = {s: False for s in steps}
    else:
        for s in steps:
            if s not in st.session_state.routine_state:
                st.session_state.routine_state[s] = False
        for k in list(st.session_state.routine_state.keys()):
            if k not in steps:
                st.session_state.routine_state.pop(k, None)
    st.markdown("<div class='card'><h4>Today's routine</h4></div>", unsafe_allow_html=True)
    for s in steps:
        st.session_state.routine_state[s] = st.checkbox(s, value=st.session_state.routine_state.get(s, False))
    done = sum(1 for v in st.session_state.routine_state.values() if v)
    total_steps = max(1, len(st.session_state.routine_state))
    st.progress(done/total_steps)
    st.markdown(f"<div class='small'>{done} of {total_steps} done</div>", unsafe_allow_html=True)

# ---- Skin Analysis (High-res camera flow) ----
elif page == "Skin Analysis":
    st.markdown("<div class='card'><h3>Skin Analysis</h3><p class='small'>Best flow on phone: Start high-res camera, Capture → Download image → save to Photos/Files → Upload below and Analyze.</p></div>", unsafe_allow_html=True)

    # Embedded high-res camera (JS); capture creates a downloadable JPG
    camera_html = r"""
    <div style="text-align:center">
      <video id="video" autoplay playsinline style="width:100%; max-width:520px; border-radius:10px; background:#000;"></video>
      <div style="margin-top:8px;">
        <button id="startBtn" style="background:#D9B89C;padding:10px;border-radius:8px;border:none;">Start camera</button>
        <button id="captureBtn" style="background:#D9B89C;padding:10px;border-radius:8px;border:none;margin-left:6px;">Capture</button>
      </div>
      <div id="down" style="margin-top:8px;"></div>
      <canvas id="canvas" style="display:none;"></canvas>
    </div>

    <script>
    const v = document.getElementById('video');
    const startBtn = document.getElementById('startBtn');
    const captureBtn = document.getElementById('captureBtn');
    const downDiv = document.getElementById('down');
    const canvas = document.getElementById('canvas');

    let stream = null;
    startBtn.onclick = async function(){
      downDiv.innerHTML = "<div style='font-size:12px;color:#555;margin-top:6px;'>Requesting camera... please allow access.</div>";
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment', width: { ideal: 1920 }, height: { ideal: 1080 } } });
        v.srcObject = stream;
        downDiv.innerHTML = "<div style='font-size:12px;color:#555;margin-top:6px;'>Camera started. Use Capture to take photo.</div>";
      } catch(err) {
        downDiv.innerHTML = "<div style='color:#c00;font-size:12px;'>Camera access failed: " + err.message + "</div>";
      }
    };

    captureBtn.onclick = function(){
      if(!stream){
        downDiv.innerHTML = "<div style='color:#c00;font-size:12px;'>Start camera first</div>";
        return;
      }
      canvas.width = v.videoWidth;
      canvas.height = v.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(v, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/jpeg', 0.95);

      // create download link
      const link = document.createElement('a');
      link.href = dataUrl;
      link.download = 'derma_capture.jpg';
      link.innerText = 'Download image (tap to save)';
      link.style.display = 'inline-block';
      link.style.marginTop = '8px';
      link.style.padding = '8px';
      link.style.background = '#D9B89C';
      link.style.color = '#333';
      link.style.borderRadius = '8px';
      link.style.textDecoration = 'none';
      downDiv.innerHTML = '';
      downDiv.appendChild(link);
    };
    </script>
    """
    components.html(camera_html, height=420)

    st.markdown("<div class='note'>After you 'Download image', open Photos/Files and Save. Then come back here and upload the saved image below.</div>", unsafe_allow_html=True)

    col_up, col_btn = st.columns([3,1])
    with col_up:
        uploaded = st.file_uploader("Upload saved high-resolution photo (recommended) or use camera input below", type=["jpg","jpeg","png"])
        st.markdown("<div class='small'>If you didn't save, you can use the basic camera input (lower-res fallback).</div>", unsafe_allow_html=True)
        cam_low = st.camera_input("Use device camera (lower-res fallback)")
    with col_btn:
        st.markdown("<div style='height:36px'></div>")
        analyze = st.button("Analyze")

    chosen = uploaded if uploaded is not None else cam_low
    if analyze:
        if chosen is None:
            st.error("Please upload the saved high-res photo or use the camera input.")
        else:
            raw = chosen.getvalue()
            img = Image.open(io.BytesIO(raw))
            img = enhance_image(img, sharpness=1.8, max_size=1400)
            st.image(img, caption="Processed (enhanced) image", use_column_width=True)

            b64 = image_to_b64(img)
            cfg = st.session_state.get("api_config", {"mode":"mock"})
            st.info("Running analysis..." if cfg.get("mode")!="mock" else "Demo analysis (mock mode).")
            status, resp = call_skin_api(b64, cfg)
            if status != 200:
                st.error(f"Analysis failed (status {status}): {resp}")
            else:
                def get_val(d, keys, default=None):
                    if not isinstance(d, dict): return default
                    for k in keys:
                        if k in d: return d[k]
                    return default
                hydration = get_val(resp, ["hydration","moisture"])
                acne = get_val(resp, ["acne_score","acne"])
                spots = get_val(resp, ["spots_score","spots"])
                pigmentation = get_val(resp, ["pigmentation_score","pigmentation"])
                notes = get_val(resp, ["notes","message","detail"], "")
                if isinstance(resp, dict) and all(k in resp for k in ["hydration","acne_score","spots_score","pigmentation_score"]):
                    hydration = resp["hydration"]; acne = resp["acne_score"]; spots = resp["spots_score"]; pigmentation = resp["pigmentation_score"]
                def to_pct(x):
                    if x is None: return None
                    if isinstance(x,(int,float)): return float(x)
                    s=str(x).lower()
                    if s in ["good","high","excellent"]: return 85.0
                    if s in ["medium","moderate"]: return 55.0
                    if s in ["low","poor","bad"]: return 20.0
                    try: return float(s)
                    except: return None
                h = to_pct(hydration); a = to_pct(acne); sp = to_pct(spots); pig = to_pct(pigmentation)
                st.markdown("<div class='card'><h4>Analysis Summary</h4></div>", unsafe_allow_html=True)
                cols = st.columns(4)
                items = [("Hydration", h, True), ("Acne (lower better)", 100-(a or 0), False), ("Spots (lower better)", 100-(sp or 0), False), ("Pigmentation", pig, False)]
                for (label, val, _), col in zip(items, cols):
                    if val is None:
                        col.write(f"**{label}**"); col.write("— no data —")
                    else:
                        v = max(0,min(100,val))
                        col.write(f"**{label}**"); col.progress(v/100.0); col.write(f"{int(v)} / 100")
                if notes:
                    st.markdown(f"**Notes:** {notes}")
                # optional: save to client
                if st.session_state.clients:
                    sel = st.selectbox("Save this analysis to client (optional)", ["-- none --"] + [c["name"] for c in st.session_state.clients])
                    if st.button("Save analysis to client"):
                        if sel == "-- none --":
                            st.warning("Choose a client to save.")
                        else:
                            for c in st.session_state.clients:
                                if c["name"] == sel:
                                    c.setdefault("analyses", []).append({"at": datetime.now().isoformat(), "hydration":h, "acne":a, "spots":sp, "pigmentation":pig})
                                    st.success(f"Saved analysis to {sel}")
                                    break

# ---- Export Data ----
elif page == "Export Data":
    st.markdown("<div class='card'><h3>Export Data</h3></div>", unsafe_allow_html=True)
    dfc = pd.DataFrame(st.session_state.clients)
    if not dfc.empty:
        st.write("Clients")
        st.dataframe(dfc)
        st.download_button("Download clients CSV", data=dfc.to_csv(index=False).encode('utf-8'), file_name="derma_clients.csv")
    else:
        st.info("No clients yet.")
    dfp = pd.DataFrame(st.session_state.products)
    st.write("Products")
    st.dataframe(dfp)
    st.download_button("Download products CSV", data=dfp.to_csv(index=False).encode('utf-8'), file_name="derma_products.csv")

# ---- Settings ----
elif page == "Settings":
    st.markdown("<div class='card'><h3>Settings</h3></div>", unsafe_allow_html=True)
    st.markdown("Configure skin-analysis API (optional). Keep demo (mock) mode if you don't have API keys.")
    mode = st.selectbox("API mode", ["mock","bearer_json","formdata_facepp"])
    if mode == "bearer_json":
        endpoint = st.text_input("Endpoint URL", value=st.session_state.api_config.get("endpoint",""))
        token = st.text_input("Bearer token", value=st.session_state.api_config.get("bearer_token",""))
        if st.button("Save bearer config"):
            st.session_state.api_config = {"mode":"bearer_json","endpoint":endpoint,"bearer_token":token}
            st.success("Saved bearer_json config")
    elif mode == "formdata_facepp":
        endpoint = st.text_input("Endpoint URL", value=st.session_state.api_config.get("endpoint",""))
        api_key = st.text_input("API Key", value=st.session_state.api_config.get("api_key",""))
        api_secret = st.text_input("API Secret", value=st.session_state.api_config.get("api_secret",""))
        if st.button("Save formdata config"):
            st.session_state.api_config = {"mode":"formdata_facepp","endpoint":endpoint,"api_key":api_key,"api_secret":api_secret}
            st.success("Saved formdata config")
    else:
        if st.button("Switch to Demo (mock) mode"):
            st.session_state.api_config = {"mode":"mock"}
            st.success("Switched to mock mode")
    cfg = st.session_state.get("api_config", {"mode":"mock"}).copy()
    if "bearer_token" in cfg: cfg["bearer_token"] = "●●●●"
    if "api_secret" in cfg: cfg["api_secret"] = "●●●●"
    st.write("Current API config (masked):", cfg)

# ---- End ----
st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
