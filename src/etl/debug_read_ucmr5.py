import pandas as pd

print("Attempting to load UCMR5...")

try:
    df = pd.read_csv(
        "data/raw/UCMR5_All.txt",
        sep="\t",
        dtype=str,
        encoding="latin1",
        on_bad_lines="skip",
        engine="python"
    )
    print("Loaded rows:", len(df))
    print("Columns:", df.columns.tolist())
    print("\nHEAD:")
    print(df.head(10))
except Exception as e:
    print("\nError while reading file:")
    print(type(e).__name__, str(e))
