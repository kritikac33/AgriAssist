#!/usr/bin/env python
"""Check listings table structure."""
import pymysql
from pymysql.cursors import DictCursor

conn = pymysql.connect(host='localhost', user='root', password='root123', database='agriassist')
cursor = conn.cursor(DictCursor)
cursor.execute('DESCRIBE listings')
print('LISTINGS TABLE COLUMNS:')
for row in cursor.fetchall():
    print(f"  {row['Field']}: {row['Type']} NULL={row['Null']} Default={row['Default']}")
conn.close()
