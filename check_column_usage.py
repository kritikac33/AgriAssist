#!/usr/bin/env python
"""Check if extra columns are used anywhere in the codebase."""
import os
import re

# Columns to check
columns_to_check = [
    'payment_id',
    'moisture',
    'irrigation_schedules.crop_id'
]

print("Checking usage of extra database columns in codebase...")
print("=" * 80)

for col in columns_to_check:
    print(f"\nColumn: {col}")
    print("-" * 40)
    found = False
    for root, dirs, files in os.walk('app'):
        # Skip __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if col in content:
                        found = True
                        print(f"  Found in: {filepath}")
                        # Show context
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if col in line:
                                start = max(0, i - 1)
                                end = min(len(lines), i + 2)
                                print(f"    Line {i+1}: {lines[start:end]}")
                                break
    if not found:
        print(f"  [NOT USED] - Safe to remove")
