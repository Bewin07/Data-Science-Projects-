import pandas as pd
from logic import process_settlement
import unittest

class TestFIFO(unittest.TestCase):
    def test_settlement(self):
        # Setup Data
        data = pd.DataFrame({
            'CustomerCode': ['C1', 'C1', 'C1', 'C2', 'C2'],
            'Transdate': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-01', '2023-01-02'],
            'InvoiceType': ['Inv', 'Inv', 'Pay', 'Inv', 'Pay'],
            'Outstanding Amount': [100.0, 50.0, -120.0, 200.0, -50.0]
        })
        
        # Run Logic
        result = process_settlement(data)
        
        # Verify Results
        # C1:
        # Inv 1 (100) - 100 (from Pay 120) = 0. Settled.
        # Inv 2 (50) - 20 (from Pay 120 rem) = 30. Not Settled.
        # Pay (120) - 100 - 20 = 0. Settled.
        
        # C2:
        # Inv 1 (200) - 50 (from Pay 50) = 150. Not Settled.
        # Pay (50) - 50 = 0. Settled.
        
        print(result[['CustomerCode', 'Outstanding Amount', 'Pending Amount', 'SettledFlag']])
        
        # C1 Tests
        c1_res = result[result['CustomerCode'] == 'C1'].reset_index(drop=True)
        self.assertTrue(c1_res.loc[0, 'SettledFlag']) # Inv 1
        self.assertAlmostEqual(c1_res.loc[0, 'Pending Amount'], 0)
        
        self.assertFalse(c1_res.loc[1, 'SettledFlag']) # Inv 2
        self.assertAlmostEqual(c1_res.loc[1, 'Pending Amount'], 30)
        
        self.assertTrue(c1_res.loc[2, 'SettledFlag']) # Pay
        self.assertAlmostEqual(c1_res.loc[2, 'Pending Amount'], 0)

        # C2 Tests
        c2_res = result[result['CustomerCode'] == 'C2'].reset_index(drop=True)
        self.assertFalse(c2_res.loc[0, 'SettledFlag']) # Inv 1
        self.assertAlmostEqual(c2_res.loc[0, 'Pending Amount'], 150)
        
        self.assertTrue(c2_res.loc[1, 'SettledFlag']) # Pay
        self.assertAlmostEqual(c2_res.loc[1, 'Pending Amount'], 0)

if __name__ == '__main__':
    unittest.main()
