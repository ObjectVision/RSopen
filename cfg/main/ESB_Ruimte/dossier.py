"""Zet de kernfiguren van de ESB-analyses in een Word-document, als intern dossier voor het gesprek met de VU over
het artikel: per figuur wat we eruit concluderen en hoe hij aansluit op de andere. De figuren zijn dezelfde als de
grafieken in de Excel van excel.py. Alleen presentatie: elk getal komt uit de csv's die GeoDMS schrijft
(ESB_Ruimte/*) of uit de figuren van figuren.py; geen getal staat hier met de hand, behalve de waarden van 1996 uit
figuur 7 van Ruimte voor werken (2022).

Gebruik: python dossier.py <map A en B> <map G> <map 13> <map D> <uitvoer.docx>
Draai eerst figuren.py met de mappen van A en B, D en G.
"""
import sys
from pathlib import Path

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

from figuren import SECTOREN, lees, nl

GRIJS = RGBColor(0x52, 0x51, 0x4E)
# Netto ruimtebeslag in m² per baan in 1996 in figuur 7 van Koomen en Claassens (2022), Ruimte voor werken,
# SPINlab Research Memorandum SL-20; de jaren voor 2012 zijn daar benaderd met het bouwjaar van de panden.
FIG7_1996 = {"Nijverheid": 61.52, "Logistiek": 39.67}
# Grenzen van de tweezijdige toets op de normale verdeling voor 10, 5 en 1 procent.
Z_STER = [(2.576, "***"), (1.960, "**"), (1.645, "*")]


class Dossier:
    def __init__(self):
        self.doc = Document()
        st = self.doc.styles["Normal"]
        st.font.name, st.font.size = "Calibri", Pt(11)
        for s in self.doc.sections:
            s.left_margin = s.right_margin = Cm(2.2)
        self.n_fig = self.n_tab = 0

    def kop(self, tekst, niveau=1):
        self.doc.add_heading(tekst, niveau)

    def alinea(self, tekst):
        return self.doc.add_paragraph(tekst)

    def opsomming(self, regels):
        for r in regels:
            self.doc.add_paragraph(r, style="List Bullet")

    def bijschrift(self, tekst):
        p = self.doc.add_paragraph()
        run = p.add_run(tekst)
        run.font.size, run.font.color.rgb, run.italic = Pt(9.5), GRIJS, True

    def figuur(self, pad, titel, onderschrift="", breedte=14.5):
        pad = Path(pad)
        if not pad.exists():
            self.alinea(f"[Figuur ontbreekt: {pad.name}]")
            return
        self.n_fig += 1
        p = self.doc.add_paragraph()
        p.add_run(f"Figuur {self.n_fig}. {titel}").bold = True
        self.doc.add_picture(str(pad), width=Cm(breedte))
        self.doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        if onderschrift:
            self.bijschrift(onderschrift)

    def tabel(self, kolommen, rijen, titel, onderschrift="", uitlijning=WD_ALIGN_PARAGRAPH.RIGHT):
        self.n_tab += 1
        p = self.doc.add_paragraph()
        p.add_run(f"Tabel {self.n_tab}. {titel}").bold = True
        t = self.doc.add_table(rows=1, cols=len(kolommen))
        t.style, t.alignment = "Light Grid Accent 1", WD_TABLE_ALIGNMENT.CENTER
        for c, k in zip(t.rows[0].cells, kolommen):
            c.text = k
        for r in rijen:
            cellen = t.add_row().cells
            for i, (c, v) in enumerate(zip(cellen, r)):
                c.text = str(v)
                if i > 0:
                    c.paragraphs[0].alignment = uitlijning
        for rij in t.rows:
            for c in rij.cells:
                for run in c.paragraphs[0].runs:
                    run.font.size = Pt(9.5)
        if onderschrift:
            self.bijschrift(onderschrift)
        else:
            self.doc.add_paragraph()

    def conclusies(self, regels):
        p = self.doc.add_paragraph()
        p.add_run("Wat we eruit halen").bold = True
        self.opsomming(regels)


def pct(x, dec=0):
    return nl(100 * x, dec) + "%"


def lees_a(map_):
    werk = lees(map_ / "WerkenPerBaan_reeks.csv")
    eind = int(werk[werk.m2_per_baan.notna()].jaar.max())
    return werk, eind


