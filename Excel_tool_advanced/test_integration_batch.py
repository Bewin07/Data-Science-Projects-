"""
Integration test for batch processing with large synthetic dataset.
This test generates a large file and compares batch vs non-batch processing.
"""
import pandas as pd
import numpy as np
from batch_processor import process_batches_parallel, process_batches_sequential
from logic import process_settlement
import time


def generate_large_dataset(num_customers=100, transactions_per_customer=1000):
    """Generate a large synthetic dataset for testing"""
    print(f"Generating dataset: {num_customers} customers, {transactions_per_customer} transactions each...")
    
    np.random.seed(42)
    data = []
    
    for customer_id in range(1, num_customers + 1):
        customer_code = f'CUST{customer_id:04d}'
        
        for txn_id in range(transactions_per_customer):
            date = pd.Timestamp('2023-01-01') + pd.Timedelta(days=txn_id % 365)
            
            # 70% debits, 30% credits
            if np.random.random() < 0.7:
                amount = np.random.choice([100, 200, 300, 500, 1000])
                invoice_type = 'Inv'
            else:
                amount = -np.random.choice([50, 100, 200, 500])
                invoice_type = 'Pay'
            
            data.append({
                'CustomerCode': customer_code,
                'Invoice/Receipt Date': date,
                'InvoiceType': invoice_type,
                'Outstanding Amount': amount
            })
    
    df = pd.DataFrame(data)
    print(f"Generated {len(df):,} rows")
    return df


def compare_results(df1, df2, name1="Result 1", name2="Result 2"):
    """Compare two result DataFrames"""
    print(f"\nComparing {name1} vs {name2}:")
    
    # Sort both
    df1_sorted = df1.sort_values(['CustomerCode', 'Invoice/Receipt Date']).reset_index(drop=True)
    df2_sorted = df2.sort_values(['CustomerCode', 'Invoice/Receipt Date']).reset_index(drop=True)
    
    # Check shape
    if df1_sorted.shape != df2_sorted.shape:
        print(f"  [FAIL] Shape mismatch: {df1_sorted.shape} vs {df2_sorted.shape}")
        return False
    
    # Check pending amounts
    pending_diff = (df1_sorted['Pending Amount'] - df2_sorted['Pending Amount']).abs()
    max_diff = pending_diff.max()
    
    if max_diff < 1e-5:
        print(f"  [PASS] Pending amounts match perfectly (max diff: {max_diff:.2e})")
        return True
    else:
        print(f"  [FAIL] Pending amounts differ (max diff: {max_diff:.2f})")
        print(f"     Rows with differences: {(pending_diff > 1e-5).sum()}")
        return False


def main():
    print("=" * 70)
    print("BATCH PROCESSING INTEGRATION TEST")
    print("=" * 70)
    
    # Generate test data
    df = generate_large_dataset(num_customers=100, transactions_per_customer=1000)
    total_rows = len(df)
    
    print(f"\nDataset statistics:")
    print(f"  Total rows: {total_rows:,}")
    print(f"  Total customers: {df['CustomerCode'].nunique():,}")
    print(f"  Date range: {df['Invoice/Receipt Date'].min()} to {df['Invoice/Receipt Date'].max()}")
    
    # Test 1: Direct processing (baseline)
    print("\n" + "=" * 70)
    print("TEST 1: Direct Processing (Baseline)")
    print("=" * 70)
    start = time.time()
    direct_result = process_settlement(df)
    direct_time = time.time() - start
    print(f"[OK] Completed in {direct_time:.2f}s ({total_rows/direct_time:,.0f} rows/s)")
    
    # Test 2: Sequential batch processing
    print("\n" + "=" * 70)
    print("TEST 2: Sequential Batch Processing")
    print("=" * 70)
    
    def progress_callback(completed, total, elapsed):
        print(f"  Progress: {completed}/{total} batches ({completed/total*100:.0f}%) - {elapsed:.1f}s elapsed")
    
    start = time.time()
    sequential_result = process_batches_sequential(
        df, 
        batch_size=10000,
        progress_callback=progress_callback
    )
    sequential_time = time.time() - start
    print(f"[OK] Completed in {sequential_time:.2f}s ({total_rows/sequential_time:,.0f} rows/s)")
    print(f"   Speedup vs direct: {direct_time/sequential_time:.2f}x")
    
    # Test 3: Parallel batch processing
    print("\n" + "=" * 70)
    print("TEST 3: Parallel Batch Processing (4 workers)")
    print("=" * 70)
    start = time.time()
    parallel_result = process_batches_parallel(
        df,
        batch_size=10000,
        max_workers=4,
        progress_callback=progress_callback
    )
    parallel_time = time.time() - start
    print(f"[OK] Completed in {parallel_time:.2f}s ({total_rows/parallel_time:,.0f} rows/s)")
    print(f"   Speedup vs direct: {direct_time/parallel_time:.2f}x")
    print(f"   Speedup vs sequential: {sequential_time/parallel_time:.2f}x")
    
    # Compare results
    print("\n" + "=" * 70)
    print("CORRECTNESS VERIFICATION")
    print("=" * 70)
    
    match1 = compare_results(direct_result, sequential_result, "Direct", "Sequential Batch")
    match2 = compare_results(direct_result, parallel_result, "Direct", "Parallel Batch")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Dataset: {total_rows:,} rows, {df['CustomerCode'].nunique():,} customers")
    print(f"\nProcessing Times:")
    print(f"  Direct:     {direct_time:6.2f}s ({total_rows/direct_time:8,.0f} rows/s)")
    print(f"  Sequential: {sequential_time:6.2f}s ({total_rows/sequential_time:8,.0f} rows/s) - {direct_time/sequential_time:.2f}x speedup")
    print(f"  Parallel:   {parallel_time:6.2f}s ({total_rows/parallel_time:8,.0f} rows/s) - {direct_time/parallel_time:.2f}x speedup")
    
    print(f"\nCorrectness:")
    print(f"  Sequential matches direct: {'[PASS]' if match1 else '[FAIL]'}")
    print(f"  Parallel matches direct:   {'[PASS]' if match2 else '[FAIL]'}")
    
    if match1 and match2:
        print("\n*** ALL TESTS PASSED! ***")
        return 0
    else:
        print("\n*** SOME TESTS FAILED ***")
        return 1


if __name__ == '__main__':
    exit(main())
