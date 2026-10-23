# =============================================================================
# Dashboard – Ventes mondiales de jeux vidéo (dataset de l'exercice : vgsales.csv)
# Lancer avec :  python -m streamlit run dashboard.py
# À placer dans le même dossier que vgsales_clean.csv (données de l'exercice nettoyées dans le notebook)
# et que le dossier .streamlit/ (qui contient le thème sombre).
# =============================================================================

import pandas as pd                # manipulation des données
import plotly.express as px        # graphiques interactifs (survol, zoom)
import streamlit as st             # transforme le script en page web

# -----------------------------------------------------------------------------
# 1. Configuration de la page et identité visuelle
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Ventes de jeux vidéo", page_icon="🎮", layout="wide")

# Palette : un fond sombre doux, UNE couleur d'accent, et du gris pour le reste
FOND, CARTE, BORD = "#0F1117", "#161922", "#232736"
TEXTE, DOUX, DISCRET = "#E8E9EE", "#9096A8", "#5B6175"
ACCENT = "#8B9CFF"          # lavande : la couleur principale
ATTENUE = "#2E3448"         # barres "secondaires"
CHAUD = "#F2B48C"           # pêche : seulement pour signaler "au-dessus de la moyenne"

REGIONS = {"na_sales": "Amérique du Nord", "eu_sales": "Europe", "jp_sales": "Japon", "other_sales": "Autres"}
COULEURS_REGIONS = {"Amérique du Nord": ACCENT, "Europe": "#6FCFB7", "Japon": CHAUD, "Autres": DISCRET}

# Style de la page (CSS) : police, cartes, onglets, éléments Streamlit masqués
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], p, label, span, div {{ font-family: 'Manrope', 'Segoe UI', Arial, sans-serif; }}
.stApp {{ background: {FOND}; }}
header[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stToolbar"] {{ display: none; }}
.block-container {{ padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px; }}
section[data-testid="stSidebar"] {{ background: {CARTE}; border-right: 1px solid {BORD}; }}
section[data-testid="stSidebar"] .block-container {{ padding-top: 2rem; }}

.titre {{ font-size: 34px; line-height: 1.15; font-weight: 800; color: {TEXTE}; letter-spacing: -0.5px; margin: 0; }}
.sous-titre {{ font-size: 15px; color: {DOUX}; margin: 4px 0 28px; }}
.sous-titre b {{ color: {TEXTE}; font-weight: 600; }}

.kpi {{ background: {CARTE}; border: 1px solid {BORD}; border-radius: 14px; padding: 18px 20px; }}
.kpi .label {{ color: {DOUX}; font-size: 13px; font-weight: 500; }}
.kpi .valeur {{ color: {TEXTE}; font-size: 30px; font-weight: 700; letter-spacing: -0.5px;
               font-variant-numeric: tabular-nums; margin-top: 2px; }}
.kpi .detail {{ color: {DISCRET}; font-size: 12.5px; margin-top: 2px; }}

.lecture {{ color: {DOUX}; font-size: 14px; margin: 2px 0 10px; }}
.lecture b {{ color: {TEXTE}; font-weight: 600; }}
.section {{ color: {TEXTE}; font-size: 17px; font-weight: 700; margin: 26px 0 2px; }}

.stTabs [data-baseweb="tab-list"] {{ gap: 28px; border-bottom: 1px solid {BORD}; }}
.stTabs [data-baseweb="tab"] {{ background: transparent; padding: 10px 2px; color: {DOUX}; font-weight: 600; }}
.stTabs [aria-selected="true"] {{ color: {TEXTE}; }}
.stTabs [data-baseweb="tab-highlight"] {{ background: {ACCENT}; }}
hr {{ border-color: {BORD}; }}
</style>
""", unsafe_allow_html=True)


def styliser(fig, hauteur=380, grille_x=True, grille_y=False):
    """Même style pour tous les graphiques : fond transparent, grille très légère, police du site."""
    fig.update_layout(
        template="plotly_dark", height=hauteur,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, Segoe UI, Arial, sans-serif", color=DOUX, size=12.5),
        title=dict(font=dict(size=15, color=TEXTE), x=0, xanchor="left", y=0.98),
        margin=dict(l=0, r=10, t=44, b=0), showlegend=False, bargap=0.35,
        hoverlabel=dict(bgcolor=CARTE, bordercolor=BORD, font=dict(color=TEXTE, family="Manrope, Arial")),
    )
    fig.update_xaxes(showgrid=grille_x, gridcolor=BORD, zeroline=False, title=None, tickfont_color=DISCRET)
    fig.update_yaxes(showgrid=grille_y, gridcolor=BORD, zeroline=False, title=None, tickfont_color=DOUX)
    return fig


def barres(donnees, x, y, titre, format_valeur=".0f", hauteur=380):
    """Barres horizontales : la première en couleur d'accent, les autres en gris."""
    couleurs = [ACCENT if i == len(donnees) - 1 else ATTENUE for i in range(len(donnees))]
    fig = px.bar(donnees, x=x, y=y, orientation="h", title=titre, text=x)
    fig.update_traces(marker_color=couleurs, marker_cornerradius=4, texttemplate=f"%{{x:{format_valeur}}}",
                      textposition="outside", textfont=dict(color=DOUX, size=12), cliponaxis=False,
                      hovertemplate="%{y} : %{x:.1f} M<extra></extra>")
    return styliser(fig, hauteur, grille_x=False)


def carte(colonne, label, valeur, detail=""):
    """Carte de chiffre clé."""
    colonne.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="valeur">{valeur}</div>'
                     f'<div class="detail">{detail}</div></div>', unsafe_allow_html=True)