def deel_a(d, map_, map_13):
    werk, eind = lees_a(map_)
    m2 = werk.pivot(index="sector", columns="jaar", values="m2_per_baan")
    banen = werk.pivot(index="sector", columns="jaar", values="banen")
    voet = werk.pivot(index="sector", columns="jaar", values="voetafdruk_m2")
    laatste_bag = int(werk[werk.voetafdruk_m2.notna()].jaar.max())
    dm2 = (m2[eind] - m2[2012]).loc[list(SECTOREN)]
    f7 = lees(map_13 / "VergelijkingFig7.csv")
    f7j = int(f7.jaar.max())
    f7n = f7[f7.sector == "Nijverheid"].set_index("jaar")
    f7l = f7[f7.sector == "Logistiek"].set_index("jaar")

    d.kop("1. Hoeveel ruimte een baan inneemt")
    d.alinea(
        "De pandvoetafdruk komt uit de BAG op 1 januari van elk jaar. Een pand met verblijfsobjecten voor meer "
        "functies verdeelt zijn voetafdruk over die functies naar hun aandeel in het vloeroppervlak; een pand dat "
        "RSopen als logistiek typeert gaat helemaal naar logistiek. Panden zonder verblijfsobject, zoals schuren en "
        "bijgebouwen, tellen niet mee. De functies gaan naar de zes werksectoren van RSopen. De banen komen uit LISA "
        f"en lopen tot en met {eind}; de BAG loopt tot {laatste_bag}.")
    d.figuur(map_ / "ESB_A1_m2_per_baan.png", "Pandvoetafdruk per baan per sector")
    rijen = []
    for s, lab in SECTOREN.items():
        rijen.append([lab, nl(m2.loc[s, 2012], 1), nl(m2.loc[s, 2019], 1), nl(m2.loc[s, eind], 1),
                      nl(banen.loc[s, eind] / 1000), nl(voet.loc[s, eind] / 1e6, 1)])
    rijen.append(["Zes sectoren samen", nl(voet[2012].sum() / banen[2012].sum(), 1),
                  nl(voet[2019].sum() / banen[2019].sum(), 1), nl(voet[eind].sum() / banen[eind].sum(), 1),
                  nl(banen[eind].sum() / 1000), nl(voet[eind].sum() / 1e6, 1)])
    d.tabel(["Sector", "m² per baan 2012", "2019", str(eind), f"banen {eind} (×1000)", f"voetafdruk {eind} (km²)"],
            rijen, "Voetafdruk per baan, banen en voetafdruk per sector",
            "Bron: BAG (Kadaster), LISA; bewerking in RSopen, ESB_Ruimte/WerkenPerBaan.")
    d.conclusies([
        f"De verschillen tussen sectoren zijn groot: een baan in de nijverheid neemt in {eind} "
        f"{nl(m2.loc['Nijverheid', eind])} m² pandvoetafdruk in, in de logistiek {nl(m2.loc['Logistiek', eind])} m², "
        f"in de zakelijke dienstverlening {nl(m2.loc['Zak_dienstverlening', eind])} m² en bij de overheid en kwartaire "
        f"diensten {nl(m2.loc['Overheid_kw_diensten', eind])} m². De twee ruimte-intensieve sectoren hebben samen "
        f"{pct((voet.loc[['Nijverheid', 'Logistiek'], eind]).sum() / voet[eind].sum())} van de voetafdruk en "
        f"{pct((banen.loc[['Nijverheid', 'Logistiek'], eind]).sum() / banen[eind].sum())} van de banen.",
        f"Binnen een sector is de ruimte per baan van 2012 tot {eind} vrij stabiel: de verandering ligt tussen "
        f"{nl(dm2.min(), 1)} m² ({SECTOREN[dm2.idxmin()].lower()}) en {nl(dm2.max(), 1)} m² "
        f"({SECTOREN[dm2.idxmax()].lower()}). Bij de diensten daalt hij licht, bij nijverheid en logistiek stijgt hij.",
        f"In figuur 7 van Ruimte voor werken (2022) stijgen nijverheid en logistiek veel harder. Dat zit vooral voor "
        f"2012: nijverheid gaat daar van {nl(FIG7_1996['Nijverheid'], 1)} m² per baan in 1996 naar "
        f"{nl(f7n.fig7[2012], 1)} in 2012, logistiek van {nl(FIG7_1996['Logistiek'], 1)} naar {nl(f7l.fig7[2012], 1)}. "
        "Voor die jaren is de voetafdruk benaderd met de panden die later in de BAG staan, op hun bouwjaar; wat "
        "tussendoor gesloopt is ontbreekt, zodat de voetafdruk in de vroege jaren te laag is en de stijging "
        "waarschijnlijk overschat. Die periode heeft de nieuwe reeks niet.",
        f"Van 2012 tot {f7j} stijgt nijverheid in figuur 7 met {nl(f7n.fig7[f7j] - f7n.fig7[2012], 1)} m² per baan en "
        f"in de nieuwe reeks met {nl(f7n.nieuw[f7j] - f7n.nieuw[2012], 1)}. Het verschil komt vooral uit de "
        "uitsplitsing van panden met meer werkfuncties, die figuur 7 helemaal bij nijverheid legde. Die uitsplitsing "
        f"haalt bij nijverheid {nl(-f7n.door_combi[2012], 1)} m² per baan weg in 2012 en "
        f"{nl(-f7n.door_combi[f7j], 1)} in {f7j}: het gemengde vastgoed groeide, en in figuur 7 telde die groei als "
        "nijverheid. De stijging bij nijverheid zit er dus nog in, maar kleiner.",
        "Verband: de ruimte per baan maal de groei van de banen bepaalt waar de extra ruimte voor werken naartoe "
        "gaat (deel 2); de ruimte per baan naast de waarde per baan geeft de waarde per m² (deel 3).",
    ])


