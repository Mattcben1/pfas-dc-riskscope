import pandas as pd

print("Testing fast PFAS load...")

try:
    df = pd.read_csv(
        "data/raw/UCMR5_All.txt",
        sep="\t",
        engine="pyarrow",        # very fast reader
        dtype=str,
        on_bad_lines="skip"
    )
    print("Loaded rows:", len(df))
    print("Columns:", df.columns.tolist()[:20])
    print(df.head(10))
except Exception as e:
    print("Arrow engine failed:", e)
    print("Falling back to python engine...")

    df = pd.read_csv(
        "data/raw/UCMR5_All.txt",
        sep="\t",
        engine="python",
        dtype=str,
        encoding="latin1",
        on_bad_lines="skip"
    )
    print("Loaded rows:", len(df))
    print("Columns:", df.columns.tolist()[:20])
    print(df.head(10))
