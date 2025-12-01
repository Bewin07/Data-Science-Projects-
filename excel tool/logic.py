import pandas as pd

def process_settlement(df):
    """
    Applies FIFO settlement logic to the dataframe.
    Expects columns: 'CustomerCode', 'Transdate', 'Outstanding Amount'.
    Returns dataframe with 'Pending Amount' column.
    """
    # Clean data
    df = df.copy()
    df["Transdate"] = pd.to_datetime(df["Transdate"], errors="coerce")
    
    # Handle column name normalization inside the function or assume it's done before?
    # The test passes 'Outstanding Amount'. app.py handles the rename before calling this.
    # But let's be safe.
    if "Oustanding Amount" in df.columns and "Outstanding Amount" not in df.columns:
        df.rename(columns={"Oustanding Amount": "Outstanding Amount"}, inplace=True)
        
    df["Amount"] = df["Outstanding Amount"].astype(float)

    # Sort for FIFO
    df = df.sort_values(["CustomerCode", "Transdate"]).reset_index(drop=True)

    output_list = []

    # Process each customer
    for cust, grp in df.groupby("CustomerCode"):

        g = grp.copy().reset_index(drop=True)

        # Separate debits & credits
        debits = g[g["Amount"] >= 0].copy()
        credits = g[g["Amount"] < 0].copy()

        # Add pending column (initially same as amount)
        debits["Pending Amount"] = debits["Amount"]
        credits["Pending Amount"] = credits["Amount"]
        
        # Initialize SettledFlag (optional, but test_logic.py expects it)
        debits["SettledFlag"] = False
        credits["SettledFlag"] = False

        # 1. Apply Credits to Debits (Calculate Pending Debits)
        credit_pool = -credits["Amount"].sum() # Total available credit
        
        for idx in debits.index:
            if credit_pool <= 0:
                break

            debit_amt = debits.at[idx, "Pending Amount"]

            if debit_amt <= credit_pool:
                credit_pool -= debit_amt
                debits.at[idx, "Pending Amount"] = 0
                debits.at[idx, "SettledFlag"] = True
            else:
                debits.at[idx, "Pending Amount"] = debit_amt - credit_pool
                credit_pool = 0
                # Partially settled is NOT settled? Test says:
                # Inv 2 (50) - 20 = 30. Not Settled.
                # So only fully settled is True.

        # 2. Apply Debits to Credits (Calculate Pending Credits)
        debit_pool = debits["Amount"].sum() # Total debit to offset credits
        
        for idx in credits.index:
            if debit_pool <= 0:
                break
            
            credit_amt = -credits.at[idx, "Pending Amount"] # Positive magnitude
            
            if debit_pool >= credit_amt:
                credits.at[idx, "Pending Amount"] = 0
                credits.at[idx, "SettledFlag"] = True
                debit_pool -= credit_amt
            else:
                credits.at[idx, "Pending Amount"] = credits.at[idx, "Pending Amount"] + debit_pool
                debit_pool = 0
                # Partially used credit is NOT settled?
                # Test says: Pay (120) - 100 - 20 = 0. Settled.
                # So if Pending is 0, it's settled.

        # Collect results
        output_list.append(debits)
        output_list.append(credits)

    # Combine all customers pending rows
    if output_list:
        pending_final = pd.concat(output_list, ignore_index=True)
    else:
        pending_final = pd.DataFrame(columns=df.columns)

    # Restore original sort order
    pending_final = pending_final.sort_values(["CustomerCode", "Transdate"]).reset_index(drop=True)

    # Remove helper column "Amount"
    pending_final = pending_final.drop(columns=["Amount"])
    
    return pending_final
