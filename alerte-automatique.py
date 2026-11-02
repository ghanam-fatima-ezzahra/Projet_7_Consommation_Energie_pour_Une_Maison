import pandas as pd
import matplotlib.pyplot as plt

# ============ CONFIGURATION ============
FICHIER_A = 'feeds_consomation_par_peices.csv'        # export ThingSpeak : compteur + pièces
FICHIER_B = 'feeds_consommation_par_equipements.csv'  # export ThingSpeak : équipements
SEUIL_W = 3000                   # seuil d'alerte de surconsommation (W)
TARIF_KWH = 1.2                  # MAD par kWh
# =======================================

NOMS_A = {
    'field1': 'Total compteur',
    'field2': 'Cuisine',
    'field3': 'Salon',
    'field4': 'Chambre',
    'field5': 'Salle de bain',
    'field6': 'Toilettes',
    'field7': 'Buanderie',
    'field8': 'Energie cumulee (kWh)',
}

NOMS_B = {
    'field1': 'Réfrigérateur',
    'field2': 'Four',
    'field3': 'Climatiseur',
    'field4': 'Chauffe-eau',
    'field5': 'TV',
    'field6': 'Lave-linge',
    'field7': 'Ordinateur',
    'field8': 'Fer à repasser',
}


def charger(fichier, noms):
    df = pd.read_csv(fichier)
    df['created_at'] = pd.to_datetime(df['created_at'])
    return df.rename(columns=noms).set_index('created_at')


a = charger(FICHIER_A, NOMS_A).sort_index()
b = charger(FICHIER_B, NOMS_B).sort_index()
print(f'Données brutes : canal A = {len(a)} mesures | canal B = {len(b)} mesures')

# ---------- Ne garder que la dernière exécution ----------
# Le cumul kWh repart de 0 à chaque lancement du simulateur : une baisse
# du cumul marque donc le début d'une nouvelle exécution.
# Pour choisir un jour précis à la place, mettez par exemple :
# JOUR = '2026-11-01'   puis   a = a.loc[JOUR]   et   b = b.loc[JOUR]
chute = a['Energie cumulee (kWh)'].diff() < 0
if chute.any():
    debut = a.index[chute][-1]
    a = a[a.index >= debut]
    b = b[b.index >= debut - pd.Timedelta(seconds=5)]
    print(f'Dernière exécution détectée à partir de {debut:%Y-%m-%d %H:%M:%S}')
print(f'Analysées : canal A = {len(a)} mesures | canal B = {len(b)} mesures (attendu : 96)')

# ---------- 1) Compteur général ----------
total = a['Total compteur']
print('\n=== COMPTEUR GÉNÉRAL ===')
print(total.describe().round(1))
print(f'Pic : {total.max():.0f} W à {total.idxmax():%H:%M:%S}')

energie = a['Energie cumulee (kWh)'].max()
print(f'Énergie totale : {energie:.2f} kWh | Coût : {energie * TARIF_KWH:.2f} MAD')
print(f'Coût mensuel estimé (x30) : {energie * TARIF_KWH * 30:.2f} MAD')

# ---------- 2) Alertes de surconsommation ----------
alertes = total[total > SEUIL_W]
print(f'\n=== ALERTES (> {SEUIL_W} W) : {len(alertes)} ===')
for t, v in alertes.items():
    print(f'  ALERTE {t:%H:%M:%S} : {v:.0f} W')
alertes.rename('puissance_W').to_csv('alertes.csv', sep=';')

# ---------- 3) Pièces et équipements ----------
pieces = a[['Cuisine', 'Salon', 'Chambre', 'Salle de bain', 'Toilettes', 'Buanderie']]
moy_pieces = pieces.mean().sort_values(ascending=False)
moy_equip = b.drop(columns=['entry_id'], errors='ignore').mean().sort_values(ascending=False)

print('\n=== PUISSANCE MOYENNE PAR PIÈCE (W) ===')
print(moy_pieces.round(1))
print('\n=== PUISSANCE MOYENNE PAR ÉQUIPEMENT SUIVI (W) ===')
print(moy_equip.round(1))

# ---------- 4) Graphiques ----------
fig, ax = plt.subplots(1, 3, figsize=(18, 5))

ax[0].plot(total.index, total.values, color='tab:blue')
ax[0].axhline(SEUIL_W, color='red', linestyle='--', label=f'Seuil {SEUIL_W} W')
ax[0].scatter(alertes.index, alertes.values, color='red', zorder=3, label='Alertes')
ax[0].set_title('Compteur général et alertes')
ax[0].set_ylabel('Puissance (W)')
ax[0].legend()
ax[0].tick_params(axis='x', rotation=45)

ax[1].barh(moy_pieces.index[::-1], moy_pieces.values[::-1], color='tab:orange')
ax[1].set_title('Puissance moyenne par pièce (W)')

ax[2].barh(moy_equip.index[::-1], moy_equip.values[::-1], color='tab:green')
ax[2].set_title('Puissance moyenne par équipement (W)')

plt.tight_layout()
plt.savefig('analyse_thingspeak.png', dpi=150)
print('\nGraphique créé : analyse_thingspeak.png | Alertes : alertes.csv')
plt.show()