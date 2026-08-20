import streamlit as st
import pandas as pd
import pdfplumber
import os
import glob
import re
import time

st.set_page_config(page_title="PBD - SMK Dato' Syed Omar", layout="wide", page_icon="🎓")

DATA_DIR = "data_pbd"
os.makedirs(DATA_DIR, exist_ok=True)
ADMIN_PASSWORD = "admin123"

LOGO_PATH = None
for ext in ["png", "jpg", "jpeg", "PNG", "JPG", "JPEG"]:
    if os.path.exists(f"logo.{ext}"):
        LOGO_PATH = f"logo.{ext}"
        break

if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .school-title { font-size: 28px; font-weight: 800; background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; }
    .system-title { font-size: 15px; color: #475569; margin: 2px 0 0 0; }
    .profile-card { background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); border-left: 6px solid #2563eb; border: 1px solid #e2e8f0; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

col_logo, col_header = st.columns([1, 6])
with col_logo:
    if LOGO_PATH and os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=85)
    else: st.markdown("<h1 style='margin:0; text-align:center;'>🏫</h1>", unsafe_allow_html=True)
with col_header:
    st.markdown("<h1 class='school-title'>SMK DATO' SYED OMAR</h1><p class='system-title'>✨ Sistem Pelaporan & Pengurusan Data PBD</p>", unsafe_allow_html=True)

st.markdown("---")

def extract_ic(text):
    match = re.search(r'\b\d{6}[-\s]?\d{2}[-\s]?\d{4}\b', str(text))
    return re.sub(r'\D', '', match.group()) if match else None

def clean_name(text, ic_str):
    clean = str(text).replace(ic_str, '')
    clean = re.sub(r'[^a-zA-Z\s/]', ' ', clean)
    words = [w.strip().upper() for w in clean.split() if len(w.strip()) > 1]
    ignored = ['LELAKI', 'PEREMPUAN', 'ISLAM', 'MELAYU', 'CINA', 'INDIA', 'BUMIPUTERA', 'KPM', 'PBD', 'NAMA', 'MURID', 'TINGKATAN', 'KELAS', 'NO', 'KAD', 'PENGENALAN', 'MYKID', 'TARIKH', 'TAHUN', 'MUKA', 'SURAT', 'SEKOLAH']
    name_words = [w for w in words if w not in ignored]
    nama = " ".join(name_words[:7]).strip()
    return nama if len(nama) > 3 else "SILA EDIT NAMA" # Tukar dari MURID

def parse_data_file(uploaded_file):
    records = []
    if uploaded_file.name.lower().endswith('.csv'):
        df = pd.read_csv(uploaded_file, dtype=str, keep_default_na=False)
        for _, row in df.iterrows():
            row_str = " ".join([str(v) for v in row.values])
            ic = extract_ic(row_str)
            if ic: records.append({'NO_KP': ic, 'NAMA': clean_name(row_str, ic)})
            
    elif uploaded_file.name.lower().endswith('.pdf'):
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            row_str = " ".join([str(cell) for cell in row if cell])
                            ic = extract_ic(row_str)
                            if ic: records.append({'NO_KP': ic, 'NAMA': clean_name(row_str, ic)})
                if not records:
                    text = page.extract_text() or ""
                    lines = text.split('\n')
                    for i, line in enumerate(lines):
                        ic = extract_ic(line)
                        if ic and not any(r['NO_KP'] == ic for r in records):
                            context = line
                            if i > 0: context += " " + lines[i-1]
                            if i < len(lines)-1: context += " " + lines[i+1]
                            records.append({'NO_KP': ic, 'NAMA': clean_name(context, ic)})

    if records:
        return pd.DataFrame(records).drop_duplicates(subset=['NO_KP'], keep='first')
    return None

def load_all_saved_data():
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not files: return None
    dfs = [pd.read_csv(f, dtype=str, keep_default_na=False) for f in files]
    return pd.concat(dfs, ignore_index=True) if dfs else None

tab_utama, tab_pengurusan = st.tabs(["🔍 Semakan PBD", "🔒 Admin (Pengurusan Data)"])

