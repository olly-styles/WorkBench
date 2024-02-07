import pandas as pd

def measure_state_change(expected_domain_changes=[], original_state={}, new_state={}):
    """Both states are a dictionary of dataframes"""
    state_change = []
    # Merge df1 with df2 indicating where each row is from
    diff_df = pd.merge(original_state, new_state, how='outer', indicator=True).loc[lambda x : x['_merge'].str.contains('_only')]
    # Drop the merge indicator column
    diff_df = diff_df.drop(columns=['_merge'])
    return diff_df