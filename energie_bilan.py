import csv
import os
import time
import requests
import matplotlib.pyplot as plt
from random import randint

# ============ CONFIGURATION ============
# Les clés ne sont PAS dans le code : définissez-les dans votre terminal
#   export THINGSPEAK_KEY_GENERAL=xxxx   et   export THINGSPEAK_KEY_EQUIP=yyyy
KEY_GENERAL = os.environ.get('THINGSPEAK_KEY_GENERAL', '')   # Write API Key du canal A
KEY_EQUIP = os.environ.get('THINGSPEAK_KEY_EQUIP', '')       # Write API Key du canal B
URL = 'https://api.thingspeak.com/update.json'

INTERVALLE = 20    # secondes entre deux envois (minimum 15 en gratuit)
PAS_MIN = 15       # minutes simulées par envoi (96 pas = 1 journée)
JOURS = 1          # nombre de jours simulés
TARIF_KWH = 1.2    # MAD par kWh
ENVOYER = bool(KEY_GENERAL and KEY_EQUIP)  # False = simulation locale rapide | True = envoi ThingSpeak (~32 min)
# =======================================

PIECES = ['Cuisine', 'Salon', 'Chambre', 'Salle de bain', 'Toilettes', 'Buanderie']

# (nom, pièce, puissance W, plages horaires, probabilité en %)
EQUIPEMENTS = [
    ('Réfrigérateur', 'Cuisine', 150, [(0, 24)], 40),
    ('Four', 'Cuisine', 2000, [(12, 14), (19, 21)], 25),
    ('Micro-ondes', 'Cuisine', 1000, [(7, 8), (12, 14), (19, 21)], 15),
    ('Éclairage cuisine', 'Cuisine', 40, [(6, 8), (18, 22)], 80),
    ('TV', 'Salon', 120, [(18, 23)], 80),
    ('Climatiseur', 'Salon', 1200, [(13, 18), (21, 24)], 50),
    ('Éclairage salon', 'Salon', 60, [(18, 23)], 90),
    ('Ordinateur', 'Chambre', 100, [(9, 12), (15, 23)], 70),
    ('Éclairage chambre', 'Chambre', 30, [(19, 23)], 50),
    ('Chauffe-eau', 'Salle de bain', 1500, [(6, 8), (19, 22)], 30),
    ('Sèche-cheveux', 'Salle de bain', 1800, [(7, 8)], 15),
    ('Éclairage SDB', 'Salle de bain', 20, [(6, 8), (19, 23)], 40),
    ('Éclairage toilettes', 'Toilettes', 10, [(6, 23)], 10),
    ('Lave-linge', 'Buanderie', 500, [(9, 12)], 40),
    ('Fer à repasser', 'Buanderie', 1000, [(15, 17)], 30),
]

# Les 8 équipements envoyés au canal B (dans l'ordre des champs)
EQUIP_CANAL_B = ['Réfrigérateur', 'Four', 'Climatiseur', 'Chauffe-eau',
                 'TV', 'Lave-linge', 'Ordinateur', 'Fer à repasser']

PIECE_DE = {nom: piece for nom, piece, *_ in EQUIPEMENTS}


def plage_active(plages, heure):
    return any(d <= heure < f for d, f in plages)


def simuler(heure):
    conso = {}
    for nom, piece, watts, plages, proba in EQUIPEMENTS:
        if plage_active(plages, heure) and randint(1, 100) <= proba:
            conso[nom] = watts + watts * randint(-5, 5) // 100
        else:
            conso[nom] = 0
    return conso


def envoyer(cle, champs):
    payload = {'api_key': cle}
    for i, v in enumerate(champs):
        payload['field' + str(i + 1)] = v
    try:
        r = requests.post(URL, data=payload, timeout=10)
        print('   HTTP', r.status_code, '|', r.text[:80])
        return r.status_code == 200 and r.json().get('entry_id', 0) > 0
    except Exception as e:
        print('   ERREUR :', e)
        return False