with tab_pengurusan:
    if not st.session_state['is_admin']:
        st.subheader("🔐 Log Masuk Pentadbir")
        c_pass, _ = st.columns([1, 2])
        with c_pass:
            input_pass = st.text_input("Kata Laluan:", type="password")
            if st.button("Log Masuk", type="primary"):
                if input_pass == ADMIN_PASSWORD:
                    st.session_state['is_admin'] = True; st.rerun()
                else: st.error("❌ Kata laluan salah.")
    else:
        st.subheader("⚙️ Panel Pengurusan")
        if st.button("🚪 Log Keluar"): st.session_state['is_admin'] = False; st.rerun()
        st.markdown("---")
        
        c_up1, c_up2 = st.columns([1, 1])
        with c_up1:
            st.markdown("**1. Muat Naik Data Kelas**")
            pilih_tg = st.selectbox("Tingkatan:", ["Tingkatan 1", "Tingkatan 2", "Tingkatan 3", "Tingkatan 4", "Tingkatan 5"])
            nama_kelas = st.text_input("Nama Kelas:", "")
            uploaded_file = st.file_uploader("Pilih Fail (PDF / CSV):", type=["pdf", "csv"])
            
            if uploaded_file:
                parsed_df = parse_data_file(uploaded_file)
                if parsed_df is not None and not parsed_df.empty:
                    st.warning("⚠️ **TINDAKAN DIPERLUKAN:** Jika nama dipaparkan sebagai 'SILA EDIT NAMA', klik pada kotak tersebut dan taip nama sebenar pelajar sebelum menekan butang Simpan.")
                    
                    edited_df = st.data_editor(parsed_df, use_container_width=True, hide_index=True)
                    
                    if st.button("💾 Simpan Data Ini", type="primary"):
                        if not nama_kelas.strip(): st.error("Masukkan Nama Kelas.")
                        else:
                            edited_df['Tingkatan_System'] = pilih_tg
                            edited_df['Kelas_System'] = nama_kelas.strip()
                            safe_fn = f"{pilih_tg}_{nama_kelas.strip()}".replace(" ", "_").replace("/", "_") + ".csv"
                            edited_df.to_csv(os.path.join(DATA_DIR, safe_fn), index=False)
                            st.success("✅ Berjaya Disimpan!"); time.sleep(1); st.rerun()
                else: st.error("Tiada data dikesan.")

        with c_up2:
            st.markdown("**2. Data Tersimpan**")
            files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
            if not files: st.info("Tiada data.")
            else:
                for f in files: st.write(f"- {os.path.basename(f).replace('.csv', '')}")
                if st.button("🔥 Reset (Padam Semua Data)"):
                    for f in files: os.remove(f)
                    st.rerun()

with tab_utama:
    df_all = load_all_saved_data()
    if df_all is None or df_all.empty:
        st.warning("⚠️ Tiada data dalam sistem.")
    else:
        search_input = st.text_input("🔎 Masukkan No. KP / Nama:", placeholder="Contoh: 131005101143").strip()
        matched_row = None
        s_digits = re.sub(r'\D', '', search_input)

        if search_input:
            for _, row in df_all.iterrows():
                if (s_digits and s_digits in str(row.get('NO_KP', ''))) or (len(search_input) > 2 and search_input.lower() in str(row.get('NAMA', '')).lower()):
                    matched_row = row
                    break
                    
        if search_input and matched_row is None: st.error("❌ Rekod tidak dijumpai.")
        elif matched_row is not None:
            nama_m = matched_row.get('NAMA', 'TIADA MAKLUMAT')
            ic_m = matched_row.get('NO_KP', search_digits)
            tingkatan_m = matched_row.get('Tingkatan_System', '-')
            kelas_m = matched_row.get('Kelas_System', '-')

            st.markdown(f"""
            <div class="profile-card">
                <span style="color: #2563eb; font-size: 11px; font-weight: 800; letter-spacing: 1px;">PROFIL PENTAKSIRAN INDIVIDU — SMK DATO' SYED OMAR</span>
                <h2 style="margin: 4px 0; color: #0f172a; font-size: 22px;">{nama_m}</h2>
                <p style="margin: 0; font-size: 14px; color: #475569;">Tingkatan / Kelas: <b>{tingkatan_m} ({kelas_m})</b> &nbsp;|&nbsp; No. KP: <b>{ic_m}</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            # MENGEMBALIKAN PAPARAN LENGKAP YANG HILANG
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.metric("Status Carian", "REKOD DIJUMPAI ✅")
                st.write(f"**No. Kad Pengenalan:** `{ic_m}`")
                st.write(f"**Nama Penuh:** `{nama_m}`")
            with col_b:
                st.success("Rekod murid disahkan wujud dan sedia dalam pangkalan data.")