def lecture(texte):
    """Une phrase de lecture du graphique, discrète."""
    st.markdown(f'<div class="lecture">{texte}</div>', unsafe_allow_html=True)


def nombre(x, decimales=0):
    """Nombre à la française : espace pour les milliers, virgule décimale."""
    return f"{x:,.{decimales}f}".replace(",", " ").replace(".", ",")


# -----------------------------------------------------------------------------
# 2. Chargement des données (le fichier nettoyé par le notebook)
# -----------------------------------------------------------------------------
@st.cache_data                     # garde le fichier en mémoire : pas rechargé à chaque clic
def charger_donnees():
    """Charge les données de l'exercice, nettoyées dans le notebook du groupe (vgsales_clean.csv)."""
    df = pd.read_csv("vgsales_clean.csv")
    # Le nettoyage est déjà fait dans le notebook ; on le revérifie ici par sécurité :
    df["Year"] = df.groupby("Platform")["Year"].transform(lambda x: x.fillna(x.median()))   # année -> médiane plateforme
    df["Year"] = df["Year"].fillna(df["Year"].median()).astype(int)
    df["Publisher"] = df["Publisher"].fillna("Unknown")                                        # éditeur -> "Unknown"
    df = (df.sort_values("Global_Sales", ascending=False)                                      # vrais doublons
            .drop_duplicates(subset=["Name", "Platform", "Year"], keep="first"))

    # Noms de colonnes utilisés dans le reste du dashboard
    return df.rename(columns={"Name": "title", "Platform": "console", "Year": "year", "Genre": "genre",
                              "Publisher": "publisher", "Global_Sales": "total_sales", "NA_Sales": "na_sales",
                              "EU_Sales": "eu_sales", "JP_Sales": "jp_sales", "Other_Sales": "other_sales"})

df = charger_donnees()


# -----------------------------------------------------------------------------
# 3. Filtres (barre de gauche)
# -----------------------------------------------------------------------------
st.sidebar.markdown(f"<p style='color:{TEXTE};font-size:18px;font-weight:700;margin:0'>Filtres</p>"
                    f"<p style='color:{DOUX};font-size:13px;margin:2px 0 18px'>Ils s'appliquent à tous les onglets.</p>",
                    unsafe_allow_html=True)

premiere, derniere = int(df["year"].min()), int(df["year"].max())
annee_min, annee_max = st.sidebar.slider("Période", premiere, derniere, (premiere, derniere))
choix_region = st.sidebar.selectbox("Région", ["Monde"] + list(REGIONS.values()))
colonne_ventes = "total_sales" if choix_region == "Monde" else \
    [col for col, nom in REGIONS.items() if nom == choix_region][0]
genres = st.sidebar.multiselect("Genres", sorted(df["genre"].unique()), placeholder="Tous")
top_plateformes = df.groupby("console")["total_sales"].sum().sort_values(ascending=False).index
plateformes = st.sidebar.multiselect("Plateformes", list(top_plateformes), placeholder="Toutes")

# Application des filtres
filtre = df[(df["year"] >= annee_min) & (df["year"] <= annee_max)]
if genres:
    filtre = filtre[filtre["genre"].isin(genres)]
