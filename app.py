import streamlit as st
import pandas as pd
import numpy as np

# --- Configuration ---
st.set_page_config(page_title="Logistics SLA Processor", layout="wide")
st.title("Logistics Data & SLA Processor (Diagnostic Mode)")

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

st.header("Upload Files")
col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("1. Upload SLA File (Must be CSV)", type=['csv'])
    file2 = st.file_uploader("2. Upload MH/DH Network File", type=['csv', 'xlsx'])
with col2:
    file3 = st.file_uploader("3. Upload Lane Promise File", type=['csv', 'xlsx'])
    file4 = st.file_uploader("4. Upload Pincode Target File", type=['csv', 'xlsx'])

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

if st.button("Process Data") and file1 and file2 and file3 and file4:
    try:
        with st.spinner("Preparing dictionaries for case-insensitive matching..."):
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

        with st.spinner("Processing massive SLA file safely..."):
            chunk_size = 100000
            processed_raw_chunks = []
            processed_clean_chunks = []
            
            file1.seek(0)
            temp_df = pd.read_csv(file1, nrows=0)
            clean_headers = temp_df.columns.astype(str).str.strip().str.lower().tolist()
            file1.seek(0)

            for chunk in pd.read_csv(file1, chunksize=chunk_size, low_memory=False, names=clean_headers, header=0):
                
                # 1. Exact Excel ROUNDUP Formula
                total_sla = pd.to_numeric(chunk['total_sla_hrs'], errors='coerce').fillna(0)
                f2f_buffer = pd.to_numeric(chunk['f2f_buffer_sla'], errors='coerce').fillna(0)
                chunk['sla in days'] = np.ceil((total_sla - f2f_buffer) / 24)
                
                chunk['ekart_mh_upper'] = chunk['ekart_mh_name'].astype(str).str.strip().str.upper()
                chunk['dh_upper'] = chunk['dh_name'].astype(str).str.strip().str.upper()
                
                # 2. SMH & DMH Mapping (Use #N/A for missing mappings to mimic Excel)
                chunk['smh'] = chunk['ekart_mh_upper'].map(SMH_MAPPING_UPPER).fillna(chunk['ekart_mh_upper'])
                chunk['dmh'] = chunk['dh_upper'].map(dh_to_mh).fillna("#N/A")
                
                # 3. Zone Mapping with Fallback Logic
                chunk['zone_from_ekart_mh'] = chunk['ekart_mh_upper'].map(mh_to_zone).fillna("#N/A")
                chunk['zone_from_smh'] = chunk['smh'].map(mh_to_zone).fillna("#N/A")
                
                # Final Source Zone: Use SMH mapping first. If #N/A, fallback to Ekart_MH mapping.
                chunk['source zone'] = np.where(
                    chunk['zone_from_smh'] != "#N/A", 
                    chunk['zone_from_smh'], 
                    chunk['zone_from_ekart_mh']
                )

                chunk['dest zone'] = chunk['dmh'].map(mh_to_zone).fillna("#N/A")
                
                # 4. Lane Mapping
                chunk['lane'] = chunk['smh'] + "-" + chunk['dmh']
                
                # 5. Pincode Formatting
                chunk['pincode_formatted'] = clean_pincode(chunk['pincode'])

                # --- DIAGNOSTIC FLAGS ---
                chunk['check_zone_mapped'] = (chunk['source zone'] != "#N/A") & (chunk['dest zone'] != "#N/A")
                chunk['check_is_interzone'] = chunk['source zone'] != chunk['dest zone']
                chunk['check_valid_lane'] = chunk['lane'].isin(valid_lanes)
                chunk['check_valid_pincode'] = chunk['pincode_formatted'].isin(valid_pincodes)

                # Determine final status for each row
                chunk['final_status'] = np.where(
                    ~chunk['check_zone_mapped'], "Dropped: Missing Zone Mapping (#N/A)",
                    np.where(~chunk['check_is_interzone'], "Dropped: Same Zone (Not Inter-zone)",
                    np.where(~chunk['check_valid_lane'], "Dropped: Lane Not in Promise File",
                    np.where(~chunk['check_valid_pincode'], "Dropped: Pincode Not in Target File", 
                             "Success: Kept in Final File"))))

                # Split chunks into raw (all data) and clean (only success)
                clean_chunk = chunk[chunk['final_status'] == "Success: Kept in Final File"].copy()
                
                # Keep all rows for the raw output
                processed_raw_chunks.append(chunk)
                processed_clean_chunks.append(clean_chunk)

        with st.spinner("Compiling datasets..."):
            if processed_raw_chunks:
                # Build Raw Diagnostic Dataframe
                df_raw = pd.concat(processed_raw_chunks, ignore_index=True)
                df_raw.columns = df_raw.columns.str.title()
                
                # Build Clean Dataframe
                df_clean = pd.concat(processed_clean_chunks, ignore_index=True) if processed_clean_chunks else pd.DataFrame()
                if not df_clean.empty:
                    # Drop diagnostic columns from the clean output (using lowercase keys as pandas is case-sensitive)
                    cols_to_drop = [
                        'ekart_mh_upper', 'dh_upper', 'zone_from_ekart_mh', 'zone_from_smh', 
                        'pincode_formatted', 'check_zone_mapped', 'check_is_interzone', 
                        'check_valid_lane', 'check_valid_pincode', 'final_status'
                    ]
                    df_clean.drop(columns=cols_to_drop, inplace=True, errors='ignore')
                    df_clean.columns = df_clean.columns.str.title()

                st.success("✅ Processing Complete! You can now download the raw diagnostic file to trace your logic.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if not df_clean.empty:
                        csv_clean = df_clean.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="⬇️ Download Clean Processed File",
                            data=csv_clean,
                            file_name='final_processed_clean.csv',
                            mime='text/csv',
                        )
                    else:
                        st.warning("No rows passed all filters to make a clean file.")

                with col2:
                    csv_raw = df_raw.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⬇️ Download RAW Diagnostic File (All Rows)",
                        data=csv_raw,
                        file_name='diagnostic_raw_all_rows.csv',
                        mime='text/csv',
                    )
                    st.info("💡 The Raw file contains a 'Final_Status' column. Filter it in Excel to see exactly why specific rows were dropped.")

    except Exception as e:
        st.error(f"Error during execution: {str(e)}")
