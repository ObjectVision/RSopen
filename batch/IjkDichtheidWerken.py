r"""Legt de dichtheid van de werknieuwbouw uit de BAG naast de dichtheid waarmee het model nieuwe banen neerzet (#907).

Gebruik:
    python batch\IjkDichtheidWerken.py --map %LocalDataProjDir%\Ijking\werkdichtheid --uitvoer <bestand.txt>

De invoer schrijft het model op aanvraag met /Diagnose/Werken/IjkingDichtheid/Generate: per blok van 100 m en per
werksubsector de pandvoetafdruk van alle panden en van de panden vanaf het beginjaar uit de BAG, de dichtheid van het
model (Templates/Densities/Werken_T, Result), dezelfde dichtheid zonder het blok zelf in het omgevingsmaximum (Omgeving),
of het blok in het basisjaar van de CBS-klasse is waarover het model de dichtheid meet (InKlasse), en de dichtheidsfactor.

Wat de dichtheid van werken is. Een cel die werken krijgt, krijgt het aantal banen dat past bij de pandvoetafdruk per
hectare van zijn blok (Result) maal de banen per vierkante meter voetafdruk van de subsector. Result is het hoogste van de
gemiddelde voetafdruk per hectare van het blok zelf en van de blokken van dezelfde CBS-klasse in buurt, wijk, gemeente,
NVM-regio, COROP en provincie, maal de dichtheidsfactor, uitgesmeerd over 2 km. Subsectoren met dezelfde CBS-klasse delen
die dichtheid: bedrijfsterreinen (nijverheid, logistiek, zakelijke dienstverlening), detailhandel en horeca (detailhandel,
overige consumentendiensten) en voorzieningen (overheid en kwartaire diensten). Anders dan bij wonen is dit geen
bovengrens naast een keuze uit pakketten: het is de dichtheid waarop gebouwd wordt. Ligt de echte nieuwbouw dichter, dan
neemt het model voor dezelfde banen meer grond.

Wat het script doet. Per klasse telt het de voetafdruk van de subsectoren op en kiest het de blokken die vooral nieuw zijn:
minstens MIN_NIEUW m2 voetafdruk vanaf het beginjaar en minstens AANDEEL_NIEUW van de voetafdruk van de klasse in het blok.
De gerealiseerde dichtheid van zo'n blok is zijn hele voetafdruk van de klasse per hectare, zoals het model de dichtheid
van een blok meet. Per klasse en kernklasse geeft het de percentielen van die dichtheid, van Result en Omgeving, en van de
verhouding tussen de gerealiseerde dichtheid en die van het model, gewogen met de nieuwe voetafdruk. De verhouding is ook
de factor waarmee de dichtheidsfactor zou moeten veranderen om dat deel van de nieuwbouw te halen, want Result is
evenredig met de factor. Dat geldt bij benadering: de factor varieert binnen de straal van de uitsmering.

Twee kanttekeningen bij de vergelijking. Het basisjaar van het model ligt na het beginjaar van de nieuwbouw, dus de
dichtheid van het model telt een deel van die nieuwbouw zelf al mee; Omgeving haalt alleen het eigen blok eruit. En een
blok aan de rand van een terrein heeft maar een deel van zijn hectare in gebruik, wat de gerealiseerde dichtheid drukt;
het model meet de dichtheid van een blok op dezelfde manier.

De weging bepaalt de uitkomst. Gewogen met de voetafdruk tellen de dicht bebouwde blokken zwaarder, zodat de percentielen
de kern van de nieuwe terreinen beschrijven. Of het model voor dezelfde nieuwbouw meer of minder grond neemt, zegt de
kolom grond: de hectares die het model voor de voetafdruk van de gekozen blokken nodig heeft (de som van de gerealiseerde
voetafdruk gedeeld door Result), gedeeld door het aantal blokken. Onder 1 neemt het model minder grond dan de praktijk.
Die kolom hangt af van MIN_NIEUW, omdat een hogere drempel de dun bebouwde randblokken weglaat.

De ijking. Het tweede deel kiest de nieuwe werklocaties uit het BBG in plaats van uit de BAG: de blokken die in 2022 van de
klasse zijn (InKlasse) en in 2012 voor hoogstens GRENS_NIEUW_2012 (Aandeel2012). Zo tellen ook de blokken van een nieuw
terrein met weinig of geen bebouwing mee. Per blok legt het de gerealiseerde dichtheid (Eigen, de voetafdruk per hectare
in het basisjaar zoals het model die meet) naast de dichtheid die het model zo'n blok geeft vanuit de werklocaties die er
in 2012 al waren (Oud_Omgeving). Die modeldichtheid is de som van zes termen (Oud_Basis, Oud_OV, Oud_Water, Oud_K100,
Oud_K20, Oud_K20min), elk maal zijn factor: de generieke factor maal Basis plus de opslag (factor min 1) maal de andere
termen. Een kleinstekwadratenschatting van de gerealiseerde dichtheid op die termen geeft dus direct de factoren waarbij
het model op dezelfde hectares dezelfde voetafdruk zet. Dezelfde schatting op Oud_Omgeving geeft de huidige factoren terug,
wat de opbouw controleert. De verhouding van de sommen (gerealiseerd gedeeld door model) is de maat voor de ijking: hij
zegt hoeveel meer of minder voetafdruk de praktijk op dezelfde grond zette dan het model zou doen.

Het BBG van 2022 is anders gemaakt dan de reeks tot en met 2017, dus een deel van de blokken die tussen 2012 en 2022 van
klasse wisselen kan een verschil in methode zijn. Daarom toetst het script de ijking ook op de blokken die binnen de oude
reeks tussen 2012 en 2017 werklocatie werden (Aandeel2017), met de voetafdruk uit de BAG van 2026, en op de bestaande
werklocaties, die in 2012 en 2022 van de klasse zijn.
"""

