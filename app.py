import streamlit as st
import pandas as pd
import numpy as np
import time

# --- Configuration & Branding ---
st.set_page_config(page_title="Air SLA Mapper", page_icon="✈️", layout="wide")

# Custom CSS for a slightly cleaner look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; background-color: #0052cc; color: white; }
    .stButton>button:hover { background-color: #003d99; color: white; }
    .stDownloadButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("✈️ Air SLA Mapper")
st.markdown("Upload your logistics files below to map SLAs, Zones, and Lanes with precision. The engine will automatically process heavy files in batches to ensure maximum stability.")
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
st.subheader("📂 Data Imports")
col1, col2, col3, col4 = st.columns(4)
with col1:
    file1 = st.file_uploader("1. SLA File (CSV)", type=['csv'], help="Must be a CSV file due to large row count.")
with col2:
    file2 = st.file_uploader("2. MH/DH Network", type=['csv', 'xlsx'])
with col3:
    file3 = st.file_uploader("3. Lane Promise", type=['csv', 'xlsx'])
with col4:
    file4 = st.file_uploader("4. Pincode Target", type=['csv', 'xlsx'])

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

# Only ONE button is defined here
if st.button("🚀 Run Air SLA Mapper Engine"):
    
    # Check if all files are uploaded FIRST
    if not (file1 and file2 and file3 and file4):
        st.warning("⚠️ Please upload all 4 required files before running the engine.")
    
    # If all files are present, proceed with processing
    else:
        try:
            with st.status("Engine Running...", expanded=True) as status:
                
                st.write("⚙️ Loading Reference Data (MH/DH, Lanes, Pincodes)...")
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

                st.write("📊 Crunching Massive SLA File...")
                
                # --- Heavy Processing with Live Progress Bar ---
                chunk_size = 100000
                processed_raw_chunks = []
                processed_clean_chunks = []
                total_rows_processed = 0
                
                file1.seek(0, 2)
                total_bytes = file1.tell()
                file1.seek(0)
                
                progress_bar = st.progress(0, text="Processing SLA chunks: 0%")
                
                temp_df = pd.read_csv(file1, nrows=0)
                clean_headers = temp_df.columns.astype(str).str.strip().str.lower().tolist()
                file1.seek(0)

                for chunk in pd.read_csv(file1, chunksize=chunk_size, low_memory=False, names=clean_headers, header=0):
                    current_bytes = file1.tell()
                    progress_pct = min(current_bytes / total_bytes, 1.0)
                    progress_bar.progress(progress_pct, text=f"Processing SLA chunks: {int(progress_pct*100)}%")
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

                progress_bar.progress(1.0, text="Processing SLA chunks: 100%")
                st.write("📦 Compiling Final Files...")
                import time
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
                
                status.update(label="✅ Mapping Complete!", state="complete", expanded=False)

            # --- Metrics Dashboard ---
            st.subheader("📈 Processing Results")
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Rows Processed", f"{total_rows_processed:,}")
            m2.metric("Valid Rows Kept (Clean)", f"{len(df_clean):,}")
            m3.metric("Rows Dropped", f"{total_rows_processed - len(df_clean):,}")
            st.divider()

            # --- Downloads & Previews ---
            col_down1, col_down2 = st.columns(2)
            
            with col_down1:
                st.markdown("### 🟢 Final Clean Data")
                st.caption("Only rows that successfully passed all mapping and validation rules.")
                if not df_clean.empty:
                    csv_clean = df_clean.to_csv(index=False).encode('utf-8')
                    st.download_button("⬇️ Download Clean Output (CSV)", data=csv_clean, file_name='Air_SLA_Mapper_Clean.csv', mime='text/csv')
                    with st.expander("Preview Clean Data"):
                        st.dataframe(df_clean.head(100), use_container_width=True)
                else:
                    st.warning("No rows passed the criteria.")

            with col_down2:
                st.markdown("### 🔍 Raw Diagnostic Data")
                st.caption("100% of data retained. Filter by the 'Final_Status' column in Excel to audit drop reasons.")
                csv_raw = df_raw.to_csv(index=False).encode('utf-8')
                st.download_button("⬇️ Download Diagnostic Report (CSV)", data=csv_raw, file_name='Air_SLA_Mapper_Diagnostic.csv', mime='text/csv')
                with st.expander("Preview Diagnostic Data"):
                    st.dataframe(df_raw.head(100), use_container_width=True)

        except Exception as e:
            st.error(f"❌ An error occurred during processing: {str(e)}")
