# =============================================================================
# Dashboard – Ventes mondiales de jeux vidéo
# Lancer avec :  streamlit run dashboard.py
# Ce fichier doit être dans le même dossier que vgsales_clean.csv
# =============================================================================

import pandas as pd                # manipulation des données
import plotly.express as px        # graphiques interactifs (survol, zoom)
import streamlit as st             # transforme le script en page web

# -----------------------------------------------------------------------------
# 1. Configuration de la page
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Ventes de jeux vidéo", layout="wide")   # page en pleine largeur

REGIONS = {"NA_Sales": "Amérique du Nord", "EU_Sales": "Europe", "JP_Sales": "Japon", "Other_Sales": "Autres"}
COULEURS = {"Amérique du Nord": "#2a78d6", "Europe": "#eb6834", "Japon": "#1baf7a", "Autres": "#9a9a9a"}


# -----------------------------------------------------------------------------
# 2. Chargement des données (le fichier nettoyé par le notebook)
# -----------------------------------------------------------------------------
@st.cache_data                     # garde le fichier en mémoire : pas rechargé à chaque clic
def charger_donnees():
    df = pd.read_csv("vgsales_clean.csv")
    df["Year"] = df["Year"].astype("Int64")   # année en entier (accepte les valeurs vides)
    return df

df = charger_donnees()


# -----------------------------------------------------------------------------
# 3. Filtres dans la barre de gauche
# -----------------------------------------------------------------------------
st.sidebar.header("Filtres")

# Période : curseur entre deux années (on s'arrête à 2016, dernière année fiable)
annee_min, annee_max = st.sidebar.slider("Période", 1980, 2016, (1980, 2016))

# Genres et plateformes : listes à choix multiples (vide = tout sélectionner)
genres = st.sidebar.multiselect("Genres", sorted(df["Genre"].unique()))
top_plateformes = df.groupby("Platform")["Global_Sales"].sum().sort_values(ascending=False).index
plateformes = st.sidebar.multiselect("Plateformes", list(top_plateformes))

# Région : choisit quelle colonne de ventes est utilisée dans les graphiques
choix_region = st.sidebar.radio("Région", ["Monde"] + list(REGIONS.values()))
colonne_ventes = "Global_Sales" if choix_region == "Monde" else \
    [col for col, nom in REGIONS.items() if nom == choix_region][0]

# Application des filtres
filtre = df[(df["Year"] >= annee_min) & (df["Year"] <= annee_max)]   # les jeux sans année sont exclus ici
if genres:                                       # si l'utilisateur a choisi des genres
    filtre = filtre[filtre["Genre"].isin(genres)]
if plateformes:
    filtre = filtre[filtre["Platform"].isin(plateformes)]

st.sidebar.caption(f"{len(filtre):,} jeux sélectionnés".replace(",", " "))

if filtre.empty:                                 # sécurité : aucun jeu ne correspond
    st.warning("Aucun jeu ne correspond à ces filtres. Élargis la période ou retire un filtre.")
    st.stop()


# -----------------------------------------------------------------------------
# 4. Titre et chiffres clés
# -----------------------------------------------------------------------------
st.title("Ventes mondiales de jeux vidéo")
st.caption(f"Ventes physiques en millions d'unités · {annee_min}–{annee_max} · région : {choix_region}")

col1, col2, col3, col4 = st.columns(4)           # 4 cases côte à côte
col1.metric("Ventes totales", f"{filtre[colonne_ventes].sum():,.0f} M".replace(",", " "))
col2.metric("Nombre de jeux", f"{len(filtre):,}".replace(",", " "))
col3.metric("Ventes moyennes par jeu", f"{filtre[colonne_ventes].mean():.2f} M")
col4.metric("Jeux à 1 M ou plus", f"{(filtre['Global_Sales'] >= 1).mean() * 100:.1f} %")


# -----------------------------------------------------------------------------
# 5. Onglets
# -----------------------------------------------------------------------------
onglet1, onglet2, onglet3, onglet4 = st.tabs(["Tendances", "Genres et plateformes", "Régions", "Éditeurs"])

