import pandas as pd
import duckdb
import math

def fill_db():
    data = pd.read_csv("data.csv")
    db = duckdb.connect("Registro_Global_Genes_y_Diagnosticos.duckdb")

    diseases = sorted(data["DISEASE"].map(lambda x: x.strip()).unique())
    for idx, disease in enumerate(diseases):
        print(disease)
        db.execute("INSERT INTO diseases VALUES (?, ?)", [idx, disease])

    # gene_data = data[~data["GENES"].str.contains("p|q")]
    for idx, row in data.iterrows():
        print(row)
        gene = row["GENES"]

        disease = row["DISEASE"]
        disease = db.execute("SELECT * FROM diseases WHERE name LIKE ?", [disease.strip()]).df()["disease_id"].item()
        
        omim = row[" OMIM #"]
        if math.isnan(omim):
            omim = -1
        
        category = row["DISEASE CATEGORY"].strip().lower()
        
        inheritance = row["INHERITANCE"]
        somatism = inheritance.endswith("(somatic)")
        inheritance = inheritance.removesuffix("(somatic)").strip()
        
        observations = row["References for disease without OMIM code"]

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
                observations
            ]
        )