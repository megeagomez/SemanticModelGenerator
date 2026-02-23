#!/usr/bin/env python
"""Verify the imported data in DuckDB"""

import duckdb

conn = duckdb.connect('data/miguel.duckdb')

# Show semantic model
print('=== SEMANTIC MODEL ===')
result = conn.execute('SELECT * FROM semantic_model').fetchall()
for row in result:
    print(f'ID: {row[0]}, Name: {row[3]}, Workspace ID: {row[2]}, Culture: {row[4]}')

# Show tables
print('\n=== SEMANTIC MODEL TABLES ===')
result = conn.execute('SELECT DISTINCT table_name FROM semantic_model_table ORDER BY table_name').fetchall()
for row in result:
    print(f'  - {row[0]}')

# Show columns for one table
print('\n=== COLUMNS IN InternetSales TABLE ===')
result = conn.execute('SELECT column_name, data_type FROM semantic_model_column WHERE table_name = ? ORDER BY column_name LIMIT 5', ['InternetSales']).fetchall()
for row in result:
    print(f'  - {row[0]}: {row[1]}')

# Show report info
print('\n=== REPORT ===')
result = conn.execute('SELECT name, report_id FROM report').fetchall()
for row in result:
    print(f'Report: {row[0]}, ID: {row[1]}')

# Show report visuals
print('\n=== REPORT VISUALS ===')
result = conn.execute('SELECT page_name, visual_type FROM report_visual ORDER BY page_name').fetchall()
for row in result:
    print(f'  - Page {row[0]}: {row[1]}')

# Show column usage
print('\n=== COLUMN USAGE IN VISUALS ===')
result = conn.execute('SELECT page_name, table_name, column_name, usage_count FROM report_column_used').fetchall()
for row in result:
    print(f'  Page {row[0]}: {row[1]}.{row[2]} (used {row[3]}x)')

# Show measure usage
print('\n=== MEASURE USAGE IN VISUALS ===')
result = conn.execute('SELECT page_name, table_name, measure_name, usage_count FROM report_measure_used').fetchall()
for row in result:
    print(f'  Page {row[0]}: {row[1]}.{row[2]} (used {row[3]}x)')

conn.close()
print('\n✅ Import verification complete!')

