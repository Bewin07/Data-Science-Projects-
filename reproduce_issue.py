import pandas as pd
import numpy as np
from logic import process_settlement

def test_reproduction():
    print("Creating test data...")
    data = pd.DataFrame({
        'CustomerCode': ['C1', 'C1', np.nan, 'C2'],
        'Invoice/Receipt Date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-01'],
        'Outstanding Amount': [100.0, 50.0, 30.0, np.nan]
    })
    
    print("Input Data:")
    print(data)
    input_sum = data['Outstanding Amount'].sum()
    print(f"Input Sum: {input_sum}")
    
    print("\nProcessing settlement...")
    try:
        result = process_settlement(data)
        print("\nOutput Data:")
        print(result)
        output_sum = result['Outstanding Amount'].sum()
        print(f"Output Sum: {output_sum}")
        
        if input_sum != output_sum:
            print(f"\nFAILURE: Sums differ! Input: {input_sum}, Output: {output_sum}")
            print(f"Difference: {input_sum - output_sum}")
        else:
            print("\nSUCCESS: Sums match.")
            
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    test_reproduction()
