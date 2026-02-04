import pandas as pd
import numpy as np
from batch_processor import chunk_dataframe_by_customer, process_batches_parallel, process_batches_sequential, get_batch_stats
from logic import process_settlement
import unittest


class TestBatchProcessor(unittest.TestCase):
    
    def setUp(self):
        """Create test data with multiple customers"""
        # Create a larger dataset with multiple customers
        np.random.seed(42)
        
        customers = ['C1', 'C2', 'C3', 'C4', 'C5']
        data = []
        
        for customer in customers:
            # Each customer has 20-30 transactions
            num_transactions = np.random.randint(20, 31)
            for i in range(num_transactions):
                date = pd.Timestamp('2023-01-01') + pd.Timedelta(days=i)
                # Mix of debits and credits
                amount = np.random.choice([100, 200, -50, -100, 150])
                invoice_type = 'Inv' if amount > 0 else 'Pay'
                
                data.append({
                    'CustomerCode': customer,
                    'Invoice/Receipt Date': date,
                    'InvoiceType': invoice_type,
                    'Outstanding Amount': amount
                })
        
        self.test_df = pd.DataFrame(data)
    
    def test_chunk_by_customer_small_file(self):
        """Test that small files are not chunked"""
        small_df = self.test_df.head(50)
        chunks = chunk_dataframe_by_customer(small_df, target_chunk_size=10000)
        
        self.assertEqual(len(chunks), 1)
        self.assertEqual(len(chunks[0]), len(small_df))
    
    def test_chunk_by_customer_no_split(self):
        """Test that customers are never split across chunks"""
        chunks = chunk_dataframe_by_customer(self.test_df, target_chunk_size=30)
        
        # Verify each customer appears in only one chunk
        for customer in self.test_df['CustomerCode'].unique():
            customer_chunks = [i for i, chunk in enumerate(chunks) 
                             if customer in chunk['CustomerCode'].values]
            self.assertEqual(len(customer_chunks), 1, 
                           f"Customer {customer} appears in multiple chunks")
    
    def test_chunk_sizes_reasonable(self):
        """Test that chunk sizes are reasonable"""
        chunks = chunk_dataframe_by_customer(self.test_df, target_chunk_size=50)
        
        # All chunks should have data
        for chunk in chunks:
            self.assertGreater(len(chunk), 0)
        
        # Total rows should match
        total_rows = sum(len(chunk) for chunk in chunks)
        self.assertEqual(total_rows, len(self.test_df))
    
    def test_batch_processing_correctness(self):
        """Test that batch processing produces same results as direct processing"""
        # Process with direct method
        direct_result = process_settlement(self.test_df)
        
        # Process with batch method (sequential for deterministic comparison)
        batch_result = process_batches_sequential(self.test_df, batch_size=50)
        
        # Sort both for comparison
        direct_sorted = direct_result.sort_values(
            ['CustomerCode', 'Invoice/Receipt Date']
        ).reset_index(drop=True)
        
        batch_sorted = batch_result.sort_values(
            ['CustomerCode', 'Invoice/Receipt Date']
        ).reset_index(drop=True)
        
        # Compare key columns
        pd.testing.assert_series_equal(
            direct_sorted['CustomerCode'], 
            batch_sorted['CustomerCode'],
            check_names=False
        )
        
        pd.testing.assert_series_equal(
            direct_sorted['Outstanding Amount'], 
            batch_sorted['Outstanding Amount'],
            check_names=False
        )
        
        pd.testing.assert_series_equal(
            direct_sorted['Pending Amount'], 
            batch_sorted['Pending Amount'],
            check_names=False
        )
    
    def test_parallel_processing_correctness(self):
        """Test that parallel processing produces same results"""
        # Process with direct method
        direct_result = process_settlement(self.test_df)
        
        # Process with parallel batch method
        parallel_result = process_batches_parallel(
            self.test_df, 
            batch_size=50,
            max_workers=2
        )
        
        # Sort both for comparison
        direct_sorted = direct_result.sort_values(
            ['CustomerCode', 'Invoice/Receipt Date']
        ).reset_index(drop=True)
        
        parallel_sorted = parallel_result.sort_values(
            ['CustomerCode', 'Invoice/Receipt Date']
        ).reset_index(drop=True)
        
        # Compare pending amounts
        pd.testing.assert_series_equal(
            direct_sorted['Pending Amount'], 
            parallel_sorted['Pending Amount'],
            check_names=False,
            check_exact=False,
            rtol=1e-5
        )
    
    def test_get_batch_stats(self):
        """Test batch statistics calculation"""
        stats = get_batch_stats(self.test_df, batch_size=50)
        
        self.assertEqual(stats['total_rows'], len(self.test_df))
        self.assertEqual(stats['total_customers'], 
                        self.test_df['CustomerCode'].nunique())
        self.assertGreater(stats['num_batches'], 0)
        self.assertGreater(stats['avg_batch_size'], 0)
        # Note: batch_sizes is now empty for performance (estimated mode)
    
    def test_empty_dataframe(self):
        """Test handling of empty DataFrame"""
        empty_df = pd.DataFrame(columns=self.test_df.columns)
        chunks = chunk_dataframe_by_customer(empty_df, target_chunk_size=100)
        
        self.assertEqual(len(chunks), 1)
        self.assertTrue(chunks[0].empty)
    
    def test_single_customer(self):
        """Test with single customer data"""
        single_customer = self.test_df[self.test_df['CustomerCode'] == 'C1'].copy()
        
        # Should not be split even with small chunk size
        chunks = chunk_dataframe_by_customer(single_customer, target_chunk_size=10)
        
        self.assertEqual(len(chunks), 1)
        self.assertEqual(len(chunks[0]), len(single_customer))


if __name__ == '__main__':
    unittest.main(verbose=2)
