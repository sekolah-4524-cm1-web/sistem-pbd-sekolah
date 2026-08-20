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

def parse_idme_file(uploaded_file):
    records = []
    
    if uploaded_file.name.lower().endswith('.pdf'):
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                
                # 1. PENGESANAN SLIP INDIVIDU IDME (NAMA DAN NO KP BERASINGAN)
                ic_matches = re.findall(r'(?:NO\.?\s*(?:KAD\s*PENGENALAN|KP|MYKID)|KAD\s*PENGENALAN)?\s*[:\.]?\s*(\d{6}[-\s]?\d{2}[-\s]?\d{4})', text, re.IGNORECASE)
                nama_matches = re.findall(r'NAMA(?:\s*MURID)?\s*[:\.]?\s*([A-Za-z@/\'\s\-]{3,60})', text, re.IGNORECASE)
                
                if ic_matches and nama_matches:
                    for ic_raw, nama_raw in zip(ic_matches, nama_matches):
                        ic = re.sub(r'\D', '', ic_raw)
                        clean_nama = re.sub(r'\b(NO|KP|KAD|PENGENALAN|MYKID|TINGKATAN|KELAS|SEKOLAH|PBD|TARIKH|JANTINA)\b.*', '', nama_raw, flags=re.IGNORECASE).strip()
                        clean_nama = re.sub(r'[^a-zA-Z\s@/\'\-]', '', clean_nama).strip()
                        records.append({'NO_KP': ic, 'NAMA': clean_nama.upper() if len(clean_nama) > 2 else "MURID"})
                    continue

                # 2. PENGESANAN JADUAL / SENARAI KELAS (BARIS TUNGGAL)
                lines = text.split('\n')
                for line in lines:
                    ic_match = re.search(r'\b\d{6}[-\s]?\d{2}[-\s]?\d{4}\b', line)
                    if ic_match:
                        ic = re.sub(r'\D', '', ic_match.group(0))
                        clean = re.sub(r'\b\d{6}[-\s]?\d{2}[-\s]?\d{4}\b', '', line)
                        clean = re.sub(r'[^a-zA-Z\s@/\'\-]', ' ', clean)
                        words = [w.strip() for w in clean.split() if len(w.strip()) > 1]
                        
                        ignored = ['BIL', 'LELAKI', 'PEREMPUAN', 'MELAYU', 'CINA', 'INDIA', 'ISLAM', 'KPM', 'PBD', 'MUKA', 'SURAT', 'TAHUN', 'TINGKATAN', 'NO', 'KAD', 'PENGENALAN', 'KP', 'MYKID', 'NAMA', 'MURID', 'KELAS', 'SEKOLAH']
                        name_words = [w for w in words if w.upper() not in ignored]
                        nama = " ".join(name_words) if name_words else "MURID"
                        records.append({'NO_KP': ic, 'NAMA': nama.upper()})
    else:
        df_raw = pd.read_csv(uploaded_file, dtype=str, keep_default_na=False)
        for _, row in df_raw.iterrows():
            row_str = " ".join([str(v) for v in row.values])
            ic_match = re.search(r'\b\d{6}[-\s]?\d{2}[-\s]?\d{4}\b', row_str)
            if ic_match:
                ic = re.sub(r'\D', '', ic_match.group(0))
                clean = re.sub(r'\b\d{6}[-\s]?\d{2}[-\s]?\d{4}\b', '', row_str)
                clean = re.sub(r'[^a-zA-Z\s@/\'\-]', ' ', clean)
                words = [w.strip() for w in clean.split() if len(w.strip()) > 1]
                ignored = ['BIL', 'LELAKI', 'PEREMPUAN', 'MELAYU', 'CINA', 'INDIA', 'ISLAM', 'KPM', 'PBD', 'NO', 'KAD', 'PENGENALAN', 'KP', 'MYKID', 'NAMA', 'MURID']
                name_words = [w for w in words if w.upper() not in ignored]
                nama = " ".join(name_words) if name_words else "MURID"
                records.append({'NO_KP': ic, 'NAMA': nama.upper()})

    if records:
        df_res = pd.DataFrame(records).drop_duplicates(subset=['NO_KP'], keep='first')
        return df_res
    return None

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