def deel_ontleding(d, map_):
    werk, eind = lees_a(map_)
    banen = werk[werk.jaar == eind].set_index("sector").banen.loc[list(SECTOREN)]
    ontl = lees(map_ / "WerkenPerBaan_ontleding.csv").set_index("sector").loc[list(SECTOREN)]
    som = ontl.sum()
    nl_log = ontl.loc[["Nijverheid", "Logistiek"]]
    diensten = ontl.loc[["Zak_dienstverlening", "Overheid_kw_diensten"]]

    d.kop("2. Waar de groei van de voetafdruk vandaan komt")
    d.alinea(
        f"Hoeveel van de groei van de voetafdruk tussen 2012 en {eind} komt door meer banen en hoeveel door meer "
        "ruimte per baan? De ontleding is logaritmisch (LMDI): het deel door de banen is de groei maal het aandeel "
        "van de groei van de banen in de groei van de voetafdruk, beide als logaritme; de twee delen tellen op tot "
        "de groei.")
    d.figuur(map_ / "ESB_A4_ontleding.png", f"Groei van de voetafdruk 2012–{eind} ontleed")
    rijen = [[lab, nl(ontl.loc[s].groei_m2 / 1e6, 1), nl(ontl.loc[s].door_banen_m2 / 1e6, 1),
              nl(ontl.loc[s].door_m2baan_m2 / 1e6, 1)] for s, lab in SECTOREN.items()]
    rijen.append(["Zes sectoren samen", nl(som.groei_m2 / 1e6, 1), nl(som.door_banen_m2 / 1e6, 1),
                  nl(som.door_m2baan_m2 / 1e6, 1)])
    d.tabel(["Sector", "groei voetafdruk (km²)", "door meer banen", "door m² per baan"], rijen,
            f"Groei van de voetafdruk 2012–{eind} ontleed",
            "Bron: BAG (Kadaster), LISA; ESB_Ruimte/WerkenPerBaan, container Ontleding.")
    d.conclusies([
        f"De voetafdruk van de zes sectoren groeide van 2012 tot {eind} met {nl(som.groei_m2 / 1e6)} km². "
        f"Nijverheid en logistiek namen daarvan {pct(nl_log.groei_m2.sum() / som.groei_m2)}, terwijl ze "
        f"in {eind} {pct(banen[['Nijverheid', 'Logistiek']].sum() / banen.sum())} van de banen hebben.",
        f"De groei komt vooral door meer banen: {pct(som.door_banen_m2 / som.groei_m2)}. Meer ruimte per baan "
        f"telt mee in nijverheid en logistiek ({nl(nl_log.door_m2baan_m2.sum() / 1e6, 1)} km² samen); in de zakelijke "
        "dienstverlening en bij de overheid nam de ruimte per baan af "
        f"({nl(diensten.door_m2baan_m2.sum() / 1e6, 1)} km² samen). Daar kwamen banen bij in minder ruimte per baan.",
        "Verband: de extra ruimte voor werken gaat vooral naar de sectoren met de laagste waarde per m² (deel 3), en "
        "die zitten op andere plekken dan de diensten (deel 4 en 5). Voor het artikel is dit de kern van de "
        "ruimtevraag: het is groei van de banen in de ruimte-intensieve sectoren, niet een sluipende groei van de "
        "ruimte per baan.",
    ])


