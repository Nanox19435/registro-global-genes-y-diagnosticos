import pandas as pd
import duckdb
import math

def fill_db():
    data = pd.read_csv("data.csv")
    db = duckdb.connect("Registro_Global_Genes_y_Diagnosticos.duckdb")

    diseases = sorted(data["Disease"].map(lambda x: str(x).strip()).unique())
    for idx, disease in enumerate(diseases):
        print(disease)
        db.execute("INSERT INTO diseases VALUES (?, ?)", [idx, disease])

    for idx, row in data.iterrows():
        print(row)
        gene = row["Gene"]

        disease = row["Disease"]
        disease = db.execute("SELECT * FROM diseases WHERE name LIKE ?", [disease.strip()]).df()["disease_id"].item()
        
        omim = row["OMIM #"]
        if math.isnan(omim):
            omim = -1
        
        category = row["Disease Category"].strip().lower() 
        
        inheritance = row["Inheritance"]
        somatism = inheritance.endswith("(somatic)")
        inheritance = inheritance.removesuffix("(somatic)").strip()

        cases = row["UDER"] + row["CONDE"]

        db.execute(
            "INSERT INTO genes VALUES (?,?,?,?,?,?,?,?)",
            [   
                idx,
                gene,
                disease,
                omim,
                category,
                inheritance,
                somatism,
                cases
            ]
        )

        if omim < 0:
            db.execute("INSERT INTO reference VALUES (?,?)", [idx, row["References for diseases without OMIM code"]])
