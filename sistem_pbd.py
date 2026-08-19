import streamlit as st
import pandas as pd
import plotly.express as px
import pdfplumber

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem PBD SMKDSO", layout="wide")

# --- SUNTIKAN GAYA CSS UNTUK TAMPILAN PREMIUM ---
st.markdown("""
    <style>
    .profile-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #4CAF50;
        margin-bottom: 25px;
    }
    .pbd-table {
        width: 100%;
        border-collapse: collapse;
        background-color: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    .pbd-table th {
        background-color: #f8f9fa;
        color: #495057;
        padding: 14px;
        font-weight: 600;
        border-bottom: 2px solid #dee2e6;
        text-align: center;
    }
    .pbd-table td {
        padding: 12px;
        border-bottom: 1px solid #f1f3f5;
        text-align: center;
        color: #343a40;
    }
    .pbd-table tr:hover { background-color: #f8f9fa; }
    .badge {
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        color: white;
        display: inline-block;
        font-size: 14px;
    }
    .badge-high { background-color: #2ece7e; box-shadow: 0 2px 5px rgba(46,206,126,0.3); }
    .badge-mid { background-color: #1a73e8; box-shadow: 0 2px 5px rgba(26,115,232,0.3); }
    .badge-low { background-color: #ee5253; box-shadow: 0 2px 5px rgba(238,82,83,0.3); }
    </style>
""", unsafe_allow_html=True)

# --- LETAK LOGO DAN TAJUK ---
col_logo, col_title = st.columns([1, 10])

with col_logo:
    try:
        st.image("Logo SMKDSO.jpg", width=95)
    except:
        st.error("Logo tidak dijumpai")

with col_title:
    st.markdown("<h1 style='color: #1a73e8; margin-bottom: 0;'>Sistem Analisis Pentaksiran Bilik Darjah (PBD)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #70757a; font-size: 16px; margin-top: 5px;'>Sistem Pelaporan Prestasi Akademik Murid Sekolah Menengah Kebangsaan Dato' Syed Omar</p>", unsafe_allow_html=True)
    
st.markdown("---")

# =========================================================
# FUNGSI PEMBANTU: DENGAN PENYERAGAMAN LAJUR AUTOMATIK
# =========================================================
def cari_lajur(df, senarai_kata_kunci):
    for col in df.columns:
        for kw in senarai_kata_kunci:
            if kw.lower() in str(col).lower().replace('\n', ' '):
                return col
    return None

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
        
    # Cari bilangan lajur maksimum di antara semua baris untuk elakkan KeyError/ValueError
    max_cols = max(len(r) for r in all_rows)
    
    # Penyeragaman: Tambah petak kosong ("") untuk baris yang mempunyai kurang lajur
    normalized_rows = [r + [""] * (max_cols - len(r)) for r in all_rows]
    
    # Membina tajuk lajur yang unik
    raw_header = normalized_rows[0]
    header = []
    for i, col in enumerate(raw_header):
        col_name = col.strip() if col.strip() else f"Lajur_{i+1}"
        if col_name in header:
            col_name = f"{col_name}_{i+1}"
        header.append(col_name)
        
    df_pdf = pd.DataFrame(normalized_rows[1:], columns=header)
    return df_pdf

# =========================================================
# 2. SEKSYEN MUAT NAIK FAIL & PENGESANAN AUTOMATIK
# =========================================================
st.sidebar.header("📁 Pengurusan Data")

uploaded_file = st.sidebar.file_uploader(
    "Muat naik fail PDF / CSV (dari idMe):", 
    type=["pdf", "csv"]
)

df = None
senarai_subjek = []
lajur_ic = None
lajur_nama = None
lajur_tingkatan = None

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.pdf'):
            df = read_pdf_to_dataframe(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, dtype=str)
            
        if df is not None and not df.empty:
            df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
            
            # Pengesan Lajur Pintar
            lajur_ic = cari_lajur(df, ['ic', 'kp', 'kad pengenalan', 'mykod'])
            lajur_nama = cari_lajur(df, ['nama', 'student', 'murid'])
            lajur_tingkatan = cari_lajur(df, ['tingkatan', 'kelas', 'form'])
            
            # Senaraikan semua lajur asas untuk diabaikan sebagai subjek
            lajur_asas = [lajur_ic, lajur_nama, lajur_tingkatan, 'Bil', 'BIL', 'No', 'NO', 'Jantina', 'Kaum']
            senarai_subjek = [c for c in df.columns if c not in lajur_asas and c is not None and not str(c).startswith('Lajur_')]
            
            if lajur_ic is None:
                st.sidebar.warning("⚠️ Lajur Kad Pengenalan tidak dikesan secara automatik.")
            else:
                st.sidebar.success(f"✅ Fail berjaya dibaca! Lajur KP: `{lajur_ic}` | Subjek: {len(senarai_subjek)}")
        else:
            st.sidebar.error("Gagal membaca kandungan fail.")
            
    except Exception as e:
        st.sidebar.error(f"Ralat membaca fail: {e}")

# =========================================================
# 3. STRUKTUR TAB ANTARAMUKA
# =========================================================
tab1, tab2 = st.tabs(["🔍 Semakan Individu (Carian IC)", "📊 Analisis Pencapaian Tingkatan"])