def deel_b(d, map_, cbs):
    w = lees(map_ / "WaardePerM2_reeks.csv")
    jaar, begin = int(w.jaar.max()), int(w.jaar.min())
    nu = w[w.jaar == jaar].set_index("sector").loc[list(SECTOREN)]
    oud = w[w.jaar == begin].set_index("sector").loc[list(SECTOREN)]
    takken = pd.read_csv(cbs, sep=";")
    totaal = takken[takken.Jaar == jaar].BTW_mln.sum() * 1e6
    idx_baan = 100 * nu.euro_per_baan / (nu.btw_euro.sum() / nu.banen.sum())
    idx_m2 = 100 * nu.euro_per_m2 / (nu.btw_euro.sum() / nu.voetafdruk_m2.sum())
    groei_m2 = nu.euro2021_per_m2 / oud.euro2021_per_m2 - 1

    d.kop("3. Toegevoegde waarde per baan en per m²")
    d.alinea(
        "De bruto toegevoegde waarde per bedrijfstak komt uit CBS StatLine 85867NED, op het fijnste niveau dat voor "
        f"elk jaar van {begin} tot en met {jaar} compleet is, zonder de toegerekende huur van eigen woningen. Een "
        "bedrijfstak heeft vaak banen in meer dan een sector; zijn waarde gaat naar de sectoren naar hun aandeel in "
        "de LISA-banen van die tak. Gedeeld door de voetafdruk en de banen uit deel 1 geeft dat de waarde per m² en "
        f"per baan. De zes sectoren dragen samen {pct(nu.btw_euro.sum() / totaal)} van de toegevoegde waarde van alle "
        f"takken in {jaar}. De figuur zet beide als index, met de zes sectoren samen op 100.")
    d.figuur(map_ / "ESB_B4_index_baan_m2.png", f"Toegevoegde waarde per baan en per m² voetafdruk, {jaar}",
             "De stippellijn is het gemiddelde van de zes sectoren.")
    rijen = [[SECTOREN[s], nl(r.btw_euro / 1e9, 1), nl(r.euro_per_baan / 1000), nl(idx_baan[s]), nl(r.euro_per_m2),
              nl(idx_m2[s]), pct(groei_m2[s])] for s, r in nu.iterrows()]
    d.tabel(["Sector", f"waarde {jaar} (mld euro)", "euro per baan (×1000)", "index", "euro per m²", "index",
             f"groei per m² {begin}–{jaar}"], rijen,
            "Toegevoegde waarde per sector, per baan en per m² voetafdruk",
            "Waarde per baan en per m² in werkelijke prijzen van dat jaar, index zes sectoren samen = 100; de groei in "
            "prijsniveau 2021, dus zonder de prijsstijging. Bron: CBS 85867NED, BAG, LISA; ESB_Ruimte/WaardePerM2.")
    laag_m2 = idx_m2.idxmin()
    d.conclusies([
        "Of een sector laagproductief is, hangt af van de noemer. Per baan liggen nijverheid "
        f"({nl(idx_baan.Nijverheid)}), logistiek ({nl(idx_baan.Logistiek)}) en zakelijke dienstverlening "
        f"({nl(idx_baan.Zak_dienstverlening)}) alle drie boven het gemiddelde; detailhandel "
        f"({nl(idx_baan.Detailhandel)}) en de overige consumentendiensten ({nl(idx_baan.Ov_consumentendiensten)}) "
        "liggen er ver onder.",
        f"Per m² is het beeld anders: de zakelijke dienstverlening haalt {nl(idx_m2.Zak_dienstverlening)} en de "
        f"overheid {nl(idx_m2.Overheid_kw_diensten)}, nijverheid {nl(idx_m2.Nijverheid)} en logistiek "
        f"{nl(idx_m2.Logistiek)}. Het laagst is de {SECTOREN[laag_m2].lower()} ({nl(idx_m2[laag_m2])}). Een m² "
        f"van de zakelijke dienstverlening levert {nl(nu.euro_per_m2.Zak_dienstverlening / nu.euro_per_m2.Logistiek, 1)} keer zoveel op als "
        "een m² logistiek.",
        "Voor de vraag van de redactie is per m² de juiste maat, want het gaat om ruimte. Maar wie ruimte van "
        "logistiek naar de zakelijke dienstverlening verschuift, krijgt per baan maar iets meer waarde (index "
        f"{nl(idx_baan.Zak_dienstverlening)} tegen {nl(idx_baan.Logistiek)}); de winst zit vooral in minder ruimte per "
        "baan.",
        f"In prijzen van 2021 veranderde de waarde per m² van {begin} tot {jaar} per sector tussen "
        f"{pct(groei_m2.min())} ({SECTOREN[groei_m2.idxmin()].lower()}) en {pct(groei_m2.max())} "
        f"({SECTOREN[groei_m2.idxmax()].lower()}). De verschillen tussen sectoren zijn dus veel groter dan de "
        "verandering in de tijd.",
        "Kanttekening: de toegevoegde waarde van de overheid meet het CBS grotendeels aan de kosten, vooral de lonen. "
        "Het hoge getal per m² zegt bij de overheid dus vooral dat er veel banen op weinig ruimte zitten.",
    ])


def ster(coef, se):
    z = abs(coef / se)
    return next((s for grens, s in Z_STER if z > grens), "")


TERMEN_C = ["ln UAI", "ln reistijd OV-knooppunt (2026)", "ln reistijd 500.000 inwoners (2024)",
            "ln afstand op- en afrit", "op een andere IBIS-werklocatie", "in het vaste zeehavengebied", "ln grondprijs",
            "aandeel overig bebouwd 1 km"]
SECTOR_C = dict(zip(["nijverheid", "logistiek", "detailhandel", "overige consumentendiensten",
                     "zakelijke dienstverlening", "overheid en kwartaire diensten"], SECTOREN.values()))
NOOT_C = ("Coëfficiënt met de significantie, daaronder de standaardfout, geclusterd per pand, tussen haakjes. "
          "*** p < 0,01; ** p < 0,05; * p < 0,10, tweezijdig.")


