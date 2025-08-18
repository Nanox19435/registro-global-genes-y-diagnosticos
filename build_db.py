import duckdb

def build():
    connection = duckdb.connect("Registro_Global_Genes_y_Diagnosticos.duckdb")

    connection.execute(
        "CREATE TABLE diseases (disease_id INTEGER PRIMARY KEY, name VARCHAR(200))"
    )
    connection.execute("""
    CREATE TYPE disease_category AS ENUM (
        'cancer',
        'cardiovascular',
        'cerebrovascular',
        'connective tissue',
        'dermatological',
        'endocrine',
        'hematological, immunological and lymphatic',
        'metabolic',
        'muscular',
        'neurodevelopmental',
        'neurological',
        'ocular',
        'renal and genitourinary',
        'skeletal'
    )""")
    connection.execute("""
        CREATE TYPE inheritance_types AS ENUM (
            'AD',
            'AR',
            'XL',
            'MT'
        )
    """)
    connection.execute("""
        CREATE TABLE genes (
            entry_id INTEGER PRIMARY KEY,
            gene VARCHAR(60),
            disease_id INTEGER,
            omim INTEGER,
            category disease_category,
            inheritance VARCHAR(2),
            somatism BOOLEAN,
            observations VARCHAR(100),
            FOREIGN KEY (disease_id) REFERENCES diseases(disease_id)
        )
    """)
