import streamlit as st
import pandas as pd
from io import BytesIO
from logic import process_settlement

st.set_page_config(page_title="FIFO Pending Amount Tool", layout="wide")

st.title("📘 FIFO Pending Amount Settlement Tool")
st.write("Upload one Excel file. Debits are positive. Credits are negative. FIFO logic is applied per customer.")

uploaded = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

if uploaded:

    df = pd.read_excel(uploaded)
    
    # Pre-process: Drop known metadata rows (e.g. "(In Lakhs)" unit row)
    # This row has mixed types (string in numeric cols) which crashes Streamlit's Arrow conversion
    if not df.empty:
        # Check all columns for the specific artifact mentioned in the error.
        # Use case=False for case insensitivity and regex=False to treat () as literals (but we can't mix both easily in standard pandas without regex=True and escaping).
        # Simplest consistent way: convert to string, lower case, check for "in lakhs".
        
        # 1. Drop rows where any column contains "(In Lakhs)" (case insensitive)
        def is_metadata_row(row):
            return row.astype(str).str.lower().str.contains("in lakhs").any()
        
        mask = df.apply(is_metadata_row, axis=1)
        if mask.any():
            df = df[~mask]
            st.warning("⚠️ Removed metadata row(s) containing '(In Lakhs)'.")
            
        # 2. Also drop rows where 'CustomerCode' or 'Outstanding Amount' is NaN (often footer/header noise)
        # But be careful not to drop valid data if only one is missing. 
        # For 'B2B2C', ensure it is numeric if it exists. 
        # The error specifically mentioned 'B2B2C' column having 'str' instead of 'int64'.
        if 'B2B2C' in df.columns:
             # Force invalid non-numeric values in B2B2C to NaN, then drop those rows if they look like garbage
             df['B2B2C'] = pd.to_numeric(df['B2B2C'], errors='coerce')
             # If B2B2C became NaN but was a string before, we might want to check if the whole row is garbage.
             # For now, just ensuring it's numeric prevents the Arrow error.
    
    # Normalize column name if typo exists (handle both spellings)
    if "Oustanding Amount" in df.columns and "Outstanding Amount" not in df.columns:
        df.rename(columns={"Oustanding Amount": "Outstanding Amount"}, inplace=True)

    required = ["CustomerCode", "Invoice/Receipt Date", "InvoiceType", "Outstanding Amount"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    st.subheader("Input Preview")
    st.dataframe(df.head(50))

    # Process settlement using external logic
    pending_final = process_settlement(df)

    st.subheader("Pending Amount Result")
    st.dataframe(pending_final)
    
    # Show summary stats to verify consistency
    input_sum = df['Outstanding Amount'].sum()
    output_sum = pending_final['Outstanding Amount'].sum()
    pending_sum = pending_final['Pending Amount'].sum()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Input Total Outstanding", f"{input_sum:,.2f}")
    col2.metric("Output Total Outstanding", f"{output_sum:,.2f}")
    col3.metric("Output Total Pending", f"{pending_sum:,.2f}")

    if abs(input_sum - output_sum) > 0.01:
        st.warning("⚠️ Discrepancy detected in Outstanding Amount sum! (This shouldn't happen now)")
    else:
        st.success("✅ Input and Output Outstanding Amount sums match.")

    # Download
    def to_excel(df):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Pending")
        return buffer.getvalue()

    st.download_button(
        "⬇ Download Pending Amount Excel",
        data=to_excel(pending_final),
        file_name="pending_output_full.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.success("Done! Your pending file is ready.")

else:
    st.info("Please upload an Excel file to begin.")
