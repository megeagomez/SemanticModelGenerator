import duckdb
con = duckdb.connect('D:/Modelos/toyotamodels.duckdb', read_only=True)

# report 8: workspace_id=6c30916d..., semantic_model_reference=edd172f8...
# SO semantic_model_reference seems to be the Power BI semantic model GUID

# Check if SM exists with that id
r = con.execute("SELECT * FROM semantic_model WHERE semantic_model_id = 'edd172f8-0f69-416e-b555-db1156566b6b'").fetchall()
print('SM by guid:', r)

# Try matching by name
r2 = con.execute("SELECT r.id, r.name, sm.id, sm.name FROM report r JOIN semantic_model sm ON sm.name = r.name || '.SemanticModel' WHERE r.id = 8").fetchall()
print('By name join:', r2)

# Try matching by report_id pattern
r3 = con.execute("SELECT r.id, r.name, sm.id, sm.name FROM report r JOIN semantic_model sm ON sm.semantic_model_id = 'local_' || r.name WHERE r.id = 8").fetchall()
print('By local_ prefix join:', r3)

# Check how many reports can match by name
r4 = con.execute("SELECT COUNT(*) FROM report r JOIN semantic_model sm ON sm.name = r.name || '.SemanticModel'").fetchone()
print(f'Reports matching by name: {r4[0]}')

# Check shared models - reports with same semantic_model_reference
r5 = con.execute("""
    SELECT r2.id, r2.name 
    FROM report r1 
    JOIN report r2 ON r2.semantic_model_reference = r1.semantic_model_reference AND r2.id != r1.id
    WHERE r1.id = 8
""").fetchall()
print('Reports sharing same semantic_model_reference:', r5)

# Check if report_page has is_visible column
print('\n=== report_page for report 8 ===')
r6 = con.execute("SELECT * FROM report_page WHERE report_name = 'Validación Profit After Sales'").fetchall()
for row in r6:
    print(row)

# Check measure DAX from semantic model 
print('\n=== Measures with DAX (sm 9) ===')
r7 = con.execute("SELECT table_name, measure_name, LEFT(expression, 100) FROM semantic_model_measure WHERE semantic_model_id = 9 LIMIT 5").fetchall()
for row in r7:
    print(row)

con.close()
