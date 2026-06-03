import streamlit as st
import pandas as pd
import numpy as np
import time
import os

# --- Configuration & Branding ---
st.set_page_config(page_title="Air SLA Mapper", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- Initialize Session State for UI Locking ---
if 'processed' not in st.session_state:
    st.session_state.processed = False

# --- HIGH-TECH UI / CYBERPUNK CSS INJECTION ---
st.markdown("""
    <style>
    .block-container { padding-left: 2rem !important; padding-right: 2rem !important; max-width: 100% !important; }
    section[data-testid="stSidebar"] { width: 260px !important; min-width: 260px !important; background-color: #060913 !important; border-right: 1px solid rgba(0, 242, 254, 0.1); }
    .stApp { background: radial-gradient(circle at 50% 0%, #111827 0%, #060913 100%); color: #e2e8f0; }
    h1 { background: -webkit-linear-gradient(45deg, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 900 !important; text-transform: uppercase; letter-spacing: 3px; text-shadow: 0px 0px 25px rgba(0, 242, 254, 0.4); }
    h2, h3 { border-left: 4px solid #00f2fe; padding-left: 12px !important; text-transform: uppercase; letter-spacing: 2px; color: #e2e8f0 !important; text-shadow: 0 0 10px rgba(0, 242, 254, 0.2); }
    hr { border: none; height: 1px; background: linear-gradient(90deg, transparent, #00f2fe, transparent); box-shadow: 0 0 10px #00f2fe; opacity: 0.6; }
    [data-testid="stFileUploadDropzone"] { background-color: rgba(0, 242, 254, 0.02) !important; border: 1px dashed rgba(0, 242, 254, 0.4) !important; border-radius: 12px !important; transition: all 0.3s ease-in-out; }
    [data-testid="stFileUploadDropzone"]:hover { background-color: rgba(0, 242, 254, 0.08) !important; border: 1px solid #00f2fe !important; box-shadow: 0 0 15px rgba(0, 242, 254, 0.3) !important; transform: scale(1.02); }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 900; font-size: 1.1rem; background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%); color: #000000 !important; border: none; box-shadow: 0 0 20px rgba(0, 201, 255, 0.5); transition: all 0.3s ease-in-out; text-transform: uppercase; letter-spacing: 2px; }
    .stButton>button:hover { box-shadow: 0 0 35px rgba(0, 201, 255, 0.9); transform: translateY(-3px); }
    .stDownloadButton>button { width: 300px; border-radius: 6px; font-weight: bold; background-color: rgba(0, 242, 254, 0.05); color: #00f2fe !important; border: 1px solid #00f2fe; box-shadow: 0 0 10px rgba(0, 242, 254, 0.1); transition: 0.3s; text-transform: uppercase; letter-spacing: 1px; }
    .stDownloadButton>button:hover { background-color: #00f2fe; color: #000 !important; box-shadow: 0 0 20px #00f2fe; }
    [data-testid="metric-container"] { background: rgba(0, 242, 254, 0.03); border: 1px solid rgba(0, 242, 254, 0.2); border-radius: 12px; padding: 15px 20px; box-shadow: inset 0 0 20px rgba(0, 242, 254, 0.05), 0 4px 15px rgba(0,0,0,0.3); backdrop-filter: blur(10px); transition: transform 0.3s ease; }
    [data-testid="metric-container"]:hover { transform: translateY(-5px); border: 1px solid rgba(0, 242, 254, 0.5); box-shadow: inset 0 0 20px rgba(0, 242, 254, 0.1), 0 8px 25px rgba(0,242,254,0.2); }
    [data-testid="stMetricValue"] { color: #00f2fe !important; font-weight: 900; font-size: 3rem; text-shadow: 0 0 15px rgba(0,242,254,0.6); font-family: 'Courier New', Courier, monospace; }
    [data-testid="stMetricLabel"] { color: #a0aec0 !important; font-size: 1rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; }
    .streamlit-expanderHeader { background-color: rgba(255,255,255,0.02) !important; border-radius: 5px; border: 1px solid rgba(255,255,255,0.05); font-family: 'Courier New', Courier, monospace; color: #4facfe !important; }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: Control Center ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2000/2000887.png", width=60)
    st.markdown("## 📡 System")
    st.success("🟢 Online")
    st.info("🧠 Mem: Direct-to-Disk")
    st.markdown("---")
    st.markdown("### 🛠️ Engine Rules")
    st.markdown("""
    - **Disk Streaming:** Active
    - **Chunking:** Active
    - **Failsafe:** Enabled
    """)
    st.markdown("---")
    st.caption("v5.0 | Multi-Level Core")

# --- MAIN DASHBOARD ---
st.title("⚡ Air SLA Mapper Engine")
st.markdown("_High-performance logistics mapping and SLA calculation core._")
st.markdown("<hr>", unsafe_allow_html=True)

# --- Dictionaries ---
SMH_MAPPING_ORIGINAL = {
    'Motherhub_JKS_GMH': 'MotherHub_FRK', 'MotherHub_YKB_Flex': 'Motherhub_DIC', 'MotherHub_NDC': 'Motherhub_DIC',
    'Motherhub_ULB': 'Motherhub_ULB', 'Motherhub_SHRTCRT_PRA': 'Motherhub_ULB', 'Motherhub_SAI_4': 'Motherhub_SAI_4',
    'Motherhub_JKS': 'Motherhub_DIC', 'Motherhub_MAL': 'Motherhub_MAL', 'MotherHub_YKB_GMH': 'Motherhub_DIC',
    'Motherhub_SHRTCRT_BRI': 'Motherhub_DIC', 'Motherhub_HRN': 'Motherhub_ULB', 'Motherhub_GGN_GMH2': 'Motherhub_GGN',
    'MotherHub_BLR': 'Motherhub_MAL','Motherhub_SHRTCRT_PIT': 'Motherhub_DIC'
}
SMH_MAPPING_UPPER = {str(k).strip().upper(): str(v).strip().upper() for k, v in SMH_MAPPING_ORIGINAL.items()}

# --- File Upload Interface ---
st.subheader("⚙️ Operation Configuration")
operation_level = st.radio("Select Routing Logic Level:", ["PH Level", "City Level"], horizontal=True)
st.markdown("<br>", unsafe_allow_html=True)

st.subheader("📂 Data Inputs")
col1, col2, col3, col4 = st.columns(4)

with col1: 
    file1 = st.file_uploader("1. SLA Query (CSV)", type=['csv', 'zip'], key="upload_f1")
with col2: 
    file2 = st.file_uploader("2. MH-DH Network", type=['csv', 'xlsx', 'zip'], key="upload_f2")
with col3: 
    file3 = st.file_uploader("3. Lane MH-MH", type=['csv', 'xlsx', 'zip'], key="upload_f3")
with col4: 
    file4 = st.file_uploader("4. MDM-Pincode", type=['csv', 'xlsx', 'zip'], key="upload_f4")

def read_file_safely(file, expected_cols=None):
    file.seek(0)
    is_csv = file.name.endswith('.csv') or file.name.endswith('.zip')
    df = pd.read_csv(file, header=0, low_memory=False) if is_csv else pd.read_excel(file, header=0)
    df.columns = df.columns.astype(str).str.strip().str.lower()
    if expected_cols:
        expected_cols_lower = [c.lower() for c in expected_cols]
        missing_cols = [c for c in expected_cols_lower if c not in df.columns]
        if missing_cols:
            file.seek(0)
            df = pd.read_csv(file, header=1, low_memory=False) if is_csv else pd.read_excel(file, header=1)
            df.columns = df.columns.astype(str).str.strip().str.lower()
            still_missing = [c for c in expected_cols_lower if c not in df.columns]
            if still_missing: raise ValueError(f"Could not find columns: {', '.join(still_missing)}")
    return df

def clean_pincode(series):
    return pd.to_numeric(series, errors='coerce').fillna(0).astype(int).astype(str)

st.markdown("<hr>", unsafe_allow_html=True)

# Define File Paths Globally
clean_csv_path = "Air_SLA_Mapper_Clean.csv"
raw_csv_path = "Air_SLA_Mapper_Diagnostic.csv"

# --- MAIN ENGINE TRIGGER ---
if st.button("🚀 INITIATE PROCESSING SEQUENCE"):
    if not (file1 and file2 and file3 and file4):
        st.error("⚠️ SYSTEM HALTED: Missing telemetry files. Please upload all 4 datasets.")
    else:
        try:
            # Reset state for a new run
            st.session_state.processed = False
            
            with st.status("🔗 Core Engine Engaged...", expanded=True) as status:
                
                ingest_bar = st.progress(0, text="Ingesting Data: Allocating Memory...")
                
                # 1. Parse MH-DH
                st.write("⚙️ Parsing MH-DH Network...")
                df2 = read_file_safely(file2, expected_cols=['dh name', 'mh name', 'zone'])
                df2['dh_upper'] = df2['dh name'].astype(str).str.strip().str.upper()
                df2['mh_upper'] = df2['mh name'].astype(str).str.strip().str.upper()
                df2['zone_upper'] = df2['zone'].astype(str).str.strip().str.upper()
                dh_to_mh = dict(zip(df2.dropna(subset=['dh_upper', 'mh_upper'])['dh_upper'], df2.dropna(subset=['dh_upper', 'mh_upper'])['mh_upper']))
                mh_to_zone = dict(zip(df2.dropna(subset=['mh_upper', 'zone_upper'])['mh_upper'], df2.dropna(subset=['mh_upper', 'zone_upper'])['zone_upper']))
                ingest_bar.progress(33, text="Ingesting Data: MH-DH Network Loaded")

                # 2. Parse Lane Logic (PH vs City Level)
                st.write(f"⚙️ Parsing Lane Logic ({operation_level})...")
                
                if operation_level == "City Level":
                    df3 = read_file_safely(file3, expected_cols=['source city', 'source_facility_id', 'destination_facility_id'])
                    df3['source_city_upper'] = df3['source city'].astype(str).str.strip().str.upper()
                    df3['src_fac_upper'] = df3['source_facility_id'].astype(str).str.strip().str.upper()
                    df3['dest_fac_upper'] = df3['destination_facility_id'].astype(str).str.strip().str.upper()
                    
                    # Create dict mapping MH -> Source City
                    mh_to_city = dict(zip(df3.dropna(subset=['src_fac_upper', 'source_city_upper'])['src_fac_upper'], 
                                          df3.dropna(subset=['src_fac_upper', 'source_city_upper'])['source_city_upper']))
                    
                    # City Level Lanes: Source City -> Dest Facility
                    df3['lane'] = df3['source_city_upper'] + "-" + df3['dest_fac_upper']
                    valid_lanes = set(df3['lane'].dropna().unique())
                    
                else:
                    df3 = read_file_safely(file3, expected_cols=['source_facility_id', 'destination_facility_id'])
                    df3['src_fac_upper'] = df3['source_facility_id'].astype(str).str.strip().str.upper()
                    df3['dest_fac_upper'] = df3['destination_facility_id'].astype(str).str.strip().str.upper()
                    
                    # PH Level Lanes: Source Facility -> Dest Facility
                    df3['lane'] = df3['src_fac_upper'] + "-" + df3['dest_fac_upper']
                    valid_lanes = set(df3['lane'].dropna().unique())

                ingest_bar.progress(66, text="Ingesting Data: Lane Network Loaded")

                # 3. Parse Pincodes
                st.write("⚙️ Parsing MDM Pincodes...")
                df4 = read_file_safely(file4, expected_cols=['pincode'])
                df4['pincode_clean'] = clean_pincode(df4['pincode'])
                valid_pincodes = set(df4['pincode_clean'].unique())
                ingest_bar.progress(100, text="Ingesting Data: 100% Complete")
                
                time.sleep(0.5)
                ingest_bar.empty()
                st.write("📊 Crunching Massive SLA Payload (Streaming to Disk)...")
                
                # Delete old files if they exist to start fresh
                if os.path.exists(clean_csv_path): os.remove(clean_csv_path)
                if os.path.exists(raw_csv_path): os.remove(raw_csv_path)

                chunk_size = 100000
                total_rows_processed = 0
                total_clean_rows = 0
                total_dropped_rows = 0
                
                file1.seek(0, 2)
                total_bytes = file1.tell()
                file1.seek(0)
                
                progress_bar = st.progress(0, text="Data Extractor: 0%")
                temp_df = pd.read_csv(file1, nrows=0)
                clean_headers = temp_df.columns.astype(str).str.strip().str.lower().tolist()
                file1.seek(0)

                for chunk in pd.read_csv(file1, chunksize=chunk_size, low_memory=False, names=clean_headers, header=0):
                    current_bytes = file1.tell()
                    progress_pct = min(current_bytes / total_bytes, 1.0)
                    progress_bar.progress(progress_pct, text=f"Data Extractor: {int(progress_pct*100)}%")
                    
                    # Base Processing
                    total_sla = pd.to_numeric(chunk['total_sla_hrs'], errors='coerce').fillna(0)
                    f2f_buffer = pd.to_numeric(chunk['f2f_buffer_sla'], errors='coerce').fillna(0)
                    chunk['sla in days'] = np.ceil((total_sla - f2f_buffer) / 24)
                    chunk['ekart_mh_upper'] = chunk['ekart_mh_name'].astype(str).str.strip().str.upper()
                    chunk['dh_upper'] = chunk['dh_name'].astype(str).str.strip().str.upper()
                    
                    chunk['smh'] = chunk['ekart_mh_upper'].map(SMH_MAPPING_UPPER).fillna(chunk['ekart_mh_upper'])
                    chunk['dmh'] = chunk['dh_upper'].map(dh_to_mh).fillna("#N/A")
                    
                    # Zone Mapping
                    chunk['zone_from_ekart_mh'] = chunk['ekart_mh_upper'].map(mh_to_zone).fillna("#N/A")
                    chunk['zone_from_smh'] = chunk['smh'].map(mh_to_zone).fillna("#N/A")
                    chunk['source zone'] = np.where(chunk['zone_from_smh'] != "#N/A", chunk['zone_from_smh'], chunk['zone_from_ekart_mh'])
                    chunk['dest zone'] = chunk['dmh'].map(mh_to_zone).fillna("#N/A")
                    
                    # Target Routing Rules Based on Radio Button Selection
                    if operation_level == "City Level":
                        chunk['city_from_smh'] = chunk['smh'].map(mh_to_city).fillna("#N/A")
                        chunk['city_from_ekart_mh'] = chunk['ekart_mh_upper'].map(mh_to_city).fillna("#N/A")
                        
                        chunk['lane_from_smh'] = chunk['city_from_smh'] + "-" + chunk['dmh']
                        chunk['lane_from_ekart_mh'] = chunk['city_from_ekart_mh'] + "-" + chunk['dmh']
                    else:
                        chunk['lane_from_smh'] = chunk['smh'] + "-" + chunk['dmh']
                        chunk['lane_from_ekart_mh'] = chunk['ekart_mh_upper'] + "-" + chunk['dmh']
                    
                    chunk['check_valid_lane_smh'] = chunk['lane_from_smh'].isin(valid_lanes)
                    chunk['check_valid_lane_ekart_mh'] = chunk['lane_from_ekart_mh'].isin(valid_lanes)
                    chunk['lane'] = np.where(chunk['check_valid_lane_smh'], chunk['lane_from_smh'], chunk['lane_from_ekart_mh'])
                    
                    # Pincode Cleanup
                    chunk['pincode_formatted'] = clean_pincode(chunk['pincode'])

                    # Validation Gates
                    chunk['check_zone_mapped'] = (chunk['source zone'] != "#N/A") & (chunk['dest zone'] != "#N/A")
                    chunk['check_is_interzone'] = chunk['source zone'] != chunk['dest zone']
                    chunk['check_valid_lane'] = chunk['check_valid_lane_smh'] | chunk['check_valid_lane_ekart_mh']
                    chunk['check_valid_pincode'] = chunk['pincode_formatted'].isin(valid_pincodes)

                    chunk['final_status'] = np.where(
                        ~chunk['check_zone_mapped'], "Dropped: Missing Zone Mapping (#N/A)",
                        np.where(~chunk['check_is_interzone'], "Dropped: Same Zone (Not Inter-zone)",
                        np.where(~chunk['check_valid_lane'], "Dropped: Lane Not in Promise File",
                        np.where(~chunk['check_valid_pincode'], "Dropped: Pincode Not in Target File", "Success: Kept in Final File"))))

                    # --- SEPARATE CHUNKS ---
                    clean_chunk = chunk[chunk['final_status'] == "Success: Kept in Final File"].copy()
                    dropped_chunk = chunk[chunk['final_status'] != "Success: Kept in Final File"].copy()
                    
                    total_rows_processed += len(chunk)
                    total_clean_rows += len(clean_chunk)
                    total_dropped_rows += len(dropped_chunk)
                    
                    # Setup drop columns for clean file export
                    cols_to_drop = [
                        'ekart_mh_upper', 'dh_upper', 'zone_from_ekart_mh', 'zone_from_smh', 
                        'lane_from_smh', 'lane_from_ekart_mh', 'check_valid_lane_smh', 'check_valid_lane_ekart_mh',
                        'pincode_formatted', 'check_zone_mapped', 'check_is_interzone', 'check_valid_lane', 'check_valid_pincode', 'final_status',
                        'city_from_smh', 'city_from_ekart_mh'
                    ]
                    
                    # 1. Format & Write RAW File (ONLY the Dropped Rows)
                    if not dropped_chunk.empty:
                        dropped_chunk.columns = dropped_chunk.columns.str.title()
                        dropped_chunk.to_csv(raw_csv_path, mode='a', index=False, header=not os.path.exists(raw_csv_path))
                    
                    # 2. Format & Write CLEAN File (Drop backend cols)
                    if not clean_chunk.empty:
                        clean_chunk_out = clean_chunk.drop(columns=cols_to_drop, errors='ignore')
                        clean_chunk_out.columns = clean_chunk_out.columns.str.title()
                        clean_chunk_out.to_csv(clean_csv_path, mode='a', index=False, header=not os.path.exists(clean_csv_path))

                progress_bar.progress(1.0, text="Data Extractor: 100%")
                st.write("📦 Packaging Final Datasets...")
                time.sleep(0.5)
                status.update(label="✅ Payload Packaged Successfully!", state="complete", expanded=False)

            # Save state metrics so UI doesn't disappear
            st.session_state.processed = True
            st.session_state.total_rows = total_rows_processed
            st.session_state.total_clean = total_clean_rows
            st.session_state.total_dropped = total_dropped_rows

        except Exception as e:
            st.error(f"❌ CRITICAL FAILURE: {str(e)}")

# --- POST-PROCESSING UI (This stays visible even after clicking download!) ---
if st.session_state.processed:
    st.toast("System Process Complete!", icon="🎉")

    # --- Metrics Dashboard ---
    st.subheader("📈 Diagnostics Dashboard")
    m1, m2, m3 = st.columns(3)
    m1.metric("TOTAL ROWS PROCESSED", f"{st.session_state.total_rows:,}")
    m2.metric("VALID ROWS KEPT", f"{st.session_state.total_clean:,}")
    m3.metric("ROWS FILTERED", f"{st.session_state.total_dropped:,}")
    st.markdown("<hr>", unsafe_allow_html=True)

    # --- Downloads & Previews ---
    st.markdown("### 🟢 Final Air SLA Lanes")
    st.caption("Passed all validation gates. Clean data output ready for downstream processes.")
    
    if os.path.exists(clean_csv_path) and st.session_state.total_clean > 0:
        with open(clean_csv_path, "rb") as f:
            st.download_button("⬇️ Download Clean Output (CSV)", data=f, file_name='Air_SLA_Mapper_Clean.csv', mime='text/csv', key='btn_clean')
        with st.expander("Preview Clean Data Stream (Full Width)", expanded=True):
            preview_clean = pd.read_csv(clean_csv_path, nrows=100)
            st.dataframe(preview_clean, use_container_width=True)
    else:
        st.warning("No rows passed the criteria.")
        
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("### 🔍 Raw Diagnostic Logs (Filtered Rows Only)")
    st.caption("Contains **only** the rows that were dropped, with full diagnostic columns so you can audit the rejections.")
    
    if os.path.exists(raw_csv_path) and st.session_state.total_dropped > 0:
        with open(raw_csv_path, "rb") as f:
            st.download_button("⬇️ Download Diagnostic Report (CSV)", data=f, file_name='Air_SLA_Mapper_Filtered.csv', mime='text/csv', key='btn_raw')
        with st.expander("Preview Filtered Data Stream (Full Width)"):
            preview_raw = pd.read_csv(raw_csv_path, nrows=100)
            st.dataframe(preview_raw, use_container_width=True)
    else:
        st.success("Zero rows were filtered out! A perfect run.")
        
