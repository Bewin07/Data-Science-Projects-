import pandas as pd
import numpy as np
from typing import List, Tuple, Callable, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import time
from functools import partial


def chunk_dataframe_by_customer(df: pd.DataFrame, target_chunk_size: int = 10000) -> List[pd.DataFrame]:
    """
    Intelligently splits DataFrame into chunks, ensuring all transactions 
    for a customer stay in the same chunk.
    
    Args:
        df: DataFrame with CustomerCode column
        target_chunk_size: Target number of rows per chunk (approximate)
    
    Returns:
        List of DataFrame chunks
    """
    if df.empty:
        return [df]
    
    # If file is small, no need to chunk
    if len(df) <= target_chunk_size:
        return [df]
    
    # Group by customer and get sizes
    customer_groups = df.groupby('CustomerCode', sort=False)
    customer_sizes = customer_groups.size()
    
    chunks = []
    current_chunk_customers = []
    current_chunk_size = 0
    
    for customer, size in customer_sizes.items():
        # If adding this customer exceeds target, start new chunk
        # (unless current chunk is empty - then we must add it)
        if current_chunk_size > 0 and current_chunk_size + size > target_chunk_size:
            # Finalize current chunk
            chunk_df = df[df['CustomerCode'].isin(current_chunk_customers)].copy()
            chunks.append(chunk_df)
            
            # Start new chunk
            current_chunk_customers = [customer]
            current_chunk_size = size
        else:
            current_chunk_customers.append(customer)
            current_chunk_size += size
    
    # Add final chunk
    if current_chunk_customers:
        chunk_df = df[df['CustomerCode'].isin(current_chunk_customers)].copy()
        chunks.append(chunk_df)
    
    return chunks


def process_single_batch(batch_data: Tuple[int, pd.DataFrame]) -> Tuple[int, pd.DataFrame]:
    """
    Process a single batch. This function is designed to be pickled for multiprocessing.
    
    Args:
        batch_data: Tuple of (batch_index, dataframe_chunk)
    
    Returns:
        Tuple of (batch_index, processed_dataframe)
    """
    from logic import process_settlement
    
    batch_idx, chunk = batch_data
    result = process_settlement(chunk)
    return batch_idx, result


def process_batches_parallel(
    df: pd.DataFrame,
    batch_size: int = 10000,
    max_workers: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int, float], None]] = None
) -> pd.DataFrame:
    """
    Process DataFrame in batches using parallel processing.
    
    Args:
        df: Input DataFrame
        batch_size: Target rows per batch
        max_workers: Number of parallel workers (None = CPU count)
        progress_callback: Function called with (completed_batches, total_batches, elapsed_time)
    
    Returns:
        Processed DataFrame with all batches merged
    """
    start_time = time.time()
    
    # Create chunks
    chunks = chunk_dataframe_by_customer(df, batch_size)
    total_batches = len(chunks)
    
    if total_batches == 1:
        # No need for parallel processing
        from logic import process_settlement
        result = process_settlement(chunks[0])
        if progress_callback:
            progress_callback(1, 1, time.time() - start_time)
        return result
    
    # Prepare batch data with indices
    batch_data = [(i, chunk) for i, chunk in enumerate(chunks)]
    
    # Process batches in parallel
    results = [None] * total_batches
    completed = 0
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all batches
        future_to_batch = {
            executor.submit(process_single_batch, data): data[0] 
            for data in batch_data
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_batch):
            batch_idx, result_df = future.result()
            results[batch_idx] = result_df
            completed += 1
            
            if progress_callback:
                elapsed = time.time() - start_time
                progress_callback(completed, total_batches, elapsed)
    
    # Merge all results
    final_result = pd.concat(results, ignore_index=True)
    
    # Sort by customer and date to maintain consistency
    final_result = final_result.sort_values(
        ['CustomerCode', 'Invoice/Receipt Date']
    ).reset_index(drop=True)
    
    return final_result


def process_batches_sequential(
    df: pd.DataFrame,
    batch_size: int = 10000,
    progress_callback: Optional[Callable[[int, int, float], None]] = None
) -> pd.DataFrame:
    """
    Process DataFrame in batches sequentially (for debugging or comparison).
    
    Args:
        df: Input DataFrame
        batch_size: Target rows per batch
        progress_callback: Function called with (completed_batches, total_batches, elapsed_time)
    
    Returns:
        Processed DataFrame with all batches merged
    """
    from logic import process_settlement
    
    start_time = time.time()
    
    # Create chunks
    chunks = chunk_dataframe_by_customer(df, batch_size)
    total_batches = len(chunks)
    
    if total_batches == 1:
        result = process_settlement(chunks[0])
        if progress_callback:
            progress_callback(1, 1, time.time() - start_time)
        return result
    
    # Process each batch
    results = []
    for i, chunk in enumerate(chunks):
        result = process_settlement(chunk)
        results.append(result)
        
        if progress_callback:
            elapsed = time.time() - start_time
            progress_callback(i + 1, total_batches, elapsed)
    
    # Merge all results
    final_result = pd.concat(results, ignore_index=True)
    
    # Sort by customer and date to maintain consistency
    final_result = final_result.sort_values(
        ['CustomerCode', 'Invoice/Receipt Date']
    ).reset_index(drop=True)
    
    return final_result


def get_batch_stats(df: pd.DataFrame, batch_size: int = 10000) -> dict:
    """
    Get statistics about how the data would be batched.
    
    Args:
        df: Input DataFrame
        batch_size: Target rows per batch
    
    Returns:
        Dictionary with batch statistics
    """
    chunks = chunk_dataframe_by_customer(df, batch_size)
    
    chunk_sizes = [len(chunk) for chunk in chunks]
    customer_counts = [chunk['CustomerCode'].nunique() for chunk in chunks]
    
    return {
        'total_rows': len(df),
        'total_customers': df['CustomerCode'].nunique(),
        'num_batches': len(chunks),
        'avg_batch_size': np.mean(chunk_sizes) if chunk_sizes else 0,
        'min_batch_size': min(chunk_sizes) if chunk_sizes else 0,
        'max_batch_size': max(chunk_sizes) if chunk_sizes else 0,
        'avg_customers_per_batch': np.mean(customer_counts) if customer_counts else 0,
        'batch_sizes': chunk_sizes,
        'customer_counts': customer_counts
    }