import argparse
from pathlib import Path

import numpy as np
import rasterio

KLASSEN = {
    'bedrijfsterreinen': ['Nijverheid', 'Logistiek', 'Zak_dienstverlening'],
    'detailhandel_horeca': ['Detailhandel', 'Ov_consumentendiensten'],
    'voorzieningen': ['Overheid_kw_diensten'],
}
MIN_NIEUW = 250.0      # m2 nieuwe voetafdruk in een blok van een hectare
AANDEEL_NIEUW = 0.5    # deel van de voetafdruk van de klasse in het blok dat nieuw moet zijn
PERCENTIELEN = (0.5, 0.75, 0.9)
GRENS_KERN = 0.5       # deel van het blok in de buffer om bij een kernklasse te horen
KLASSE_BBG = {'bedrijfsterreinen': 'bedrijfsterreinen', 'detailhandel_horeca': 'Detailhandel_en_horeca',
              'voorzieningen': 'Voorzieningen'}
GRENS_NIEUW_2012 = 0.25  # hoogstens dit deel van het blok was in BBG 2012 van de klasse: een nieuwe werklocatie
GRENS_LIGGING = 0.5      # nabijheid van een railhalte of groot water vanaf waar een blok daarbij ligt
GRENS_UITLEG = 0.5       # deel van het blok dat in 2012 buiten het bebouwd gebied lag om als uitleg te tellen
TERMEN = ('Basis', 'OV', 'Water', 'K100', 'K20', 'K20min')
PARAMETER = {'Basis': 'Generiek', 'OV': 'OV', 'Water': 'Water', 'K100': 'BevKern100kPlus', 'K20': 'BevKern20kPlus',
             'K20min': 'BevKern20kMin'}
GEVOELIGHEID = ((0.0, 'Eigen'), (0.5, 'Eigen'), (0.25, 'Totaal'))  # andere grens voor nieuw en de BAG van 2026


def lees(map_, naam):
    with rasterio.open(map_ / f'{naam}_100m.tif') as bron:
        data = bron.read(1).astype(np.float64)
        if bron.nodata is not None:
            data[data == bron.nodata] = np.nan
    return data


def gewogen_percentiel(waarden, gewichten, p):
    volgorde = np.argsort(waarden)
    w = np.cumsum(gewichten[volgorde])
    return float(waarden[volgorde][np.searchsorted(w, p * w[-1])])


def kernklasse(map_):
    k100, k20, k20min = (np.nan_to_num(lees(map_, n)) for n in ('K100', 'K20', 'K20min'))
    klasse = np.full(k100.shape, 'buiten de kernen', dtype=object)
    klasse[k20min >= GRENS_KERN] = 'kern <20k'
    klasse[k20 >= GRENS_KERN] = 'kern 20k-100k'
    klasse[k100 >= GRENS_KERN] = 'kern 100k+'
    return klasse


