import streamlit as st
import pandas as pd
from io import BytesIO
from logic import process_settlement
from batch_processor import process_batches_parallel, get_batch_stats
import time

st.set_page_config(page_title="FIFO Pending Amount Tool", layout="wide")

st.title("📘 FIFO Pending Amount Settlement Tool")
st.write("Upload one Excel file. Debits are positive. Credits are negative. FIFO logic is applied per customer.")

# Batch processing settings in sidebar
with st.sidebar:
    st.header("⚙️ Processing Settings")
    batch_size = st.slider(
        "Batch Size (rows per batch)",
        min_value=1000,
        max_value=50000,
        value=10000,
        step=1000,
        help="Larger batches use more memory but may be faster. Adjust based on your file size."
    )
    
    use_parallel = st.checkbox(
        "Enable Parallel Processing",
        value=True,
        help="Process batches in parallel for maximum speed (recommended for large files)"
    )
    
    max_workers = st.slider(
        "Parallel Workers",
        min_value=1,
        max_value=8,
        value=4,
        step=1,
        help="Number of CPU cores to use for parallel processing",
        disabled=not use_parallel
    )

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

    # Get batch statistics
    stats = get_batch_stats(df, batch_size)
    
    # Show batch info
    if stats['num_batches'] > 1:
        st.info(f"📊 File will be processed in **{stats['num_batches']} batches** "
                f"({stats['total_rows']:,} rows, {stats['total_customers']:,} customers)")
    
    # Process settlement using batch processing with progress tracking
    st.subheader("Processing...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    start_time = time.time()
    
    def update_progress(completed, total, elapsed):
        progress = completed / total
        progress_bar.progress(progress)
        
        avg_time = elapsed / completed if completed > 0 else 0
        remaining = (total - completed) * avg_time
        
        status_text.text(
            f"Batch {completed}/{total} completed | "
            f"Elapsed: {elapsed:.1f}s | "
            f"ETA: {remaining:.1f}s"
        )
    
    # Choose processing method based on settings
    if stats['num_batches'] > 1 and use_parallel:
        pending_final = process_batches_parallel(
            df, 
            batch_size=batch_size,
            max_workers=max_workers,
            progress_callback=update_progress
        )
    elif stats['num_batches'] > 1:
        from batch_processor import process_batches_sequential
        pending_final = process_batches_sequential(
            df,
            batch_size=batch_size,
            progress_callback=update_progress
        )
    else:
        # Small file, use direct processing
        pending_final = process_settlement(df)
        progress_bar.progress(1.0)
        status_text.text("Processing complete!")
    
    processing_time = time.time() - start_time
    
    progress_bar.empty()
    status_text.empty()
    
    st.subheader("Pending Amount Result")
    st.dataframe(pending_final)
    
    # Show summary stats to verify consistency
    input_sum = df['Outstanding Amount'].sum()
    output_sum = pending_final['Outstanding Amount'].sum()
    pending_sum = pending_final['Pending Amount'].sum()
    
    # Performance metrics
    st.subheader("📈 Processing Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Processing Time", f"{processing_time:.2f}s")
    col2.metric("Rows Processed", f"{len(df):,}")
    col3.metric("Throughput", f"{len(df)/processing_time:,.0f} rows/s")
    col4.metric("Batches Used", stats['num_batches'])
    
    # Financial summary
    st.subheader("💰 Financial Summary")
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