def lees_c(map_):
    c = pd.read_csv(map_ / "C_coefficienten_708.csv")
    c["cel"] = c.apply(lambda r: f"{nl(r.coef, 3)}{ster(r.coef, r.se)}\n({nl(r.se, 3)})", axis=1)
    return c, c.pivot(index="term", columns="sector", values="cel"), c.pivot(index="term", columns="sector",
                                                                             values="coef")


def deel_d(d, map_):
    s = lees(map_ / "IbisTerreinen_sectoren.csv").set_index("sector")
    k = lees(map_ / "IbisTerreinen_terreinklassen.csv").set_index("klasse")
    namen = dict(SECTOREN, Alle_zes="Zes sectoren samen")

    d.kop("4. Waar de sectoren nu zitten")
    d.alinea(
        "Per sector het deel van de banen (LISA 2023) op een IBIS-werklocatie van 2023 en op de plekken met de "
        "hoogste UAI. De UAI (Urban Attractivity Index) meet de voorzieningen binnen 5 km met afstandsverval. Hij is "
        "in vijf klassen verdeeld die elk een vijfde van alle banen bevatten, K1 laag tot K5 hoog; een sector die even "
        "vaak op zulke plekken zit als de gemiddelde baan, heeft in K5 dus 20 procent. Een vestiging telt op de plek "
        "van haar punt, een pand op zijn zwaartepunt.")
    d.figuur(map_ / "IbisTerreinen_banen.png", "Deel van de banen op een IBIS-werklocatie en bij de hoogste UAI",
             "De stippellijn is 20 procent: zoveel banen van de gemiddelde baan liggen in K5.")
    rijen = []
    for sec, lab in namen.items():
        r = s.loc[sec]
        rijen.append([lab, pct(r.banen_ibis) + " / " + pct(r.voet_ibis),
                      pct(r.banen_uai_hoogst) + " / " + pct(r.voet_uai_hoogst),
                      pct(r.banen_ov_kortst) + " / " + pct(r.voet_ov_kortst),
                      nl(r.reistijd_gem_banen, 1) + " / " + nl(r.reistijd_gem_voet, 1)])
    d.tabel(["Sector", "op IBIS", "hoogste UAI (K5)", "dichtst bij OV (20%)", "reistijd OV (min)"], rijen,
            "Waar de banen en de voetafdruk van elke sector liggen, 2023",
            "Per cel eerst het deel van de banen en dan het deel van de voetafdruk. De reistijd is het gemiddelde "
            "per baan en per m². Bron: LISA, BAG, IBIS 2023, UAI uit de BAG van 2023, reistijdkaart van 2026; "
            "ESB_Ruimte/IbisTerreinen.")
    d.conclusies([
        f"Nijverheid en logistiek zitten voor {pct(s.banen_ibis.Nijverheid)} en {pct(s.banen_ibis.Logistiek)} van hun "
        f"banen op een IBIS-werklocatie, de zakelijke dienstverlening voor {pct(s.banen_ibis.Zak_dienstverlening)} en "
        f"de overheid voor {pct(s.banen_ibis.Overheid_kw_diensten)}.",
        f"Op de plekken met de hoogste UAI zitten vooral de detailhandel ({pct(s.banen_uai_hoogst.Detailhandel)} van "
        f"de banen) en de overige consumentendiensten ({pct(s.banen_uai_hoogst.Ov_consumentendiensten)}). De zakelijke "
        f"dienstverlening ({pct(s.banen_uai_hoogst.Zak_dienstverlening)}) en de overheid "
        f"({pct(s.banen_uai_hoogst.Overheid_kw_diensten)}) zitten daar ongeveer zo vaak als de gemiddelde baan, "
        f"nijverheid ({pct(s.banen_uai_hoogst.Nijverheid)}) en logistiek ({pct(s.banen_uai_hoogst.Logistiek)}) "
        "nauwelijks.",
        "De ruimte-intensieve sectoren zitten dus grotendeels op andere plekken dan de sectoren met veel waarde per "
        "m². Waar ze elkaar wel treffen is op de bedrijventerreinen zelf: daar daalt het aandeel van logistiek in de "
        f"werkvoetafdruk van {pct(k.uai_aandeel_logistiek.K1)} op terreinen in K1 tot "
        f"{pct(k.uai_aandeel_logistiek.K5)} in K5, en stijgt dat van de zakelijke dienstverlening van "
        f"{pct(k.uai_aandeel_zak.K1)} tot {pct(k.uai_aandeel_zak.K5)}. Er zijn maar {nl(k.uai_terreinen.K5)} "
        f"terreinen in K5, tegen {nl(k.uai_terreinen.K2)} in K2.",
        "De voetafdruk van logistiek ligt bijna helemaal op IBIS, maar dat volgt waarschijnlijk deels uit de "
        "definitie: een pand is in RSopen logistiek als het in een vaste set grote logistieke panden staat (stand "
        "2021), aangevuld met nieuwbouw die LISA als logistiek herkent; andere logistiek telt bij nijverheid "
        "(ObjectVision/RSopen#889). De banen zijn hier de schonere maat.",
        "Verband: deel 5 laat zien dat dit patroon ook geldt voor de nieuwbouw van werkpanden, dus dat het een "
        "keuze is en niet alleen een erfenis.",
    ])