def regel(label, d, res, omg, fac, w):
    if w.size == 0:
        return f'{label:<20}{0:>7}'
    delen = [f'{label:<20}{w.size:>7}{w.sum() / 1e4:>9.0f}']
    for reeks in (d, res, omg):
        delen += [f'{gewogen_percentiel(reeks, w, p):>7.0f}' for p in PERCENTIELEN]
    for reeks in (d / res, d / omg):
        delen += [f'{gewogen_percentiel(reeks, w, p):>6.2f}' for p in PERCENTIELEN]
    delen.append(f'{w[d > res].sum() / w.sum():>7.2f}')
    delen.append(f'{np.mean(d / res):>6.2f}')
    delen.append(f'{gewogen_percentiel(fac, w, 0.5):>7.2f}')
    return ''.join(delen)


def kop():
    p = ''.join(f'{"P" + str(round(q * 100)):>7}' for q in PERCENTIELEN)
    pr = ''.join(f'{"P" + str(round(q * 100)):>6}' for q in PERCENTIELEN)
    return ('\n' + ' ' * 36 + f'{"gerealiseerd m2/ha":<21}{"model Result m2/ha":<21}{"model Omgeving m2/ha":<21}'
            f'{"gerealiseerd/Result":<18}{"gerealiseerd/Omgeving":<18}\n'
            f'{"":<20}{"blokken":>7}{"nieuw ha":>9}' + p * 3 + pr * 2 + f'{">Result":>7}{"grond":>6}{"factor":>7}')


def ols(x, y):
    """Kleinste kwadraten zonder constante, met de robuuste standaardfout (HC1); ruimtelijke samenhang maakt die te klein."""
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    e = y - x @ beta
    inv = np.linalg.inv(x.T @ x)
    cov = inv @ ((x * e[:, None] ** 2).T @ x) @ inv * len(y) / (len(y) - x.shape[1])
    return beta, np.sqrt(np.diag(cov))


def factor(term, coef):
    """De waarde van de parameter in VariantK: de generieke factor is de coefficient zelf, een opslag is 1 plus die."""
    return coef if term == 'Basis' else 1 + coef


def locatietype(map_):
    ov, water, uitleg = (np.nan_to_num(lees(map_, n)) for n in ('OV', 'Water', 'Uitleg2012'))
    ligging = np.where(ov >= GRENS_LIGGING, 'bij OV', np.where(water >= GRENS_LIGGING, 'bij water', 'elders'))
    herkomst = np.where(uitleg >= GRENS_UITLEG, 'uitleg', 'in bebouwd gebied')
    return ligging, herkomst


def ijk_klasse(map_, klasse, grens_nieuw, bron):
    subs = KLASSEN[klasse]
    t = np.stack([lees(map_, f'Oud_{n}_{subs[0]}') for n in TERMEN], axis=-1)
    omg_nu = lees(map_, f'Oud_Omgeving_{subs[0]}')
    for s in subs[1:]:
        if not np.allclose(lees(map_, f'Oud_Omgeving_{s}'), omg_nu, equal_nan=True):
            raise SystemExit(f'Oud_Omgeving van {s} wijkt af van {subs[0]}: de indeling in KLASSEN klopt niet meer')
    inkl = lees(map_, f'InKlasse_{subs[0]}') == 1
    aandeel = np.nan_to_num(lees(map_, f'Aandeel2012_{KLASSE_BBG[klasse]}'))
    if bron == 'Eigen':
        d = lees(map_, f'Eigen_{subs[0]}')
    else:
        d = sum(np.nan_to_num(lees(map_, f'Totaal_{s}')) for s in subs)
    geldig = inkl & np.all(np.isfinite(t), axis=-1) & np.isfinite(omg_nu) & (omg_nu > 0) & np.isfinite(d)
    nieuw = geldig & (aandeel <= grens_nieuw)
    return t, omg_nu, d, geldig, nieuw