tab_utama, tab_pengurusan = st.tabs(["🔍 Semakan & Analisis PBD", "🔒 Pengurusan Data & Logo (Admin)"])

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
            st.markdown("**1. Muat Naik & Semak Fail idMe**")
            pilih_tingkatan = st.selectbox("Tingkatan:", ["Tingkatan 1", "Tingkatan 2", "Tingkatan 3", "Tingkatan 4", "Tingkatan 5"])
            nama_kelas = st.text_input("Nama Kelas (Contoh: 1 KRK 1):", "")
            uploaded_file = st.file_uploader("Pilih Fail PDF / CSV idMe:", type=["pdf", "csv"])
            
            if uploaded_file is not None:
                parsed_df = parse_idme_file(uploaded_file)
                if parsed_df is not None and not parsed_df.empty:
                    st.success(f"✅ {len(parsed_df)} rekod murid dikesan. Anda boleh menyunting Nama Penuh di bawah jika perlu:")
                    
                    # JADUAL INTERAKTIF UNTUK SEMAK/EDIT NAMA SEBELUM SIMPAN
                    edited_df = st.data_editor(
                        parsed_df,
                        column_config={
                            "NO_KP": st.column_config.TextColumn("No. Kad Pengenalan", required=True),
                            "NAMA": st.column_config.TextColumn("Nama Penuh Murid", required=True),
                        },
                        use_container_width=True,
                        num_rows="dynamic",
                        key="editor_pbd"
                    )
                    
                    if st.button("💾 Simpan Data Kelas Ini Secara Kekal", type="primary"):
                        if not nama_kelas.strip():
                            st.error("❌ Sila masukkan Nama Kelas dahulu.")
                        else:
                            edited_df['Tingkatan_System'] = pilih_tingkatan
                            edited_df['Kelas_System'] = nama_kelas.strip()
                            safe_fn = f"{pilih_tingkatan}_{nama_kelas.strip()}".replace(" ", "_").replace("/", "_") + ".csv"
                            file_path = os.path.join(DATA_DIR, safe_fn)
                            
                            edited_df.to_csv(file_path, index=False, encoding='utf-8-sig')
                            st.success(f"✅ Data kelas `{pilih_tingkatan} - {nama_kelas}` berjaya disimpan!")
                            time.sleep(1.5)
                            st.rerun()
                else:
                    st.error("❌ Gagal mengesan No. Kad Pengenalan daripada fail.")

            st.markdown("---")
            st.markdown("**🖼️ Muat Naik Logo Sekolah**")
            uploaded_logo = st.file_uploader("Pilih Fail Logo (PNG / JPG):", type=["png", "jpg", "jpeg"])
            if st.button("🖼️ Simpan Logo"):
                if uploaded_logo is not None:
                    ext = uploaded_logo.name.split('.')[-1]
                    for f in glob.glob("logo.*"): os.remove(f)
                    with open(f"logo.{ext}", "wb") as f: f.write(uploaded_logo.getbuffer())
                    st.success("✅ Logo dikemas kini!")
                    st.rerun()

        with col_up2:
            st.markdown("**2. Data Kelas Tersimpan**")
            files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
            if not files: st.info("Tiada data tersimpan.")
            else:
                info_list = []
                for fp in files:
                    fn = os.path.basename(fp).replace(".csv", "").replace("_", " ")
                    tdf = pd.read_csv(fp, dtype=str, keep_default_na=False)
                    info_list.append({"Kelas": fn, "Jumlah Murid": len(tdf)})
                info_df = pd.DataFrame(info_list)
                st.dataframe(info_df, use_container_width=True)
                
                st.markdown("---")
                st.markdown("**🗑️ Pembersihan Data**")
                if st.button("🔥 Padam Semua Fail (Reset Total)", type="secondary"):
                    for fp in files: os.remove(fp)
                    st.success("Semua data lama telah dibersihkan.")
                    st.rerun()

with tab_utama:
    df_all = load_all_saved_data()
    
    if df_all is None or df_all.empty:
        st.warning("⚠️ **Tiada data tersimpan dalam sistem.** Sila muat naik fail PDF di Tab Admin terlebih dahulu.")
    else:
        search_input = st.text_input("🔎 Masukkan No. Kad Pengenalan ATAU Nama Murid:", value="", placeholder="Contoh No. KP: 131005101143").strip()
        matched_row = None
        search_digits = re.sub(r'\D', '', search_input)

        if search_input:
            if len(search_digits) >= 6:
                for idx, row in df_all.iterrows():
                    db_ic = str(row.get('NO_KP', ''))
                    if search_digits in db_ic:
                        matched_row = row
                        break

            if matched_row is None and len(search_input) >= 3:
                for idx, row in df_all.iterrows():
                    db_nama = str(row.get('NAMA', '')).lower()
                    if search_input.lower() in db_nama:
                        matched_row = row
                        break

        if search_input and matched_row is None:
            st.error(f"❌ Rekod murid `{search_input}` tidak dijumpai.")
            with st.expander("🔍 Klik Di Sini Untuk Lihat Senarai Murid Yang Berjaya Disimpan"):
                cols = [c for c in ['NO_KP', 'NAMA', 'Kelas_System', 'Tingkatan_System'] if c in df_all.columns]
                st.dataframe(df_all[cols] if cols else df_all, use_container_width=True)

        elif matched_row is not None:
            nama_m = matched_row.get('NAMA', 'MURID')
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
                st.metric("Status Carian", "REKOD DIJUMPAI ✅")
                st.write(f"**No. Kad Pengenalan:** `{ic_m}`")
                st.write(f"**Nama Penuh:** `{nama_m}`")
            with col_b:
                st.success("Rekod murid disahkan wujud dan sedia dalam pangkalan data.")