if plateformes:
    filtre = filtre[filtre["console"].isin(plateformes)]

st.sidebar.markdown(f"<p style='color:{DISCRET};font-size:12.5px;margin-top:28px;line-height:1.5'>"
                    "Source : vgsales.csv (données de l'exercice), nettoyé dans le notebook du groupe. "
                    "Ventes physiques en millions d'unités. Données jusqu'en 2016.</p>", unsafe_allow_html=True)

if filtre.empty or filtre[colonne_ventes].sum() == 0:      # sécurité : aucun jeu ou aucune vente
    st.warning("Aucune vente ne correspond à ces filtres. Élargis la période ou retire un filtre.")
    st.stop()


# -----------------------------------------------------------------------------
# 4. Titre et chiffres clés
# -----------------------------------------------------------------------------
st.markdown(f'<div class="titre">Ventes mondiales de jeux vidéo</div>'
            f'<div class="sous-titre"><b>{choix_region}</b> · {annee_min} – {annee_max} · {nombre(len(filtre))} jeux</div>',
            unsafe_allow_html=True)

meilleur = filtre.loc[filtre[colonne_ventes].idxmax()]
c1, c2, c3, c4 = st.columns(4, gap="medium")
carte(c1, "Ventes totales", f"{nombre(filtre[colonne_ventes].sum())} M", "millions d'unités")
carte(c2, "Ventes moyennes", f"{nombre(filtre[colonne_ventes].mean(), 2)} M", "par jeu")
carte(c3, "Jeux à succès", f"{nombre((filtre['total_sales'] >= 1).mean() * 100, 1)} %", "vendus à 1 million ou plus")
carte(c4, "Meilleure vente", f"{nombre(meilleur[colonne_ventes], 1)} M", f"{meilleur['title'][:30]} · {meilleur['console']}")
st.write("")


# -----------------------------------------------------------------------------
# 5. Onglets
# -----------------------------------------------------------------------------
onglet1, onglet2, onglet3, onglet4 = st.tabs(["Tendances", "Genres et plateformes", "Régions", "Éditeurs"])

# ---------- Onglet 1 : tendances ----------
with onglet1:
    par_an = filtre.groupby("year")[colonne_ventes].sum().reset_index(name="Ventes")
    record = par_an.loc[par_an["Ventes"].idxmax()]
    st.markdown('<p class="section">Évolution des ventes</p>', unsafe_allow_html=True)
    lecture(f"Année record : <b>{int(record['year'])}</b> ({nombre(record['Ventes'])} M). "
            "Après 2010, la baisse vient en partie du passage au téléchargement, absent des données.")

    fig = px.area(par_an, x="year", y="Ventes")
    fig.update_traces(line=dict(color=ACCENT, width=2.5), fillcolor="rgba(139,156,255,0.12)",
                      hovertemplate="%{x} : %{y:.0f} M<extra></extra>")
    fig.add_scatter(x=[record["year"]], y=[record["Ventes"]], mode="markers+text",
                    marker=dict(size=9, color=ACCENT, line=dict(color=FOND, width=2)),
                    text=[f"  {int(record['year'])}"], textposition="middle right",
                    textfont=dict(color=TEXTE, size=13), hoverinfo="skip")
    st.plotly_chart(styliser(fig, 340, grille_x=False, grille_y=True), width="stretch")

    st.markdown('<p class="section">Les 10 jeux les plus vendus</p>', unsafe_allow_html=True)
    top10 = filtre.nlargest(10, colonne_ventes)[["title", "console", "year", "genre", "publisher", colonne_ventes]]
    st.dataframe(
        top10, hide_index=True, width="stretch",
        column_config={
            "title": "Jeu", "console": "Console", "year": st.column_config.NumberColumn("Année", format="%d"),
            "genre": "Genre", "publisher": "Éditeur",
            colonne_ventes: st.column_config.ProgressColumn("Ventes (M)", format="%.1f", min_value=0,
                                                            max_value=float(top10[colonne_ventes].max())),
        })