def ijking(map_, kern):
    """De factoren waarbij het model op de nieuwe werklocaties van 2012 tot 2022 de voetafdruk zet die er staat."""
    ligging, herkomst = locatietype(map_)
    regels = [f'\nIjking op de nieuwe werklocaties: blokken die in BBG 2022 van de klasse zijn en in BBG 2012 voor hoogstens '
              f'{GRENS_NIEUW_2012:.0%}. gerealiseerd en model zijn de gemiddelde voetafdruk per hectare (m2/ha), som/som de '
              'verhouding van de sommen (boven 1 zette de praktijk meer voetafdruk op dezelfde grond dan het model), '
              'gem en P50 het gemiddelde en de mediaan van die verhouding per blok, als nu de verhouding met de dichtheid van '
              'het model zoals hij nu is (met de nieuwe blokken zelf in de regionale gemiddelden), na ijking de verhouding '
              f'met de geijkte factoren. bij OV en bij water: nabijheid minstens {GRENS_LIGGING}; uitleg: minstens '
              f'{GRENS_UITLEG:.0%} van het blok was in 2012 geen bebouwd gebied.']
    for klasse, subs in KLASSEN.items():
        t, omg_nu, d, geldig, nieuw = ijk_klasse(map_, klasse, GRENS_NIEUW_2012, 'Eigen')
        omg_model = lees(map_, f'Omgeving_{subs[0]}')
        bag_nieuw = sum(np.nan_to_num(lees(map_, f'Nieuw_{s}')) for s in subs)
        bag_totaal = sum(np.nan_to_num(lees(map_, f'Totaal_{s}')) for s in subs)

        nu, _ = ols(t[geldig], omg_nu[geldig])
        rest = np.abs(t[geldig] @ nu - omg_nu[geldig]).max() / omg_nu[geldig].max()
        beta, se = ols(t[nieuw], d[nieuw])
        omg_ijk = t @ beta

        regels.append(f'\n{klasse} ({", ".join(subs)}): {nieuw.sum()} nieuwe blokken van {geldig.sum()} in de klasse; '
                      f'de opbouw uit de termen wijkt hoogstens {rest:.1e} van het maximum af van Oud_Omgeving')
        regels.append(f'{"":<20}{"blokken":>8}{"aandeel":>8}{"BAG nieuw":>10}{"gerealiseerd":>13}{"model":>7}'
                      f'{"som/som":>8}{"gem":>6}{"P50":>6}{"als nu":>7}{"na ijking":>10}')
        groepen = [('Nederland', nieuw)]
        groepen += [(k, nieuw & (kern == k)) for k in ('kern 100k+', 'kern 20k-100k', 'kern <20k', 'buiten de kernen')]
        groepen += [(s, nieuw & (ligging == s)) for s in ('bij OV', 'bij water', 'elders')]
        groepen += [(s, nieuw & (herkomst == s)) for s in ('uitleg', 'in bebouwd gebied')]
        for label, m in groepen:
            if m.sum() == 0:
                continue
            q = d[m] / omg_nu[m]
            om = np.isfinite(omg_model) & m
            regels.append(f'{label:<20}{m.sum():>8}{m.sum() / nieuw.sum():>8.2f}'
                          f'{bag_nieuw[m].sum() / max(bag_totaal[m].sum(), 1):>10.2f}{d[m].mean():>13.0f}'
                          f'{omg_nu[m].mean():>7.0f}{d[m].sum() / omg_nu[m].sum():>8.2f}{q.mean():>6.2f}'
                          f'{np.median(q):>6.2f}{d[om].sum() / omg_model[om].sum():>7.2f}'
                          f'{d[m].sum() / omg_ijk[m].sum():>10.2f}')
        regels.append(f'{"factor":<20}{"nu":>8}{"geijkt":>8}{"fout":>7}')
        for n, c_nu, c, s in zip(TERMEN, nu, beta, se):
            regels.append(f'{PARAMETER[n]:<20}{factor(n, c_nu):>8.2f}{factor(n, c):>8.2f}{s:>7.2f}')
        regels.append('Geijkt per kernklasse, generiek plus de opslag voor de kern, zonder OV en water: '
                      + ', '.join(f'{k} {beta[0] + beta[i]:.2f}' for k, i in (('100k+', 3), ('20k-100k', 4), ('<20k', 5))))
        regels.append(f'Met alleen een generieke factor en geen opslagen: {d[nieuw].sum() / t[nieuw][:, 0].sum():.2f}.')
        aandeel = np.nan_to_num(lees(map_, f'Aandeel2012_{KLASSE_BBG[klasse]}'))
        oud = geldig & (aandeel >= 0.5)
        regels.append(f'Bestaande werklocaties (in 2012 en 2022 van de klasse, {oud.sum()} blokken): som/som '
                      f'{d[oud].sum() / omg_nu[oud].sum():.2f}, met de geijkte factoren {d[oud].sum() / omg_ijk[oud].sum():.2f}; '
                      f'zonder voetafdruk {np.mean(d[oud] == 0):.2f} van de blokken, bij de nieuwe {np.mean(d[nieuw] == 0):.2f}.')
        a17 = np.nan_to_num(lees(map_, f'Aandeel2017_{KLASSE_BBG[klasse]}'))
        b17 = (a17 >= 0.5) & (aandeel <= GRENS_NIEUW_2012) & np.all(np.isfinite(t), axis=-1) & (omg_nu > 0)
        d17 = bag_totaal
        regels.append(f'Toets zonder het methodeverschil tussen het oude en nieuwe BBG: nieuw tussen BBG 2012 en 2017 '
                      f'({b17.sum()} blokken, voetafdruk uit de BAG van 2026), som/som {d17[b17].sum() / omg_nu[b17].sum():.2f}, '
                      f'met de geijkte factoren {d17[b17].sum() / omg_ijk[b17].sum():.2f}, zonder voetafdruk '
                      f'{np.mean(d17[b17] == 0):.2f}; met alleen een generieke factor '
                      f'{d17[b17].sum() / t[b17][:, 0].sum():.2f}; per kernklasse met de huidige factoren '
                      + ', '.join(f'{k} {d17[b17 & (kern == k)].sum() / omg_nu[b17 & (kern == k)].sum():.2f}'
                                  for k in ('kern 100k+', 'kern 20k-100k', 'kern <20k')) + '.')
        for grens, bron in GEVOELIGHEID:
            t2, omg2, d2, _, nieuw2 = ijk_klasse(map_, klasse, grens, bron)
            b2, _ = ols(t2[nieuw2], d2[nieuw2])
            regels.append(f'  gevoeligheid nieuw tot {grens:.0%} in 2012, gerealiseerd uit {bron}: {nieuw2.sum()} blokken, '
                          f'som/som {d2[nieuw2].sum() / omg2[nieuw2].sum():.2f}, geijkt '
                          + ', '.join(f'{PARAMETER[n]} {factor(n, c):.2f}' for n, c in zip(TERMEN, b2)))
    return regels


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--map', required=True, type=Path)
    ap.add_argument('--uitvoer', required=True, type=Path)
    args = ap.parse_args()

    kern = kernklasse(args.map)
    regels = [f'Werknieuwbouw uit de BAG tegen de dichtheid van het model, uit {args.map}',
              f'Blokken van 100 m met minstens {MIN_NIEUW:.0f} m2 nieuwe voetafdruk en minstens {AANDEEL_NIEUW:.0%} van '
              'de voetafdruk van de klasse nieuw. Percentielen gewogen met de nieuwe voetafdruk; nieuw ha is de nieuwe '
              'voetafdruk in hectare, >Result het deel daarvan in blokken boven Result, grond de hectares die het model nodig '
              'heeft voor de voetafdruk van deze blokken gedeeld door hun aantal (ongewogen), factor de mediaan van de '
              'dichtheidsfactor van het model.']
    for klasse, subs in KLASSEN.items():
        nieuw = sum(np.nan_to_num(lees(args.map, f'Nieuw_{s}')) for s in subs)
        totaal = sum(np.nan_to_num(lees(args.map, f'Totaal_{s}')) for s in subs)
        res = lees(args.map, f'Result_{subs[0]}')
        for s in subs[1:]:
            if not np.allclose(lees(args.map, f'Result_{s}'), res, equal_nan=True):
                raise SystemExit(f'Result van {s} wijkt af van {subs[0]}: de indeling in KLASSEN klopt niet meer')
        omg = lees(args.map, f'Omgeving_{subs[0]}')
        fac = lees(args.map, f'Factor_{subs[0]}')
        inkl = lees(args.map, f'InKlasse_{subs[0]}') == 1
        keuze = ((nieuw >= MIN_NIEUW) & (nieuw >= AANDEEL_NIEUW * totaal)
                 & np.isfinite(res) & (res > 0) & np.isfinite(omg) & (omg > 0))
        for titel, masker in (('in de CBS-klasse van het basisjaar', keuze & inkl), ('alle blokken', keuze)):
            regels.append(f'\n{klasse} ({", ".join(subs)}), {titel}')
            regels.append(kop())
            for label, sel in [('Nederland', masker)] + [
                    (k, masker & (kern == k)) for k in ('kern 100k+', 'kern 20k-100k', 'kern <20k', 'buiten de kernen')]:
                regels.append(regel(label, totaal[sel], res[sel], omg[sel], fac[sel], nieuw[sel]))
    regels += ijking(args.map, kern)
    tekst = '\n'.join(regels) + '\n'
    args.uitvoer.write_text(tekst, encoding='utf-8')
    print(tekst)


if __name__ == '__main__':
    main()
