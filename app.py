import streamlit as st
import pandas as pd
import numpy as np
import time

# --- Configuration & Branding ---
st.set_page_config(page_title="Air SLA Mapper", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- HIGH-TECH CSS INJECTION ---
st.markdown("""
    <style>
    /* Main Background & Text */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    
    /* Glowing Title */
    h1 {
        background: -webkit-linear-gradient(45deg, #00f2fe, #4facfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900 !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0px 0px 20px rgba(0, 242, 254, 0.3);
    }

    /* Cyberpunk Button */
    .stButton>button {
        width: 100%; 
        border-radius: 8px; 
        font-weight: 800; 
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        color: #000000;
        border: none;
        box-shadow: 0 0 15px rgba(0, 201, 255, 0.4);
        transition: all 0.3s ease-in-out;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover { 
        box-shadow: 0 0 25px rgba(0, 201, 255, 0.8);
        transform: translateY(-2px);
    }

    /* Secondary Download Buttons */
    .stDownloadButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: bold; 
        background-color: rgba(255, 255, 255, 0.05);
        color: #00f2fe;
        border: 1px solid #00f2fe;
        transition: 0.3s;
    }
    .stDownloadButton>button:hover {
        background-color: #00f2fe;
        color: #000;
        box-shadow: 0 0 15px #00f2fe;
    }

    /* Glassmorphism Metric Cards */
    [data-testid="stMetricValue"] {
        color: #00f2fe;
        font-weight: 900;
        font-size: 2.5rem;
        text-shadow: 0 0 10px rgba(0,242,254,0.5);
    }
    [data-testid="stMetricLabel"] {
        color: #a0aec0;
        font-size: 1.1rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR: Control Center ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2000/2000887.png", width=80) # Techy icon
    st.markdown("## 📡 System Status")
    st.success("🟢 Engine Online")
    st.info("🧠 Memory Allocation: Optimal")
    st.markdown("---")
    st.markdown("### 🛠️ Engine Capabilities")
    st.markdown("""
    - **Chunk Processing:** Active
    - **VLOOKUP Bypass:** Enabled
    - **Failsafe Drops:** Enabled
    """)
    st.markdown("---")
    st.caption("Air SLA Mapper v2.0 | Core Routing Engine")

# --- MAIN DASHBOARD ---
st.title("⚡ Air SLA Mapper Engine")
st.markdown("_High-performance logistics mapping and SLA calculation core. Please initialize data inputs below._")
st.divider()

# --- Dictionaries ---
SMH_MAPPING_ORIGINAL = {
    'Motherhub_JKS_GMH': 'MotherHub_FRK',
    'MotherHub_YKB_Flex': 'Motherhub_DIC',
    'MotherHub_NDC': 'Motherhub_DIC',
    'Motherhub_ULB': 'Motherhub_ULB',
    'Motherhub_SHRTCRT_PRA': 'Motherhub_ULB',
    'Motherhub_SAI_4': 'Motherhub_SAI_4',
    'Motherhub_JKS': 'Motherhub_DIC',
    'Motherhub_MAL': 'Motherhub_MAL',
    'MotherHub_YKB_GMH': 'Motherhub_DIC',
    'Motherhub_SHRTCRT_BRI': 'Motherhub_DIC',
    'Motherhub_HRN': 'Motherhub_ULB',
    'Motherhub_GGN_GMH2': 'Motherhub_GGN',
    'MotherHub_BLR': 'Motherhub_MAL'
}
SMH_MAPPING_UPPER = {str(k).strip().upper(): str(v).strip().upper() for k, v in SMH_MAPPING_ORIGINAL.items()}

# --- File Upload Interface ---
st.subheader("📂 Data Inputs")
col1, col2, col3, col4 = st.columns(4)
with col1:
    file1 = st.file_uploader("1. SLA Query (CSV)", type=['csv'], help="Massive dataset. Must be CSV.")
with col2:
    file2 = st.file_uploader("2. MH-DH Network", type=['csv', 'xlsx'])
with col3:
    file3 = st.file_uploader("3. Lane SMH-DMH", type=['csv', 'xlsx'])
with col4:
    file4 = st.file_uploader("4. MDM-Pincode", type=['csv', 'xlsx'])

# --- Helper Functions ---
def read_file_safely(file, expected_cols=None):
    file.seek(0)
    is_csv = file.name.endswith('.csv')
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
            if still_missing:
                raise ValueError(f"Could not find columns: {', '.join(still_missing)}")
    return df

def clean_pincode(series):
    return pd.to_numeric(series, errors='coerce').fillna(0).astype(int).astype(str)

# --- Main Processing Block ---
st.divider()

if st.button("🚀 INITIATE PROCESSING SEQUENCE"):
    
    if not (file1 and file2 and file3 and file4):
        st.error("⚠️ SYSTEM HALTED: Missing telemetry files. Please upload all 4 datasets.")
    
    else:
        try:
            st.toast("Initialization Sequence Started...", icon="⏳")
            time.sleep(1)
            
            with st.status("🔗 Core Engine Engaged...", expanded=True) as status:
                
                st.write("⚙️ Compiling Reference Memory (MH/DH, Lanes, Pincodes)...")
                # --- Lookup Data Loading ---
                df2 = read_file_safely(file2, expected_cols=['dh name', 'mh name', 'zone'])
                df2['dh_upper'] = df2['dh name'].astype(str).str.strip().str.upper()
                df2['mh_upper'] = df2['mh name'].astype(str).str.strip().str.upper()
                df2['zone_upper'] = df2['zone'].astype(str).str.strip().str.upper()

                df2_clean = df2.dropna(subset=['dh_upper', 'mh_upper'])
                dh_to_mh = dict(zip(df2_clean['dh_upper'], df2_clean['mh_upper']))
                
                df2_zone = df2.dropna(subset=['mh_upper', 'zone_upper'])
                mh_to_zone = dict(zip(df2_zone['mh_upper'], df2_zone['zone_upper']))

                df3 = read_file_safely(file3)
                df3['lane'] = df3['source_facility_id'].astype(str).str.strip().str.upper() + "-" + df3['destination_facility_id'].astype(str).str.strip().str.upper()
                valid_lanes = set(df3['lane'].dropna().unique())

                df4 = read_file_safely(file4, expected_cols=['pincode'])
                df4['pincode_clean'] = clean_pincode(df4['pincode'])
                valid_pincodes = set(df4['pincode_clean'].unique())
                
                st.toast("Reference Memory Compiled. Engaging Heavy Processing.", icon="✅")

                st.write("📊 Crunching Massive SLA Payload...")
                
                # --- Heavy Processing with Live Progress Bar ---
                chunk_size = 100000
                processed_raw_chunks = []
                processed_clean_chunks = []
                total_rows_processed = 0
                
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
                    total_rows_processed += len(chunk)
                    
                    # 1. Exact Excel ROUNDUP Formula
                    total_sla = pd.to_numeric(chunk['total_sla_hrs'], errors='coerce').fillna(0)
                    f2f_buffer = pd.to_numeric(chunk['f2f_buffer_sla'], errors='coerce').fillna(0)
                    chunk['sla in days'] = np.ceil((total_sla - f2f_buffer) / 24)
                    
                    chunk['ekart_mh_upper'] = chunk['ekart_mh_name'].astype(str).str.strip().str.upper()
                    chunk['dh_upper'] = chunk['dh_name'].astype(str).str.strip().str.upper()
                    
                    # 2. SMH & DMH Mapping
                    chunk['smh'] = chunk['ekart_mh_upper'].map(SMH_MAPPING_UPPER).fillna(chunk['ekart_mh_upper'])
                    chunk['dmh'] = chunk['dh_upper'].map(dh_to_mh).fillna("#N/A")
                    
                    # 3. Zone Mapping
                    chunk['zone_from_ekart_mh'] = chunk['ekart_mh_upper'].map(mh_to_zone).fillna("#N/A")
                    chunk['zone_from_smh'] = chunk['smh'].map(mh_to_zone).fillna("#N/A")
                    chunk['source zone'] = np.where(chunk['zone_from_smh'] != "#N/A", chunk['zone_from_smh'], chunk['zone_from_ekart_mh'])
                    chunk['dest zone'] = chunk['dmh'].map(mh_to_zone).fillna("#N/A")
                    
                    # 4. Lane Mapping
                    chunk['lane_from_smh'] = chunk['smh'] + "-" + chunk['dmh']
                    chunk['lane_from_ekart_mh'] = chunk['ekart_mh_upper'] + "-" + chunk['dmh']
                    chunk['check_valid_lane_smh'] = chunk['lane_from_smh'].isin(valid_lanes)
                    chunk['check_valid_lane_ekart_mh'] = chunk['lane_from_ekart_mh'].isin(valid_lanes)
                    chunk['lane'] = np.where(chunk['check_valid_lane_smh'], chunk['lane_from_smh'], chunk['lane_from_ekart_mh'])
                    
                    # 5. Pincode Formatting
                    chunk['pincode_formatted'] = clean_pincode(chunk['pincode'])

                    # --- DIAGNOSTIC FLAGS ---
                    chunk['check_zone_mapped'] = (chunk['source zone'] != "#N/A") & (chunk['dest zone'] != "#N/A")
                    chunk['check_is_interzone'] = chunk['source zone'] != chunk['dest zone']
                    chunk['check_valid_lane'] = chunk['check_valid_lane_smh'] | chunk['check_valid_lane_ekart_mh']
                    chunk['check_valid_pincode'] = chunk['pincode_formatted'].isin(valid_pincodes)

                    chunk['final_status'] = np.where(
                        ~chunk['check_zone_mapped'], "Dropped: Missing Zone Mapping (#N/A)",
                        np.where(~chunk['check_is_interzone'], "Dropped: Same Zone (Not Inter-zone)",
                        np.where(~chunk['check_valid_lane'], "Dropped: Lane Not in Promise File",
                        np.where(~chunk['check_valid_pincode'], "Dropped: Pincode Not in Target File", 
                                 "Success: Kept in Final File"))))

                    clean_chunk = chunk[chunk['final_status'] == "Success: Kept in Final File"].copy()
                    processed_raw_chunks.append(chunk)
                    processed_clean_chunks.append(clean_chunk)

                progress_bar.progress(1.0, text="Data Extractor: 100%")
                st.write("📦 Packaging Final Datasets...")
                time.sleep(0.5)
                
                # --- Compiling Final Files ---
                df_raw = pd.concat(processed_raw_chunks, ignore_index=True)
                df_raw.columns = df_raw.columns.str.title()
                
                df_clean = pd.concat(processed_clean_chunks, ignore_index=True) if processed_clean_chunks else pd.DataFrame()
                if not df_clean.empty:
                    cols_to_drop = [
                        'ekart_mh_upper', 'dh_upper', 'zone_from_ekart_mh', 'zone_from_smh', 
                        'lane_from_smh', 'lane_from_ekart_mh', 'check_valid_lane_smh', 'check_valid_lane_ekart_mh',
                        'pincode_formatted', 'check_zone_mapped', 'check_is_interzone', 
                        'check_valid_lane', 'check_valid_pincode', 'final_status'
                    ]
                    df_clean.drop(columns=cols_to_drop, inplace=True, errors='ignore')
                    df_clean.columns = df_clean.columns.str.title()
                
                status.update(label="✅ Payload Packaged Successfully!", state="complete", expanded=False)

            # Trigger celebratory visual
            st.balloons()
            st.toast("System Process Complete!", icon="🎉")

            # --- Metrics Dashboard ---
            st.subheader("📈 Diagnostics Dashboard")
            m1, m2, m3 = st.columns(3)
            m1.metric("TOTAL ROWS PROCESSED", f"{total_rows_processed:,}")
            m2.metric("VALID ROWS KEPT", f"{len(df_clean):,}")
            m3.metric("ROWS FILTERED", f"{total_rows_processed - len(df_clean):,}")
            st.divider()

            # --- Downloads & Previews ---
            col_down1, col_down2 = st.columns(2)
            
            with col_down1:
                st.markdown("### 🟢 Final Clean Payload")
                st.caption("Passed all validation gates. Ready for deployment.")
                if not df_clean.empty:
                    csv_clean = df_clean.to_csv(index=False).encode('utf-8')
                    st.download_button("⬇️ Download Clean Output (CSV)", data=csv_clean, file_name='Air_SLA_Mapper_Clean.csv', mime='text/csv')
                    with st.expander("Preview Clean Data Stream"):
                        st.dataframe(df_clean.head(100), use_container_width=True)
                else:
                    st.warning("No rows passed the criteria.")

            with col_down2:
                st.markdown("### 🔍 Raw Diagnostic Logs")
                st.caption("100% of data retained. Trace error origins via 'Final_Status' column.")
                csv_raw = df_raw.to_csv(index=False).encode('utf-8')
                st.download_button("⬇️ Download Diagnostic Report (CSV)", data=csv_raw, file_name='Air_SLA_Mapper_Diagnostic.csv', mime='text/csv')
                with st.expander("Preview Raw Data Stream"):
                    st.dataframe(df_raw.head(100), use_container_width=True)

        except Exception as e:
            st.error(f"❌ CRITICAL FAILURE: {str(e)}")
