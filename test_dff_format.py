#!/usr/bin/env python3
"""Test DFF file format"""

import tkinter as tk
from tkinter import filedialog
import pandas as pd

# Hide the root window
root = tk.Tk()
root.withdraw()

print("🔍 Select your DFF file...")
file_path = filedialog.askopenfilename(
    title="Select DFF File",
    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
)

if file_path:
    print(f"\n📂 Selected: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        print(f"✅ Loaded successfully!")
        print(f"📊 Shape: {df.shape}")
        print(f"\n📋 Columns:")
        for i, col in enumerate(df.columns):
            print(f"  {i}: {col}")
        
        print(f"\n👀 First 3 rows:")
        print(df.head(3))
        
        # Check for expected columns
        name_cols = [col for col in df.columns if 'name' in col.lower()]
        proj_cols = [col for col in df.columns if 'proj' in col.lower() or 'ppg' in col.lower()]
        
        print(f"\n🔍 Found name columns: {name_cols}")
        print(f"🔍 Found projection columns: {proj_cols}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ No file selected")
