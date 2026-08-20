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

# Cari fail logo secara automatik dalam direktori
LOGO_PATH = None
for ext in ["png", "jpg", "jpeg", "PNG", "JPG", "JPEG"]:
    if os.path.exists(f"logo.{ext}"):
        LOGO_PATH = f"logo.{ext}"
        break

if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

# =========================================================
# GAYA CSS & HEADER
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
        border-left: 6px solid #2563eb; border-top: 1px solid #e2e8f0;
        border-right: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    .pbd-table {
        width: 100%; border-collapse: separate; border-spacing: 0;
        background-color: white; border-radius: 10px; overflow: hidden;
        border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .pbd-table th { background: #0f172a; color: #ffffff; padding: 12px 14px; font-weight: 600; font-size: 13px; }
    .pbd-table td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; color: #334155; font-size: 13px; }
    .badge { padding: 4px 12px; border-radius: 14px; font-weight: 700; color: white; display: inline-block; font-size: 11px; }
    .badge-tp6 { background: #059669; } .badge-tp5 { background: #16a34a; }
    .badge-tp4 { background: #2563eb; } .badge-tp3 { background: #d97706; }
    .badge-tp2 { background: #ea580c; } .badge-tp1 { background: #dc2626; }
    </style>
""", unsafe_allow_html=True)

# Paparan Header & Logo Native Streamlit
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
# FUNGSI PEMBANTU & EKSTRAKSI JITU
# =========================================================
KATA_KUNCI_METADATA = ['bil', 'bil.', 'no', 'no.', 'nama', 'ic', 'kp', 'nokp', 'tingkatan', 'kelas', 'jantina', 'kaum', '_ic_clean_']

def clean_text(val):
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip()
    if 'e+' in s.lower() or 'e-' in s.lower():
        try: s = f"{float(s):.0f}"
        except Exception: pass
    elif s.endswith('.0'): s = s[:-2]
    return s

def extract_12_digit_ic(row_values):
    """Mengekstrak 12 digit IC jitu daripada mana-mana sel dalam baris."""
    for val in row_values:
        cleaned = clean_text(val)
        digits = re.sub(r'\D', '', cleaned)
        if len(digits) == 12:
            return digits
    concat_digits = re.sub(r'\D', '', " ".join([clean_text(v) for v in row_values]))
    match = re.findall(r'\d{12}', concat_digits)
    return match[0] if match else ""

def read_pdf_to_dataframe(pdf_file):
    all_rows = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if row and any(row):
                        clean_row = [clean_text(c) for c in row]
                        all_rows.append(clean_row)
    if not all_rows:
        return None

    # Cari baris header utama
    header_idx = -1
    for idx, row in enumerate(all_rows[:20]):
        row_str = " ".join(row).lower()
        if ('nama' in row_str or 'murid' in row_str) and ('kp' in row_str or 'ic' in row_str or 'nokp' in row_str or 'pengenalan' in row_str):
            header_idx = idx
            break
            
    if header_idx == -1: header_idx = 0
    raw_header = all_rows[header_idx]
    
    header = []
    for i, col in enumerate(raw_header):
        c_name = col.strip() if col.strip() else f"Lajur_{i+1}"
        if c_name in header: c_name = f"{c_name}_{i+1}"
        header.append(c_name)

    data_rows = all_rows[header_idx+1:]
    valid_student_rows = []
    max_cols = len(header)

    # TAPISAN JITU: Hanya ambil baris yang mempunyai 12-digit IC sah sahaja!
    for r in data_rows:
        row_str = " ".join(r).lower()
        if 'muka surat' in row_str or 'tarikh cetak' in row_str or 'disahkan' in row_str:
            continue
        
        ic_val = extract_12_digit_ic(r)
        if ic_val:
            if len(r) < max_cols: r = r + [""] * (max_cols - len(r))
            elif len(r) > max_cols: r = r[:max_cols]
            r.append(ic_val)  # Tambah IC bersih di hujung baris
            valid_student_rows.append(r)

    if not valid_student_rows:
        return None

    full_header = header + ['_IC_CLEAN_']
    return pd.DataFrame(valid_student_rows, columns=full_header)

def load_all_saved_data():
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not files: return None
    dfs = []
    for f in files:
        try:
            temp_df = pd.read_csv(f, dtype=str, keep_default_na=False, encoding='utf-8-sig')
            dfs.append(temp_df)
        except Exception: pass
    return pd.concat(dfs, ignore_index=True) if dfs else None

def dapatkan_tafsiran_tp(tp_val):
    tafsiran = {
        6: ("Cemerlang / Tahu, Faham & Boleh Meneladani", "badge-tp6"),
        5: ("Sangat Baik / Tahu, Faham & Boleh Buat Beradab Terpuji", "badge-tp5"),
        4: ("Baik / Tahu, Faham & Boleh Buat Beradab", "badge-tp4"),
        3: ("Memuaskan / Tahu, Faham & Boleh Buat", "badge-tp3"),
        2: ("Tahap Minimum / Tahu & Faham", "badge-tp2"),
        1: ("Perlu Bimbingan / Tahu Sahaja", "badge-tp1")
    }
    return tafsiran.get(int(tp_val), ("Tidak Nyata", "badge-tp3"))

# =========================================================
# TAB UTAMA
# =========================================================
tab_utama, tab_pengurusan = st.tabs(["🔍 Semakan & Analisis PBD", "🔒 Pengurusan Data & Logo (Admin)"])

# ---------------------------------------------------------
# TAB ADMIN
# ---------------------------------------------------------
with tab_pengurusan:
    if not st.session_state['is_admin']:
        st.subheader("🔐 Log Masuk Pentadbir")
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
        with c_title: st.subheader("⚙️ Panel Pengurusan Data & Logo")
        with c_logout:
            if st.button("🚪 Log Keluar"):
                st.session_state['is_admin'] = False
                st.rerun()
                
        st.markdown("---")
        col_up1, col_up2 = st.columns([1, 1])
        
        with col_up1:
            st.markdown("### 1. Muat Naik Data PBD Kelas")
            pilih_tingkatan = st.selectbox("Tingkatan:", ["Tingkatan 1", "Tingkatan 2", "Tingkatan 3", "Tingkatan 4", "Tingkatan 5"])
            nama_kelas = st.text_input("Nama Kelas (Contoh: 1 KRK 1):", "")
            uploaded_file = st.file_uploader("Fail PDF / CSV idMe:", type=["pdf", "csv"])
            
            if st.button("💾 Simpan Data Kelas", type="primary"):
                if not nama_kelas.strip() or uploaded_file is None:
                    st.error("Sila lengkapkan Nama Kelas dan muat naik fail.")
                else:
                    try:
                        if uploaded_file.name.endswith('.pdf'):
                            df_upload = read_pdf_to_dataframe(uploaded_file)
                        else:
                            df_raw = pd.read_csv(uploaded_file, dtype=str, keep_default_na=False, encoding='utf-8-sig')
                            ic_list = [extract_12_digit_ic(r.values) for _, r in df_raw.iterrows()]
                            df_raw['_IC_CLEAN_'] = ic_list
                            df_upload = df_raw[df_raw['_IC_CLEAN_'] != ""].copy()
                            
                        if df_upload is not None and not df_upload.empty:
                            df_upload['Tingkatan_System'] = pilih_tingkatan
                            df_upload['Kelas_System'] = nama_kelas.strip()
                            safe_fn = f"{pilih_tingkatan}_{nama_kelas.strip()}".replace(" ", "_").replace("/", "_") + ".csv"
                            df_upload.to_csv(os.path.join(DATA_DIR, safe_fn), index=False, encoding='utf-8-sig')
                            st.success(f"✅ Data `{pilih_tingkatan} - {nama_kelas}` disimpan ({len(df_upload)} murid sah)!")
                            st.rerun()
                        else:
                            st.error("Gagal mengekstrak data murid sah. Sila semak fail PDF/CSV.")
                    except Exception as e: st.error(f"Ralat: {e}")

            st.markdown("---")
            st.markdown("### 🖼️ Muat Naik Logo Sekolah")
            uploaded_logo = st.file_uploader("Pilih Fail Logo (PNG/JPG):", type=["png", "jpg", "jpeg"])
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
            if not files: st.info("Tiada data tersimpan.")
            else:
                info_list = []
                for fp in files:
                    fn = os.path.basename(fp).replace(".csv", "").replace("_", " ")
                    tdf = pd.read_csv(fp, dtype=str, keep_default_na=False)
                    info_list.append({"Kelas": fn, "Jumlah Murid Sah": len(tdf), "Path": fp})
                info_df = pd.DataFrame(info_list)
                st.dataframe(info_df[["Kelas", "Jumlah Murid Sah"]], use_container_width=True)
                
                st.markdown("---")
                pilih_padam = st.selectbox("Padam Data Kelas:", info_df["Kelas"].tolist())
                if st.button("❌ Padam Kelas Ini"):
                    pth = info_df[info_df["Kelas"] == pilih_padam]["Path"].values[0]
                    if os.path.exists(pth): os.remove(pth); st.rerun()

# ---------------------------------------------------------
# TAB SEMAKAN
# ---------------------------------------------------------
with tab_utama:
    df_all = load_all_saved_data()
    
    if df_all is None or df_all.empty:
        st.warning("⚠️ **Tiada data tersimpan.** Sila ke Tab Admin untuk muat naik data kelas.")
    else:
        search_input = st.text_input("🔎 Masukkan No. Kad Pengenalan ATAU Nama Murid:", value="", placeholder="Contoh: 111013020847 ATAU MUHAMMAD ADAM").strip()
        matched_row = None
        search_digits = re.sub(r'\D', '', search_input)

        if search_input:
            # 1. Carian tepat menggunakan digit IC bersih
            if len(search_digits) >= 6:
                for idx, row in df_all.iterrows():
                    row_ic = str(row.get('_IC_CLEAN_', ''))
                    if search_digits in row_ic:
                        matched_row = row
                        break

            # 2. Carian berasaskan Nama sekiranya tiada padanan IC
            if matched_row is None and len(search_input) >= 3:
                for idx, row in df_all.iterrows():
                    row_str = " ".join([clean_text(v) for v in row.values]).lower()
                    if search_input.lower() in row_str:
                        matched_row = row
                        break

        if search_input and matched_row is None:
            st.error(f"❌ Rekod murid `{search_input}` tidak dijumpai.")
            with st.expander("🔍 Lihat Senarai Rekod Murid Yang Sah Dalam Sistem"):
                show_list = []
                for _, r in df_all.iterrows():
                    r_vals = [clean_text(v) for k, v in r.items() if k != '_IC_CLEAN_']
                    nama_f = next((v for v in r_vals if len(v) > 3 and not v.isdigit()), "Murid")
                    show_list.append({"Nama": nama_f, "No. IC": r.get('_IC_CLEAN_', '-'), "Kelas": r.get('Kelas_System', '-')})
                st.dataframe(pd.DataFrame(show_list), use_container_width=True)

        elif matched_row is not None:
            r_vals = [clean_text(v) for k, v in matched_row.items() if k not in ['_IC_CLEAN_', 'Tingkatan_System', 'Kelas_System']]
            
            # Ekstrak Nama
            nama_murid = ""
            for col, val in matched_row.items():
                if any(k in str(col).lower() for k in ['nama', 'student', 'murid', 'name']):
                    s = clean_text(val)
                    if s and s.lower() not in ['nan', 'none']: nama_murid = s; break
            if not nama_murid:
                nama_murid = next((v for v in r_vals if len(v) > 3 and not re.search(r'\d', v)), "Murid")

            ic_display = matched_row.get('_IC_CLEAN_', search_digits)
            tingkatan_m = matched_row.get('Tingkatan_System', '-')
            kelas_m = matched_row.get('Kelas_System', '-')

            # Ekstrak Subjek & TP
            senarai_subjek = []
            for col in df_all.columns:
                col_c = str(col).lower().strip()
                if not any(col_c == k or col_c.startswith('lajur_') for k in KATA_KUNCI_METADATA) and col not in ['Tingkatan_System', 'Kelas_System']:
                    senarai_subjek.append(col)

            tp_data = matched_row[senarai_subjek].reset_index()
            tp_data.columns = ['Subjek', 'TP_Raw']
            tp_data['TP'] = tp_data['TP_Raw'].astype(str).str.extract(r'(\d+)')[0]
            tp_data = tp_data.dropna(subset=['TP'])
            tp_data['TP'] = tp_data['TP'].astype(int)
            tp_data = tp_data[(tp_data['TP'] >= 1) & (tp_data['TP'] <= 6)]
            tp_data['TP_Str'] = "TP " + tp_data['TP'].astype(str)

            st.markdown(f"""
            <div class="profile-card">
                <span style="color: #2563eb; font-size: 11px; font-weight: 800; letter-spacing: 1px;">PROFIL PENTAKSIRAN INDIVIDU — SMK DATO' SYED OMAR</span>
                <h2 style="margin: 4px 0; color: #0f172a; font-size: 22px;">{nama_murid}</h2>
                <p style="margin: 0; font-size: 14px; color: #475569;">Tingkatan / Kelas: <b>{tingkatan_m} ({kelas_m})</b> &nbsp;|&nbsp; No. KP: <b>{ic_display}</b></p>
            </div>
            """, unsafe_allow_html=True)

            m1, m2, m3, m4 = st.columns(4)
            with m1: st.metric("Jumlah Subjek", f"{len(tp_data)} Subjek")
            with m2: st.metric("TP Tinggi (5-6)", f"{len(tp_data[tp_data['TP'] >= 5])} Subjek")
            with m3: st.metric("TP Bimbingan (1-2)", f"{len(tp_data[tp_data['TP'] <= 2])} Subjek")
            with m4: st.metric("TP Tertinggi", f"TP {tp_data['TP'].max() if not tp_data.empty else 0}")

            st.markdown("---")
            col_graf, col_jadual = st.columns([10, 12])

            color_map = {'TP 6': '#059669', 'TP 5': '#16a34a', 'TP 4': '#2563eb', 'TP 3': '#d97706', 'TP 2': '#ea580c', 'TP 1': '#dc2626'}

            with col_graf:
                st.subheader("📊 Grafik Tahap Penguasaan")
                fig_bar = px.bar(tp_data, x='TP', y='Subjek', orientation='h', text='TP_Str', color='TP_Str', color_discrete_map=color_map)
                fig_bar.update_layout(xaxis=dict(range=[0, 6.5], dtick=1), yaxis=dict(categoryorder='total ascending'), showlegend=False, height=420)
                st.plotly_chart(fig_bar, use_container_width=True)

            with col_jadual:
                st.subheader("📋 Perincian Subjek")
                rows_h = ""
                for _, r in tp_data.iterrows():
                    txt, cls = dapatkan_tafsiran_tp(r['TP'])
                    rows_h += f"<tr><td><b>{r['Subjek']}</b></td><td style='text-align:center;'><span class='badge {cls}'>TP {r['TP']}</span></td><td style='font-size:12px;'>{txt}</td></tr>"
                st.markdown(f"<table class='pbd-table'><thead><tr><th>Subjek</th><th style='text-align:center;'>TP</th><th>Tafsiran</th></tr></thead><tbody>{rows_h}</tbody></table>", unsafe_allow_html=True)