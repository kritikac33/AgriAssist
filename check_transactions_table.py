#!/usr/bin/env python
"""Check transactions table structure."""
import pymysql
from pymysql.cursors import DictCursor

conn = pymysql.connect(host='localhost', user='root', password='root123', database='agriassist')
cursor = conn.cursor(DictCursor)
cursor.execute('DESCRIBE transactions')
print('TRANSACTIONS TABLE COLUMNS:')
for row in cursor.fetchall():
    print(f"  {row['Field']}: {row['Type']} NULL={row['Null']} Default={row['Default']}")
conn.close()