# ---------- Onglet 1 : tendances dans le temps ----------
with onglet1:
    par_an = filtre.groupby("Year").agg(Ventes=(colonne_ventes, "sum"), Jeux=("Name", "count")).reset_index()

    gauche, droite = st.columns(2)
    fig = px.line(par_an, x="Year", y="Ventes", markers=True,
                  title="Évolution des ventes", labels={"Year": "Année", "Ventes": "Ventes (M)"})
    gauche.plotly_chart(fig, width="stretch")

    fig = px.line(par_an, x="Year", y="Jeux", markers=True,
                  title="Nombre de jeux sortis par année", labels={"Year": "Année", "Jeux": "Nombre de jeux"})
    droite.plotly_chart(fig, width="stretch")
    st.caption("2016 est incomplète : le dataset a été collecté en cours d'année.")

    st.subheader("Top 10 des jeux")
    top10 = filtre.nlargest(10, colonne_ventes)[["Name", "Platform", "Year", "Genre", "Publisher", colonne_ventes]]
    st.dataframe(top10.rename(columns={colonne_ventes: "Ventes (M)"}), hide_index=True, width="stretch")

# ---------- Onglet 2 : genres et plateformes ----------
with onglet2:
    gauche, droite = st.columns(2)

    ventes_genre = filtre.groupby("Genre")[colonne_ventes].sum().sort_values().reset_index()
    fig = px.bar(ventes_genre, x=colonne_ventes, y="Genre", orientation="h",
                 title="Ventes par genre", labels={colonne_ventes: "Ventes (M)"})
    gauche.plotly_chart(fig, width="stretch")

    ventes_plat = filtre.groupby("Platform")[colonne_ventes].sum().nlargest(10).sort_values().reset_index()
    fig = px.bar(ventes_plat, x=colonne_ventes, y="Platform", orientation="h",
                 title="Top 10 des plateformes", labels={colonne_ventes: "Ventes (M)", "Platform": "Plateforme"})
    droite.plotly_chart(fig, width="stretch")

    # Cycle de vie des 6 plateformes les plus vendues sur la sélection
    top6 = filtre.groupby("Platform")[colonne_ventes].sum().nlargest(6).index
    cycle = filtre[filtre["Platform"].isin(top6)].groupby(["Year", "Platform"])[colonne_ventes].sum().reset_index()
    fig = px.line(cycle, x="Year", y=colonne_ventes, color="Platform", markers=True,
                  title="Cycle de vie des 6 plateformes principales",
                  labels={"Year": "Année", colonne_ventes: "Ventes (M)", "Platform": "Plateforme"})
    st.plotly_chart(fig, width="stretch")