# ---------- Onglet 2 : genres et plateformes ----------
with onglet2:
    ventes_genre = filtre.groupby("genre")[colonne_ventes].sum().nlargest(10).sort_values().reset_index()
    ventes_plat = filtre.groupby("console")[colonne_ventes].sum().nlargest(10).sort_values().reset_index()
    st.markdown('<p class="section">Ce qui se vend le plus</p>', unsafe_allow_html=True)
    lecture(f"Genre n°1 : <b>{ventes_genre.iloc[-1]['genre']}</b> · Console n°1 : <b>{ventes_plat.iloc[-1]['console']}</b>.")

    gauche, droite = st.columns(2, gap="large")
    gauche.plotly_chart(barres(ventes_genre, colonne_ventes, "genre", "Top 10 des genres (M)"), width="stretch")
    droite.plotly_chart(barres(ventes_plat, colonne_ventes, "console", "Top 10 des consoles (M)"), width="stretch")

    with st.expander("Voir le cycle de vie des consoles"):
        top6 = filtre.groupby("console")[colonne_ventes].sum().nlargest(6).index
        cycle = filtre[filtre["console"].isin(top6)].groupby(["year", "console"])[colonne_ventes].sum().reset_index()
        fig = px.line(cycle, x="year", y=colonne_ventes, color="console",
                      color_discrete_sequence=[ACCENT, "#6FCFB7", CHAUD, "#C4A7F5", "#7FB6E8", "#E8A0B8"])
        fig.update_traces(line=dict(width=2.2), hovertemplate="%{x} : %{y:.0f} M<extra></extra>")
        fig = styliser(fig, 340, grille_x=False, grille_y=True)
        fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.12, x=0, title=None, bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig, width="stretch")
        lecture("Chaque console vit 7 à 10 ans : montée, pic, puis déclin à l'arrivée de la génération suivante.")

# ---------- Onglet 3 : régions ----------
with onglet3:
    parts = filtre[list(REGIONS)].sum().rename(REGIONS)
    parts = (parts / parts.sum() * 100).reset_index()
    parts.columns = ["Région", "Part"]
    st.markdown('<p class="section">Où se vendent les jeux</p>', unsafe_allow_html=True)
    lecture(f"L'Amérique du Nord représente <b>{nombre(parts['Part'].iloc[0])} %</b> des ventes de la sélection.")

    # Une seule barre empilée à 100 % : plus lisible qu'un camembert
    fig = px.bar(parts, x="Part", y=["Ventes"] * len(parts), color="Région", orientation="h",
                 color_discrete_map=COULEURS_REGIONS, text=parts["Part"].map(lambda p: f"{p:.0f} %"))
    fig.update_traces(textposition="inside", textfont=dict(color=FOND, size=13), marker_line_width=0,
                      hovertemplate="%{fullData.name} : %{x:.1f} %<extra></extra>")
    fig = styliser(fig, 96, grille_x=False)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.6, x=0, title=None, bgcolor="rgba(0,0,0,0)"),
                      margin=dict(l=0, r=0, t=34, b=0), bargap=0.05)
    fig.update_xaxes(visible=False, range=[0, 100])
    fig.update_yaxes(visible=False)
    st.plotly_chart(fig, width="stretch")

    # Indice d'affinité : 100 = moyenne mondiale, au-dessus = la région aime plus ce genre
    gr = filtre.groupby("genre")[["na_sales", "eu_sales", "jp_sales"]].sum()
    gr = gr[gr.sum(axis=1) >= 0.01 * gr.values.sum()]          # genres qui pèsent au moins 1 % des ventes
    affinite = (gr / gr.sum()).div(gr.sum(axis=1) / gr.values.sum(), axis=0) * 100
    affinite.columns = ["Amérique du Nord", "Europe", "Japon"]

    st.markdown('<p class="section">Les goûts de chaque région</p>', unsafe_allow_html=True)
    lecture("100 = moyenne mondiale. Plus la case est cuivrée, plus la région aime ce genre <b>au-dessus</b> de la moyenne.")
    fig = px.imshow(affinite.round(0), text_auto=True, aspect="auto", zmin=0, zmax=200,
                    color_continuous_scale=[[0, "#1E2436"], [0.5, CARTE], [1, "#B9775A"]])
    fig.update_traces(hovertemplate="%{y} · %{x} : %{z}<extra></extra>", textfont=dict(color=TEXTE, size=12.5),
                      xgap=3, ygap=3)
    fig = styliser(fig, 460, grille_x=False)
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(side="top", tickfont_color=TEXTE)
    st.plotly_chart(fig, width="stretch")

    # ----- Heatmap détaillée : une région, genres × années ou consoles -----
    st.markdown('<p class="section">Explorer une région en détail</p>', unsafe_allow_html=True)
    lecture("Les données donnent des régions, pas des pays.")
    f1, f2, f3 = st.columns(3)
    region_hm = f1.selectbox("Région ", list(REGIONS.values()), index=2)          # Japon par défaut
    axe_hm = f2.selectbox("Croiser les genres avec", ["Année", "Console"])
    mesure_hm = f3.selectbox("Afficher", ["Ventes (M)", "Part du genre (%)"])
    col_region = [col for col, nom in REGIONS.items() if nom == region_hm][0]

    if axe_hm == "Année":
        colonne_x, donnees_hm = "year", filtre
    else:
        colonne_x = "console"
        top_plat_region = filtre.groupby("console")[col_region].sum().nlargest(12).index   # 12 consoles max
        donnees_hm = filtre[filtre["console"].isin(top_plat_region)]

    if donnees_hm[col_region].sum() > 0:
        top_genres = donnees_hm.groupby("genre")[col_region].sum().nlargest(10).index      # 10 genres max
        hm = donnees_hm[donnees_hm["genre"].isin(top_genres)].pivot_table(
            index="genre", columns=colonne_x, values=col_region, aggfunc="sum", fill_value=0)
        if mesure_hm == "Part du genre (%)":
            hm = hm.div(hm.sum(axis=0), axis=1).fillna(0) * 100      # chaque colonne = 100 %
        fig = px.imshow(hm.round(1), aspect="auto", text_auto=".0f" if hm.shape[1] <= 15 else False,
                        color_continuous_scale=[[0, FOND], [1, ACCENT]])
        fig.update_traces(hovertemplate="%{y} · %{x} : %{z:.1f}<extra></extra>", xgap=2, ygap=2)
        fig = styliser(fig, 420, grille_x=False)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, width="stretch")

        genre_top = donnees_hm.groupby("genre")[col_region].sum().idxmax()
        part_top = donnees_hm.groupby("genre")[col_region].sum().max() / donnees_hm[col_region].sum() * 100
        dans = {"Amérique du Nord": "en Amérique du Nord", "Europe": "en Europe",
                "Japon": "au Japon", "Autres": "dans les autres régions"}[region_hm]
        lecture(f"Genre n°1 {dans} sur la sélection : <b>{genre_top}</b> ({nombre(part_top)} % des ventes).")

