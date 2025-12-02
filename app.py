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