def deel_c(d, map_):
    c, tab, coef = lees_c(map_)
    k = {s: coef[s] for s in SECTOR_C}

    d.kop("5. Waar sectoren zich vestigen")
    d.alinea(
        "Uit de herschatting van de geschiktheid voor werken in RSopen (ObjectVision/RSopen#708, november 2026): een "
        "multinomiale logit op de bouw van werkpanden van 2017 tot 2022 per cel van 100 m, getoetst op de bouw van "
        "2022 tot 2026. Een positieve coëfficiënt maakt een cel aantrekkelijker; bij een afstand of reistijd betekent "
        "een negatieve coëfficiënt dat de sector de nabijheid zoekt. De tabel toont de termen die voor de vraag naar "
        "verdringing tussen sectoren het meest zeggen; de volledige tabel staat in de bijlage.")
    rijen = [[t] + [tab.loc[t, s] for s in SECTOR_C] for t in TERMEN_C]
    d.tabel(["Term"] + list(SECTOR_C.values()), rijen, "Coëfficiënten van de locatiekeuze per sector (selectie)",
            NOOT_C + " Bron: ObjectVision/RSopen#708, comment van 17 november 2026.",
            uitlijning=WD_ALIGN_PARAGRAPH.CENTER)
    t_ibis, t_uai, t_ov = "op een andere IBIS-werklocatie", "ln UAI", "ln reistijd OV-knooppunt (2026)"
    t_rit, t_500, t_haven = "ln afstand op- en afrit", "ln reistijd 500.000 inwoners (2024)", "in het vaste zeehavengebied"
    t_bebouwd = "aandeel overig bebouwd 1 km"
    d.conclusies([
        f"Logistiek kiest het sterkst voor een IBIS-werklocatie ({nl(k['logistiek'][t_ibis], 2)}), het zeehavengebied "
        f"({nl(k['logistiek'][t_haven], 2)}) en de nabijheid van een op- en afrit ({nl(k['logistiek'][t_rit], 2)}), en "
        f"is de enige sector die plekken met veel voorzieningen mijdt (ln UAI {nl(k['logistiek'][t_uai], 3)}). "
        f"Nijverheid lijkt daarop, minder uitgesproken.",
        f"De zakelijke dienstverlening en de overheid zoeken juist een OV-knooppunt (ln reistijd "
        f"{nl(k['zakelijke dienstverlening'][t_ov], 2)} en {nl(k['overheid en kwartaire diensten'][t_ov], 2)}); "
        f"logistiek zit liever verder van een knooppunt ({nl(k['logistiek'][t_ov], 2)}), en bij nijverheid is het "
        "effect klein en alleen op 10 procent significant. De detailhandel zoekt het sterkst de voorzieningen (ln UAI "
        f"{nl(k['detailhandel'][t_uai], 2)}).",
        "Een omgeving met veel ander bebouwd gebied binnen 1 km trekt alle sectoren behalve de detailhandel aan, de "
        f"zakelijke dienstverlening het sterkst ({nl(k['zakelijke dienstverlening'][t_bebouwd], 2)}) en nijverheid "
        f"het zwakst ({nl(k['nijverheid'][t_bebouwd], 2)}).",
        "Alle sectoren zoeken de nabijheid van een grote bevolking (reistijd tot 500.000 inwoners), logistiek het "
        f"sterkst ({nl(k['logistiek'][t_500], 2)}). Daar overlappen de sectoren: ze willen allemaal in de "
        "Randstad en de grote stedelijke regio's zitten, maar binnen die regio's op verschillende plekken.",
        "Voor de vraag van de redactie: op het niveau van de precieze plek zitten laag- en hoogproductieve sectoren "
        "elkaar weinig in de weg, want ze zoeken andere plekken. De concurrentie zit waarschijnlijk op het niveau van "
        "de regio, om de schaarse grond binnen bereik van de grote steden, en op de bedrijventerreinen met een hoge "
        "UAI (deel 4).",
        "Kanttekening: de coëfficiënten zeggen iets over de bouw van werkpanden van 2017 tot 2022, niet over de "
        "verhuizing van bestaande bedrijven of over prijzen.",
    ])
    return tab


def bijlage_c(d, tab):
    d.kop("Bijlage. Alle coëfficiënten van de herschatting", 1)
    rijen = [[t] + [tab.loc[t, s] for s in SECTOR_C] for t in tab.index]
    d.tabel(["Term"] + list(SECTOR_C.values()), rijen, "Alle coëfficiënten van de locatiekeuze per sector", NOOT_C,
            uitlijning=WD_ALIGN_PARAGRAPH.CENTER)


