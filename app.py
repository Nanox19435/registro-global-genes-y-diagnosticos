import os
import pandas as pd

from shiny.express import render, ui
from sqlalchemy import create_engine, text

df = None

if not os.path.isfile("data.csv"):
    DB_CONFIG = {
        'host': os.getenv('DB_ADDRESS'),
        'port': os.getenv('DB_PORT'),
        'database': 'mexgdd',
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PWD')
    }

    conn = create_engine(
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )

    genes = pd.read_sql("SELECT * FROM genes", conn)
    observations = pd.read_sql("SELECT * FROM reference", conn)
    collaborators = pd.read_sql("SELECT * FROM collaborators", conn)
    patients = pd.read_sql("SELECT * FROM patients", conn)
    inheritance_counts = (pd.read_sql("SELECT inheritance FROM genes", conn).value_counts())

    case_count = pd.read_sql("""
    SELECT 
        genes.entry_id,
        COALESCE(optional_counts.cases, 0) + COUNT(patients.entry_id) as cases
    FROM genes
    LEFT JOIN optional_counts ON optional_counts.entry_id = genes.entry_id
    LEFT JOIN patients ON patients.entry_id = genes.entry_id
    GROUP BY genes.entry_id, optional_counts.cases
    ORDER BY genes.entry_id;
    """, conn)

    df = pd.merge(left=genes, right=case_count, how="left", on="entry_id")
    df = pd.merge(left=df, right=collaborators, how="left", on="entry_id")
    df["omim"] = [
        ui.HTML(
            f'<a href="https://www.omim.org/entry/{omim}">{omim}</a>'
            if 0 < omim
            else f"<p>{observations[observations['entry_id'] == id].values[0][1]}</p>"
        )
        for id, omim in enumerate(df["omim"])
    ]


    def inheritance(row):
        inheritance = row["inheritance"]
        if bool(row["somatism"]):
            return inheritance + " (somatic)"
        else:
            return inheritance

    df["Inheritance"] = df.apply(inheritance, axis=1)
    df = df[["gene", "disease", "omim", "category", "Inheritance", "cases", "informed_by"]]
    df = df.rename(
        columns={
            "gene": "Gene",
            "name": "Disease",
            "omim": "OMIM #",
            "category": "Disease Category",
            "cases": "Number of Confirmed Patients",
            "informed_by": "Informed by"
        }
    )
    df.to_csv("data.csv", index=False)
else:
    df = pd.read_csv("data.csv")

inheritance_counts = df["Inheritance"].str[:2].value_counts()

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

ui.page_opts(
    title=ui.img(src="logo.jpeg", style="width:500px"),
    window_title="MexGDD",
    fillable=True,
)
with ui.navset_card_tab(id="tab"):
    with ui.nav_panel("Summary"):
        ui.div(
            ui.p(
                "MexGDD is a curated database of over 600 genetic diseases occurring in Mexico and confirmed by DNA testing in a single hospital-based center from 2005 to 2025.",
                class_ = "fw-bold"
            ),
            ui.p(
                "Information on genes carrying disease-causing mutations and resulting phenotypes are included. For any contribution or comment please contact us directly at: ",
                ui.a(
                    "jczenteno@facmed.unam.mx", href="mailto:jczenteno@facmed.unam.mx"
                ),
                ".",
                class_ = "fw-bold"
            ),
            ui.p("""
Genes and disease curation was led by: Juan C. Zenteno, Vianey Ordoñez-Labastida, Luis Montes-Almanza, Froylan Garcia-Martinez, Alejandro Martinez-Herrera, David Carreño-Bolaños, Rocio Arce-Gonzalez and Oscar F. Chacón-Camacho, from the Rare Diseases Diagnostic Unit (UDER)-Faculty of Medicine , UNAM and the Department of Genetics of the Institute of Ophthalmology “Conde de Valenciana”, Mexico City, Mexico.
            """, class_ = "fw-bold"),
            ui.a("Read the MexGDD article in Orphanet Journal of Rare Diseases.", href="https://link.springer.com/article/10.1186/s13023-026-04318-1"),
            ui.p(),
            ui.p("Version V1.1 released March 20 2026."),
            ui.p("Current version V1.2 released June 8 2026.")
        )


    with ui.nav_panel("Statistics"):
        with ui.layout_columns():
            with ui.card(full_screen=True):
                ui.card_header("Frequency of Inheritance Patterns")
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
chart.legend.labels.template.text = "{{inheritance}}: n={{instances}}";
chart.legend.valueLabels.template.text = "";

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
                    category_gene = pd.read_sql("SELECT category, gene FROM genes", conn)
                    category_count = category_gene["category"].value_counts()
                    gene_count = category_gene.groupby("category")["gene"].nunique()
                    table = pd.DataFrame(
                        data={
                            "n (%)": category_count,
                            "Involved genes/loci": gene_count,
                        }
                    )
                    total = table.sum()
                    table.loc["Total"] = total
                    table["n (%)"] = [f"{n} ({n/total.get('n (%)'):.2%})" for n in table["n (%)"]]
                    table["n (%)"]["Total"] = f"{sum(category_count)} (100%)"
                    table["Disease Category"] = [
                        disease.title().replace("And", "and") for disease in table.index
                    ]
                    table = table[["Disease Category", "n (%)", "Involved genes/loci"]]
                    return render.DataGrid(table, width="100%", styles=[{"style": {"font-weight": "bold"}}])

    with ui.nav_panel("Genes"):

        @render.data_frame
        def gene_db():
            return render.DataGrid(
                df, 
                width="100%", 
                filters=True, 
                styles=[
                    {"style": {"font-weight": "bold"}}
                ]
            )
