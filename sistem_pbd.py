import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman 
st.set_page_config(page_title="Sistem PBD", layout="wide")

# --- LETAK LOGO DAN TAJUK BARU ---
col_logo, col_title = st.columns([1, 10])

with col_logo:
    # Pastikan fail 'Logo SMKDSO.jpg' ada dalam folder yang sama dengan fail ini
    try:
        st.image("Logo SMKDSO.jpg", width=100)
    except:
        st.error("Logo tidak dijumpai")

with col_title:
    st.title("Sistem Analisis Pentaksiran Bilik Darjah (PBD)")
    
st.markdown("---")

# 2. Penjanaan Data Pelajar (Dari Google Sheets)
@st.cache_data(ttl=60)
def load_data():
    # SILA MASUKKAN PAUTAN GOOGLE SHEETS (.CSV) ANDA DI BAWAH INI
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR45w6BLBf-xTzMNEIsemaSHS-9ZOHU4ri5C_l9l9Gathd3Cqci6GN4kL0v_4rjmTs1GdD_j8Mc6pm8/pub?output=csv"
    
    df = pd.read_csv(sheet_url, dtype={'IC': str}) 
    df.columns = df.columns.str.strip() 
    return df

df = load_data()

# Senarai Subjek Terkini
senarai_subjek = ['BM', 'BI', 'Matematik', 'Sains', 'Sejarah', 'Pend Islam', 'BA', 'Geografi', 'ASK', 'PSV', 'PM', 'PJK']

# 3. Struktur Tab Antaramuka
tab1, tab2 = st.tabs(["🔍 Semakan Individu (Carian IC)", "📊 Analisis Pencapaian Tingkatan"])

# ==========================================
# TAB 1: CARIAN INDIVIDU 
# ==========================================
with tab1:
    st.header("Semakan Tahap Penguasaan (TP) Murid")
    search_ic = st.text_input("Masukkan No. Kad Pengenalan Murid (Tanpa sengkang '-', Contoh: 080101141234):", "")
    
    if search_ic:
        murid = df[df['IC'] == search_ic]
        
        if not murid.empty:
            st.success(f"🧑‍🎓 Rekod ditemui: **{murid['Nama'].values[0]}** | Tingkatan: **{murid['Tingkatan'].values[0]}**")
            
            tp_data = murid[senarai_subjek].T.reset_index()
            tp_data.columns = ['Subjek', 'Tahap Penguasaan (TP)']
            
            tp_data = tp_data.dropna()
            tp_data = tp_data[tp_data['Tahap Penguasaan (TP)'].astype(str).str.strip().str.lower() != 'none']
            
            tp_data['Tahap Penguasaan (TP)'] = pd.to_numeric(tp_data['Tahap Penguasaan (TP)'])
            
            st.markdown("<h3 style='text-align: center; margin-top: 20px;'>Keputusan PBD Keseluruhan</h3>", unsafe_allow_html=True)
            
            col_kiri, col_tengah, col_kanan = st.columns([1, 2, 1])
            
            with col_tengah:
                jadual_paparan = tp_data.copy()
                jadual_paparan['Tahap Penguasaan (TP)'] = jadual_paparan['Tahap Penguasaan (TP)'].astype(int).astype(str)
                
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
                fig_radar = px.line_polar(tp_data, r='Tahap Penguasaan (TP)', theta='Subjek', line_close=True,
                                          range_r=[0,6])
                fig_radar.update_traces(fill='toself', line_color='#4CAF50')
                fig_radar.update_layout(title_text="Profil Penguasaan Murid", title_x=0.5, font=dict(size=14))
                st.plotly_chart(fig_radar, use_container_width=True)
                
        else:
            st.error("No. Kad Pengenalan tidak ditemui dalam sistem. Sila semak semula.")

# ==========================================
# TAB 2: ANALISIS TINGKATAN
# ==========================================
with tab2:
    st.header("Analisis Mendalam Mengikut Tingkatan")
    
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
        
        # --- KEMAS KINI: BUANG PERPULUHAN DAN PAKSA KE TENGAH ---
        df_kemas = df_tingkatan.fillna("-").replace("None", "-")
        
        # Tukar ke teks dan buang ".0" di hujung nilai secara automatik
        df_kemas = df_kemas.astype(str).replace(r'\.0$', '', regex=True)
        
        # Jana HTML Jadual dengan CSS memaksa ke tengah
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
        
        # Paparkan HTML tulen ke dalam Streamlit
        st.markdown(jadual_html, unsafe_allow_html=True)
        
    else:
        st.error("Ralat: Lajur 'Tingkatan' tidak dijumpai. Sila semak Google Sheets anda.")