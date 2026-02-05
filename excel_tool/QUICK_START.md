# ⚡ Quick Start Guide

## For Users Who Want to Run Locally (Offline)

### 1️⃣ One-Time Setup (Requires Internet)

```bash
# Download the code
git clone https://github.com/Bewin07/Data-Science-Projects-.git
cd Data-Science-Projects-/excel_tool

# Install Python packages
pip install -r requirements.txt
```

### 2️⃣ Run the App (Works Offline)

```bash
streamlit run app.py
```

Open your browser to: **http://localhost:8501**

### 3️⃣ Use the App

1. Upload your Excel file
2. Wait for processing
3. Download the results

**That's it! No internet needed after setup.** 🎉

---

## Alternative: Simple Batch Script (Windows)

Create a file named `run_app.bat` with this content:

```batch
@echo off
echo Starting FIFO Settlement Tool...
streamlit run app.py
pause
```

Double-click `run_app.bat` to start the app instantly!

---

## Alternative: Shell Script (Mac/Linux)

Create a file named `run_app.sh` with this content:

```bash
#!/bin/bash
echo "Starting FIFO Settlement Tool..."
streamlit run app.py
```

Make it executable and run:
```bash
chmod +x run_app.sh
./run_app.sh
```
