import streamlit as st
import pandas as pd
import plotly.express as px
import pdfplumber
import os
import glob
import re

# 1. Konfigurasi Halaman & Folder Storage Setempat
st.set_page_config(page_title="Sistem Pengurusan & Analisis PBD", layout="wide")

DATA_DIR = "data_pbd"
os.makedirs(DATA_DIR, exist_ok=True)

ADMIN_PASSWORD = "admin123"

if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

# --- SUNTIKAN GAYA CSS PREMIUM ---
st.markdown("""
    <style>
    .profile-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 22px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        border-left: 6px solid #1a73e8;
        margin-bottom: 25px;
    }
    .pbd-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background-color: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .pbd-table th {
        background-color: #f1f3f4;
        color: #3c4043;
        padding: 14px;
        font-weight: 700;
        text-align: left;
        border-bottom: 2px solid #dadce0;
    }
    .pbd-table td {
        padding: 12px 14px;
        border-bottom: 1px solid #f1f3f5;
        color: #343a40;
    }
    .pbd-table tr:hover { background-color: #f8f9fa; }
    .badge {
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        color: white;
        display: inline-block;
        font-size: 13px;
        text-align: center;
        min-width: 60px;
    }
    .badge-tp6 { background-color: #0d904f; }
    .badge-tp5 { background-color: #34a853; }
    .badge-tp4 { background-color: #1a73e8; }
    .badge-tp3 { background-color: #fbbc04; color: #333; }
    .badge-tp2 { background-color: #e67c73; }
    .badge-tp1 { background-color: #d93025; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='color: #1a73e8;'>Sistem Pelaporan & Pengurusan Data PBD</h1>", unsafe_allow_html=True)
st.markdown("---")

# =========================================================
# FUNGSI PEMBANTU & PEMBERSIHAN DATA
# =========================================================
KATA_KUNCI_BUKAN_SUBJEK = [
    'bil', 'bil.', 'no', 'no.', 'nama', 'ic', 'kp', 'no kp', 'no. kp', 'no.kp', 'nokp',
    'tingkatan', 'kelas', 'jantina', 'kaum', 'bangsa', 'agregat', 'jumlah', 'purata'
]

def clean_ic(val):
    """Nyahformat perpuluhan/notasi saintifik kepada rentetan digit bersih."""
    if pd.isna(val) or val is None:
        return ""
    s = str(val).strip()
    if s.endswith('.0'):
        s = s[:-2]
    if 'e+' in s.lower() or 'e-' in s.lower():
        try:
            s = f"{float(s):.0f}"
        except Exception:
            pass
    return re.sub(r'\D', '', s)

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
    df = df.dropna(how='all').copy()
    col_ref = df.columns[0]
    for c in df.columns:
        c_lower = str(c).lower().strip()
        if any(k in c_lower for k in ['nama', 'ic', 'kp', 'kad pengenalan', 'nokp', 'mykad']):
            col_ref = c
            break

    kata_kunci_header = ['nama murid', 'kad pengenalan', 'no. kp', 'no kp', 'nokp', 'mykad', 'bil.', 'jumlah', 'purata']
    def is_student_row(val):
        s = str(val).lower().strip()
        if not s or s in ['nan', 'none', '']:
            return False
        if any(s == k for k in kata_kunci_header):
            return False
        return True
    return df[df[col_ref].apply(is_student_row)].copy()

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
            temp_df = pd.read_csv(f, dtype=str)
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
tab_utama, tab_pengurusan = st.tabs(["🔍 Semakan & Analisis PBD", "🔒 Pengurusan Data (Admin Only)"])

# ---------------------------------------------------------
# TAB 2: PENGURUSAN DATA KEKAL (ADMIN ONLY)
# ---------------------------------------------------------
with tab_pengurusan:
    if not st.session_state['is_admin']:
        st.subheader("🔐 Pengesahan Pentadbir (Admin)")
        st.info("Bahagian ini terhad kepada Pentadbir Sistem sahaja untuk muat naik atau memadam data.")
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
            st.subheader("📥 Muat Naik & Memadam Data PBD Kelas")
        with c_logout:
            if st.button("🚪 Log Keluar Admin"):
                st.session_state['is_admin'] = False
                st.rerun()
                
        st.markdown("---")
        col_up1, col_up2 = st.columns([1, 1])
        with col_up1:
            st.markdown("**1. Maklumat Kelas & Fail Baru**")
            pilih_tingkatan = st.selectbox("Pilih Tingkatan:", ["Tingkatan 1", "Tingkatan 2", "Tingkatan 3", "Tingkatan 4", "Tingkatan 5"])
            nama_kelas = st.text_input("Nama Kelas (Contoh: 1 KRK 1 / 2 Amanah):", "")
            uploaded_file = st.file_uploader("Pilih Fail PDF / CSV (idMe):", type=["pdf", "csv"])
            
            if st.button("💾 Simpan Data Secara Kekal", type="primary"):
                if not nama_kelas.strip():
                    st.error("Sila masukkan Nama Kelas terlebih dahulu.")
                elif uploaded_file is None:
                    st.error("Sila muat naik fail PDF atau CSV.")
                else:
                    try:
                        if uploaded_file.name.endswith('.pdf'):
                            df_upload = read_pdf_to_dataframe(uploaded_file)
                        else:
                            df_upload = pd.read_csv(uploaded_file, dtype=str)
                            df_upload = bersihkan_df_murid(df_upload)
                            
                        if df_upload is not None and not df_upload.empty:
                            df_upload.columns = [str(c).strip().replace('\n', ' ') for c in df_upload.columns]
                            df_upload['Tingkatan_System'] = pilih_tingkatan
                            df_upload['Kelas_System'] = nama_kelas.strip()
                            
                            safe_filename = f"{pilih_tingkatan}_{nama_kelas.strip()}".replace(" ", "_").replace("/", "_") + ".csv"
                            file_path = os.path.join(DATA_DIR, safe_filename)
                            
                            df_upload.to_csv(file_path, index=False)
                            st.success(f"✅ Data `{pilih_tingkatan} - {nama_kelas}` berjaya disimpan ({len(df_upload)} murid)!")
                            st.rerun()
                        else:
                            st.error("Gagal membaca kandungan fail. Sila semak format PDF/CSV.")
                    except Exception as e:
                        st.error(f"Ralat semasa menyimpan: {e}")

        with col_up2:
            st.markdown("**2. Senarai Data Tersimpan Dalam Sistem**")
            fail_tersimpan = glob.glob(os.path.join(DATA_DIR, "*.csv"))
            if not fail_tersimpan:
                st.info("Belum ada data disimpan dalam sistem.")
            else:
                senarai_info = []
                for filepath in fail_tersimpan:
                    fname = os.path.basename(filepath).replace(".csv", "").replace("_", " ")
                    temp_df = pd.read_csv(filepath, dtype=str)
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
# TAB 1: SEMAKAN & ANALISIS PBD INDIVIDU (MANUAL INPUT ONLY)
# ---------------------------------------------------------
with tab_utama:
    df_all = load_all_saved_data()
    
    if df_all is None or df_all.empty:
        st.warning("⚠️ **Tiada data tersimpan.** Hubungi Admin untuk muat naik data kelas terlebih dahulu.")
    else:
        # Kesan Lajur Nama & IC
        lajur_ic, lajur_nama = None, None
        for c in df_all.columns:
            c_lower = str(c).lower().strip()
            if any(k in c_lower for k in ['ic', 'kp', 'kad pengenalan', 'mykad', 'nokp', 'no.kp', 'no_kp', 'id']):
                if not lajur_ic: lajur_ic = c
            elif any(k in c_lower for k in ['nama', 'student', 'murid', 'name', 'pemohon']):
                if not lajur_nama: lajur_nama = c

        senarai_subjek = []
        for col in df_all.columns:
            col_clean = str(col).lower().strip()
            is_metadata = any(col_clean == k or col_clean.startswith('lajur_') for k in KATA_KUNCI_BUKAN_SUBJEK)
            if not is_metadata and col not in [lajur_ic, lajur_nama, 'Tingkatan_System', 'Kelas_System']:
                senarai_subjek.append(col)

        # Satu Kotak Input Carian Utama
        search_input = st.text_input("Masukkan No. Kad Pengenalan atau Nama Murid:", "")

        if search_input.strip():
            clean_query_digit = clean_ic(search_input)
            raw_query_text = search_input.strip().lower()
            
            matched_row = None
            
            # Algoritma Carian Pintar
            for _, row in df_all.iterrows():
                # 1. Semak lajur IC spesifik
                if lajur_ic and lajur_ic in row:
                    cell_ic_clean = clean_ic(row[lajur_ic])
                    if clean_query_digit and clean_query_digit in cell_ic_clean and len(clean_query_digit) >= 4:
                        matched_row = row
                        break
                
                # 2. Semak lajur Nama spesifik
                if lajur_nama and lajur_nama in row:
                    cell_nama_raw = str(row[lajur_nama]).lower().strip()
                    if raw_query_text in cell_nama_raw:
                        matched_row = row
                        break

                # 3. Fallback: Semak keseluruhan sel dalam baris ini
                row_all_str = " ".join([str(v) for v in row.values if pd.notna(v)]).lower()
                row_all_digits = " ".join([clean_ic(v) for v in row.values if pd.notna(v)])

                if (clean_query_digit and clean_query_digit in row_all_digits and len(clean_query_digit) >= 4) or \
                   (raw_query_text and raw_query_text in row_all_str):
                    matched_row = row
                    break

            if matched_row is not None:
                # Ekstrak Nama
                nama_murid = matched_row[lajur_nama] if lajur_nama and lajur_nama in matched_row else None
                if not nama_murid or str(nama_murid).strip().lower() in ['nan', 'none', '']:
                    for val in matched_row.values:
                        s_val = str(val).strip()
                        if len(s_val) > 3 and not s_val.isdigit() and not clean_ic(s_val):
                            nama_murid = s_val
                            break
                if not nama_murid:
                    nama_murid = "Murid"

                # Ekstrak IC
                ic_display = clean_ic(matched_row[lajur_ic]) if lajur_ic and lajur_ic in matched_row else ""
                if not ic_display or len(ic_display) < 6:
                    for val in matched_row.values:
                        c_v = clean_ic(val)
                        if len(c_v) >= 8:
                            ic_display = c_v
                            break
                if not ic_display:
                    ic_display = search_input

                tingkatan_murid = matched_row.get('Tingkatan_System', '-')
                kelas_murid = matched_row.get('Kelas_System', '-')

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
    <span style="color: #5f6368; font-size: 13px; font-weight: bold; letter-spacing: 1px;">PROFIL PENTAKSIRAN INDIVIDU</span>
    <h2 style="margin: 4px 0; color: #1a73e8;">{nama_murid}</h2>
    <p style="margin: 0; font-size: 15px; color: #3c4043;">Tingkatan / Kelas: <b>{tingkatan_murid} ({kelas_murid})</b> &nbsp;|&nbsp; No. KP: <b>{ic_display}</b></p>
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
                    color_map = {'TP 6': '#0d904f', 'TP 5': '#34a853', 'TP 4': '#1a73e8', 'TP 3': '#fbbc04', 'TP 2': '#e67c73', 'TP 1': '#d93025'}
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
                        rows_html += f"<tr><td><b>{subjek_name}</b></td><td style='text-align: center;'><span class='badge {badge_cls}'>TP {tp_val}</span></td><td style='font-size: 13px; color: #495057;'>{tafsiran_txt}</td></tr>"
                    st.markdown(f"<table class='pbd-table'><thead><tr><th style='width: 30%;'>Subjek</th><th style='width: 25%; text-align: center;'>Tahap Penguasaan</th><th style='width: 45%;'>Tafsiran & Status</th></tr></thead><tbody>{rows_html}</tbody></table>", unsafe_allow_html=True)

                st.markdown("---")
                st.subheader("📈 Analisis Taburan Penguasaan Murid")
                c_pie, c_analisis = st.columns([1, 1])
                with c_pie:
                    taburan_tp = tp_data['TP_Str'].value_counts().reset_index()
                    taburan_tp.columns = ['TP_Str', 'Bilangan']
                    fig_pie = px.pie(taburan_tp, values='Bilangan', names='TP_Str', hole=0.4, title="Nisbah Taburan TP Keseluruhan Subjek", color='TP_Str', color_discrete_map=color_map)
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

            else:
                st.error(f"No. Kad Pengenalan atau Nama **'{search_input}'** tidak dijumpai. Sila pastikan data kelas telah dimuat naik di tab Pengurusan Data.")