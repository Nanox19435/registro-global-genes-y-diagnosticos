import os
import duckdb
import build_db
import pandas as pd
import sheet_processing
from shiny.express import render, ui

if not os.path.isfile("Registro_Global_Genes_y_Diagnosticos.duckdb"):
    build_db.build()
    sheet_processing.fill_db()

ui.page_opts(fillable=True)
db = duckdb.connect("Registro_Global_Genes_y_Diagnosticos.duckdb")
i_data = db.execute("SELECT * FROM diseases").df()
g_data = db.execute("SELECT * FROM genes").df()
# No se muestran los indices al usuario
df = pd.merge(left=g_data, right=i_data, how="left", on="disease_id")
df["omim"] = [
    ui.HTML(
        f'<a href="https://www.omim.org/entry/{id}">{id}</a>' if 0 < id else "<span>N/A</span>"
    )
    for id in df["omim"]
]


def inheritance(row):
    if bool(row["somatism"]):
        return row["inheritance"] + " (somatic)"
    else:
        return row["inheritance"]


df["Inheritance"] = df.apply(inheritance, axis=1)

df = df[["gene", "name", "omim", "category", "Inheritance", "observations"]]
df["observations"] = ["" if "nan" == obs else obs for obs in df["observations"]]
df = df.rename(
    columns={
        "gene": "Gene",
        "name": "Disease",
        "omim": "OMIM #",
        "category": "Disease Category",
        "observations": "Observations",
    }
)

with ui.navset_card_tab(id="tab"):
    with ui.nav_panel("Diseases"):

        @render.data_frame
        def database():
            return render.DataGrid(i_data, width="100%")

    with ui.nav_panel("Genes"):

        @render.data_frame
        def db():
            return render.DataGrid(df, width="100%", filters=True)