def tracer(energie, historique):
    total = sum(energie.values())
    par_piece = {p: 0.0 for p in PIECES}
    for nom, e in energie.items():
        par_piece[PIECE_DE[nom]] += e
    couleurs = dict(zip(PIECES, plt.cm.tab10.colors))

    fig, ax = plt.subplots(2, 2, figsize=(17, 11))
    fig.suptitle(f'Bilan de consommation : {total:.2f} kWh | {total * TARIF_KWH:.2f} MAD',
                 fontsize=16, fontweight='bold')

    # 1) Consommation par pièce
    pieces = sorted([(p, e) for p, e in par_piece.items() if e > 0], key=lambda x: x[1])
    noms = [p for p, _ in pieces]
    vals = [e for _, e in pieces]
    barres = ax[0, 0].barh(noms, vals, color=[couleurs[p] for p in noms])
    for b, v in zip(barres, vals):
        ax[0, 0].text(v, b.get_y() + b.get_height() / 2,
                      f'  {v:.2f} kWh ({v / total * 100:.0f} %)', va='center')
    ax[0, 0].set_xlim(0, max(vals) * 1.4)
    ax[0, 0].set_xlabel('kWh')
    ax[0, 0].set_title('Consommation par pièce')

    # 2) Répartition en anneau
    ax[0, 1].pie(vals[::-1], colors=[couleurs[p] for p in noms[::-1]],
                 autopct=lambda x: f'{x:.0f} %' if x >= 4 else '',
                 pctdistance=0.8, startangle=90,
                 wedgeprops={'width': 0.45, 'edgecolor': 'white'})
    ax[0, 1].legend(noms[::-1], loc='center left', bbox_to_anchor=(1, 0.5))
    ax[0, 1].set_title('Répartition par pièce')

    # 3) Top 8 équipements
    top = sorted([(n, e) for n, e in energie.items() if e > 0], key=lambda x: -x[1])[:8][::-1]
    barres = ax[1, 0].barh([n for n, _ in top], [e for _, e in top],
                           color=[couleurs[PIECE_DE[n]] for n, _ in top])
    for b, (n, e) in zip(barres, top):
        ax[1, 0].text(e, b.get_y() + b.get_height() / 2, f'  {e:.2f} kWh', va='center')
    ax[1, 0].set_xlim(0, max(e for _, e in top) * 1.25)
    ax[1, 0].set_xlabel('kWh')
    ax[1, 0].set_title('Top 8 équipements')

    # 4) Profil de puissance sur la journée
    heures = [h for h, _ in historique]
    series = [[d[p] for _, d in historique] for p in PIECES]
    ax[1, 1].stackplot(heures, series, labels=PIECES,
                       colors=[couleurs[p] for p in PIECES])
    ax[1, 1].set_xlim(0, 24)
    ax[1, 1].set_xticks(range(0, 25, 3))
    ax[1, 1].set_xlabel('Heure de la journée')
    ax[1, 1].set_ylabel('Puissance (W)')
    ax[1, 1].set_title('Profil de consommation du compteur')
    ax[1, 1].legend(loc='upper left', fontsize=8)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('docs/bilan.png', dpi=150)
    print('Graphique créé : bilan.png')
    plt.show()


def bilan(energie, historique):
    total = sum(energie.values())
    par_piece = {p: 0.0 for p in PIECES}
    for nom, e in energie.items():
        par_piece[PIECE_DE[nom]] += e

    print('\nBILAN PAR PIÈCE')
    for p, e in sorted(par_piece.items(), key=lambda x: -x[1]):
        print(f'{p:<16}{e:8.3f} kWh {e / total * 100:6.1f} % {e * TARIF_KWH:8.2f} MAD')

    print('\nBILAN PAR ÉQUIPEMENT')
    for nom, e in sorted(energie.items(), key=lambda x: -x[1]):
        print(f'{nom:<22}{PIECE_DE[nom]:<15}{e:8.3f} kWh {e / total * 100:6.1f} %')

    print(f'\nTOTAL COMPTEUR : {total:.3f} kWh | {total * TARIF_KWH:.2f} MAD')
    print(f'Vérification somme des pièces : {sum(par_piece.values()):.3f} kWh')

    with open('data/bilan_equipements.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['Equipement', 'Piece', 'kWh', 'Pourcentage', 'Cout_MAD'])
        for nom, e in energie.items():
            w.writerow([nom, PIECE_DE[nom], round(e, 4),
                        round(e / total * 100, 1), round(e * TARIF_KWH, 3)])

    tracer(energie, historique)


def main():
    energie = {nom: 0.0 for nom in PIECE_DE}
    historique = []
    nb_pas = int(24 * 60 / PAS_MIN) * JOURS
    pause = INTERVALLE if ENVOYER else 0
    journal = open('data/journal.csv', 'w', newline='', encoding='utf-8-sig')
    wj = csv.writer(journal, delimiter=';')
    wj.writerow(['heure', 'total_W'] + PIECES)
    mode = 'avec envoi ThingSpeak' if ENVOYER else 'simulation locale rapide'
    print(f'{nb_pas} pas ({mode}). Ctrl+C pour arrêter.')

    try:
        for pas in range(nb_pas):
            heure = (pas * PAS_MIN / 60) % 24
            conso = simuler(heure)

            par_piece = {p: 0 for p in PIECES}
            for nom, w in conso.items():
                par_piece[PIECE_DE[nom]] += w
                energie[nom] += w * (PAS_MIN / 60) / 1000
            total_w = sum(conso.values())
            total_kwh = sum(energie.values())
            historique.append((heure, dict(par_piece)))

            etat_a = etat_b = '-'
            if ENVOYER:
                champs_a = [total_w] + [par_piece[p] for p in PIECES] + [round(total_kwh, 4)]
                etat_a = 'OK' if envoyer(KEY_GENERAL, champs_a) else 'ECHEC'
                etat_b = 'OK' if envoyer(KEY_EQUIP, [conso[n] for n in EQUIP_CANAL_B]) else 'ECHEC'

            hh, mm = int(heure), int((heure % 1) * 60)
            wj.writerow([f'{hh:02d}:{mm:02d}', total_w] + [par_piece[p] for p in PIECES])
            print(f'[{hh:02d}:{mm:02d}] Total={total_w:5d} W | A:{etat_a} B:{etat_b}')
            time.sleep(pause)
    except KeyboardInterrupt:
        print('\nArrêt demandé : bilan sur les données déjà simulées.')

    journal.close()
    if sum(energie.values()) > 0:
        bilan(energie, historique)


if __name__ == '__main__':
    main()