import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
import re
import base64
import time

# 1. Konfigurasi Halaman & Folder Storage Setempat
st.set_page_config(page_title="PBD - SMK Dato' Syed Omar", layout="wide", page_icon="🎓")

DATA_DIR = "data_pbd"
os.makedirs(DATA_DIR, exist_ok=True)

ADMIN_PASSWORD = "admin123"
LOGO_PATH = "logo.png"

if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

# =========================================================
# FUNGSI TUKAR IMEJ KEPADA BASE64 UNTUK HTML
# =========================================================
def get_base64_image(image_path):
    if os.path.exists(image_path):
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
        font-size: 32px;
        font-weight: 800;
        letter-spacing: 0.5px;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    }
    
    .system-title {
        font-size: 17px;
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

    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
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
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="85" style="border-radius: 10px; padding: 4px; background: rgba(255, 255, 255, 0.95); box-shadow: 0 4px 10px rgba(0,0,0,0.15);">'
else:
    logo_html = '<div style="background: rgba(255,255,255,0.15); border-radius: 14px; width: 85px; height: 85px; display: flex; align-items: center; justify-content: center; font-size: 38px;">🏫</div>'

st.markdown(f"""
<div class="header-banner">
    <div style="flex-shrink: 0;">{logo_html}</div>
    <div>
        <h1 class="school-title">SMK DATO' SYED OMAR</h1>
        <p class="system-title">✨ Sistem Pelaporan & Pengurusan Data Pentaksiran Bilik Darjah (PBD)</p>
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# FUNGSI PEMBANTU & PROCESSOR CSV PINTAR
# =========================================================
KATA_KUNCI_BUKAN_SUBJEK = [
    'bil', 'bil.', 'no', 'no.', 'nama', 'ic', 'kp', 'no kp', 'no. kp', 'no.kp', 'nokp',
    'tingkatan', 'kelas', 'jantina', 'kaum', 'bangsa', 'agregat', 'jumlah', 'purata',
    'tingkatan_system', 'kelas_system', 'sekolah', 'kpm', 'laporan', 'guru', 'tarikh', 'kod',
    'menengah', 'kebangsaan', 'status', 'catatan'
]

def clean_ic_digits(val):
    if pd.isna(val) or val is None: return ""
    s = str(val).strip()
    if 'e+' in s.lower() or 'e-' in s.lower():
        try: s = f"{float(s):.0f}"
        except Exception: pass
    elif s.endswith('.0'): s = s[:-2]
    return re.sub(r'\D', '', s)

def is_ic_match(ic1, ic2):
    c1 = clean_ic_digits(ic1)
    c2 = clean_ic_digits(ic2)
    if not c1 or not c2: return False
    if c1 == c2: return True
    if len(c1) == 11 and '0' + c1 == c2: return True
    if len(c2) == 11 and '0' + c2 == c1: return True
    return False

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

def read_idme_csv(uploaded_file):
    """Pembaca CSV idMe Pintar dengan Sokongan Auto-Pemisah (Comma, Semicolon, Tab) & Multi-Encoding"""
    try:
        raw_df = None
        encodings = ['utf-8', 'latin1', 'cp1252', 'utf-8-sig']
        
        # 1. Cuba pembacaan auto-detect delimiter
        for enc in encodings:
            try:
                uploaded_file.seek(0)
                raw_df = pd.read_csv(uploaded_file, header=None, dtype=str, keep_default_na=False, sep=None, engine='python', encoding=enc)
                if raw_df is not None and raw_df.shape[1] > 1:
                    break
            except Exception:
                continue

        # 2. Jika auto-detect gagal, cuba senarai pemisah manual
        if raw_df is None or raw_df.shape[1] <= 1:
            for sep_char in [';', ',', '\t']:
                for enc in encodings:
                    try:
                        uploaded_file.seek(0)
                        raw_df = pd.read_csv(uploaded_file, header=None, dtype=str, keep_default_na=False, sep=sep_char, encoding=enc)
                        if raw_df is not None and raw_df.shape[1] > 1:
                            break
                    except Exception:
                        continue
                if raw_df is not None and raw_df.shape[1] > 1:
                    break

        if raw_df is None or raw_df.empty:
            return None

        # 3. Cari baris header
        header_idx = None
        for idx, row in raw_df.iterrows():
            row_str = " ".join([str(v).upper() for v in row.values if pd.notna(v)])
            if ('NAMA' in row_str) and any(k in row_str for k in ['KP', 'IC', 'MYKAD', 'KAD PENGENALAN', 'NO_KP', 'NO.KP']):
                header_idx = idx
                break

        # Fallback 1: Cari baris berhampiran nombor IC pertama
        if header_idx is None:
            for idx, row in raw_df.iterrows():
                row_str = " ".join([str(v) for v in row.values if pd.notna(v)])
                if re.search(r'\b\d{12}\b', row_str) or re.search(r'\b\d{6}-\d{2}-\d{4}\b', row_str):
                    header_idx = max(0, idx - 1)
                    break

        # Fallback 2: Guna baris pertama jika tiada ditemui
        if header_idx is None:
            header_idx = 0

        header_row = raw_df.iloc[header_idx].values
        prev_row = raw_df.iloc[header_idx - 1].values if header_idx > 0 else None

        final_cols = []
        for i, col_val in enumerate(header_row):
            c_str = str(col_val).strip().replace('\n', ' ')
            p_str = str(prev_row[i]).strip().replace('\n', ' ') if prev_row is not None and i < len(prev_row) else ""
            
            if not c_str or c_str.startswith('Unnamed'):
                c_str = p_str if p_str else f"Lajur_{i+1}"
            elif p_str and p_str.upper() not in ['BIL', 'NAMA', 'NO KP', 'NO. KP', 'NO.KP', 'IC', 'JANTINA', 'KAUM'] and not p_str.upper().startswith('SEKOLAH'):
                if 'TP' in c_str.upper():
                    c_str = p_str
                elif c_str.upper() != p_str.upper():
                    c_str = f"{p_str} ({c_str})"

            final_cols.append(c_str)

        df = raw_df.iloc[header_idx + 1:].copy()
        df.columns = final_cols
        df = df.dropna(how='all').copy()

        # Garis semula nama lajur NO_KP & NAMA
        col_ic, col_nama = None, None
        for c in df.columns:
            c_u = str(c).upper().strip()
            if not col_ic and any(k in c_u for k in ['KP', 'IC', 'KAD', 'MYKAD', 'NO_KP', 'NO.KP', 'NO KP']) and 'SEKOLAH' not in c_u:
                col_ic = c
            elif not col_nama and any(k in c_u for k in ['NAMA', 'NAME', 'MURID', 'PELAJAR']) and 'SEKOLAH' not in c_u and 'GURU' not in c_u:
                col_nama = c

        rename_map = {}
        if col_ic: rename_map[col_ic] = 'NO_KP'
        if col_nama: rename_map[col_nama] = 'NAMA'
        if rename_map: df = df.rename(columns=rename_map)

        # Penapis hanya baris murid yang mempunyai No. KP sah (>= 8 digit)
        if 'NO_KP' in df.columns:
            df['NO_KP_CLEAN'] = df['NO_KP'].apply(clean_ic_digits)
            df = df[df['NO_KP_CLEAN'].str.len() >= 8].copy()
            df = df.drop(columns=['NO_KP_CLEAN'])

        # Buang lajur kosong
        valid_cols = [c for c in df.columns if str(c).strip() != '']
        df = df[valid_cols].copy()

        return df
    except Exception as e:
        st.error(f"Ralat membaca CSV: {e}")
        return None

def load_all_saved_data():
    files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not files: return None
    dfs = []
    for f in files:
        try:
            temp_df = pd.read_csv(f, dtype=str, keep_default_na=False)
            temp_df = temp_df.dropna(how='all').copy()
            dfs.append(temp_df)
        except Exception: pass
    return pd.concat(dfs, ignore_index=True) if dfs else None

# =========================================================
# TAB UTAMA
# =========================================================
tab_utama, tab_pengurusan = st.tabs(["🔍 Semakan & Analisis PBD", "🔒 Pengurusan Data (Admin Only)"])

# ---------------------------------------------------------
# TAB 2: PENGURUSAN DATA (ADMIN ONLY)
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
                    st.error("❌ Kata laluan salah.")
    else:
        c_title, c_logout = st.columns([4, 1])
        with c_title: st.subheader("📥 Muat Naik & Memadam Data PBD Kelas (CSV sahaja)")
        with c_logout:
            if st.button("🚪 Log Keluar Admin"):
                st.session_state['is_admin'] = False
                st.rerun()
                
        st.markdown("---")
        col_up1, col_up2 = st.columns([1, 1])
        with col_up1:
            st.markdown("**1. Maklumat Kelas & Fail CSV**")
            pilih_tingkatan = st.selectbox("Pilih Tingkatan:", ["Tingkatan 1", "Tingkatan 2", "Tingkatan 3", "Tingkatan 4", "Tingkatan 5"])
            nama_kelas = st.text_input("Nama Kelas (Contoh: 1 KRK 1 / 2 KRK 2):", "")
            uploaded_file = st.file_uploader("Pilih Fail CSV (idMe / Excel):", type=["csv"])
            
            if uploaded_file:
                df_upload = read_idme_csv(uploaded_file)
                if df_upload is not None and not df_upload.empty:
                    st.info("💡 **SEMAKAN TERAKHIR:** Semak senarai nama murid dan lajur subjek di bawah sebelum menyimpan.")
                    edited_df = st.data_editor(df_upload, use_container_width=True, hide_index=True)
                    
                    if st.button("💾 Simpan Data Secara Kekal", type="primary"):
                        if not nama_kelas.strip():
                            st.error("Sila masukkan Nama Kelas terlebih dahulu.")
                        else:
                            edited_df['Tingkatan_System'] = pilih_tingkatan
                            edited_df['Kelas_System'] = nama_kelas.strip()
                            
                            safe_fn = f"{pilih_tingkatan}_{nama_kelas.strip()}".replace(" ", "_").replace("/", "_") + ".csv"
                            file_path = os.path.join(DATA_DIR, safe_fn)
                            edited_df.to_csv(file_path, index=False)
                            
                            st.success(f"✅ Data `{pilih_tingkatan} - {nama_kelas}` berjaya disimpan!")
                            time.sleep(1)
                            st.rerun()
                else:
                    st.error("❌ Gagal membaca fail CSV. Pastikan fail mengandungi jadual murid idMe yang sah.")

        with col_up2:
            st.markdown("**2. Senarai Data Tersimpan Dalam Sistem**")
            fail_tersimpan = glob.glob(os.path.join(DATA_DIR, "*.csv"))
            if not fail_tersimpan:
                st.info("Belum ada data disimpan dalam sistem.")
            else:
                senarai_info = []
                for filepath in fail_tersimpan:
                    fname = os.path.basename(filepath).replace(".csv", "").replace("_", " ")
                    temp_df = pd.read_csv(filepath, dtype=str, keep_default_na=False)
                    senarai_info.append({"Fail / Kelas": fname, "Jumlah Murid": len(temp_df), "Path": filepath})
                
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
                        st.success(f"Data `{pilih_padam}` telah dipadam.")
                        time.sleep(1)
                        st.rerun()

# ---------------------------------------------------------
# TAB 1: SEMAKAN & ANALISIS PBD INDIVIDU
# ---------------------------------------------------------
with tab_utama:
    df_all = load_all_saved_data()
    
    if df_all is None or df_all.empty:
        st.warning("⚠️ **Tiada data tersimpan.** Hubungi Admin untuk muat naik data kelas terlebih dahulu di Tab 'Pengurusan Data'.")
    else:
        lajur_ic = next((c for c in df_all.columns if 'NO_KP' in str(c).upper() or 'IC' in str(c).upper() or 'KP' in str(c).upper()), None)
        lajur_nama = next((c for c in df_all.columns if 'NAMA' in str(c).upper()), None)

        senarai_subjek = []
        for col in df_all.columns:
            col_clean = str(col).lower().strip()
            is_metadata = any(col_clean == k or col_clean.startswith('lajur_') or k in col_clean for k in KATA_KUNCI_BUKAN_SUBJEK)
            if not is_metadata and col not in [lajur_ic, lajur_nama, 'Tingkatan_System', 'Kelas_System']:
                senarai_subjek.append(col)

        search_ic_input = st.text_input("🔎 Masukkan No. Kad Pengenalan Murid (Lengkap):", value="", placeholder="Contoh: 111013020847 atau 111013-02-0847")
        user_ic_digits = clean_ic_digits(search_ic_input)
        matched_row = None

        if user_ic_digits and lajur_ic:
            for _, row in df_all.iterrows():
                target_ic = str(row.get(lajur_ic, ''))
                if is_ic_match(user_ic_digits, target_ic):
                    matched_row = row
                    break

        if search_ic_input.strip() and matched_row is None:
            st.error(f"❌ Rekod murid dengan No. KP `{search_ic_input}` tidak dijumpai dalam sistem SMK Dato' Syed Omar.")
            with st.expander("🔍 Semak Senarai Nama & No. IC yang Wujud Dalam Fail"):
                preview_list = []
                for _, r in df_all.iterrows():
                    n = r[lajur_nama] if lajur_nama and lajur_nama in r else "Nama Tidak Nyata"
                    ic_raw = r[lajur_ic] if lajur_ic and lajur_ic in r else ""
                    preview_list.append({"Nama Murid": n, "No. IC Asal": ic_raw, "Digit IC": clean_ic_digits(ic_raw), "Kelas": r.get('Kelas_System', '-')})
                st.dataframe(pd.DataFrame(preview_list), use_container_width=True)

        elif matched_row is not None:
            nama_murid = matched_row.get(lajur_nama, 'REKOD TANPA NAMA')
            ic_display = clean_ic_digits(matched_row.get(lajur_ic, ''))
            if not ic_display: ic_display = user_ic_digits

            tingkatan_murid = matched_row.get('Tingkatan_System', '-')
            kelas_murid = matched_row.get('Kelas_System', '-')

            subjek_records = []
            for sub in senarai_subjek:
                val = matched_row.get(sub, '')
                tp_match = re.search(r'(\d+)', str(val))
                if tp_match:
                    tp_num = int(tp_match.group(1))
                    if 1 <= tp_num <= 6:
                        subjek_records.append({'Subjek': sub, 'TP': tp_num, 'TP_Str': f"TP {tp_num}"})

            tp_data = pd.DataFrame(subjek_records)

            total_subjek = len(tp_data)
            tp_cemerlang = len(tp_data[tp_data['TP'] >= 5]) if not tp_data.empty else 0
            tp_perlu_perhatian = len(tp_data[tp_data['TP'] <= 2]) if not tp_data.empty else 0

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
            if not tp_data.empty:
                col_graf, col_jadual = st.columns([10, 12])

                color_map = {
                    'TP 6': '#10b981', 'TP 5': '#22c55e', 'TP 4': '#3b82f6', 
                    'TP 3': '#f59e0b', 'TP 2': '#f97316', 'TP 1': '#ef4444'
                }

                with col_graf:
                    st.subheader("📊 Pencapaian TP Mengikut Subjek")
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