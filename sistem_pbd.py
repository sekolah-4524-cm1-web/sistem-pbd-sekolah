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
# SUNTIKAN GAYA CSS PREMIUM
# =========================================================
st.markdown("""
    <style>
    .stApp {
        background-color: #f8fafc;
    }
    
    .header-box {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #1e3a8a 100%);
        padding: 20px 25px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
    }
    
    .school-title {
        font-size: 28px;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .system-title {
        font-size: 15px;
        color: #e2e8f0;
        margin-top: 4px;
        margin-bottom: 0;
    }

    .profile-card {
        background: #ffffff;
        padding: 22px;
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border-left: 6px solid #2563eb;
        border-top: 1px solid #e2e8f0;
        border-right: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }

    .pbd-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background-color: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.04);
        border: 1px solid #e2e8f0;
    }
    .pbd-table th {
        background: #1e293b;
        color: #ffffff;
        padding: 14px;
        font-weight: 600;
        font-size: 14px;
        text-align: left;
    }
    .pbd-table td {
        padding: 12px 14px;
        border-bottom: 1px solid #f1f5f9;
        color: #334155;
        font-size: 14px;
    }

    .badge {
        padding: 5px 14px;
        border-radius: 18px;
        font-weight: 700;
        color: white;
        display: inline-block;
        font-size: 12px;
    }
    .badge-tp6 { background: #059669; }
    .badge-tp5 { background: #16a34a; }
    .badge-tp4 { background: #2563eb; }
    .badge-tp3 { background: #d97706; }
    .badge-tp2 { background: #ea580c; }
    .badge-tp1 { background: #dc2626; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# BANNER HEADER & LOGO SEKOLAH (STREAMLIT NATIVE)
# =========================================================
with st.container():
    col_l, col_r = st.columns([1, 6])
    with col_l:
        if LOGO_PATH and os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=90)
        else:
            st.markdown("<h1 style='text-align:center; margin:0;'>🏫</h1>", unsafe_allow_html=True)
    with col_r:
        st.markdown("""
        <div style="padding-top: 5px;">
            <h1 class="school-title">SMK DATO' SYED OMAR</h1>
            <p class="system-title">✨ Sistem Pelaporan & Pengurusan Data Pentaksiran Bilik Darjah (PBD)</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# FUNGSI PEMBANTU & PEMBERSIHAN DATA ULTRAROBUST
# =========================================================
KATA_KUNCI_BUKAN_SUBJEK = [
    'bil', 'bil.', 'no', 'no.', 'nama', 'ic', 'kp', 'no kp', 'no. kp', 'no.kp', 'nokp',
    'tingkatan', 'kelas', 'jantina', 'kaum', 'bangsa', 'agregat', 'jumlah', 'purata'
]

def clean_val(val):
    """Membersihkan sebarang format nombor/saintifik/sempang."""
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

def extract_pure_digits(val):
    """Mengambil digit sahaja daripada teks."""
    return re.sub(r'\D', '', clean_val(val))

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

def read_pdf_to_dataframe(pdf_file):
    all_rows = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if any(row):
                        clean_row = [clean_val(cell) for cell in row]
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
    return df_pdf.dropna(how='all')

def load_all_saved_data():
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not files:
        return None
    dfs = []
    for f in files:
        try:
            temp_df = pd.read_csv(f, dtype=str, keep_default_na=False, encoding='utf-8-sig')
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
# TAB 2: PENGURUSAN DATA & LOGO (ADMIN)
# ---------------------------------------------------------
with tab_pengurusan:
    if not st.session_state['is_admin']:
        st.subheader("🔐 Pengesahan Pentadbir (Admin)")
        col_pass, _ = st.columns([1, 2])
        with col_pass:
            input_pass = st.text_input("Masukkan Kata Laluan Admin:", type="password")
            if st.button("Log Masuk Admin", type="primary"):
                if input_pass == ADMIN_PASSWORD:
                    st.session_state['is_admin'] = True
                    st.success("✅ Log masuk berjaya!")
                    st.rerun()
                else:
                    st.error("❌ Kata laluan salah.")
    else:
        c_title, c_logout = st.columns([4, 1])
        with c_title:
            st.subheader("⚙️ Panel Pentadbir Sistem")
        with c_logout:
            if st.button("🚪 Log Keluar Admin"):
                st.session_state['is_admin'] = False
                st.rerun()
                
        st.markdown("---")
        col_up1, col_up2 = st.columns([1, 1])
        
        with col_up1:
            st.markdown("### 1. Muat Naik Data PBD Kelas")
            pilih_tingkatan = st.selectbox("Pilih Tingkatan:", ["Tingkatan 1", "Tingkatan 2", "Tingkatan 3", "Tingkatan 4", "Tingkatan 5"])
            nama_kelas = st.text_input("Nama Kelas (Contoh: 1 KRK 1 / 2 Amanah):", "")
            uploaded_file = st.file_uploader("Pilih Fail PDF / CSV (idMe):", type=["pdf", "csv"])
            
            if st.button("💾 Simpan Data Kelas", type="primary"):
                if not nama_kelas.strip():
                    st.error("Sila masukkan Nama Kelas.")
                elif uploaded_file is None:
                    st.error("Sila muat naik fail PDF atau CSV.")
                else:
                    try:
                        if uploaded_file.name.endswith('.pdf'):
                            df_upload = read_pdf_to_dataframe(uploaded_file)
                        else:
                            df_upload = pd.read_csv(uploaded_file, dtype=str, keep_default_na=False, encoding='utf-8-sig')
                            
                        if df_upload is not None and not df_upload.empty:
                            df_upload.columns = [str(c).strip().replace('\n', ' ') for c in df_upload.columns]
                            df_upload['Tingkatan_System'] = pilih_tingkatan
                            df_upload['Kelas_System'] = nama_kelas.strip()
                            
                            safe_filename = f"{pilih_tingkatan}_{nama_kelas.strip()}".replace(" ", "_").replace("/", "_") + ".csv"
                            file_path = os.path.join(DATA_DIR, safe_filename)
                            
                            df_upload.to_csv(file_path, index=False, encoding='utf-8-sig')
                            st.success(f"✅ Data `{pilih_tingkatan} - {nama_kelas}` berjaya disimpan ({len(df_upload)} rekod)!")
                            st.rerun()
                        else:
                            st.error("Fail kosong atau gagal dibaca.")
                    except Exception as e:
                        st.error(f"Ralat: {e}")

            st.markdown("---")
            st.markdown("### 🖼️ Muat Naik Logo Sekolah")
            uploaded_logo = st.file_uploader("Pilih Fail Gambar Logo (PNG/JPG):", type=["png", "jpg", "jpeg"])
            if st.button("🖼️ Simpan Logo"):
                if uploaded_logo is not None:
                    ext = uploaded_logo.name.split('.')[-1]
                    for old_file in glob.glob("logo.*"):
                        os.remove(old_file)
                    with open(f"logo.{ext}", "wb") as f:
                        f.write(uploaded_logo.getbuffer())
                    st.success("✅ Logo sekolah berjaya dikemas kini!")
                    st.rerun()

        with col_up2:
            st.markdown("### 2. Data Kelas Tersimpan")
            fail_tersimpan = glob.glob(os.path.join(DATA_DIR, "*.csv"))
            if not fail_tersimpan:
                st.info("Tiada data tersimpan.")
            else:
                senarai_info = []
                for filepath in fail_tersimpan:
                    fname = os.path.basename(filepath).replace(".csv", "").replace("_", " ")
                    temp_df = pd.read_csv(filepath, dtype=str, keep_default_na=False, encoding='utf-8-sig')
                    senarai_info.append({
                        "Fail / Kelas": fname,
                        "Jumlah Murid": len(temp_df),
                        "Path": filepath
                    })
                info_df = pd.DataFrame(senarai_info)
                st.dataframe(info_df[["Fail / Kelas", "Jumlah Murid"]], use_container_width=True)
                
                st.markdown("---")
                st.markdown("### 🗑️ Padam Data Kelas")
                pilih_padam = st.selectbox("Pilih Kelas Untuk Dipadam:", info_df["Fail / Kelas"].tolist())
                if st.button("❌ Padam Data Kelas Ini"):
                    path_to_delete = info_df[info_df["Fail / Kelas"] == pilih_padam]["Path"].values[0]
                    if os.path.exists(path_to_delete):
                        os.remove(path_to_delete)
                        st.success(f"Data `{pilih_padam}` dipadam.")
                        st.rerun()

# ---------------------------------------------------------
# TAB 1: SEMAKAN INDIVIDU
# ---------------------------------------------------------
with tab_utama:
    df_all = load_all_saved_data()
    
    if df_all is None or df_all.empty:
        st.warning("⚠️ **Tiada data dalam sistem.** Sila muat naik data di Tab Admin dahulu.")
    else:
        search_input = st.text_input(
            "🔎 Masukkan No. Kad Pengenalan ATAU Nama Murid:",
            value="",
            placeholder="Contoh No. KP: 111013020847 ATAU Nama: MUHAMMAD ADAM"
        ).strip()

        matched_row = None
        search_digits = extract_pure_digits(search_input)

        # LOGIK CARIAN TEPAT & SEJAJAT
        if search_input:
            for idx, row in df_all.iterrows():
                # Gabungkan seluruh kandungan sel dalam baris ini
                row_cells = [clean_val(v) for v in row.values]
                row_digits_concat = "".join([extract_pure_digits(v) for v in row_cells])
                row_text_concat = " ".join(row_cells).lower()

                # 1. Carian Digit IC (Jika pengguna taip sekurang-kurangnya 6 digit)
                if len(search_digits) >= 6 and search_digits in row_digits_concat:
                    matched_row = row
                    break

                # 2. Carian Teks Nama
                if len(search_input) >= 3 and search_input.lower() in row_text_concat:
                    matched_row = row
                    break

        if search_input and matched_row is None:
            st.error(f"❌ Rekod murid `{search_input}` tidak dijumpai dalam sistem SMK Dato' Syed Omar.")
            
            with st.expander("🔍 Klik Di Sini Untuk Semak Kandungan Data Yang Ada Dalam Sistem"):
                st.write("Senarai penuh rekod yang berjaya dibaca daripada fail tersimpan:")
                debug_list = []
                for _, r in df_all.iterrows():
                    r_vals = [clean_val(v) for v in r.values]
                    
                    # Cari Nama & IC
                    nama_found = next((v for v in r_vals if len(v) > 3 and not v.isdigit()), "Tanda Nama")
                    ic_found = next((extract_pure_digits(v) for v in r_vals if len(extract_pure_digits(v)) >= 10), "Tiada IC Dikesan")
                    
                    debug_list.append({
                        "Nama Dikesan": nama_found,
                        "No. IC Dikesan": ic_found,
                        "Kelas": r.get('Kelas_System', '-')
                    })
                st.dataframe(pd.DataFrame(debug_list), use_container_width=True)

        elif matched_row is not None:
            row_cells = [clean_val(v) for v in matched_row.values]

            # Dapatkan Nama Murid
            nama_murid = ""
            for col, val in matched_row.items():
                if any(k in str(col).lower() for k in ['nama', 'student', 'murid', 'name']):
                    s_val = clean_val(val)
                    if s_val and s_val.lower() not in ['nan', 'none']:
                        nama_murid = s_val
                        break
            if not nama_murid:
                nama_murid = next((v for v in row_cells if len(v) > 3 and not re.search(r'\d', v)), "Murid")

            # Dapatkan IC
            ic_display = next((extract_pure_digits(v) for v in row_cells if len(extract_pure_digits(v)) in [11, 12]), search_digits if search_digits else "-")

            tingkatan_murid = matched_row.get('Tingkatan_System', '-')
            kelas_murid = matched_row.get('Kelas_System', '-')

            # Extrak Subjek & TP
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
    <span style="color: #2563eb; font-size: 12px; font-weight: 800; letter-spacing: 1px;">PROFIL PENTAKSIRAN INDIVIDU — SMK DATO' SYED OMAR</span>
    <h2 style="margin: 6px 0; color: #0f172a; font-size: 24px; font-weight: 700;">{nama_murid}</h2>
    <p style="margin: 0; font-size: 14px; color: #475569;">Tingkatan / Kelas: <b style="color: #1e293b;">{tingkatan_murid} ({kelas_murid})</b> &nbsp;|&nbsp; No. KP: <b style="color: #1e293b;">{ic_display}</b></p>
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
                    'TP 6': '#059669', 
                    'TP 5': '#16a34a', 
                    'TP 4': '#2563eb', 
                    'TP 3': '#d97706', 
                    'TP 2': '#ea580c', 
                    'TP 1': '#dc2626'
                }
                fig_bar = px.bar(tp_data, x='TP', y='Subjek', orientation='h', text='TP_Str', color='TP_Str', color_discrete_map=color_map)
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
                fig_pie = px.pie(taburan_tp, values='Bilangan', names='TP_Str', hole=0.45, title="Nisbah Taburan TP Keseluruhan", color='TP_Str', color_discrete_map=color_map)
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