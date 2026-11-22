
from pathlib import Path
import pandas as pd

# Find the main project folder
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "raw"
REPORT_DIR = BASE_DIR / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

report = []

def add(message=""):
    print(message)
    report.append(str(message))

add("=" * 65)
add("INDIAN E-COMMERCE DATASET INSPECTION")
add("=" * 65)

# Find all CSV files
csv_files = list(DATA_DIR.glob("*.csv"))

if not csv_files:
    add("ERROR: No CSV files found in data/raw.")
    add("Please check that your dataset files are in the correct folder.")
else:
    add(f"\nTotal CSV files found: {len(csv_files)}")

    for file in csv_files:
        add("\n" + "=" * 65)
        add(f"FILE NAME: {file.name}")
        add("=" * 65)

        try:
            try:
                df = pd.read_csv(file, encoding="utf-8", low_memory=False)
            except UnicodeDecodeError:
                df = pd.read_csv(file, encoding="latin1", low_memory=False)

            add(f"Rows: {df.shape[0]}")
            add(f"Columns: {df.shape[1]}")

            add("\nCOLUMN NAMES:")
            for col in df.columns:
                add(f"- {col}")

            add("\nDATA TYPES:")
            add(df.dtypes.to_string())

            add("\nMISSING VALUES:")
            missing = df.isnull().sum()
            missing = missing[missing > 0]

            if missing.empty:
                add("No missing values found.")
            else:
                add(missing.to_string())

            add("\nDUPLICATE ROWS:")
            add(str(df.duplicated().sum()))

            add("\nSAMPLE DATA (first 3 rows):")
            add(df.head(3).to_string(index=False))

        except Exception as error:
            add(f"ERROR reading {file.name}: {error}")

# Save inspection report
report_path = REPORT_DIR / "dataset_inspection.txt"
report_path.write_text("\n".join(report), encoding="utf-8")

add("\n" + "=" * 65)
add(f"Inspection report saved to: {report_path}")
add("=" * 65)
