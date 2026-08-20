import streamlit as st
import pandas as pd
import plotly.express as px
import pdfplumber
import os
import glob
import re

# 1. Konfigurasi Halaman & Folder Storage
st.set_page_config(page_title="PBD - SMK Dato' Syed Omar", layout="wide", page_icon="🎓")

DATA_DIR = "data_pbd"
os.makedirs(DATA_DIR, exist_ok=True)
ADMIN_PASSWORD = "admin123"

# Cari fail logo secara automatik
LOGO_PATH = None
for ext in ["png", "jpg", "jpeg", "PNG", "JPG", "JPEG"]:
    if os.path.exists(f"logo.{ext}"):
        LOGO_PATH = f"logo.{ext}"
        break

if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

# =========================================================
# GAYA CSS UTAMA
# =========================================================
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .school-title {
        font-size: 28px; font-weight: 800;
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;
    }
    .system-title { font-size: 15px; color: #475569; margin: 2px 0 0 0; }
    .profile-card {
        background: #ffffff; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border-left: 6px solid #2563eb; border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Header & Logo
col_logo, col_header = st.columns([1, 6])
with col_logo:
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=85)
    else:
        st.markdown("<h1 style='margin:0; text-align:center;'>🏫</h1>", unsafe_allow_html=True)
with col_header:
    st.markdown("""
        <h1 class="school-title">SMK DATO' SYED OMAR</h1>
        <p class="system-title">✨ Sistem Pelaporan & Pengurusan Data Pentaksiran Bilik Darjah (PBD)</p>
    """, unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# ENJIN PEMPROSESAN DATA KALIS-AGAL
# =========================================================
def extract_clean_ic(text):
    """Mengekstrak 12 digit IC daripada sebarang teks."""
    digits = re.sub(r'\D', '', str(text))
    matches = re.findall(r'\d{12}', digits)
    return matches[0] if matches else None

def parse_idme_file(uploaded_file):
    """Membaca fail PDF/CSV idMe dan mengekstrak rekod murid yang sah."""
    records = []
    
    if uploaded_file.name.endswith('.pdf'):
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if not row or not any(row):
                            continue
                        row_str = " ".join([str(c) for c in row if c])
                        if any(x in row_str.lower() for x in ['muka surat', 'disahkan', 'tarikh cetak', 'kementerian']):
                            continue
                        
                        ic = extract_clean_ic(row_str)
                        if ic:
                            clean_cells = [str(c).strip().replace('\n', ' ') for c in row if c]
                            nama = ""
                            for cell in clean_cells:
                                clean_c = re.sub(r'[^a-zA-L\s@/\']', '', cell).strip()
                                if len(clean_c) > 3 and not extract_clean_ic(cell):
                                    nama = clean_c
                                    break
                            
                            records.append({
                                'NO_KP': ic,
                                'NAMA': nama if nama else "MURID",
                                'RAW_ROW': row_str,
                                'CELLS': clean_cells
                            })
    else:
        df_raw = pd.read_csv(uploaded_file, dtype=str, keep_default_na=False)
        for _, row in df_raw.iterrows():
            row_str = " ".join([str(v) for v in row.values])
            ic = extract_clean_ic(row_str)
            if ic:
                nama = ""
                for v in row.values:
                    clean_v = re.sub(r'[^a-zA-L\s@/\']', '', str(v)).strip()
                    if len(clean_v) > 3 and not extract_clean_ic(v):
                        nama = clean_v
                        break
                records.append({
                    'NO_KP': ic,
                    'NAMA': nama if nama else "MURID",
                    'RAW_ROW': row_str,
                    'CELLS': [str(v) for v in row.values]
                })

    return pd.DataFrame(records) if records else None

def load_all_saved_data():
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not files: return None
    dfs = []
    for f in files:
        try:
            temp_df = pd.read_csv(f, dtype=str, keep_default_na=False)
            dfs.append(temp_df)
        except Exception: pass
    return pd.concat(dfs, ignore_index=True) if dfs else None

# =========================================================
# TAB UTAMA
# =========================================================
tab_utama, tab_pengurusan = st.tabs(["🔍 Semakan & Analisis PBD", "🔒 Pengurusan Data & Logo (Admin)"])

# ---------------------------------------------------------
# TAB ADMIN
# ---------------------------------------------------------
with tab_pengurusan:
    if not st.session_state['is_admin']:
        st.subheader("🔐 Log Masuk Pentadbir (Admin)")
        col_pass, _ = st.columns([1, 2])
        with col_pass:
            input_pass = st.text_input("Kata Laluan Admin:", type="password")
            if st.button("Log Masuk", type="primary"):
                if input_pass == ADMIN_PASSWORD:
                    st.session_state['is_admin'] = True
                    st.rerun()
                else: st.error("❌ Kata laluan salah.")
    else:
        c_title, c_logout = st.columns([4, 1])
        with c_title: st.subheader("⚙️ Panel Pengurusan Data Kelas & Logo")
        with c_logout:
            if st.button("🚪 Log Keluar Admin"):
                st.session_state['is_admin'] = False
                st.rerun()
                
        st.markdown("---")
        col_up1, col_up2 = st.columns([1, 1])
        
        with col_up1:
            st.markdown("### 1. Muat Naik Fail idMe Kelas")
            pilih_tingkatan = st.selectbox("Tingkatan:", ["Tingkatan 1", "Tingkatan 2", "Tingkatan 3", "Tingkatan 4", "Tingkatan 5"])
            nama_kelas = st.text_input("Nama Kelas (Contoh: 1 KRK 1 / 2 Amanah):", "")
            uploaded_file = st.file_uploader("Pilih Fail PDF / CSV idMe:", type=["pdf", "csv"])
            
            if uploaded_file is not None:
                parsed_df = parse_idme_file(uploaded_file)
                if parsed_df is not None and not parsed_df.empty:
                    st.success(f"✅ Dikesan **{len(parsed_df)} murid** dalam fail ini.")
                    st.markdown("**Pra-paparan Data Yang Dikesan:**")
                    
                    show_cols = [c for c in ['NAMA', 'NO_KP'] if c in parsed_df.columns]
                    st.dataframe(parsed_df[show_cols], use_container_width=True)
                    
                    if st.button("💾 Simpan Data Kelas Ini", type="primary"):
                        if not nama_kelas.strip():
                            st.error("Sila masukkan Nama Kelas dahulu.")
                        else:
                            parsed_df['Tingkatan_System'] = pilih_tingkatan
                            parsed_df['Kelas_System'] = nama_kelas.strip()
                            safe_fn = f"{pilih_tingkatan}_{nama_kelas.strip()}".replace(" ", "_").replace("/", "_") + ".csv"
                            parsed_df.to_csv(os.path.join(DATA_DIR, safe_fn), index=False, encoding='utf-8-sig')
                            st.success(f"✅ Data `{pilih_tingkatan} - {nama_kelas}` berjaya disimpan!")
                            st.rerun()
                else:
                    st.error("❌ Gagal mengekstrak No. KP murid daripada fail.")

            st.markdown("---")
            st.markdown("### 🖼️ Muat Naik Logo Sekolah")
            uploaded_logo = st.file_uploader("Pilih Fail Logo (PNG / JPG):", type=["png", "jpg", "jpeg"])
            if st.button("🖼️ Simpan Logo"):
                if uploaded_logo is not None:
                    ext = uploaded_logo.name.split('.')[-1]
                    for f in glob.glob("logo.*"): os.remove(f)
                    with open(f"logo.{ext}", "wb") as f: f.write(uploaded_logo.getbuffer())
                    st.success("✅ Logo dikemas kini!")
                    st.rerun()

        with col_up2:
            st.markdown("### 2. Data Kelas Tersimpan")
            files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
            if not files: st.info("Tiada data tersimpan dalam sistem.")
            else:
                info_list = []
                for fp in files:
                    fn = os.path.basename(fp).replace(".csv", "").replace("_", " ")
                    tdf = pd.read_csv(fp, dtype=str, keep_default_na=False)
                    info_list.append({"Kelas": fn, "Jumlah Rekod": len(tdf), "Path": fp})
                info_df = pd.DataFrame(info_list)
                st.dataframe(info_df[["Kelas", "Jumlah Rekod"]], use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 🗑️ Padam Data Kelas")
                pilih_padam = st.selectbox("Pilih Kelas Untuk Dipadam:", info_df["Kelas"].tolist())
                if st.button("❌ Padam Kelas Ini"):
                    pth = info_df[info_df["Kelas"] == pilih_padam]["Path"].values[0]
                    if os.path.exists(pth): os.remove(pth); st.rerun()

                if st.button("🔥 Padam Semua Data Lama (Reset Total)"):
                    for fp in files: os.remove(fp)
                    st.success("Semua data lama dibersihkan.")
                    st.rerun()

# ---------------------------------------------------------
# TAB SEMAKAN INDIVIDU
# ---------------------------------------------------------
with tab_utama:
    df_all = load_all_saved_data()
    
    if df_all is None or df_all.empty:
        st.warning("⚠️ **Tiada data tersimpan dalam sistem.** Sila muat naik data kelas di Tab Admin terlebih dahulu.")
    else:
        search_input = st.text_input("🔎 Masukkan No. Kad Pengenalan ATAU Nama Murid:", value="", placeholder="Contoh No. KP: 111013020847 ATAU Nama: MUHAMMAD ADAM").strip()
        matched_row = None
        search_digits = re.sub(r'\D', '', search_input)

        if search_input:
            # 1. Carian No. KP
            if len(search_digits) >= 6:
                for idx, row in df_all.iterrows():
                    row_str = " ".join([str(v) for v in row.values])
                    if search_digits in re.sub(r'\D', '', row_str):
                        matched_row = row
                        break

            # 2. Carian Nama Murid
            if matched_row is None and len(search_input) >= 3:
                for idx, row in df_all.iterrows():
                    row_str = " ".join([str(v) for v in row.values]).lower()
                    if search_input.lower() in row_str:
                        matched_row = row
                        break

        if search_input and matched_row is None:
            st.error(f"❌ Rekod murid `{search_input}` tidak dijumpai dalam pangkalan data.")
            with st.expander("🔍 Klik Di Sini Untuk Semak Senarai Data Tersimpan"):
                # PAPARAN KALIS-RALAT (Mencegah KeyError)
                available_cols = [c for c in ['NAMA', 'NO_KP', 'Kelas_System', 'Tingkatan_System'] if c in df_all.columns]
                if available_cols:
                    st.dataframe(df_all[available_cols], use_container_width=True)
                else:
                    st.dataframe(df_all, use_container_width=True)

        elif matched_row is not None:
            nama_m = matched_row.get('NAMA', next((v for v in matched_row.values if len(str(v)) > 3 and not str(v).isdigit()), "MURID"))
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

            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.metric("Status Rekod", "BERJAYA DIJUMPAI ✅")
                st.write(f"**No. Kad Pengenalan:** `{ic_m}`")
                st.write(f"**Nama Penuh:** `{nama_m}`")
            with col_b:
                st.success(" Rekod murid disahkan wujud dan tersimpan dengan selamat.")