def deel_g(d, map_):
    pijp = lees(map_ / "Bouwterrein_pijplijn_totaal.csv").set_index("jaar")
    bbg = lees(map_ / "Bouwterrein_overlay_BBG.csv").set_index("jaar")
    verder = bbg.ha_raster - bbg.ha_nabij_recent_ruim
    j0, j1 = int(bbg.index.min()), int(bbg.index.max())
    p0, p1 = int(pijp.index.min()), int(pijp.index.max())

    d.kop("6. Bouwterrein en de pijplijn van de BAG")
    d.alinea(
        "De pijplijn is wat op 1 januari in de BAG vergund of in aanbouw is en nog niet in gebruik: panden met de "
        "status bouwvergunning verleend of bouw gestart. Een pand waarvan die status meer dan vijf jaar oud is, telt "
        "niet mee, want zo'n vergunning wordt vaak nooit gebouwd. Bouwterrein komt uit het Bestand Bodemgebruik van "
        "het CBS. Een cel van 25 m bouwterrein telt als nabij als het zwaartepunt van een pand uit de pijplijn binnen "
        "100 m of 250 m ligt; verder weg is bouwterrein zonder zichtbaar bouwproject in de BAG.")
    d.figuur(map_ / "Bouwterrein_afstand.png", "Bouwterrein naar de afstand tot een bouwproject in de BAG")
    rijen = [[str(j), nl(b.ha_raster), nl(b.ha_nabij_recent), nl(b.ha_nabij_recent_ruim - b.ha_nabij_recent),
              nl(verder[j]), nl(pijp.woningen_recent[j]), nl(pijp.footprint_recent[j] / 1e4)]
             for j, b in bbg.iterrows()]
    rijen.append([str(p1), "", "", "", "", nl(pijp.woningen_recent[p1]), nl(pijp.footprint_recent[p1] / 1e4)])
    d.tabel(["jaar", "BBG-bouwterrein (ha)", "binnen 100 m", "100 tot 250 m", "verder dan 250 m",
             "woningen in de pijplijn", "voetafdruk pijplijn (ha)"], rijen, "Het bouwterrein en de pijplijn",
            "BBG-jaar X naast de BAG van 1 januari X; tussen BBG 2017 en NBBG 2020 zit een methodebreuk. Pijplijn: "
            "vergunning hooguit vijf jaar oud. Bron: BAG (Kadaster), BBG en NBBG (CBS); ESB_Ruimte/Bouwterrein.")
    d.conclusies([
        f"Het bouwterrein van het CBS daalt van {nl(bbg.ha_raster[j0])} ha in {j0} naar {nl(bbg.ha_raster[j1])} ha "
        f"in {j1}. Het deel binnen 100 m van een bouwproject blijft ongeveer gelijk, tussen "
        f"{nl(bbg.ha_nabij_recent.min())} en {nl(bbg.ha_nabij_recent.max())} ha. De daling zit bijna helemaal in "
        f"het bouwterrein verder dan 250 m van een bouwproject: van {nl(verder[j0])} naar {nl(verder[j1])} ha.",
        f"Ondertussen groeit de pijplijn van {nl(pijp.woningen_recent[p0])} woningen op 1 januari {p0} naar "
        f"{nl(pijp.woningen_recent[p1])} op 1 januari {p1}, terwijl de voetafdruk van de pijplijn rond de "
        f"{nl(round(pijp.footprint_recent.median() / 1e4, -2))} ha blijft. Er zitten dus meer woningen op dezelfde "
        "voetafdruk. Dat past bij de bevinding dat ongeveer driekwart van de woningen die van 2012 tot 2025 aan de "
        "voorraad zijn toegevoegd binnen bestaand stedelijk gebied kwam (Claassens e.a., 2026), waar vaak geen "
        "bouwterrein voor nodig is.",
        "Wat verdwijnt is vooral bouwterrein zonder zichtbaar bouwproject: grond die bouwrijp lag of als bouwterrein "
        "gekarteerd stond zonder dat er iets in de BAG op vergund was. Een deel van de daling tussen 2017 en 2020 is "
        "waarschijnlijk de methodebreuk naar het NBBG.",
        "Verband met de vraag van de redactie naar de bouwgrond na 2022: de pijplijn loopt tot 1 januari "
        f"{p1} en laat zien wat in de komende jaren gebouwd wordt. Een kleiner areaal bouwterrein betekent nog geen "
        "kleinere bouwproductie.",
    ])


def weggelaten(d):
    d.kop("Wat uit het vorige dossier wegbleef")
    d.alinea(
        "Niet opgenomen uit het dossier van 20 november (v4): de banen en de voetafdruk per sector als losse "
        "figuren, de toegevoegde waarde in prijsniveau 2021 als reeks, de stapsgewijze vergelijking met figuur 7 "
        "(de kern staat nu in deel 1), de IBIS-terreinen naar UAI als figuur (de kern staat in deel 4), werk dat "
        "wonen werd, de kaart van het bouwterrein en het voorstel voor vervolganalyses. Ze staan nog in v4 en "
        "zijn met dezelfde scripts te maken.")


