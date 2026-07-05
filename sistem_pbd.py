import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman (Menggunakan tema moden)
st.set_page_config(page_title="Sistem PBD SMKDSO", layout="wide")

# --- SUNTIKAN GAYA CSS UNTUK TAMPILAN PREMUM ---
st.markdown("""
    <style>
    /* Rekabentuk Kad Profil */
    .profile-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border-left: 5px solid #4CAF50;
        margin-bottom: 25px;
    }
    /* Rekabentuk Jadual Keputusan */
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
    .pbd-table tr:hover {
        background-color: #f8f9fa;
    }
    /* Lencana Warna Dinamik untuk TP */
    .badge {
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: bold;
        color: white;
        display: inline-block;
        font-size: 14px;
    }
    .badge-high { background-color: #2ece7e; box-shadow: 0 2px 5px rgba(46,206,126,0.3); } /* TP 5-6 */
    .badge-mid { background-color: #1a73e8; box-shadow: 0 2px 5px rgba(26,115,232,0.3); }  /* TP 3-4 */
    .badge-low { background-color: #ee5253; box-shadow: 0 2px 5px rgba(238,82,83,0.3); }  /* TP 1-2 */
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
# 2. SEKSYEN MUAT NAIK FAIL & PENGESANAN SUBJEK AUTOMATIK
# =========================================================
st.sidebar.header("📁 Pengurusan Data")
uploaded_file = st.sidebar.file_uploader(
    "Muat naik fail CSV (dari idMe):", 
    type=["csv"]
)

df = None
senarai_subjek = []

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, dtype={'IC': str}) 
        df.columns = df.columns.str.strip() 
        
        # Penapis lajur asas bukan subjek
        lajur_bukan_subjek = ['Bil', 'Nama', 'IC', 'Tingkatan'] 
        senarai_subjek = [kolom for kolom in df.columns if kolom not in lajur_bukan_subjek]
        
        st.sidebar.success(f"✅ Fail berjaya dibaca! {len(senarai_subjek)} subjek dikesan.")
    except Exception as e:
        st.sidebar.error(f"Ralat membaca fail: {e}. Sila pastikan fail berformat CSV.")

# =========================================================
# 3. STRUKTUR TAB ANTARAMUKA
# =========================================================
tab1, tab2 = st.tabs(["🔍 Semakan Individu (Carian IC)", "📊 Analisis Pencapaian Tingkatan"])

# ==========================================
# TAB 1: CARIAN INDIVIDU (KINI DENGAN UI PREMIUM)
# ==========================================
with tab1:
    st.markdown("<h2 style='color: #3c4043;'>Semakan Tahap Penguasaan (TP) Murid</h2>", unsafe_allow_html=True)
    
    if df is None:
        st.info("💡 **Panduan:** Sila muat naik fail data PBD (.CSV) pada bahagian **Sidebar di sebelah kiri** terlebih dahulu untuk memulakan carian.")
    else:
        search_ic = st.text_input("Masukkan No. Kad Pengenalan Murid (Tanpa sengkang '-', Contoh: 080101141234):", "")
        
        if search_ic:
            murid = df[df['IC'] == search_ic]
            
            if not murid.empty:
                # 1. Ekstrak Data Murid
                nama_murid = murid['Nama'].values[0]
                tingkatan_murid = murid['Tingkatan'].values[0]
                
                tp_data = murid[senarai_subjek].T.reset_index()
                tp_data.columns = ['Subjek', 'TP']
                tp_data = tp_data.dropna()
                tp_data = tp_data[tp_data['TP'].astype(str).str.strip().str.lower() != 'none']
                tp_data['TP'] = pd.to_numeric(tp_data['TP'])
                
                purata_tp = tp_data['TP'].mean()
                total_subjek = len(tp_data)
                
                # 2. PAPARAN KAD PROFIL & RINGKASAN EKSEKUTIF
                st.markdown(f"""
                    <div class="profile-card">
                        <span style="color: #70757a; font-size: 14px; font-weight: bold; text-transform: uppercase;">Profil Murid</span>
                        <h2 style="margin: 5px 0 0 0; color: #1a73e8;">{nama_murid}</h2>
                        <p style="margin: 5px 0 0 0; font-size: 15px; color: #3c4043;">Tingkatan: <b>{tingkatan_murid}</b> | No. KP: <b>{search_ic}</b></p>
                    </div>
                """, unsafe_allow_html=True)
                
                # Paparan KPI Ringkas (Metrics)
                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.metric("Jumlah Subjek Diambil", f"{total_subjek} Subjek")
                with m_col2:
                    st.metric("Purata Tahap Penguasaan (TP)", f"{purata_tp:.2f} / 6.00")
                with m_col3:
                    tp_tertinggi = int(tp_data['TP'].max()) if not tp_data.empty else 0
                    st.metric("TP Tertinggi Dicapai", f"TP {tp_tertinggi}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # 3. SUSUN ATUR 2 LAJUR: JADUAL (KIRI) & CARTA (KANAN)
                col_kiri, col_kanan = st.columns([11, 10])
                
                with col_kiri:
                    st.markdown("<h4 style='text-align: center; color: #3c4043; margin-bottom: 15px;'>Jadual Pencapaian Subjek</h4>", unsafe_allow_html=True)
                    
                    # Membina Jadual HTML Cantik Bersama Lencana Warna Dinamik
                    html_table = "<table class='pbd-table'>"
                    html_table += "<thead><tr><th>Subjek</th><th>Tahap Penguasaan (TP)</th></tr></thead>"
                    html_table += "<tbody>"
                    
                    for _, row in tp_data.iterrows():
                        tp_val = int(row['TP'])
                        # Tentukan kelas warna lencana mengikut nilai TP
                        if tp_val >= 5:
                            badge_class = "badge-high"
                        elif tp_val >= 3:
                            badge_class = "badge-mid"
                        else:
                            badge_class = "badge-low"
                            
                        html_table += "<tr>"
                        html_table += f"<td><b>{row['Subjek']}</b></td>"
                        html_table += f"<td><span class='badge {badge_class}'>TP {tp_val}</span></td>"
                        html_table += "</tr>"
                        
                    html_table += "</tbody></table>"
                    st.markdown(html_table, unsafe_allow_html=True)
                
                with col_kanan:
                    # Menjana Carta Radar Moden dengan Plotly
                    fig_radar = px.line_polar(tp_data, r='TP', theta='Subjek', line_close=True, range_r=[0,6])
                    fig_radar.update_traces(fill='toself', fillcolor='rgba(26, 115, 232, 0.2)', line_color='#1a73e8', line_width=2)
                    fig_radar.update_layout(
                        title={
                            'text': "Profil Kognitif & Penguasaan",
                            'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top'
                        },
                        font=dict(size=13, color="#3c4043"),
                        polar=dict(
                            radialaxis=dict(visible=True, range=[0, 6], gridcolor="#dee2e6"),
                            angularaxis=dict(gridcolor="#dee2e6")
                        ),
                        margin=dict(t=80, b=20, l=40, r=40),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
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
        st.info("💡 **Panduan:** Sila muat naik fail data PBD (.CSV) pada bahagian **Sidebar di sebelah kiri** terlebih dahulu untuk melihat analisis penuh.")
    else:
        if 'Tingkatan' in df.columns:
            senarai_tingkatan = df['Tingkatan'].dropna().unique()
            pilihan_tingkatan = st.selectbox("Pilih Tingkatan:", senarai_tingkatan)
            
            df_tingkatan = df[df['Tingkatan'] == pilihan_tingkatan]
            
            st.write(f"### Analisis Keseluruhan bagi {pilihan_tingkatan}")
            
            df_melt = df_tingkatan.melt(id_vars=['IC', 'Nama', 'Tingkatan'], 
                                        value_vars=senarai_subjek,
                                        var_name='Subjek', value_name='TP')
            
            df_melt = df_melt.dropna(subset=['TP'])
            df_melt = df_melt[df_melt['TP'].astype(str).str.strip().str.lower() != 'none']
            df_melt['TP'] = pd.to_numeric(df_melt['TP'], errors='coerce')
            df_melt = df_melt.dropna(subset=['TP'])
            
            col3, col4 = st.columns(2)
            
            with col3:
                fig_bar = px.histogram(df_melt, x="Subjek", color="TP", barmode="group",
                                       title="Taburan Tahap Penguasaan (TP) Mengikut Subjek",
                                       category_orders={"TP": [1, 2, 3, 4, 5, 6]},
                                       color_discrete_sequence=px.colors.sequential.Viridis)
                st.plotly_chart(fig_bar, use_container_width=True)
                
            with col4:
                purata_subjek = df_melt.groupby('Subjek')['TP'].mean().reset_index()
                fig_line = px.bar(purata_subjek, x='Subjek', y='TP',
                                  title="Purata TP Keseluruhan Subjek", text_auto='.2f')
                fig_line.update_layout(yaxis=dict(range=[0,6]))
                st.plotly_chart(fig_line, use_container_width=True)
    
            st.write("### Senarai Pelajar & Keputusan")
            
            df_kemas = df_tingkatan.fillna("-").replace("None", "-")
            df_kemas = df_kemas.astype(str).replace(r'\.0$', '', regex=True)
            
            jadual_html = df_kemas.style.set_properties(**{
                'text-align': 'center', 
                'border': '1px solid #e6e6eb',
                'padding': '10px',
                'font-family': 'sans-serif'
            }).set_table_styles([{
                'selector': 'th', 
                'props': [('text-align', 'center'), ('background-color', '#f0f2f6'), ('padding', '10px'), ('border', '1px solid #e6e6eb')]
            }, {
                'selector': 'table',
                'props': [('width', '100%'), ('border-collapse', 'collapse')]
            }]).hide(axis="index").to_html()
            
            st.markdown(jadual_html, unsafe_allow_html=True)
            
        else:
            st.error("Ralat: Lajur 'Tingkatan' tidak dijumpai di dalam fail CSV anda.")