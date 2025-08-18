import os
import duckdb
import build_db
import pandas as pd
import sheet_processing
from shiny.express import render, ui

if not os.path.isfile("Registro_Global_Genes_y_Diagnosticos.duckdb"):
    build_db.build()
    sheet_processing.fill_db()


def full_names(acronym):
    match acronym:
        case "AD":
            return "Autosomal Dominant"
        case "AR":
            return "Autosomal recessive"
        case "XL":
            return "X-linked"
        case "MT":
            return "Mitochondrial"


ui.page_opts(fillable=True)
db = duckdb.connect("Registro_Global_Genes_y_Diagnosticos.duckdb")
i_data = db.execute("SELECT * FROM diseases").df()
g_data = db.execute("SELECT * FROM genes").df()
# No se muestran los indices al usuario
df = pd.merge(left=g_data, right=i_data, how="left", on="disease_id")
df["omim"] = [
    ui.HTML(
        f'<a href="https://www.omim.org/entry/{id}">{id}</a>'
        if 0 < id
        else "<span>N/A</span>"
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
    with ui.nav_panel("Statistics"):
        with ui.layout_columns():
            with ui.card(full_screen=True):
                ui.card_header("Frequency of Inheritance Patterns")
                inheritance_counts = (
                    db.execute("SELECT inheritance FROM genes").df().value_counts()
                )
                inheritance_counts = (
                    str(
                        [
                            {"inheritance": full_names(a[0]), "instances": b}
                            for a, b in inheritance_counts.items()
                        ]
                    )
                    .replace("'inheritance'", "inheritance")
                    .replace("'instances'", "instances")
                )
                print(inheritance_counts)
                ui.HTML(f"""
<!-- Styles -->
<style>
#chartdiv {{
  width: 100%;
  height: 500px;
}}

</style>

<!-- Resources -->
<script src="https://cdn.amcharts.com/lib/4/core.js"></script>
<script src="https://cdn.amcharts.com/lib/4/charts.js"></script>
<script src="https://cdn.amcharts.com/lib/4/themes/animated.js"></script>

<!-- Chart code -->
<script>
am4core.ready(function() {{

// Themes begin
am4core.useTheme(am4themes_animated);
// Themes end

var chart = am4core.create("chartdiv", am4charts.PieChart3D);
chart.hiddenState.properties.opacity = 0; // this creates initial fade-in

chart.legend = new am4charts.Legend();

chart.data = {inheritance_counts};

var series = chart.series.push(new am4charts.PieSeries3D());
series.dataFields.value = "instances";
series.dataFields.category = "inheritance";

}}); // end am4core.ready()
</script>

<!-- HTML -->
<div id="chartdiv"></div>
                """)
            with ui.card(full_screen=True):
                ui.card_header("Disease Category and Gene distribution")
                @render.data_frame
                def table():
                    category_gene = db.execute("SELECT category, gene FROM genes").df()
                    category_count = category_gene["category"].value_counts()
                    gene_count = category_gene.groupby("category")["gene"].nunique()
                    table = pd.DataFrame(data={"n (%)": category_count, "Involved genes/loci": gene_count})
                    table["Disease category"] = table.index
                    table = table[["Disease category", "n (%)", "Involved genes/loci"]]
                    return render.DataGrid(table, width="100%")

    with ui.nav_panel("Genes"):

        @render.data_frame
        def gene_db():
            return render.DataGrid(df, width="100%", filters=True)
