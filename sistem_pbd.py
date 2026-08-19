import streamlit as st
import pandas as pd
import plotly.express as px
import pdfplumber

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem Analisis PBD Individu", layout="wide")

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

# --- TAJUK UTAMA ---
st.markdown("<h1 style='color: #1a73e8;'>Sistem Pelaporan Pencapaian Individu PBD</h1>", unsafe_allow_html=True)
st.markdown("---")

# =========================================================
# FUNGSI PEMBANTU & PENAPISAN LAJUR
# =========================================================
KATA_KUNCI_BUKAN_SUBJEK = [
    'bil', 'bil.', 'no', 'no.', 'nama', 'ic', 'kp', 'no kp', 'no. kp', 'no.kp',
    'tingkatan', 'kelas', 'jantina', 'kaum', 'bangsa', 'agregat', 'jumlah', 'purata'
]

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
                        clean_row = [str(cell).replace('\n', ' ').strip() if cell else "" for cell in row]
                        all_rows.append(clean_row)
                        
    if not all_rows:
        return None
        
    max_cols = max(len(r) for r in all_rows)
    normalized_rows = [r + [""] * (max_cols - len(r)) for r in all_rows]
    
    header_idx = 0
    for idx, row in enumerate(normalized_rows[:15]):
        row_str = " ".join(row).lower()
        if any(k in row_str for k in ['nama', 'kp', 'ic', 'kad pengenalan', 'mykad']):
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
    return df_pdf

# =========================================================
# MUAT NAIK FAIL & PROSES DATA
# =========================================================
st.sidebar.header("📁 Pengurusan Data PBD")
uploaded_file = st.sidebar.file_uploader("Muat naik fail PDF / CSV (idMe):", type=["pdf", "csv"])

df = None
senarai_subjek = []
lajur_ic, lajur_nama, lajur_tingkatan = None, None, None

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.pdf'):
            df = read_pdf_to_dataframe(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, dtype=str)
            
        if df is not None and not df.empty:
            df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
            
            for c in df.columns:
                c_lower = c.lower()
                if any(k == c_lower or k in c_lower for k in ['ic', 'kp', 'kad pengenalan', 'mykad']):
                    if not lajur_ic: lajur_ic = c
                elif any(k == c_lower or k in c_lower for k in ['nama', 'student', 'murid']):
                    if not lajur_nama: lajur_nama = c
                elif any(k == c_lower or k in c_lower for k in ['tingkatan', 'kelas', 'form']):
                    if not lajur_tingkatan: lajur_tingkatan = c

            st.sidebar.markdown("---")
            st.sidebar.subheader("⚙️ Tetapan Lajur Sistem")
            
            if not lajur_ic:
                lajur_ic = st.sidebar.selectbox("Pilih Lajur Kad Pengenalan:", df.columns)
            if not lajur_nama:
                lajur_nama = st.sidebar.selectbox("Pilih Lajur Nama Murid:", df.columns)

            for col in df.columns:
                col_clean = col.lower().strip()
                is_metadata = any(col_clean == k or col_clean.startswith('lajur_') for k in KATA_KUNCI_BUKAN_SUBJEK)
                if not is_metadata and col not in [lajur_ic, lajur_nama, lajur_tingkatan]:
                    senarai_subjek.append(col)

            st.sidebar.success(f"✅ {len(senarai_subjek)} Subjek Dikesan")
            
    except Exception as e:
        st.sidebar.error(f"Ralat membaca fail: {e}")

# =========================================================
# PAPARAN INDIVIDU & ANALISIS SUBJEK
# =========================================================
if df is None:
    st.info("💡 **Panduan:** Sila muat naik fail data PBD (.PDF / .CSV) di bahagian **Sidebar** untuk memulakan.")
