import os
import pandas as pd


def search_for_tag_102():
    target = "Ewes"
    print(
        f"🔍 Scanning all Excel and CSV files in project directory for Tag #{target}...\n"
    )

    found_any = False

    # Walk through current directory and all subdirectories
    for root, dirs, files in os.walk("."):
        for file in files:
            file_path = os.path.join(root, file)

            # Check Excel files
            if file.endswith((".xlsx", ".xls")):
                try:
                    xls = pd.ExcelFile(file_path)
                    for sheet_name in xls.sheet_names:
                        df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
                        for col in df.columns:
                            # Search for '102' in the column
                            match = df[df[col].str.contains(target, na=False)]
                            if not match.empty:
                                found_any = True
                                print(
                                    f"🎯 FOUND in Excel File: '{file_path}' | Sheet: '{sheet_name}' | Column: '{col}'"
                                )
                                print(match)
                                print("=" * 70)
                except Exception as e:
                    print(f"⚠️ Could not read Excel file {file_path}: {e}")

            # Check CSV files
            elif file.endswith(".csv"):
                try:
                    df = pd.read_csv(file_path, dtype=str, low_memory=False)
                    for col in df.columns:
                        match = df[df[col].str.contains(target, na=False)]
                        if not match.empty:
                            found_any = True
                            print(
                                f"🎯 FOUND in CSV File: '{file_path}' | Column: '{col}'"
                            )
                            print(match)
                            print("=" * 70)
                except Exception as e:
                    print(f"⚠️ Could not read CSV file {file_path}: {e}")

    if not found_any:
        print(
            f"❌ Tag #{target} was not found in any local Excel or CSV files in this directory."
        )
    else:
        print(
            "\n✅ Search complete! Review the matching records above to locate Tag #102."
        )


if __name__ == "__main__":
    search_for_tag_102()
