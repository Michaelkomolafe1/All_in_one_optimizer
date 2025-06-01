
import os

def find_csv_files():
    """Find CSV files in current directory"""

    print("🔍 Looking for CSV files...")

    files = os.listdir('.')
    csv_files = [f for f in files if f.endswith('.csv')]

    print(f"📊 Found {len(csv_files)} CSV files:")
    for i, file in enumerate(csv_files):
        size = os.path.getsize(file) / 1024
        print(f"   {i+1}. {file} ({size:.1f} KB)")

    dk_files = [f for f in csv_files if 'DK' in f or 'salary' in f.lower()]
    dff_files = [f for f in csv_files if 'DFF' in f or 'cheat' in f.lower()]

    print(f"\n📊 DraftKings files: {dk_files}")
    print(f"🎯 DFF files: {dff_files}")

if __name__ == "__main__":
    find_csv_files()
