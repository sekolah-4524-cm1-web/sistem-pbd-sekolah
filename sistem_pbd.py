import streamlit as st
import pandas as pd
import plotly.express as px
import pdfplumber
import os
import glob
import re
import base64

# 1. Konfigurasi Halaman & Folder Storage Setempat
st.set_page_config(page_title="PBD - SMK Dato' Syed Omar", layout="wide", page_icon="🎓")

DATA_DIR = "data_pbd"
os.makedirs(DATA_DIR, exist_ok=True)

ADMIN_PASSWORD = "admin123"

# Cari fail logo secara automatik (png, jpg, jpeg)
LOGO_PATH = None
for ext in ["png", "jpg", "jpeg", "PNG", "JPG", "JPEG"]:
    if os.path.exists(f"logo.{ext}"):
        LOGO_PATH = f"logo.{ext}"
        break

if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

# =========================================================
# FUNGSI TUKAR IMEJ KEPADA BASE64 UNTUK HTML
# =========================================================
def get_base64_image(image_path):
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception:
            return None
    return None

# =========================================================
# SUNTIKAN GAYA CSS PREMIUM
# =========================================================
st.markdown("""
    <style>
    .stApp {
        background-color: #f8fafc;
    }
    
    .header-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 40%, #1e3a8a 100%);
        padding: 24px 30px;
        border-radius: 20px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.15);
        margin-bottom: 28px;
        display: flex;
        align-items: center;
        gap: 20px;
    }
    
    .school-title {
        font-size: 30px;
        font-weight: 800;
        letter-spacing: 0.5px;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    }
    
    .system-title {
        font-size: 16px;
        color: #e2e8f0;
        font-weight: 500;
        margin-top: 6px;
        margin-bottom: 0;
        letter-spacing: 0.3px;
    }

    .profile-card {
        background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.06);
        border-left: 6px solid #3b82f6;
        border-top: 1px solid #e2e8f0;
        border-right: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 25px;
    }
    
    .profile-tag {
        color: #3b82f6;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }

    .pbd-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background-color: white;
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        border: 1px solid #e2e8f0;
    }
    .pbd-table th {
        background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
        color: #ffffff;
        padding: 16px;
        font-weight: 600;
        font-size: 14px;
        text-align: left;
    }
    .pbd-table td {
        padding: 14px 16px;
        border-bottom: 1px solid #f1f5f9;
        color: #334155;
        font-size: 14px;
    }
    .pbd-table tr:hover { background-color: #f8fafc; }

    .badge {
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 700;
        color: white;
        display: inline-block;
        font-size: 12px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.12);
    }
    .badge-tp6 { background: linear-gradient(135deg, #059669, #10b981); }
    .badge-tp5 { background: linear-gradient(135deg, #16a34a, #22c55e); }
    .badge-tp4 { background: linear-gradient(135deg, #2563eb, #3b82f6); }
    .badge-tp3 { background: linear-gradient(135deg, #d97706, #f59e0b); color: #fff; }
    .badge-tp2 { background: linear-gradient(135deg, #ea580c, #f97316); }
    .badge-tp1 { background: linear-gradient(135deg, #dc2626, #ef4444); }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 10px 20px;
        border: 1px solid #e2e8f0;
        font-weight: 600;
        color: #64748b;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# BANNER HEADER & LOGO SEKOLAH
# =========================================================
logo_b64 = get_base64_image(LOGO_PATH)

if logo_b64:
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="80" style="border-radius: 10px; padding: 4px; background: rgba(255, 255, 255, 0.95); box-shadow: 0 4px 10px rgba(0,0,0,0.15); max-height: 80px; object-fit: contain;">'
else:
    logo_html = '<div style="background: rgba(255,255,255,0.15); border-radius: 14px; width: 75px; height: 75px; display: flex; align-items: center; justify-content: center; font-size: 35px;">🏫</div>'

st.markdown(f"""
<div class="header-banner">
    <div style="flex-shrink: 0;">
        {logo_html}
    </div>
    <div>
        <h1 class="school-title">SMK DATO' SYED OMAR</h1>
        <p class="system-title">✨ Sistem Pelaporan & Pengurusan Data Pentaksiran Bilik Darjah (PBD)</p>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# FUNGSI PEMBANTU & PEMBERSIHAN DATA ULTRAROBUST
# =========================================================
KATA_KUNCI_BUKAN_SUBJEK = [
    'bil', 'bil.', 'no', 'no.', 'nama', 'ic', 'kp', 'no kp', 'no. kp', 'no.kp', 'nokp',
    'tingkatan', 'kelas', 'jantina', 'kaum', 'bangsa', 'agregat', 'jumlah', 'purata'
]

def clean_cell_string(val):
    """Menukar nilai sel kepada teks bersih tanpa format saintifik."""
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip()
    if 'e+' in s.lower() or 'e-' in s.lower():
        try:
            s = f"{float(s):.0f}"
        except Exception:
            pass
    elif s.endswith('.0'):
        s = s[:-2]
    return s

def dapatkan_tafsiran_tp(tp_val):
    tafsiran = {
        6: ("Cemerlang / Tahu, Faham & Boleh Meneladani", "badge-tp6"),
        5: ("Sangat Baik / Tahu, Faham & Boleh Buat dengan Adab Terpuji", "badge-tp5"),
        4: ("Baik / Tahu, Faham & Boleh Buat Beradab", "badge-tp4"),
        3: ("Memuaskan / Tahu, Faham & Boleh Buat", "badge-tp3"),
        2: ("Tahap Minimum / Tahu & Faham", "badge-tp2"),
        1: ("Perlu Bimbingan / Tahu Sahaja", "badge-tp1")
    }
    return tafsiran.get(int(tp_val), ("Tidak Nyata", "badge-tp3"))

def bersihkan_df_murid(df):
    if df is None or df.empty:
        return df
    return df.dropna(how='all').copy()

def read_pdf_to_dataframe(pdf_file):
    all_rows = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if any(row):
                        clean_row = [str(cell).replace('\n', ' ').strip() if cell else "" for cell in row]
                        all_rows.append(clean_row)
    if not all_rows:
        return None
    max_cols = max(len(r) for r in all_rows)
    normalized_rows = [r + [""] * (max_cols - len(r)) for r in all_rows]
    header_idx = 0
    for idx, row in enumerate(normalized_rows[:15]):
        row_str = " ".join(row).lower()
        if any(k in row_str for k in ['nama', 'kp', 'ic', 'kad pengenalan', 'mykad', 'nokp']):
            header_idx = idx
            break
    raw_header = normalized_rows[header_idx]
    header = []
    for i, col in enumerate(raw_header):
        col_name = col.strip() if col.strip() else f"Lajur_{i+1}"
        if col_name in header:
            col_name = f"{col_name}_{i+1}"
        header.append(col_name)
    df_pdf = pd.DataFrame(normalized_rows[header_idx+1:], columns=header)
    return bersihkan_df_murid(df_pdf)

def load_all_saved_data():
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not files:
        return None
    dfs = []
    for f in files:
        try:
            temp_df = pd.read_csv(f, dtype=str, keep_default_na=False, encoding='utf-8-sig')
            temp_df = bersihkan_df_murid(temp_df)
            dfs.append(temp_df)
        except Exception:
            pass
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return None

# =========================================================
# TAB UTAMA
# =========================================================
tab_utama, tab_pengurusan = st.tabs(["🔍 Semakan & Analisis PBD", "🔒 Pengurusan Data & Logo (Admin)"])

# ---------------------------------------------------------
# TAB 2: PENGURUSAN DATA KEKAL & LOGO (ADMIN ONLY)
# ---------------------------------------------------------
with tab_pengurusan:
    if not st.session_state['is_admin']:
        st.subheader("🔐 Pengesahan Pentadbir (Admin)")
        st.info("Bahagian ini terhad kepada Pentadbir Sistem sahaja untuk muat naik data atau logo sekolah.")
        col_pass, _ = st.columns([1, 2])
        with col_pass:
            input_pass = st.text_input("Masukkan Kata Laluan Admin:", type="password")
            if st.button("Log Masuk Admin", type="primary"):
                if input_pass == ADMIN_PASSWORD:
                    st.session_state['is_admin'] = True
                    st.success("✅ Log masuk berjaya!")
                    st.rerun()
                else:
                    st.error("❌ Kata laluan salah. Sila cuba lagi.")
    else:
        c_title, c_logout = st.columns([4, 1])
        with c_title:
            st.subheader("📥 Pengurusan Data PBD Kelas & Logo Sekolah")
        with c_logout:
            if st.button("🚪 Log Keluar Admin"):
                st.session_state['is_admin'] = False
                st.rerun()
                
        st.markdown("---")
        col_up1, col_up2 = st.columns([1, 1])
        with col_up1:
            st.markdown("**1. Muat Naik Data PBD Kelas**")
            pilih_tingkatan = st.selectbox("Pilih Tingkatan:", ["Tingkatan 1", "Tingkatan 2", "Tingkatan 3", "Tingkatan 4", "Tingkatan 5"])
            nama_kelas = st.text_input("Nama Kelas (Contoh: 1 KRK 1 / 2 Amanah):", "")
            uploaded_file = st.file_uploader("Pilih Fail PDF / CSV (idMe):", type=["pdf", "csv"])
            
            if st.button("💾 Simpan Data Kelas", type="primary"):
                if not nama_kelas.strip():
                    st.error("Sila masukkan Nama Kelas terlebih dahulu.")
                elif uploaded_file is None:
                    st.error("Sila muat naik fail PDF atau CSV.")
                else:
                    try:
                        if uploaded_file.name.endswith('.pdf'):
                            df_upload = read_pdf_to_dataframe(uploaded_file)
                        else:
                            df_upload = pd.read_csv(uploaded_file, dtype=str, keep_default_na=False, encoding='utf-8-sig')
                            df_upload = bersihkan_df_murid(df_upload)
                            
                        if df_upload is not None and not df_upload.empty:
                            df_upload.columns = [str(c).strip().replace('\n', ' ') for c in df_upload.columns]
                            df_upload['Tingkatan_System'] = pilih_tingkatan
                            df_upload['Kelas_System'] = nama_kelas.strip()
                            
                            safe_filename = f"{pilih_tingkatan}_{nama_kelas.strip()}".replace(" ", "_").replace("/", "_") + ".csv"
                            file_path = os.path.join(DATA_DIR, safe_filename)
                            
                            df_upload.to_csv(file_path, index=False, encoding='utf-8-sig')
                            st.success(f"✅ Data `{pilih_tingkatan} - {nama_kelas}` berjaya disimpan ({len(df_upload)} murid)!")
                            st.rerun()
                        else:
                            st.error("Gagal membaca kandungan fail. Sila semak format PDF/CSV.")
                    except Exception as e:
                        st.error(f"Ralat semasa menyimpan: {e}")

            st.markdown("---")
            st.markdown("**🖼️ Muat Naik / Kemas Kini Logo Sekolah**")
            uploaded_logo = st.file_uploader("Pilih Fail Logo Sekolah (PNG / JPG):", type=["png", "jpg", "jpeg"])
            if st.button("🖼️ Simpan Logo Sekolah"):
                if uploaded_logo is not None:
                    ext = uploaded_logo.name.split('.')[-1]
                    logo_save_path = f"logo.{ext}"
                    with open(logo_save_path, "wb") as f:
                        f.write(uploaded_logo.getbuffer())
                    st.success("✅ Logo sekolah berjaya dikemas kini!")
                    st.rerun()
                else:
                    st.error("Sila pilih fail imej logo dahulu.")

        with col_up2:
            st.markdown("**2. Senarai Data Tersimpan Dalam Sistem**")
            fail_tersimpan = glob.glob(os.path.join(DATA_DIR, "*.csv"))
            if not fail_tersimpan:
                st.info("Belum ada data disimpan dalam sistem.")
            else:
                senarai_info = []
                for filepath in fail_tersimpan:
                    fname = os.path.basename(filepath).replace(".csv", "").replace("_", " ")
                    temp_df = pd.read_csv(filepath, dtype=str, keep_default_na=False, encoding='utf-8-sig')
                    temp_df = bersihkan_df_murid(temp_df)
                    senarai_info.append({
                        "Fail / Kelas": fname,
                        "Jumlah Murid": len(temp_df),
                        "Path": filepath
                    })
                info_df = pd.DataFrame(senarai_info)
                info_df.index = range(1, len(info_df) + 1)
                st.dataframe(info_df[["Fail / Kelas", "Jumlah Murid"]], use_container_width=True)
                st.markdown("---")
                st.markdown("**🗑️ Padam Data Kelas**")
                pilih_padam = st.selectbox("Pilih Kelas Untuk Dipadam:", info_df["Fail / Kelas"].tolist())
                if st.button("❌ Padam Data Kelas Ini", type="secondary"):
                    path_to_delete = info_df[info_df["Fail / Kelas"] == pilih_padam]["Path"].values[0]
                    if os.path.exists(path_to_delete):
                        os.remove(path_to_delete)
                        st.success(f"Data `{pilih_padam}` telah dipadam secara kekal.")
                        st.rerun()

# ---------------------------------------------------------
# TAB 1: SEMAKAN & ANALISIS PBD INDIVIDU
# ---------------------------------------------------------
with tab_utama:
    df_all = load_all_saved_data()
    
    if df_all is None or df_all.empty:
        st.warning("⚠️ **Tiada data tersimpan.** Hubungi Admin untuk muat naik data kelas terlebih dahulu di Tab 'Pengurusan Data & Logo'.")
    else:
        search_input = st.text_input(
            "🔎 Masukkan No. Kad Pengenalan ATAU Nama Murid:",
            value="",
            placeholder="Contoh No. KP: 110616020075 ATAU Nama: MUHAMMAD ADAM"
        ).strip()

        matched_row = None
        search_digits = re.sub(r'\D', '', search_input)

        # LOGIK CARIAN ULTRAROBUST (DIGIT & TEKS SEJAJAT)
        if search_input:
            for idx, row in df_all.iterrows():
                # Gabungkan seluruh kandungan baris menjadi satu teks & satu rentetan digit
                row_raw_list = [clean_cell_string(val) for val in row.values]
                row_full_str = " ".join(row_raw_list)
                row_full_digits = re.sub(r'\D', '', row_full_str)

                # 1. Padanan Berdasarkan Digit IC (Sekiranya pengguna memasukkan sekurang-kurangnya 6 digit)
                if search_digits and len(search_digits) >= 6:
                    if search_digits in row_full_digits:
                        matched_row = row
                        break

                # 2. Padanan Berdasarkan Teks Nama Murid
                if len(search_input) >= 3 and search_input.lower() in row_full_str.lower():
                    matched_row = row
                    break

        if search_input and matched_row is None:
            st.error(f"❌ Rekod murid `{search_input}` tidak dijumpai dalam sistem SMK Dato' Syed Omar.")
            
            with st.expander("🔍 Semak Senarai Data Yang Dikesan Dalam Sistem"):
                st.write("Semak senarai penuh data yang wujud dalam pangkalan data tersimpan:")
                preview_list = []
                for _, r in df_all.iterrows():
                    row_vals = [clean_cell_string(v) for v in r.values]
                    # Cari Nama
                    nama_tmp = next((v for v in row_vals if len(v) > 3 and not v.isdigit()), "Murid")
                    # Cari IC (12 digit atau terdekat)
                    ic_tmp = next((v for v in row_vals if len(re.sub(r'\D', '', v)) >= 10), "-")
                    preview_list.append({"Nama Murid": nama_tmp, "No. IC Dikesan": ic_tmp, "Kelas": r.get('Kelas_System', '-')})
                st.dataframe(pd.DataFrame(preview_list), use_container_width=True)

        elif matched_row is not None:
            row_clean_vals = [clean_cell_string(val) for val in matched_row.values]

            # Ekstrak Nama Murid
            nama_murid = ""
            for col, val in matched_row.items():
                if any(k in str(col).lower() for k in ['nama', 'student', 'murid', 'name']):
                    s_val = clean_cell_string(val)
                    if s_val and s_val.lower() not in ['nan', 'none']:
                        nama_murid = s_val
                        break
            if not nama_murid:
                best_text = ""
                for col, val in matched_row.items():
                    if col in ['Tingkatan_System', 'Kelas_System']:
                        continue
                    s_val = clean_cell_string(val)
                    if len(s_val) > len(best_text) and not re.search(r'\d', s_val):
                        best_text = s_val
                nama_murid = best_text if best_text else "Murid"

            # Ekstrak No. KP Paparan
            ic_display = "-"
            for v in row_clean_vals:
                d = re.sub(r'\D', '', v)
                if len(d) in [11, 12]:
                    ic_display = d
                    break
            if ic_display == "-" and search_digits:
                ic_display = search_digits

            tingkatan_murid = matched_row.get('Tingkatan_System', '-')
            kelas_murid = matched_row.get('Kelas_System', '-')

            # Tapis Subjek & TP
            senarai_subjek = []
            for col in df_all.columns:
                col_clean = str(col).lower().strip()
                is_metadata = any(col_clean == k or col_clean.startswith('lajur_') for k in KATA_KUNCI_BUKAN_SUBJEK)
                if not is_metadata and col not in ['Tingkatan_System', 'Kelas_System']:
                    senarai_subjek.append(col)

            tp_series = matched_row[senarai_subjek]
            tp_data = tp_series.reset_index()
            tp_data.columns = ['Subjek', 'TP_Raw']

            tp_data['TP'] = tp_data['TP_Raw'].astype(str).str.extract(r'(\d+)')[0]
            tp_data = tp_data.dropna(subset=['TP'])
            tp_data['TP'] = tp_data['TP'].astype(int)
            tp_data = tp_data[(tp_data['TP'] >= 1) & (tp_data['TP'] <= 6)]
            tp_data['TP_Str'] = "TP " + tp_data['TP'].astype(str)

            total_subjek = len(tp_data)
            tp_cemerlang = len(tp_data[tp_data['TP'] >= 5])
            tp_perlu_perhatian = len(tp_data[tp_data['TP'] <= 2])

            st.markdown(f"""
<div class="profile-card">
    <span class="profile-tag">PROFIL PENTAKSIRAN INDIVIDU — SMK DATO' SYED OMAR</span>
    <h2 style="margin: 6px 0; color: #0f172a; font-size: 26px; font-weight: 700;">{nama_murid}</h2>
    <p style="margin: 0; font-size: 15px; color: #475569;">Tingkatan / Kelas: <b style="color: #1e293b;">{tingkatan_murid} ({kelas_murid})</b> &nbsp;|&nbsp; No. KP: <b style="color: #1e293b;">{ic_display}</b></p>
</div>
""", unsafe_allow_html=True)

            m1, m2, m3, m4 = st.columns(4)
            with m1: st.metric("Jumlah Subjek Dinilai", f"{total_subjek} Subjek")
            with m2: st.metric("Subjek Penguasaan Tinggi (TP 5-6)", f"{tp_cemerlang} Subjek")
            with m3: st.metric("Subjek Bimbingan (TP 1-2)", f"{tp_perlu_perhatian} Subjek")
            with m4:
                tp_max = tp_data['TP'].max() if not tp_data.empty else 0
                st.metric("Pencapaian TP Tertinggi", f"TP {tp_max}")

            st.markdown("---")
            col_graf, col_jadual = st.columns([10, 12])

            with col_graf:
                st.subheader("📊 Pencapaian TP Mengikut Subjek")
                color_map = {
                    'TP 6': '#10b981', 
                    'TP 5': '#22c55e', 
                    'TP 4': '#3b82f6', 
                    'TP 3': '#f59e0b', 
                    'TP 2': '#f97316', 
                    'TP 1': '#ef4444'
                }
                fig_bar = px.bar(tp_data, x='TP', y='Subjek', orientation='h', text='TP_Str', color='TP_Str', color_discrete_map=color_map, title="Skor TP Bagi Setiap Subjek")
                fig_bar.update_layout(xaxis=dict(range=[0, 6.5], dtick=1, title="Tahap Penguasaan (TP)"), yaxis=dict(title="", categoryorder='total ascending'), showlegend=False, height=450)
                fig_bar.update_traces(textposition='outside')
                st.plotly_chart(fig_bar, use_container_width=True)

            with col_jadual:
                st.subheader("📋 Senarai Pencapaian Setiap Subjek")
                rows_html = ""
                for _, row in tp_data.iterrows():
                    subjek_name = row['Subjek']
                    tp_val = row['TP']
                    tafsiran_txt, badge_cls = dapatkan_tafsiran_tp(tp_val)
                    rows_html += f"<tr><td><b>{subjek_name}</b></td><td style='text-align: center;'><span class='badge {badge_cls}'>TP {tp_val}</span></td><td style='font-size: 13px; color: #475569;'>{tafsiran_txt}</td></tr>"
                st.markdown(f"<table class='pbd-table'><thead><tr><th style='width: 32%;'>Subjek</th><th style='width: 23%; text-align: center;'>Tahap Penguasaan</th><th style='width: 45%;'>Tafsiran & Status</th></tr></thead><tbody>{rows_html}</tbody></table>", unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("📈 Analisis Taburan Penguasaan Murid")
            c_pie, c_analisis = st.columns([1, 1])
            with c_pie:
                taburan_tp = tp_data['TP_Str'].value_counts().reset_index()
                taburan_tp.columns = ['TP_Str', 'Bilangan']
                fig_pie = px.pie(taburan_tp, values='Bilangan', names='TP_Str', hole=0.45, title="Nisbah Taburan TP Keseluruhan Subjek", color='TP_Str', color_discrete_map=color_map)
                st.plotly_chart(fig_pie, use_container_width=True)
            with c_analisis:
                st.markdown("#### Ringkasan Analisis Pentaksiran")
                subjek_tinggi = tp_data[tp_data['TP'] >= 5]['Subjek'].tolist()
                subjek_rendah = tp_data[tp_data['TP'] <= 2]['Subjek'].tolist()
                if subjek_tinggi:
                    st.success(f"🌟 **Kekuatan:** Murid menonjol dalam **{len(subjek_tinggi)}** subjek ({', '.join(subjek_tinggi)}).")
                else:
                    st.info("ℹ️ Tiada subjek mencapai TP 5 atau TP 6 buat masa ini.")
                if subjek_rendah:
                    st.error(f"⚠️ **Saranan Intervensi:** Bimbingan khusus diperlukan bagi **{len(subjek_rendah)}** subjek ({', '.join(subjek_rendah)}).")
                else:
                    st.success("✅ **Prestasi Baik:** Semua subjek telah melepasi Tahap Penguasaan Minimum (TP 3 dan ke atas).")