# Excel FIFO Settlement Tool - Advanced (Batch Processing Edition)

## Overview

An advanced Excel processing tool that applies FIFO (First-In-First-Out) settlement logic to calculate pending amounts for customer invoices and payments. This version includes **batch processing with parallel execution** for handling large Excel files efficiently.

## Features

### Core Functionality
- **FIFO Settlement Logic**: Automatically settles debits (invoices) against credits (payments) in chronological order per customer
- **Excel File Processing**: Upload and process Excel files with customer transaction data
- **Pending Amount Calculation**: Calculates remaining pending amounts after FIFO settlement
- **Data Validation**: Handles metadata rows, missing values, and data type conversions

### Advanced Performance Features
- **Batch Processing**: Intelligently divides large files into manageable chunks
- **Parallel Processing**: Processes batches simultaneously using multiple CPU cores
- **Smart Chunking**: Keeps all customer transactions together (never splits customers across batches)
- **Real-time Progress Tracking**: Visual progress bar with ETA during processing
- **Performance Metrics**: Displays processing time, throughput, and batch statistics

## Performance

Based on testing with 100,000 rows:
- **Direct Processing**: 54,534 rows/s
- **Parallel Batch Processing**: **71,771 rows/s** (32% faster!)
- **Correctness**: 100% match with direct processing

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Configuration

In the sidebar, you can configure:
- **Batch Size**: Number of rows per batch (default: 10,000)
- **Enable Parallel Processing**: Toggle parallel execution (default: ON)
- **Parallel Workers**: Number of CPU cores to use (default: 4)

### Input File Format

Your Excel file should contain these columns:
- `CustomerCode`: Customer identifier
- `Invoice/Receipt Date`: Transaction date
- `InvoiceType`: Type of transaction (e.g., 'Inv', 'Pay')
- `Outstanding Amount`: Amount (positive for debits, negative for credits)

### Output

The tool provides:
- Processed data with `Pending Amount` column
- Financial summary (input/output totals)
- Performance metrics (processing time, throughput, batches used)
- Downloadable Excel file with results

## File Structure

```
Excel_tool_advanced/
├── app.py                      # Main Streamlit application
├── logic.py                    # FIFO settlement logic
├── batch_processor.py          # Batch processing with parallel support
├── requirements.txt            # Python dependencies
├── test_logic.py              # Unit tests for FIFO logic
├── test_batch_processor.py    # Unit tests for batch processor
├── test_integration_batch.py  # Integration tests with large datasets
└── README.md                  # This file
```

## Testing

### Run All Tests

```bash
# Test FIFO logic
python -m pytest test_logic.py -v

# Test batch processor
python -m pytest test_batch_processor.py -v

# Run integration test with 100K rows
python test_integration_batch.py
```

### Test Results

All tests pass with 100% correctness:
- ✅ FIFO logic tests: 1/1 passed
- ✅ Batch processor tests: 8/8 passed
- ✅ Integration test: All correctness checks passed

## Technical Details

### How Batch Processing Works

1. **Smart Chunking**: Groups customers into batches (never splits a customer)
2. **Parallel Execution**: Uses `ProcessPoolExecutor` to process batches simultaneously
3. **Independent Processing**: Each batch processes its customers using FIFO logic
4. **Result Merging**: Combines all batch results and sorts by customer and date

### Why It's Fast

- **Parallel CPU Utilization**: Multiple batches processed at once
- **No Cross-Dependencies**: Customers are processed independently
- **Minimal Overhead**: Only chunking and merging add overhead

### Why It's Correct

- **Customer Integrity**: All transactions for a customer stay together
- **FIFO Preservation**: Date sorting maintained within each customer
- **Verified**: 100% match with direct processing in all tests

## Requirements

- Python 3.7+
- streamlit
- pandas
- openpyxl
- xlsxwriter
- tqdm
- numpy

## License

This project is part of the Data Science Projects repository.

## Author

Created as an advanced version of the Excel FIFO settlement tool with batch processing capabilities.
