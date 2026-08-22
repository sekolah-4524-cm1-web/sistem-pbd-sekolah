import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
import re
import base64
import time

# =========================================================
# 1. KONFIGURASI HALAMAN & FOLDER STORAGE SETEMPAT
# =========================================================
st.set_page_config(page_title="PBD - SMK Dato' Syed Omar", layout="wide", page_icon="🎓")

DATA_DIR = "data_pbd"
os.makedirs(DATA_DIR, exist_ok=True)

ADMIN_PASSWORD = "admin123"
LOGO_PATH = "logoSMKDSO.png"

if 'is_admin' not in st.session_state:
    st.session_state['is_admin'] = False

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
    .stApp { background-color: #f8fafc; }
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
        padding: 14px 16px;
        font-weight: 600;
        font-size: 14px;
        text-align: left;
    }
    .pbd-table td {
        padding: 12px 16px;
        border-bottom: 1px solid #f1f5f9;
        color: #334155;
        font-size: 14px;
        font-weight: 600;
    }
    .pbd-table tr:hover { background-color: #f8fafc; }
    .badge {
        padding: 5px 14px;
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
logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="85" style="border-radius: 10px; padding: 4px; background: rgba(255, 255, 255, 0.95); box-shadow: 0 4px 10px rgba(0,0,0,0.15);">' if logo_b64 else '<div style="background: rgba(255,255,255,0.15); border-radius: 14px; width: 85px; height: 85px; display: flex; align-items: center; justify-content: center; font-size: 38px;">🏫</div>'

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
# FUNGSI PEMBANTU & PEMBACA CSV PINTAR
# =========================================================
def clean_ic_digits(val):
    if pd.isna(val) or val is None: return ""
    s = str(val).strip().replace('="', '').replace('"', '').replace("'", "")
    if 'e' in s.lower():
        try: s = f"{float(s):.0f}"
        except Exception: pass
    elif s.endswith('.0'): s = s[:-2]
    return re.sub(r'\D', '', s)

def is_ic_match(ic1, ic2):
    c1 = clean_ic_digits(ic1)
    c2 = clean_ic_digits(ic2)
    if not c1 or not c2: return False
    if c1 == c2: return True
    if c1.zfill(12) == c2.zfill(12): return True
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
    try:
        raw_df = None
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
        
        for enc in encodings:
            try:
                uploaded_file.seek(0)
                temp = pd.read_csv(uploaded_file, header=None, dtype=str, keep_default_na=False, encoding=enc)
                if temp is not None and temp.shape[1] > 1:
                    raw_df = temp
                    break
            except Exception: continue

        if raw_df is None or raw_df.empty: return None

        header_idx = 0
        for idx in range(min(20, len(raw_df))):
            row_str = " ".join([str(v).upper().strip() for v in raw_df.iloc[idx].values])
            if 'NAMA' in row_str and any(k in row_str for k in ['KP', 'IC', 'MYKAD', 'PENGENALAN', 'NO_KP', 'NO.KP']):
                header_idx = idx
                break

        final_cols = []
        num_cols = raw_df.shape[1]

        for c in range(num_cols):
            col_texts = []
            for r in range(header_idx + 1):
                val = str(raw_df.iloc[r, c]).strip().replace('\n', ' ')
                if val and not val.startswith('Unnamed') and not val.startswith('Lajur') and len(val) < 40:
                    val_u = val.upper()
                    if val_u not in ['BIL', 'NO', 'NO.', 'BIL.'] and not val.isdigit():
                        if val not in col_texts:
                            col_texts.append(val)

            chosen = ""
            for txt in reversed(col_texts):
                txt_u = txt.upper()
                if txt_u not in ['NAMA', 'NO KP', 'NO. KP', 'NO.KP', 'IC', 'JANTINA', 'KAUM', 'BANGSA', 'TP', 'PENTAKSIRAN']:
                    chosen = txt
                    break
            
            if not chosen and col_texts:
                chosen = col_texts[-1]
            if not chosen:
                chosen = f"Subjek_Tiada_Nama_{c+1}"

            final_cols.append(chosen)

        unique_cols = []
        seen = {}
        for col in final_cols:
            col_str = str(col).strip()
            if col_str not in seen:
                seen[col_str] = 1
                unique_cols.append(col_str)
            else:
                unique_cols.append(f"{col_str}_{seen[col_str]}")
                seen[col_str] += 1

        df = raw_df.iloc[header_idx + 1:].copy()
        df.columns = unique_cols 
        df = df.dropna(how='all').copy()

        col_ic, col_nama = None, None
        for c in df.columns:
            c_u = str(c).upper().strip()
            if not col_ic and any(k in c_u for k in ['KP', 'IC', 'KAD', 'MYKAD', 'NO_KP', 'NO.KP', 'NO KP', 'PENGENALAN']):
                col_ic = c
            elif not col_nama and any(k in c_u for k in ['NAMA', 'NAME', 'MURID', 'PELAJAR']):
                col_nama = c

        rename_map = {}
        if col_ic: rename_map[col_ic] = 'NO_KP'
        if col_nama: rename_map[col_nama] = 'NAMA'
        if rename_map: df = df.rename(columns=rename_map)

        if 'NO_KP' in df.columns:
            df['NO_KP_CLEAN'] = df['NO_KP'].apply(clean_ic_digits)
            df = df[df['NO_KP_CLEAN'].str.len() >= 8].copy()
            df = df.drop(columns=['NO_KP_CLEAN'])

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
                    st.info("💡 **SEMAKAN TERAKHIR:** Pastikan jadual kelihatan kemas sebelum menekan butang simpan.")
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
        st.warning("⚠️ **Tiada data tersimpan.** Sila pergi ke Tab 'Pengurusan Data' untuk muat naik data terkini.")
    else:
        lajur_ic = next((c for c in df_all.columns if any(k in str(c).upper() for k in ['NO_KP', 'IC', 'KP', 'PENGENALAN'])), None)
        lajur_nama = next((c for c in df_all.columns if 'NAMA' in str(c).upper()), None)

        if not lajur_ic:
            for c in df_all.columns:
                sample = [clean_ic_digits(v) for v in df_all[c].dropna().head(15)]
                if len(sample) > 0 and sum(1 for v in sample if len(v) in [11, 12]) / len(sample) >= 0.5:
                    lajur_ic = c
                    break

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
            st.error(f"❌ Rekod murid dengan No. KP `{search_ic_input}` tidak dijumpai.")
        elif matched_row is not None:
            nama_murid = matched_row.get(lajur_nama, 'REKOD TANPA NAMA')
            ic_display = clean_ic_digits(matched_row.get(lajur_ic, ''))
            if len(ic_display) == 11: ic_display = "0" + ic_display
            if not ic_display: ic_display = user_ic_digits

            tingkatan_murid = matched_row.get('Tingkatan_System', '-')
            kelas_murid = matched_row.get('Kelas_System', '-')

            subjek_records = []
            abaikan_lajur = [lajur_ic, lajur_nama, 'Tingkatan_System', 'Kelas_System', 'NO_KP', 'NAMA']
            
            for col in df_all.columns:
                if col in abaikan_lajur: continue
                
                # Baca nilai pada sel ini & buang ruang kosong
                val = str(matched_row.get(col, '')).strip().upper()
                
                tp_num = None
                
                # Ujian 1: Jika nilai adalah sekadar "1" hingga "6"
                if val in ['1', '2', '3', '4', '5', '6']:
                    tp_num = int(val)
                else:
                    # Ujian 2: Mengesan jika tertulis "TP 4", "TP:4", "TP4"
                    match1 = re.search(r'TP\s*[:\-]?\s*([1-6])', val)
                    if match1:
                        tp_num = int(match1.group(1))
                    else:
                        # Ujian 3: Mengesan jika tertulis "TAHAP PENGUASAAN 4", "TAHAP 4" dsb
                        match2 = re.search(r'TAHAP(?:PENGUASAAN)?\s*([1-6])', val.replace(" ", ""))
                        if match2:
                            tp_num = int(match2.group(1))

                # Jika dijumpai TP, kita kumpulkan
                if tp_num is not None:
                    display_subjek = str(col).strip()
                    display_subjek = re.sub(r'Subjek_Tiada_Nama_\d+', 'Subjek', display_subjek)
                    if len(display_subjek) > 40:
                        display_subjek = display_subjek[:40] + "..."

                    subjek_records.append({
                        'Subjek': display_subjek,
                        'TP': tp_num,
                        'TP_Str': f"TP {tp_num}"
                    })

            tp_data = pd.DataFrame(subjek_records)
            
            if tp_data.empty:
                st.warning("⚠️ **Tiada data Tahap Penguasaan (TP) dapat dipisahkan (extracted) dari profil murid ini.**")
                
                # KOTAK DIAGNOSTIK BARU
                with st.expander("🛠️ BANTUAN DIAGNOSTIK (Sila klik dan salin kotak di bawah)", expanded=True):
                    st.markdown("Oleh kerana graf masih tidak keluar, sistem memaparkan bagaimana **Data Sebenar CSV** dibaca oleh sistem. Sila *copy* semua teks di bawah ini dan beri kepada saya (AI) supaya saya boleh membina kod tapisan yang 100% tepat:")
                    st.json(matched_row.to_dict())
            else:
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
                    tp_max = tp_data['TP'].max()
                    st.metric("Pencapaian TP Tertinggi", f"TP {tp_max}")

                st.markdown("---")
                
                color_map = {
                    'TP 6': '#10b981', 'TP 5': '#22c55e', 'TP 4': '#3b82f6', 
                    'TP 3': '#f59e0b', 'TP 2': '#f97316', 'TP 1': '#ef4444'
                }

                col_graf, col_jadual = st.columns([1.6, 1.0], gap="large")

                with col_graf:
                    st.subheader("📊 Skor Tahap Penguasaan (TP)")
                    chart_height = max(450, len(tp_data) * 48)

                    fig_bar = px.bar(
                        tp_data, x='TP', y='Subjek', orientation='h', 
                        text='TP_Str', color='TP_Str', color_discrete_map=color_map
                    )
                    
                    fig_bar.update_layout(
                        xaxis=dict(
                            range=[0, 6.9], tickvals=[1, 2, 3, 4, 5, 6],
                            title="<b>Tahap Penguasaan (TP)</b>", tickfont=dict(size=12)
                        ),
                        yaxis=dict(
                            title="", categoryorder='total ascending', 
                            tickfont=dict(size=16, color="#0f172a", family="Arial Black, sans-serif"),
                            automargin=False
                        ),
                        bargap=0.2, showlegend=False, height=chart_height,
                        margin=dict(l=350, r=40, t=10, b=30),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
                    )
                    fig_bar.update_traces(
                        textposition='outside',
                        textfont=dict(size=12, color="#0f172a", weight="bold"),
                        cliponaxis=False
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

                with col_jadual:
                    st.subheader("📋 Rujukan TP & Tafsiran Subjek")
                    rows_html = ""
                    for _, row in tp_data.iterrows():
                        subjek_name = row['Subjek']
                        tp_val = row['TP']
                        tafsiran_txt, badge_cls = dapatkan_tafsiran_tp(tp_val)
                        rows_html += f"<tr><td><b>{subjek_name}</b></td><td style='text-align: center;'><span class='badge {badge_cls}'>TP {tp_val}</span></td><td style='font-size: 13px; color: #475569;'>{tafsiran_txt}</td></tr>"
                    st.markdown(f"<table class='pbd-table'><thead><tr><th style='width: 35%;'>Subjek</th><th style='width: 20%; text-align: center;'>Tahap</th><th style='width: 45%;'>Tafsiran Status</th></tr></thead><tbody>{rows_html}</tbody></table>", unsafe_allow_html=True)