# ---------- Onglet 3 : régions ----------
with onglet3:
    gauche, droite = st.columns(2)

    # Part de chaque région dans les ventes (toujours sur les 4 régions)
    parts = filtre[list(REGIONS)].sum().rename(REGIONS).reset_index()
    parts.columns = ["Région", "Ventes"]
    fig = px.pie(parts, names="Région", values="Ventes", title="Répartition des ventes par région",
                 color="Région", color_discrete_map=COULEURS, hole=0.45)
    gauche.plotly_chart(fig, width="stretch")

    # Indice d'affinité genre–région : 100 = moyenne, > 100 = la région aime plus ce genre
    gr = filtre.groupby("Genre")[["NA_Sales", "EU_Sales", "JP_Sales"]].sum()
    affinite = (gr / gr.sum()).div(gr.sum(axis=1) / gr.values.sum(), axis=0) * 100
    affinite.columns = ["Amérique du Nord", "Europe", "Japon"]
    fig = px.imshow(affinite.round(0), text_auto=True, color_continuous_scale="RdBu_r",
                    color_continuous_midpoint=100, zmin=0, zmax=200, aspect="auto",
                    title="Affinités genre – région (100 = moyenne)",
                    labels={"x": "Région", "y": "Genre", "color": "Indice"})
    droite.plotly_chart(fig, width="stretch")

    st.caption("Lecture : au Japon, le Role-Playing a un indice d'environ 255, "
               "soit 2,5 fois plus de poids que dans le marché moyen.")

    # ----- Heatmap régionale détaillée, avec ses propres filtres -----
    st.divider()
    st.subheader("Heatmap régionale détaillée")
    st.caption("Le dataset ne donne pas les ventes par pays, seulement par région : "
               "Amérique du Nord, Europe, Japon et Autres.")

    f1, f2, f3 = st.columns(3)                      # 3 menus déroulants côte à côte
    region_hm = f1.selectbox("Région", list(REGIONS.values()), index=2)              # Japon par défaut
    axe_hm = f2.selectbox("Croiser les genres avec", ["Année", "Plateforme"])
    mesure_hm = f3.selectbox("Afficher", ["Ventes (millions)", "Part du genre (%)"])

    col_region = [col for col, nom in REGIONS.items() if nom == region_hm][0]       # ex. "JP_Sales"

    if axe_hm == "Année":
        colonne_x = "Year"
    else:
        colonne_x = "Platform"
        # on garde les 12 plateformes qui vendent le plus dans cette région, pour rester lisible
        top_plat_region = filtre.groupby("Platform")[col_region].sum().nlargest(12).index
        filtre_hm = filtre[filtre["Platform"].isin(top_plat_region)]

    donnees_hm = filtre if axe_hm == "Année" else filtre_hm
    # tableau croisé : une ligne par genre, une colonne par année (ou plateforme)
    hm = donnees_hm.pivot_table(index="Genre", columns=colonne_x, values=col_region,
                                aggfunc="sum", fill_value=0)

    if mesure_hm == "Part du genre (%)":
        hm = hm.div(hm.sum(axis=0), axis=1).fillna(0) * 100   # chaque colonne = 100 %

    # les valeurs sont écrites dans les cases seulement s'il n'y a pas trop de colonnes
    fig = px.imshow(hm.round(0), text_auto=hm.shape[1] <= 15,
                    color_continuous_scale="Blues", aspect="auto",
                    title=f"{region_hm} : {mesure_hm.lower()} par genre et par {axe_hm.lower()}",
                    labels={"x": axe_hm, "y": "Genre", "color": mesure_hm})
    fig.update_layout(height=520)
    st.plotly_chart(fig, width="stretch")

    # phrase d'interprétation automatique
    genre_top = donnees_hm.groupby("Genre")[col_region].sum().idxmax()
    part_top = donnees_hm.groupby("Genre")[col_region].sum().max() / donnees_hm[col_region].sum() * 100
    prefixe = {"Amérique du Nord": "En Amérique du Nord", "Europe": "En Europe",
               "Japon": "Au Japon", "Autres": "Dans les autres régions"}[region_hm]
    st.info(f"{prefixe}, sur la sélection actuelle, le genre n°1 est **{genre_top}** "
            f"({part_top:.0f} % des ventes de la région).")

# ---------- Onglet 4 : éditeurs ----------
with onglet4:
    gauche, droite = st.columns(2)

    top_edit = filtre.groupby("Publisher")[colonne_ventes].sum().nlargest(10).sort_values().reset_index()
    fig = px.bar(top_edit, x=colonne_ventes, y="Publisher", orientation="h",
                 title="Top 10 des éditeurs", labels={colonne_ventes: "Ventes (M)", "Publisher": "Éditeur"})
    gauche.plotly_chart(fig, width="stretch")

    # Éditeur leader de chaque genre et sa part de marché
    ge = filtre.groupby(["Genre", "Publisher"])[colonne_ventes].sum().reset_index()
    ge["Part (%)"] = (ge[colonne_ventes] / ge.groupby("Genre")[colonne_ventes].transform("sum") * 100).round(1)
    leaders = ge.sort_values("Part (%)", ascending=False).drop_duplicates("Genre")
    fig = px.bar(leaders.sort_values("Part (%)"), x="Part (%)", y="Genre", color="Publisher", orientation="h",
                 title="Leader de chaque genre (part de marché)", labels={"Publisher": "Éditeur"})
    fig.add_vline(x=30, line_dash="dash", line_color="grey")      # seuil de leadership du sujet
    droite.plotly_chart(fig, width="stretch")
    st.caption("Ligne pointillée : seuil de 30 %, au-delà duquel un éditeur « domine » un genre.")
