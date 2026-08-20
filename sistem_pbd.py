import streamlit as st
import pandas as pd
import os
import glob
import re
import time

# KONFIGURASI HALAMAN
st.set_page_config(page_title="PBD - SMK Dato' Syed Omar", layout="wide", page_icon="🎓")

DATA_DIR = "data_pbd"
os.makedirs(DATA_DIR, exist_ok=True)
ADMIN_PASSWORD = "admin123"

if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

# CSS UNTUK UI (Stabil dan Kemas)
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .school-title { font-size: 28px; font-weight: 800; color: #2563eb; margin: 0; }
    .system-title { font-size: 15px; color: #475569; margin: 2px 0 20px 0; }
    .profile-card { background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); border-left: 6px solid #2563eb; border: 1px solid #e2e8f0; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='school-title'>SMK DATO' SYED OMAR</h1>", unsafe_allow_html=True)
st.markdown("<p class='system-title'>✨ Sistem Pelaporan & Pengurusan Data Pentaksiran Bilik Darjah (PBD)</p>", unsafe_allow_html=True)
st.markdown("---")

def parse_csv_file(uploaded_file):
    records = []
    try:
        # Membaca fail CSV
        df = pd.read_csv(uploaded_file, dtype=str)
        
        # Mencari kolum yang mengandungi perkataan NAMA atau KP/IC secara automatik
        name_col = next((c for c in df.columns if 'NAMA' in str(c).upper()), None)
        ic_col = next((c for c in df.columns if 'KP' in str(c).upper() or 'IC' in str(c).upper() or 'KAD' in str(c).upper()), None)
        
        if name_col and ic_col:
            for _, row in df.iterrows():
                if pd.isna(row[ic_col]) or pd.isna(row[name_col]): continue
                ic = re.sub(r'\D', '', str(row[ic_col]))
                nama = str(row[name_col]).upper().strip()
                if len(ic) >= 12: records.append({'NO_KP': ic, 'NAMA': nama})
        else:
            # Fallback jika nama kolum di CSV pelik/tidak dijumpai
            for _, row in df.iterrows():
                row_str = " ".join([str(v) for v in row.values if pd.notna(v)])
                match = re.search(r'\b\d{6}[-\s]?\d{2}[-\s]?\d{4}\b', row_str)
                if match:
                    ic = re.sub(r'\D', '', match.group(0))
                    clean = re.sub(r'[^a-zA-Z\s@\']', ' ', row_str.replace(match.group(0), ''))
                    words = [w for w in clean.split() if len(w) > 2 and w.upper() not in ['LELAKI','PEREMPUAN','ISLAM','MELAYU','KPM', 'TINGKATAN', 'TAHUN']]
                    nama = " ".join(words[:6]).strip().upper()
                    if not nama: nama = "SILA KEMASKINI NAMA"
                    records.append({'NO_KP': ic, 'NAMA': nama})
        
        return pd.DataFrame(records).drop_duplicates(subset=['NO_KP']) if records else None
    except Exception:
        return None

def load_all_saved_data():
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not files: return None
    return pd.concat([pd.read_csv(f, dtype=str) for f in files], ignore_index=True)

tab_utama, tab_pengurusan = st.tabs(["🔍 Semakan & Analisis PBD", "🔒 Pengurusan Data (Admin)"])

# TAB 2: ADMIN
with tab_pengurusan:
    if not st.session_state['is_admin']:
        st.subheader("🔐 Log Masuk Pentadbir (Admin)")
        col_pass, _ = st.columns([1, 2])
        with col_pass:
            input_pass = st.text_input("Kata Laluan Admin:", type="password")
            if st.button("Log Masuk", type="primary") and input_pass == ADMIN_PASSWORD:
                st.session_state['is_admin'] = True; st.rerun()
    else:
        c_title, c_logout = st.columns([4, 1])
        with c_title: st.subheader("⚙️ Panel Pengurusan Data Kelas")
        with c_logout:
            if st.button("🚪 Log Keluar Admin"): st.session_state['is_admin'] = False; st.rerun()
        st.markdown("---")
        
        col_up1, col_up2 = st.columns([1, 1])
        with col_up1:
            st.markdown("**1. Muat Naik Fail CSV Data Kelas**")
            pilih_tingkatan = st.selectbox("Tingkatan:", ["Tingkatan 1", "Tingkatan 2", "Tingkatan 3", "Tingkatan 4", "Tingkatan 5"])
            nama_kelas = st.text_input("Nama Kelas (Contoh: 1 KRK 1):", "")
            
            # HANYA MEMBENARKAN CSV SAHAJA DI SINI
            uploaded_file = st.file_uploader("Pilih Fail CSV idMe / Excel:", type=["csv"])
            
            if uploaded_file:
                parsed_df = parse_csv_file(uploaded_file)
                if parsed_df is not None and not parsed_df.empty:
                    st.info("💡 **SEMAKAN TERAKHIR:** Sila pastikan nama dan No. KP di bawah adalah tepat. Jika ada kesilapan, **klik dua kali pada petak jadual untuk membetulkannya** sebelum menekan butang Simpan.")
                    
                    edited_df = st.data_editor(parsed_df, use_container_width=True, hide_index=True)
                    
                    if st.button("💾 Simpan Data Kelas", type="primary"):
                        if not nama_kelas.strip(): st.error("❌ Sila masukkan Nama Kelas.")
                        else:
                            edited_df['Tingkatan_System'] = pilih_tingkatan
                            edited_df['Kelas_System'] = nama_kelas.strip()
                            safe_fn = f"{pilih_tingkatan}_{nama_kelas.strip()}.csv".replace(" ", "_").replace("/", "_")
                            edited_df.to_csv(os.path.join(DATA_DIR, safe_fn), index=False)
                            st.success("✅ Berjaya Disimpan!"); time.sleep(1); st.rerun()
                else: st.error("❌ Gagal membaca fail. Pastikan fail CSV anda mempunyai senarai nama dan No. KP yang jelas.")
        
        with col_up2:
            st.markdown("**2. Data Tersimpan**")
            files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
            if not files: st.info("Tiada data tersimpan.")
            else:
                for f in files: st.write(f"📄 {os.path.basename(f).replace('.csv', '')}")
                if st.button("🔥 Padam Semua Data (Reset)"):
                    for f in files: os.remove(f)
                    st.success("Semua data lama dibersihkan."); time.sleep(1); st.rerun()

# TAB 1: SEMAKAN
with tab_utama:
    df_all = load_all_saved_data()
    if df_all is None or df_all.empty:
        st.warning("⚠️ **Tiada data tersimpan.** Sila ke Tab Admin untuk muat naik fail CSV.")
    else:
        search_input = st.text_input("🔎 Masukkan No. Kad Pengenalan ATAU Nama Murid:", placeholder="Contoh: 131005101143").strip()
        matched_row = None
        s_digits = re.sub(r'\D', '', search_input)

        if search_input:
            for _, row in df_all.iterrows():
                db_ic = str(row.get('NO_KP', ''))
                db_nama = str(row.get('NAMA', '')).lower()
                if (s_digits and s_digits in db_ic) or (len(search_input) >= 3 and search_input.lower() in db_nama):
                    matched_row = row
                    break
                    
        if search_input and matched_row is None: st.error("❌ Rekod tidak dijumpai.")
        elif matched_row is not None:
            nama_m = matched_row.get('NAMA', 'TIADA MAKLUMAT')
            ic_m = matched_row.get('NO_KP', s_digits)
            tingkatan_m = matched_row.get('Tingkatan_System', '-')
            kelas_m = matched_row.get('Kelas_System', '-')

            st.markdown(f"""
            <div class="profile-card">
                <span style="color: #2563eb; font-size: 11px; font-weight: 800; letter-spacing: 1px;">PROFIL PENTAKSIRAN INDIVIDU — SMK DATO' SYED OMAR</span>
                <h2 style="margin: 8px 0; color: #0f172a; font-size: 24px;">{nama_m}</h2>
                <p style="margin: 0; font-size: 14px; color: #475569;">Tingkatan / Kelas: <b>{tingkatan_m} ({kelas_m})</b> &nbsp;|&nbsp; No. KP: <b>{ic_m}</b></p>
            </div>
            """, unsafe_allow_html=True)

            col_a, col_b = st.columns([1, 1.5])
            with col_a:
                st.write("<p style='margin-bottom: 5px; color: #475569; font-size: 14px;'>Status Carian</p>", unsafe_allow_html=True)
                st.markdown("<h2 style='margin-top: 0; font-size: 32px; color: #374151;'>REKOD DIJUMPAI ✅</h2>", unsafe_allow_html=True)
                st.write("")
                st.write(f"**No. Kad Pengenalan:** <span style='color: #16a34a;'>{ic_m}</span>", unsafe_allow_html=True)
                st.write(f"**Nama Penuh:** <span style='color: #16a34a;'>{nama_m}</span>", unsafe_allow_html=True)
            with col_b:
                st.success("Rekod murid disahkan wujud dan sedia dalam pangkalan data.")