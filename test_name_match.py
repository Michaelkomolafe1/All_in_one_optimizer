#!/usr/bin/env python3
"""Test if DFF names will match DraftKings names"""

# DFF format: first_name, last_name
dff_examples = [
    ("Garrett", "Crochet"),
    ("Brandon", "Woodruff"),
    ("George", "Kirby")
]

# DraftKings typically has full names
dk_examples = [
    "Garrett Crochet",
    "Brandon Woodruff", 
    "George Kirby"
]

print("Testing name matching:")
print("="*40)

for (first, last) in dff_examples:
    dff_full = f"{first} {last}"
    for dk_name in dk_examples:
        if dff_full.lower() == dk_name.lower():
            print(f"✅ Match: DFF '{first} {last}' = DK '{dk_name}'")
            break
    else:
        print(f"❌ No match for: {first} {last}")

print("\nName format should work! ✅")
