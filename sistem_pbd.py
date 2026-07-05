import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Sistem PBD", layout="wide")

# --- LETAK LOGO DAN TAJUK ---
col_logo, col_title = st.columns([1, 10])

with col_logo:
    try:
        # Pastikan fail 'Logo SMKDSO.jpg' berada dalam folder yang sama dengan skrip ini
        st.image("Logo SMKDSO.jpg", width=100)
    except:
        st.error("Logo tidak dijumpai")

with col_title:
    st.title("Sistem Analisis Pentaksiran Bilik Darjah (PBD)")
    
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
senarai_subjek = [] # Dikosongkan dahulu sebagai persediaan

if uploaded_file is not None:
    try:
        # Membaca fail CSV dan menetapkan lajur IC sebagai teks (string)
        df = pd.read_csv(uploaded_file, dtype={'IC': str}) 
        df.columns = df.columns.str.strip() 
        
        # --- PENGESANAN SUBJEK SECARA AUTOMATIK ---
        # Sila tambah nama lajur maklumat peribadi lain di bawah sekiranya ada dalam fail CSV anda.
        # Contoh: 'Bil', 'Nama', 'IC', 'Tingkatan', 'Jantina', 'Kelas'
        lajur_bukan_subjek = ['Bil', 'Nama', 'IC', 'Tingkatan'] 
        
        # Sistem menapis tajuk lajur dan mengambil baki lajur sebagai senarai subjek secara automatik
        senarai_subjek = [kolom for kolom in df.columns if kolom not in lajur_bukan_subjek]
        
        st.sidebar.success(f"✅ Fail berjaya dibaca! {len(senarai_subjek)} subjek dikesan.")
    except Exception as e:
        st.sidebar.error(f"Ralat membaca fail: {e}. Sila pastikan fail berformat CSV.")

# =========================================================
# 3. STRUKTUR TAB ANTARAMUKA (Sentiasa Dipaparkan)
# =========================================================
tab1, tab2 = st.tabs(["🔍 Semakan Individu (Carian IC)", "📊 Analisis Pencapaian Tingkatan"])

# ==========================================
# TAB 1: CARIAN INDIVIDU 
# ==========================================
with tab1:
    st.header("Semakan Tahap Penguasaan (TP) Murid")
    
    if df is None:
        # Mesej panduan mesra pengguna jika fail belum dimuat naik
        st.info("💡 **Panduan:** Sila muat naik fail data PBD (.CSV) pada bahagian **Sidebar di sebelah kiri** terlebih dahulu untuk memulakan carian.")
    else:
        search_ic = st.text_input("Masukkan No. Kad Pengenalan Murid (Tanpa sengkang '-', Contoh: 080101141234):", "")
        
        if search_ic:
            murid = df[df['IC'] == search_ic]
            
            if not murid.empty:
                st.success(f"🧑‍🎓 Rekod ditemui: **{murid['Nama'].values[0]}** | Tingkatan: **{murid['Tingkatan'].values[0]}**")
                
                # Menggunakan senarai_subjek yang telah dikesan secara automatik
                tp_data = murid[senarai_subjek].T.reset_index()
                tp_data.columns = ['Subjek', 'Tahap Penguasaan (TP)']
                
                # Menapis data kosong atau nilai 'None'
                tp_data = tp_data.dropna()
                tp_data = tp_data[tp_data['Tahap Penguasaan (TP)'].astype(str).str.strip().str.lower() != 'none']
                tp_data['Tahap Penguasaan (TP)'] = pd.to_numeric(tp_data['Tahap Penguasaan (TP)'])
                
                st.markdown("<h3 style='text-align: center; margin-top: 20px;'>Keputusan PBD Keseluruhan</h3>", unsafe_allow_html=True)
                
                col_kiri, col_tengah, col_kanan = st.columns([1, 2, 1])
                
                with col_tengah:
                    jadual_paparan = tp_data.copy()
                    jadual_paparan['Tahap Penguasaan (TP)'] = jadual_paparan['Tahap Penguasaan (TP)'].astype(int).astype(str)
                    
                    # Membina jadual HTML tersuai supaya kedudukannya kemas di tengah halaman
                    html_table = "<table style='width: 100%; border-collapse: collapse; font-family: sans-serif; margin-bottom: 20px;'>"
                    html_table += "<thead><tr style='border-bottom: 2px solid #ddd;'>"
                    html_table += "<th style='padding: 12px; text-align: center; color: #555;'>Subjek</th>"
                    html_table += "<th style='padding: 12px; text-align: center; color: #555;'>Tahap Penguasaan (TP)</th>"
                    html_table += "</tr></thead><tbody>"
                    
                    for _, row in jadual_paparan.iterrows():
                        html_table += "<tr style='border-bottom: 1px solid #eee;'>"
                        html_table += f"<td style='padding: 10px; text-align: center;'>{row['Subjek']}</td>"
                        html_table += f"<td style='padding: 10px; text-align: center; font-weight: bold;'>{row['Tahap Penguasaan (TP)']}</td>"
                        html_table += "</tr>"
                        
                    html_table += "</tbody></table>"
                    st.markdown(html_table, unsafe_allow_html=True)
                
                st.divider() 
                
                col_g1, col_g2, col_g3 = st.columns([1, 3, 1])
                
                with col_g2:
                    # Menjana carta radar profil pelajar
                    fig_radar = px.line_polar(tp_data, r='Tahap Penguasaan (TP)', theta='Subjek', line_close=True,
                                              range_r=[0,6])
                    fig_radar.update_traces(fill='toself', line_color='#4CAF50')
                    fig_radar.update_layout(title_text="Profil Penguasaan Murid", title_x=0.5, font=dict(size=14))
                    st.plotly_chart(fig_radar, use_container_width=True)
                    
            else:
                # BAHAGIAN YANG TELAH DIBETULKAN (Mengelakkan Ralat SyntaxError)
                st.error("No. Kad Pengenalan tidak ditemui dalam fail. Sila semak semula.")

# ==========================================
# TAB 2: ANALISIS TINGKATAN
# ==========================================
with tab2:
    st.header("Analisis Mendalam Mengikut Tingkatan")
    
    if df is None:
        # Mesej panduan jika fail belum dimuat naik
        st.info("💡 **Panduan:** Sila muat naik fail data PBD (.CSV) pada bahagian **Sidebar di sebelah kiri** terlebih dahulu untuk melihat analisis penuh.")
    else:
        if 'Tingkatan' in df.columns:
            senarai_tingkatan = df['Tingkatan'].dropna().unique()
            pilihan_tingkatan = st.selectbox("Pilih Tingkatan:", senarai_tingkatan)
            
            df_tingkatan = df[df['Tingkatan'] == pilihan_tingkatan]
            
            st.write(f"### Analisis Keseluruhan bagi {pilihan_tingkatan}")
            
            # Menyusun data dari bentuk melintang ke menegak untuk tujuan carta histogram/bar
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
            
            # Mengemaskan jadual besar (membuang ".0" perpuluhan dan menggantikan None/NaN kepada "-")
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