import streamlit as st
import pandas as pd
import numpy as np

# --- Configuration ---
st.set_page_config(page_title="Logistics SLA Processor", layout="wide")
st.title("Logistics Data & SLA Processor (Memory Optimized)")

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
    # Force CSV for the large file so pandas can chunk it properly
    file1 = st.file_uploader("1. Upload SLA File (Must be CSV for chunking >10L rows)", type=['csv'])
    file2 = st.file_uploader("2. Upload MH/DH Network File", type=['csv', 'xlsx'])
with col2:
    file3 = st.file_uploader("3. Upload Lane Promise File", type=['csv', 'xlsx'])
    file4 = st.file_uploader("4. Upload Pincode Target File", type=['csv', 'xlsx'])

def load_lookup_data(file, header=0):
    if file.name.endswith('.csv'):
        return pd.read_csv(file, header=header, low_memory=False)
    return pd.read_excel(file, header=header)

if st.button("Process Data") and file1 and file2 and file3 and file4:
    try:
        with st.spinner("Loading lookup files into memory..."):
            # Load smaller lookup files fully into memory
            df2 = load_lookup_data(file2, header=1)
            df2_clean_dh = df2.dropna(subset=['DH Name', 'MH Name'])
            dh_to_mh = dict(zip(df2_clean_dh['DH Name'], df2_clean_dh['MH Name']))
            
            df2_clean_mh = df2.dropna(subset=['MH Name', 'Zone'])
            mh_to_zone = dict(zip(df2_clean_mh['MH Name'], df2_clean_mh['Zone']))

            df3 = load_lookup_data(file3)
            df3['Lane'] = df3['source_facility_id'].astype(str) + "-" + df3['destination_facility_id'].astype(str)
            valid_lanes = set(df3['Lane'].dropna().unique())

            df4 = load_lookup_data(file4)
            df4['pincode'] = df4['pincode'].astype(str).str.split('.').str[0]
            valid_pincodes = set(df4['pincode'].unique())

        with st.spinner("Processing massive SLA file in chunks (this will take a minute)..."):
            chunk_size = 100000
            processed_chunks = []
            
            # Using pandas chunksize to read large file without crashing RAM
            for chunk in pd.read_csv(file1, chunksize=chunk_size, low_memory=False):
                
                # 1. SLA Calc
                chunk['SLA in days'] = np.ceil((chunk['total_sla_hrs'] - chunk['f2f_buffer_sla']) / 24)
                
                # 2. SMH & DMH Mapping
                chunk['SMH'] = chunk['ekart_mh_name'].map(SMH_MAPPING).fillna(chunk.get('SMH', chunk['ekart_mh_name']))
                chunk['DMH'] = chunk['dh_name'].map(dh_to_mh)
                
                # 3. Zone Mapping
                chunk['Source Zone'] = chunk['SMH'].map(mh_to_zone)
                chunk['Dest Zone'] = chunk['DMH'].map(mh_to_zone)
                
                # Drop rows missing zone mappings to avoid errors during comparison
                chunk.dropna(subset=['Source Zone', 'Dest Zone'], inplace=True)
                
                # Segregate non-zonal lanes (Inter-zone)
                chunk = chunk[chunk['Source Zone'] != chunk['Dest Zone']]
                
                # 4. Lane Mapping & Filtering
                chunk['Lane'] = chunk['SMH'].astype(str) + "-" + chunk['DMH'].astype(str)
                chunk = chunk[chunk['Lane'].isin(valid_lanes)]
                
                # 5. Pincode Filtering
                chunk['pincode'] = chunk['pincode'].astype(str).str.split('.').str[0]
                chunk = chunk[chunk['pincode'].isin(valid_pincodes)]
                
                # Store the filtered, processed chunk
                processed_chunks.append(chunk)

        with st.spinner("Compiling final dataset..."):
            if processed_chunks:
                # Combine all surviving rows from the chunks into one final dataframe
                df_final = pd.concat(processed_chunks, ignore_index=True)
                
                st.success("✅ Processing Complete!")
                st.dataframe(df_final.head(50))
                
                csv = df_final.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="⬇️ Download Final Processed File (CSV)",
                    data=csv,
                    file_name='final_processed_lanes.csv',
                    mime='text/csv',
                )
            else:
                st.warning("Processing finished, but no data matched all the filtering criteria.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
