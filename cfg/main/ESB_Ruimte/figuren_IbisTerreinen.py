"""Twee figuren bij taak D van het ESB-dossier, alleen uit de csv's die IbisTerreinen.dms schrijft; geen eigen berekeningen behalve schalen naar procenten."""
import csv, os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

d = sys.argv[1]
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
BLAUW, ORANJE = '#2a78d6', '#eb6834'
AQUA, VIOLET = '#1baf7a', '#6250d6'
plt.rcParams.update({'font.size': 13, 'axes.edgecolor': INK2, 'axes.labelcolor': INK, 'xtick.color': INK2, 'ytick.color': INK,
                     'axes.facecolor': SURF, 'figure.facecolor': SURF, 'font.family': 'DejaVu Sans'})

def lees(naam):
    with open(os.path.join(d, naam), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

NAAM = {'Nijverheid': 'Nijverheid', 'Logistiek': 'Logistiek', 'Detailhandel': 'Detailhandel',
        'Ov_consumentendiensten': 'Overige consumentendiensten', 'Zak_dienstverlening': 'Zakelijke dienstverlening',
        'Overheid_kw_diensten': 'Overheid en kwartaire diensten', 'Alle_zes': 'Alle zes sectoren'}
NADRUK = {'Logistiek', 'Zak_dienstverlening'}

# Figuur 1: per sector het deel van banen en voetafdruk op IBIS, in de hoogste UAI-klasse en in de kortste reistijdklasse.
s = lees('IbisTerreinen_sectoren.csv')
rijen = list(reversed(s))
y = list(range(len(rijen)))
panelen = [('Banen_IBIS', 'Voet_IBIS', 'Op een IBIS-werklocatie', None),
           ('Banen_UAI_hoogst', 'Voet_UAI_hoogst', 'Hoogste UAI (de bovenste 20%)', 20),
           ('Banen_OV_kortst', 'Voet_OV_kortst', 'Dichtst bij een OV-knooppunt (20%)', 20)]
fig, axs = plt.subplots(3, 1, figsize=(7.2, 12.5), sharex=True)
for ax, (kb, kv, titel, ref) in zip(axs, panelen):
    for i, r in enumerate(rijen):
        b, v = 100 * float(r[kb]), 100 * float(r[kv])
        ax.plot([b, v], [i, i], color=GRID, lw=3, zorder=1, solid_capstyle='round')
        ax.scatter([b], [i], s=90, color=BLAUW, marker='o', zorder=3, edgecolors=SURF, linewidths=1.5)
        ax.scatter([v], [i], s=90, color=ORANJE, marker='s', zorder=3, edgecolors=SURF, linewidths=1.5)
        if r['Sector'] in NADRUK:
            lo, hi = min(b, v), max(b, v)
            if lo >= 10:
                ax.annotate(f'{lo:.0f}%', (lo, i), xytext=(-8, 0), textcoords='offset points', ha='right', va='center', fontsize=11, color=INK2)
                ax.annotate(f'{hi:.0f}%', (hi, i), xytext=(8, 0), textcoords='offset points', ha='left', va='center', fontsize=11, color=INK2)
            else:
                ax.annotate(f'banen {b:.0f}%, voet {v:.0f}%', (hi, i), xytext=(8, 0), textcoords='offset points', ha='left', va='center', fontsize=11, color=INK2)
    if ref is not None:
        ax.axvline(ref, color=INK2, lw=1, ls=(0, (3, 3)), zorder=0)
        ax.annotate('gemiddelde baan', (ref, len(rijen) - 0.4), xytext=(4, 0), textcoords='offset points', fontsize=10, color=INK2, va='bottom')
    ax.set_yticks(y)
    ax.set_yticklabels([NAAM[r['Sector']] for r in rijen])
    for lab, r in zip(ax.get_yticklabels(), rijen):
        if r['Sector'] in NADRUK:
            lab.set_fontweight('bold')
    ax.set_title(titel, loc='left', fontsize=14, color=INK, pad=8)
    ax.set_xlim(-2, 104)
    ax.set_ylim(-0.6, len(rijen) - 0.2)
    ax.grid(axis='x', color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for k in ['top', 'right', 'left']:
        ax.spines[k].set_visible(False)
    ax.tick_params(axis='y', length=0)
axs[-1].set_xticks([0, 25, 50, 75, 100])
axs[-1].set_xticklabels(['0%', '25%', '50%', '75%', '100%'])
h1 = axs[0].scatter([], [], s=90, color=BLAUW, marker='o', label='deel van de banen (LISA 2023)')
h2 = axs[0].scatter([], [], s=90, color=ORANJE, marker='s', label='deel van de pandvoetafdruk (BAG 2023)')
fig.legend(handles=[h1, h2], loc='upper left', bbox_to_anchor=(0.02, 0.985), frameon=False, fontsize=12, ncol=1)
fig.suptitle('Waar de werksectoren zitten, 2023', x=0.02, y=0.999, ha='left', fontsize=16, color=INK)
fig.text(0.02, 0.005, 'UAI en reistijd in vijf klassen met elk 20% van alle banen.\nBron: LISA, BAG, IBIS 2023; berekening RSopen.', fontsize=10, color=INK2, ha='left', va='bottom')
fig.tight_layout(rect=(0, 0.04, 1, 0.955))
p1 = os.path.join(d, 'IbisTerreinen_sectoren.png')
fig.savefig(p1, dpi=200)
plt.close(fig)

# Figuur 2: per IBIS-terrein het aandeel logistiek in de werkvoetafdruk tegen de UAI van het terrein, en opgeteld per UAI-klasse.
t = [r for r in lees('IbisTerreinen_perterrein.csv') if r['Aandeel_logistiek'] != '' and float(r['UAI']) > 0]
n_weg = len(lees('IbisTerreinen_perterrein.csv')) - len(t)
g = lees('IbisTerreinen_grenzen.csv')
k = lees('IbisTerreinen_terreinklassen.csv')
fig, (a1, a2) = plt.subplots(2, 1, figsize=(7.2, 11.5), gridspec_kw={'height_ratios': [1.25, 1]})
x = [float(r['UAI']) for r in t]
yv = [100 * float(r['Aandeel_logistiek']) for r in t]
sz = [float(r['Werk_m2']) / 4000 for r in t]
a1.scatter(x, yv, s=sz, color=BLAUW, alpha=0.35, edgecolors='none')
a1.set_xscale('log')
xmin = min(x)
grens = [float(r['UAI_ondergrens']) for r in g]
for i, gr in enumerate(grens[1:], start=1):
    a1.axvline(gr, color=INK2, lw=1, ls=(0, (3, 3)))
randen = [xmin] + grens[1:] + [max(x)]
for i in range(len(grens)):
    lo, hi = randen[i], randen[i + 1]
    a1.text((lo * hi) ** 0.5, 103, g[i]['Klasse'], ha='center', va='bottom', fontsize=11, color=INK2)
a1.set_ylim(-3, 110)
a1.set_yticks([0, 25, 50, 75, 100])
a1.set_yticklabels(['0%', '25%', '50%', '75%', '100%'])
a1.set_xlabel('UAI van het terrein (logaritmische schaal)')
a1.set_ylabel('logistiek in de werkvoetafdruk')
a1.set_title('Per IBIS-terrein; cirkel naar werkvoetafdruk', loc='left', fontsize=14, color=INK, pad=8)
a1.grid(color=GRID, lw=0.8)
a1.set_axisbelow(True)
for kk in ['top', 'right']:
    a1.spines[kk].set_visible(False)

kl = [r['Klasse'] for r in k]
xi = list(range(len(kl)))
w = 0.38
lg = [100 * float(r['UAI_aandeel_logistiek']) for r in k]
zk = [100 * float(r['UAI_aandeel_zak']) for r in k]
b1 = a2.bar([i - w / 2 - 0.01 for i in xi], lg, w, color=AQUA, label='logistiek')
b2 = a2.bar([i + w / 2 + 0.01 for i in xi], zk, w, color=VIOLET, label='zakelijke dienstverlening')
for bars in (b1, b2):
    for bb in bars:
        a2.annotate(f'{bb.get_height():.0f}%', (bb.get_x() + bb.get_width() / 2, bb.get_height()), xytext=(0, 3), textcoords='offset points', ha='center', va='bottom', fontsize=11, color=INK)
a2.set_xticks(xi)
a2.set_xticklabels([f"{r['Klasse']}\n{int(r['UAI_terreinen'])} terr.\n{float(r['UAI_werk_m2']) / 1e6:.0f} km²" for r in k], fontsize=11)
a2.set_ylim(0, 70)
a2.set_yticks([0, 20, 40, 60])
a2.set_yticklabels(['0%', '20%', '40%', '60%'])
a2.set_ylabel('deel van de werkvoetafdruk')
a2.set_title('Opgeteld per UAI-klasse van het terrein', loc='left', fontsize=14, color=INK, pad=8)
a2.legend(frameon=False, fontsize=12, loc='upper right')
a2.grid(axis='y', color=GRID, lw=0.8)
a2.set_axisbelow(True)
for kk in ['top', 'right']:
    a2.spines[kk].set_visible(False)
fig.suptitle('Logistiek op IBIS-terreinen naar UAI, 2023', x=0.02, y=0.995, ha='left', fontsize=16, color=INK)
fig.text(0.02, 0.005, f'Klassen K1 tot K5 met elk 20% van alle banen. {n_weg} terreinen zonder werkvoetafdruk\nontbreken boven; km² onder is de werkvoetafdruk. Bron: BAG, IBIS 2023; berekening RSopen.', fontsize=10, color=INK2, ha='left', va='bottom')
fig.tight_layout(rect=(0, 0.045, 1, 0.975))
p2 = os.path.join(d, 'IbisTerreinen_terreinen.png')
fig.savefig(p2, dpi=200)
plt.close(fig)
print(p1)
print(p2)
print('terreinen in scatter', len(t), 'weggelaten', n_weg, 'min UAI', xmin)
