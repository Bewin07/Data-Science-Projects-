# 📘 FIFO Pending Amount Settlement Tool

A Streamlit application that processes Excel files using FIFO (First-In-First-Out) settlement logic to calculate pending amounts for customer invoices and receipts.

## ✨ Features

- 📊 FIFO settlement logic per customer
- 🚀 Batch processing for large files
- ⚡ Parallel processing support
- 📈 Real-time progress tracking
- 💾 Export results to Excel
- 🎯 Works completely offline (no internet required)

## 🖥️ Local Installation (Offline Use)

Follow these steps to run the app on your local machine without internet:

### Prerequisites

- Python 3.8 or higher installed on your computer
- Internet connection **only for initial setup** (to download dependencies)

### Step 1: Download the Code

**Option A: Using Git (Recommended)**
```bash
git clone https://github.com/Bewin07/Data-Science-Projects-.git
cd Data-Science-Projects-/excel_tool
```

**Option B: Download ZIP**
1. Go to https://github.com/Bewin07/Data-Science-Projects-
2. Click "Code" → "Download ZIP"
3. Extract the ZIP file
4. Navigate to the `excel_tool` folder

### Step 2: Install Dependencies

Open a terminal/command prompt in the `excel_tool` folder and run:

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

> **Note:** This step requires internet connection. Once installed, you can use the app offline.

### Step 3: Run the App

```bash
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`

### Step 4: Use Offline

After the initial setup, you can run the app **completely offline**:

1. Open terminal in the `excel_tool` folder
2. Activate virtual environment (if using one)
3. Run `streamlit run app.py`
4. Upload your Excel files and process them

**No internet connection needed for processing!**

## 📋 Excel File Requirements

Your Excel file must contain these columns:
- `CustomerCode` - Customer identifier
- `Invoice/Receipt Date` - Transaction date
- `InvoiceType` - Type of transaction
- `Outstanding Amount` - Amount (positive for debits, negative for credits)

## 🎯 How It Works

1. **Upload** your Excel file
2. **Configure** batch size and parallel processing (optional)
3. **Process** - The app applies FIFO logic per customer
4. **Download** the results with pending amounts calculated

## 🚀 Performance Tips

- **Large files (>10,000 rows):** Enable parallel processing
- **Batch size:** Adjust based on your file size (default: 10,000 rows)
- **Workers:** Set to number of CPU cores for best performance

## 📦 What Gets Installed

The app uses these Python packages:
- `streamlit` - Web interface
- `pandas` - Data processing
- `openpyxl` - Excel file reading
- `xlsxwriter` - Excel file writing
- `numpy` - Numerical operations

All packages work offline after installation.

## 🔧 Troubleshooting

### "streamlit: command not found"
Make sure you activated the virtual environment and installed dependencies.

### "Module not found" errors
Run `pip install -r requirements.txt` again.

### App won't start
Check that port 8501 is not already in use. You can specify a different port:
```bash
streamlit run app.py --server.port 8502
```

## 📞 Support

For issues or questions, please open an issue on the GitHub repository.

## 📄 License

This project is part of the Data Science Projects repository.

---

**Enjoy processing your Excel files offline! 🎉**
