#!/usr/bin/env python
"""Check for schema drift between models and actual database tables."""
import pymysql
from pymysql.cursors import DictCursor
from sqlalchemy import inspect
from app.database import engine
from app.models import *
from sqlalchemy import text

def get_actual_columns():
    """Get actual columns from database via information_schema."""
    conn = pymysql.connect(host='localhost', user='root', password='root123', database='agriassist')
    cursor = conn.cursor(DictCursor)
    
    query = """
    SELECT 
        TABLE_NAME,
        COLUMN_NAME,
        DATA_TYPE,
        COLUMN_TYPE,
        IS_NULLABLE,
        COLUMN_DEFAULT,
        COLUMN_KEY
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = 'agriassist'
    ORDER BY TABLE_NAME, ORDINAL_POSITION
    """
    cursor.execute(query)
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    
    tables = {}
    for row in result:
        table_name = row['TABLE_NAME']
        if table_name not in tables:
            tables[table_name] = []
        tables[table_name].append(row)
    
    return tables

def get_model_columns():
    """Get column definitions from SQLAlchemy models."""
    inspector = inspect(engine)
    tables = {}
    
    for table in Base.metadata.sorted_tables:
        table_name = table.name
        columns = []
        for column in table.columns:
            col_info = {
                'name': column.name,
                'type': str(column.type),
                'nullable': column.nullable,
                'default': column.default,
                'primary_key': column.primary_key
            }
            columns.append(col_info)
        tables[table_name] = columns
    
    return tables

def compare_schemas():
    """Compare model definitions with actual database schema."""
    actual = get_actual_columns()
    model = get_model_columns()
    
    print("=" * 80)
    print("SCHEMA DRIFT ANALYSIS")
    print("=" * 80)
    
    all_drift = []
    
    # Check each model table
    for table_name in sorted(model.keys()):
        model_cols = {col['name']: col for col in model[table_name]}
        
        if table_name not in actual:
            print(f"\n[X] TABLE MISSING IN DB: {table_name}")
            all_drift.append(f"Table {table_name} missing in database")
            continue
        
        actual_cols = {row['COLUMN_NAME']: row for row in actual[table_name]}
        
        # Check for missing columns in database
        for col_name, col_def in model_cols.items():
            if col_name not in actual_cols:
                print(f"\n[X] MISSING COLUMN IN DB: {table_name}.{col_name}")
                print(f"   Model expects: {col_def['type']}, nullable={col_def['nullable']}")
                all_drift.append(f"Table {table_name} missing column {col_name}")
        
        # Check for extra columns in database
        for col_name, col_def in actual_cols.items():
            if col_name not in model_cols:
                print(f"\n[!] EXTRA COLUMN IN DB: {table_name}.{col_name}")
                print(f"   Database has: {col_def['COLUMN_TYPE']}")
                all_drift.append(f"Table {table_name} has extra column {col_name}")
    
    # Check for tables in database but not in models
    for table_name in sorted(actual.keys()):
        if table_name not in model:
            # alembic_version is expected and not a model
            if table_name == 'alembic_version':
                continue
            print(f"\n[!] TABLE IN DB BUT NOT IN MODELS: {table_name}")
            all_drift.append(f"Table {table_name} exists in DB but not in models")
    
    print("\n" + "=" * 80)
    if all_drift:
        print(f"TOTAL DRIFT ISSUES FOUND: {len(all_drift)}")
        for issue in all_drift:
            print(f"  - {issue}")
    else:
        print("[OK] NO SCHEMA DRIFT DETECTED - All tables match models")
    print("=" * 80)
    
    return all_drift

if __name__ == "__main__":
    drift = compare_schemas()
    exit(len(drift))