else:
    search_ic = st.text_input("Masukkan No. Kad Pengenalan Murid (Tanpa sengkang '-'):", "")
    
    if search_ic:
        clean_search = search_ic.replace('-', '').strip()
        murid = df[df[lajur_ic].astype(str).str.replace('-', '').str.strip() == clean_search]
        
        if not murid.empty:
            nama_murid = murid[lajur_nama].values[0] if lajur_nama in murid.columns else "Murid"
            tingkatan_murid = murid[lajur_tingkatan].values[0] if lajur_tingkatan and lajur_tingkatan in murid.columns else "-"
            
            tp_data = murid[senarai_subjek].T.reset_index()
            tp_data.columns = ['Subjek', 'TP_Raw']
            
            tp_data['TP'] = tp_data['TP_Raw'].astype(str).str.extract(r'(\d+)')[0]
            tp_data = tp_data.dropna(subset=['TP'])
            tp_data['TP'] = tp_data['TP'].astype(int)
            tp_data = tp_data[(tp_data['TP'] >= 1) & (tp_data['TP'] <= 6)]
            
            # Penukaran kategori teks untuk Plotly
            tp_data['TP_Str'] = "TP " + tp_data['TP'].astype(str)
            
            total_subjek = len(tp_data)
            tp_cemerlang = len(tp_data[tp_data['TP'] >= 5])
            tp_perlu_perhatian = len(tp_data[tp_data['TP'] <= 2])
            
            st.markdown(f"""
<div class="profile-card">
    <span style="color: #5f6368; font-size: 13px; font-weight: bold; letter-spacing: 1px;">PROFIL PENTAKSIRAN INDIVIDU</span>
    <h2 style="margin: 4px 0; color: #1a73e8;">{nama_murid}</h2>
    <p style="margin: 0; font-size: 15px; color: #3c4043;">Tingkatan / Kelas: <b>{tingkatan_murid}</b> &nbsp;|&nbsp; No. KP: <b>{search_ic}</b></p>
</div>
""", unsafe_allow_html=True)
            
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Jumlah Subjek Dinilai", f"{total_subjek} Subjek")
            with m2:
                st.metric("Subjek Penguasaan Tinggi (TP 5-6)", f"{tp_cemerlang} Subjek")
            with m3:
                st.metric("Subjek Bimbingan (TP 1-2)", f"{tp_perlu_perhatian} Subjek")
            with m4:
                tp_max = tp_data['TP'].max() if not tp_data.empty else 0
                st.metric("Pencapaian TP Tertinggi", f"TP {tp_max}")
                
            st.markdown("---")
            
            col_graf, col_jadual = st.columns([10, 12])
            
            with col_graf:
                st.subheader("📊 Pencapaian TP Mengikut Subjek")
                
                color_map = {
                    'TP 6': '#0d904f', 
                    'TP 5': '#34a853', 
                    'TP 4': '#1a73e8', 
                    'TP 3': '#fbbc04', 
                    'TP 2': '#e67c73', 
                    'TP 1': '#d93025'
                }
                
                fig_bar = px.bar(
                    tp_data,
                    x='TP',
                    y='Subjek',
                    orientation='h',
                    text='TP_Str',
                    color='TP_Str',
                    color_discrete_map=color_map,
                    title="Skor TP Bagi Setiap Subjek"
                )
                fig_bar.update_layout(
                    xaxis=dict(range=[0, 6.5], dtick=1, title="Tahap Penguasaan (TP)"),
                    yaxis=dict(title="", categoryorder='total ascending'),
                    showlegend=False,
                    height=450
                )
                fig_bar.update_traces(textposition='outside')
                st.plotly_chart(fig_bar, use_container_width=True)

            with col_jadual:
                st.subheader("📋 Senarai Pencapaian Setiap Subjek")
                
                # Pembinaan rentetan HTML bersih tanpa inden ruang berlebihan
                rows_html = ""
                for _, row in tp_data.iterrows():
                    subjek_name = row['Subjek']
                    tp_val = row['TP']
                    tafsiran_txt, badge_cls = dapatkan_tafsiran_tp(tp_val)
                    rows_html += f"<tr><td><b>{subjek_name}</b></td><td style='text-align: center;'><span class='badge {badge_cls}'>TP {tp_val}</span></td><td style='font-size: 13px; color: #495057;'>{tafsiran_txt}</td></tr>"
                
                html_table = f"<table class='pbd-table'><thead><tr><th style='width: 30%;'>Subjek</th><th style='width: 25%; text-align: center;'>Tahap Penguasaan</th><th style='width: 45%;'>Tafsiran & Status</th></tr></thead><tbody>{rows_html}</tbody></table>"
                
                st.markdown(html_table, unsafe_allow_html=True)
                
            st.markdown("---")
            st.subheader("📈 Analisis Taburan Penguasaan Murid")
            
            c_pie, c_analisis = st.columns([1, 1])
            
            with c_pie:
                taburan_tp = tp_data['TP_Str'].value_counts().reset_index()
                taburan_tp.columns = ['TP_Str', 'Bilangan']
                
                fig_pie = px.pie(
                    taburan_tp, 
                    values='Bilangan', 
                    names='TP_Str',
                    hole=0.4,
                    title="Nisbah Taburan TP Keseluruhan Subjek",
                    color='TP_Str',
                    color_discrete_map=color_map
                )
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
            st.error("No. Kad Pengenalan tidak dijumpai dalam rekod. Sila pastikan carian adalah betul.")