# ---------- Onglet 4 : éditeurs ----------
with onglet4:
    top_edit = filtre.groupby("publisher")[colonne_ventes].sum().nlargest(10).sort_values().reset_index()
    part_top10 = top_edit[colonne_ventes].sum() / filtre[colonne_ventes].sum() * 100
    st.markdown('<p class="section">Qui domine le marché</p>', unsafe_allow_html=True)
    lecture(f"Les 10 premiers éditeurs font <b>{nombre(part_top10)} %</b> des ventes de la sélection.")

    # Éditeur leader de chaque genre (genres d'au moins 10 M) et sa part de marché
    ge = filtre.groupby(["genre", "publisher"])[colonne_ventes].sum().reset_index()
    ge = ge[ge.groupby("genre")[colonne_ventes].transform("sum") >= 10]
    ge["Part"] = ge[colonne_ventes] / ge.groupby("genre")[colonne_ventes].transform("sum") * 100
    leaders = ge.sort_values("Part", ascending=False).drop_duplicates("genre").sort_values("Part")

    gauche, droite = st.columns(2, gap="large")
    gauche.plotly_chart(barres(top_edit, colonne_ventes, "publisher", "Top 10 des éditeurs (M)", hauteur=420),
                        width="stretch")

    couleurs = [ACCENT if p > 30 else ATTENUE for p in leaders["Part"]]   # accent = domine son genre (> 30 %)
    fig = px.bar(leaders, x="Part", y="genre", orientation="h", title="Leader de chaque genre (% du genre)")
    fig.update_traces(marker_color=couleurs, marker_cornerradius=4, text=leaders["publisher"],
                      textposition="outside", textfont=dict(color=DOUX, size=12), cliponaxis=False,
                      hovertemplate="%{y} : %{text}, %{x:.0f} %<extra></extra>")
    fig.add_vline(x=30, line_dash="dot", line_color=DISCRET, layer="below")        # seuil de 30 % du sujet
    fig = styliser(fig, 420, grille_x=False)
    fig.update_xaxes(range=[0, max(100, leaders["Part"].max() + 30)], ticksuffix=" %")
    droite.plotly_chart(fig, width="stretch")
    lecture("En lavande : l'éditeur contrôle plus de 30 % du genre (pointillés = seuil de 30 %).")