def kern(d, map_ab, map_g, map_d, cbs):
    werk, eind = lees_a(map_ab)
    m2 = werk[werk.jaar == eind].set_index("sector").m2_per_baan
    ontl = lees(map_ab / "WerkenPerBaan_ontleding.csv").set_index("sector").loc[list(SECTOREN)]
    w = lees(map_ab / "WaardePerM2_reeks.csv")
    nu = w[w.jaar == w.jaar.max()].set_index("sector").loc[list(SECTOREN)]
    idx_baan = 100 * nu.euro_per_baan / (nu.btw_euro.sum() / nu.banen.sum())
    ibis = lees(map_d / "IbisTerreinen_sectoren.csv").set_index("sector")
    bbg = lees(map_g / "Bouwterrein_overlay_BBG.csv").set_index("jaar")
    pijp = lees(map_g / "Bouwterrein_pijplijn_totaal.csv").set_index("jaar")
    j0, j1 = int(bbg.index.min()), int(bbg.index.max())

    d.kop("Het verhaal in het kort")
    d.opsomming([
        f"Een baan in de logistiek neemt {nl(m2.Logistiek)} m² pandvoetafdruk in, een baan in de zakelijke "
        f"dienstverlening {nl(m2.Zak_dienstverlening)} m² ({eind}). Binnen een sector verandert dat sinds 2012 weinig "
        "(deel 1).",
        f"De werkvoetafdruk groeide van 2012 tot {eind} met {nl(ontl.groei_m2.sum() / 1e6)} km², voor "
        f"{pct(ontl.loc[['Nijverheid', 'Logistiek']].groei_m2.sum() / ontl.groei_m2.sum())} bij nijverheid en "
        f"logistiek, en voor {pct(ontl.door_banen_m2.sum() / ontl.groei_m2.sum())} door meer banen (deel 2).",
        "Per m² zijn nijverheid en logistiek laagproductief, per baan niet: daar liggen ze met index "
        f"{nl(idx_baan.Nijverheid)} en {nl(idx_baan.Logistiek)} boven het gemiddelde (deel 3).",
        f"Ze zitten op andere plekken dan de diensten: {pct(ibis.banen_ibis.Logistiek)} van de logistieke banen op een "
        f"bedrijventerrein, {pct(ibis.banen_uai_hoogst.Logistiek)} bij de hoogste UAI (deel 4), en de nieuwbouw "
        "volgt hetzelfde patroon (deel 5). Ze treffen elkaar in de regio en op de bedrijventerreinen met veel "
        "voorzieningen.",
        f"Het bouwterrein daalde van {nl(bbg.ha_raster[j0])} naar {nl(bbg.ha_raster[j1])} ha ({j0}–{j1}), bijna "
        "helemaal in terrein zonder bouwproject; de pijplijn groeide naar "
        f"{nl(pijp.woningen_recent.iloc[-1])} woningen in {int(pijp.index.max())} (deel 6).",
    ])


def main(map_ab, map_g, map_13, map_d, uit):
    map_ab, map_g, map_13, map_d = Path(map_ab), Path(map_g), Path(map_13), Path(map_d)
    cbs = Path(__file__).resolve().parents[3] / "data" / "CBS_85867NED" / "Toegevoegde_waarde_bedrijfstak.csv"
    d = Dossier()
    d.doc.add_heading("Ruimte voor werken: kernfiguren voor het ESB-artikel", 0)
    d.alinea("Intern werkdocument van Object Vision voor het overleg met de VU, 20 november 2026. Niet verspreiden: "
             "de cijfers zijn nog niet getoetst door anderen.")
    d.alinea(
        "De vraag van de ESB-redactie is of laagproductieve sectoren hoogproductieve ruimtelijk in de weg zitten. Dit "
        "dossier zet de figuren op een rij die daar iets over zeggen, met bij elke figuur wat we eruit halen en hoe "
        "hij aansluit op de andere. De figuren zijn dezelfde als in de Excel met de figuurdata. Alles is landelijk en "
        "gerekend in GeoDMS op de tak esb-ruimte van RSopen (cfg/main/ESB_Ruimte), zodat het na te rekenen is.")
    kern(d, map_ab, map_g, map_d, cbs)
    deel_a(d, map_ab, map_13)
    deel_ontleding(d, map_ab)
    deel_b(d, map_ab, cbs)
    deel_d(d, map_d)
    tab_c = deel_c(d, map_ab)
    deel_g(d, map_g)
    weggelaten(d)
    bijlage_c(d, tab_c)
    d.doc.save(uit)
    print("dossier:", uit)


if __name__ == "__main__":
    main(*sys.argv[1:6])
