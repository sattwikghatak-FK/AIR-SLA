import streamlit as st
import pandas as pd
import numpy as np

# --- Configuration ---
st.set_page_config(page_title="SLA Processor", layout="wide")
st.title("Air Network SLA mapper")

SMH_MAPPING = {
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

# --- File Uploaders ---
st.header("Upload Files")
col1, col2 = st.columns(2)
with col1:
    file1 = st.file_uploader("1. Upload SLA File (Must be CSV)", type=['csv'])
    file2 = st.file_uploader("2. Upload MH-DH Network File", type=['csv', 'xlsx'])
with col2:
    file3 = st.file_uploader("3. Upload SMH-DMH Network File", type=['csv', 'xlsx'])
    file4 = st.file_uploader("4. Upload MDM pincode mapper File", type=['csv', 'xlsx'])

def read_file_safely(file, expected_cols=None):
    """Automatically finds the correct header row and cleans all column names."""
    file.seek(0)
    is_csv = file.name.endswith('.csv')
    
    # Try reading the first row as headers
    df = pd.read_csv(file, header=0, low_memory=False) if is_csv else pd.read_excel(file, header=0)
    df.columns = df.columns.astype(str).str.strip().str.lower()
    
    # If we specified columns we absolutely need, check if they exist
    if expected_cols:
        expected_cols_lower = [c.lower() for c in expected_cols]
        missing_cols = [c for c in expected_cols_lower if c not in df.columns]
        
        # If missing, try header=1 (skipping the first row entirely)
        if missing_cols:
            file.seek(0)
            df = pd.read_csv(file, header=1, low_memory=False) if is_csv else pd.read_excel(file, header=1)
            df.columns = df.columns.astype(str).str.strip().str.lower()
            
            # Double check if still missing, raise a clear error
            still_missing = [c for c in expected_cols_lower if c not in df.columns]
            if still_missing:
                raise ValueError(f"Could not find columns: {', '.join(still_missing)} in the file.")
                
    return df

def clean_pincode(series):
    """Removes decimals from Excel floats and converts to string"""
    return pd.to_numeric(series, errors='coerce').fillna(0).astype(int).astype(str)

if st.button("Process Data") and file1 and file2 and file3 and file4:
    try:
        with st.spinner("Analyzing and cleaning lookup files..."):
            # Load File 2 with auto-header detection
            df2 = read_file_safely(file2, expected_cols=['dh name', 'mh name', 'zone'])
            
            # Clean exact cell values to prevent trailing space errors during mapping
            df2['dh name'] = df2['dh name'].astype(str).str.strip()
            df2['mh name'] = df2['mh name'].astype(str).str.strip()
            df2['zone'] = df2['zone'].astype(str).str.strip()

            df2_clean = df2.dropna(subset=['dh name', 'mh name'])
            dh_to_mh = dict(zip(df2_clean['dh name'], df2_clean['mh name']))
            
            df2_zone = df2.dropna(subset=['mh name', 'zone'])
            mh_to_zone = dict(zip(df2_zone['mh name'], df2_zone['zone']))

            # Load File 3
            df3 = read_file_safely(file3)
            df3['lane'] = df3['source_facility_id'].astype(str).str.strip() + "-" + df3['destination_facility_id'].astype(str).str.strip()
            valid_lanes = set(df3['lane'].dropna().unique())

            # Load File 4
            df4 = read_file_safely(file4, expected_cols=['pincode'])
            df4['pincode'] = clean_pincode(df4['pincode'])
            valid_pincodes = set(df4['pincode'].unique())

        with st.spinner("Processing massive SLA file safely..."):
            chunk_size = 100000
            processed_chunks = []
            
            # Get safe headers for chunking
            file1.seek(0)
            temp_df = pd.read_csv(file1, nrows=0)
            clean_headers = temp_df.columns.astype(str).str.strip().str.lower().tolist()
            file1.seek(0)

            for chunk in pd.read_csv(file1, chunksize=chunk_size, low_memory=False, names=clean_headers, header=0):
                
                # 1. Safe SLA Calc
                total_sla = pd.to_numeric(chunk['total_sla_hrs'], errors='coerce').fillna(0)
                f2f_buffer = pd.to_numeric(chunk['f2f_buffer_sla'], errors='coerce').fillna(0)
                chunk['sla in days'] = np.ceil((total_sla - f2f_buffer) / 24)
                
                # Clean merge columns
                chunk['ekart_mh_name'] = chunk['ekart_mh_name'].astype(str).str.strip()
                chunk['dh_name'] = chunk['dh_name'].astype(str).str.strip()
                
                # 2. SMH & DMH Mapping
                chunk['smh'] = chunk['ekart_mh_name'].map(SMH_MAPPING).fillna(chunk.get('smh', chunk['ekart_mh_name']))
                chunk['dmh'] = chunk['dh_name'].map(dh_to_mh)
                
                # 3. Zone Mapping
                chunk['source zone'] = chunk['smh'].map(mh_to_zone)
                chunk['dest zone'] = chunk['dmh'].map(mh_to_zone)
                
                # Drop rows missing zone mappings
                chunk.dropna(subset=['source zone', 'dest zone'], inplace=True)
                
                # Segregate non-zonal lanes (Inter-zone)
                chunk = chunk[chunk['source zone'] != chunk['dest zone']]
                
                # 4. Lane Mapping & Filtering
                chunk['lane'] = chunk['smh'].astype(str) + "-" + chunk['dmh'].astype(str)
                chunk = chunk[chunk['lane'].isin(valid_lanes)]
                
                # 5. Safe Pincode Filtering
                chunk['pincode'] = clean_pincode(chunk['pincode'])
                chunk = chunk[chunk['pincode'].isin(valid_pincodes)]
                
                processed_chunks.append(chunk)

        with st.spinner("Compiling final dataset..."):
            if processed_chunks:
                df_final = pd.concat(processed_chunks, ignore_index=True)
                
                # Capitalize headers back to normal for the final output file
                df_final.columns = df_final.columns.str.title()
                
                st.success("✅ Processing Complete! Your data was mapped and cleaned successfully.")
                st.dataframe(df_final.head(50))
                
                csv = df_final.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Download Final Processed File (CSV)",
                    data=csv,
                    file_name='final_processed_lanes.csv',
                    mime='text/csv',
                )
            else:
                st.warning("Processing finished, but no data matched all the filtering criteria (Zones, Lanes, and Pincodes).")

    except Exception as e:
        st.error(f"Error during execution: {str(e)}")