# ==========================================
# TAB 1: CARIAN INDIVIDU
# ==========================================
with tab1:
    st.markdown("<h2 style='color: #3c4043;'>Semakan Tahap Penguasaan (TP) Murid</h2>", unsafe_allow_html=True)
    
    if df is None:
        st.info("💡 **Panduan:** Sila muat naik fail data PBD (.PDF / .CSV) pada bahagian **Sidebar di sebelah kiri** terlebih dahulu.")
    elif lajur_ic is None:
        st.error("Ralat: Lajur Kad Pengenalan tidak dijumpai di dalam fail anda.")
    else:
        search_ic = st.text_input("Masukkan No. Kad Pengenalan Murid (Tanpa sengkang '-', Contoh: 080101141234):", "")
        
        if search_ic:
            clean_search = search_ic.replace('-', '').strip()
            murid = df[df[lajur_ic].astype(str).str.replace('-', '').str.strip() == clean_search]
            
            if not murid.empty:
                nama_murid = murid[lajur_nama].values[0] if lajur_nama else "Murid"
                tingkatan_murid = murid[lajur_tingkatan].values[0] if lajur_tingkatan else "-"
                
                tp_data = murid[senarai_subjek].T.reset_index()
                tp_data.columns = ['Subjek', 'TP']
                tp_data = tp_data.dropna()
                tp_data = tp_data[tp_data['TP'].astype(str).str.strip().str.lower() != 'none']
                tp_data['TP'] = pd.to_numeric(tp_data['TP'], errors='coerce')
                tp_data = tp_data.dropna(subset=['TP'])
                
                purata_tp = tp_data['TP'].mean() if not tp_data.empty else 0
                total_subjek = len(tp_data)
                
                st.markdown(f"""
                    <div class="profile-card">
                        <span style="color: #70757a; font-size: 14px; font-weight: bold; text-transform: uppercase;">Profil Murid</span>
                        <h2 style="margin: 5px 0 0 0; color: #1a73e8;">{nama_murid}</h2>
                        <p style="margin: 5px 0 0 0; font-size: 15px; color: #3c4043;">Tingkatan: <b>{tingkatan_murid}</b> | No. KP: <b>{search_ic}</b></p>
                    </div>
                """, unsafe_allow_html=True)
                
                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.metric("Jumlah Subjek Diambil", f"{total_subjek} Subjek")
                with m_col2:
                    st.metric("Purata Tahap Penguasaan (TP)", f"{purata_tp:.2f} / 6.00")
                with m_col3:
                    tp_tertinggi = int(tp_data['TP'].max()) if not tp_data.empty else 0
                    st.metric("TP Tertinggi Dicapai", f"TP {tp_tertinggi}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_kiri, col_kanan = st.columns([11, 10])
                
                with col_kiri:
                    st.markdown("<h4 style='text-align: center; color: #3c4043; margin-bottom: 15px;'>Jadual Pencapaian Subjek</h4>", unsafe_allow_html=True)
                    
                    html_table = "<table class='pbd-table'>"
                    html_table += "<thead><tr><th>Subjek</th><th>Tahap Penguasaan (TP)</th></tr></thead><tbody>"
                    
                    for _, row in tp_data.iterrows():
                        tp_val = int(row['TP'])
                        badge_class = "badge-high" if tp_val >= 5 else ("badge-mid" if tp_val >= 3 else "badge-low")
                        html_table += f"<tr><td><b>{row['Subjek']}</b></td><td><span class='badge {badge_class}'>TP {tp_val}</span></td></tr>"
                        
                    html_table += "</tbody></table>"
                    st.markdown(html_table, unsafe_allow_html=True)
                
                with col_kanan:
                    fig_radar = px.line_polar(tp_data, r='TP', theta='Subjek', line_close=True, range_r=[0,6])
                    fig_radar.update_traces(fill='toself', fillcolor='rgba(26, 115, 232, 0.2)', line_color='#1a73e8', line_width=2)
                    fig_radar.update_layout(
                        title={'text': "Profil Kognitif & Penguasaan", 'y': 0.95, 'x': 0.5, 'xanchor': 'center'},
                        font=dict(size=13, color="#3c4043"),
                        polar=dict(radialaxis=dict(visible=True, range=[0, 6])),
                        margin=dict(t=80, b=20, l=40, r=40)
                    )
                    st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.error("No. Kad Pengenalan tidak ditemui dalam fail. Sila semak semula.")

# ==========================================
# TAB 2: ANALISIS TINGKATAN
# ==========================================
with tab2:
    st.header("Analisis Mendalam Mengikut Tingkatan")
    if df is None:
        st.info("💡 **Panduan:** Sila muat naik fail data PBD (.PDF / .CSV) pada bahagian **Sidebar di sebelah kiri** terlebih dahulu.")
    else:
        if lajur_tingkatan in df.columns:
            senarai_tingkatan = df[lajur_tingkatan].dropna().unique()
            pilihan_tingkatan = st.selectbox("Pilih Tingkatan:", senarai_tingkatan)
            
            df_tingkatan = df[df[lajur_tingkatan] == pilihan_tingkatan]
            st.write(f"### Analisis Keseluruhan bagi {pilihan_tingkatan}")
            
            df_melt = df_tingkatan.melt(id_vars=[c for c in df.columns if c not in senarai_subjek], 
                                        value_vars=senarai_subjek,
                                        var_name='Subjek', value_name='TP')
            
            df_melt['TP'] = pd.to_numeric(df_melt['TP'], errors='coerce')
            df_melt = df_melt.dropna(subset=['TP'])
            
            col3, col4 = st.columns(2)
            with col3:
                fig_bar = px.histogram(df_melt, x="Subjek", color="TP", barmode="group",
                                       title="Taburan Tahap Penguasaan (TP) Mengikut Subjek",
                                       category_orders={"TP": [1, 2, 3, 4, 5, 6]})
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with col4:
                purata_subjek = df_melt.groupby('Subjek')['TP'].mean().reset_index()
                fig_line = px.bar(purata_subjek, x='Subjek', y='TP', title="Purata TP Keseluruhan Subjek", text_auto='.2f')
                fig_line.update_layout(yaxis=dict(range=[0,6]))
                st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("Lajur 'Tingkatan' tidak dikesan dalam fail ini.")