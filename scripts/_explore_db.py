import duckdb
con = duckdb.connect('D:/Modelos/toyotamodels.duckdb', read_only=True)

# Check how reports link to models
print('=== Sample semantic_model_reference values ===')
for r in con.execute('SELECT id, name, semantic_model_reference FROM report LIMIT 5').fetchall():
    print(r)

print('\n=== Semantic models ===')
for r in con.execute('SELECT id, name, semantic_model_id, workspace_id FROM semantic_model LIMIT 10').fetchall():
    print(r)

print('\n=== Report 8 details ===')
for r in con.execute("SELECT * FROM report WHERE id = 8").fetchall():
    print(r)

# Check if report name matches a semantic model name
print('\n=== SM by name Profit ===')
for r in con.execute("SELECT id, name FROM semantic_model WHERE name ILIKE '%profit%'").fetchall():
    print(r)

print('\n=== SM partition sample with source_expression ===')
for r in con.execute("SELECT table_name, partition_name, source_type, LEFT(source_expression, 120) FROM semantic_model_partitions WHERE semantic_model_id = 6 AND source_expression != '' LIMIT 5").fetchall():
    print(r)

con.close()
import sys; sys.exit(0)

# DEAD CODE BELOW
rows = []
print('=== Report ===')
for r in rows:
    print(r)

if rows:
    rid = rows[0][0]
    rname = rows[0][1]
    sm_ref = rows[0][3]
    
    # Pages
    print(f'\n=== Pages for {rname} ===')
    pages = con.execute('SELECT name, display_name, height, width, is_visible FROM report_page WHERE report_name = ?', [rname]).fetchall()
    for p in pages:
        print(p)
    
    # Visual count per page
    print(f'\n=== Visuals per page ===')
    vpp = con.execute('SELECT page_name, COUNT(*) FROM report_visual WHERE report_id = ? GROUP BY page_name', [rid]).fetchall()
    for v in vpp:
        print(v)
    
    # Sample visual data
    print(f'\n=== Sample visuals (first 5) ===')
    vs = con.execute('SELECT name, visual_type, position_x, position_y, position_width, position_height, text_content FROM report_visual WHERE report_id = ? LIMIT 5', [rid]).fetchall()
    for v in vs:
        print(v)
    
    # Semantic model reference
    print(f'\n=== Semantic model ref: {sm_ref} ===')
    sm = con.execute('SELECT id, name, semantic_model_id FROM semantic_model WHERE semantic_model_id = ?', [sm_ref]).fetchall()
    print(sm)
    if not sm:
        sm = con.execute("SELECT id, name, semantic_model_id FROM semantic_model LIMIT 5").fetchall()
        print('First 5 models:', sm)

    # Reports sharing same model  
    print(f'\n=== Reports sharing same semantic_model_reference ===')
    shared = con.execute('SELECT id, name FROM report WHERE semantic_model_reference = ? AND id != ?', [sm_ref, rid]).fetchall()
    for s in shared:
        print(s)
    
    # Columns used sample
    print(f'\n=== Columns used (first 5) ===')
    cols = con.execute('SELECT page_name, visual_name, table_name, column_name FROM report_column_used WHERE report_id = ? LIMIT 5', [rid]).fetchall()
    for c in cols:
        print(c)
    
    # Measures used sample
    print(f'\n=== Measures used (first 5) ===')
    meas = con.execute('SELECT page_name, visual_name, table_name, measure_name FROM report_measure_used WHERE report_id = ? LIMIT 5', [rid]).fetchall()
    for m in meas:
        print(m)
    
    # Partitions sample
    if sm:
        smid = sm[0][0]
        print(f'\n=== Partitions sample (sm_id={smid}) ===')
        parts = con.execute('SELECT table_name, partition_name, source_type, mode, LEFT(source_expression, 80) FROM semantic_model_partitions WHERE semantic_model_id = ? LIMIT 5', [smid]).fetchall()
        for p in parts:
            print(p)

con.close()
