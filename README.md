# Projet 7 – Gestion d'énergie de la maison (IoT / ThingSpeak)

Simulation de la consommation électrique d'une maison (6 pièces, plusieurs équipements), envoi des mesures vers **ThingSpeak**, visualisation sur un dashboard, détection de surconsommation et bilan énergétique avec coût en MAD.

## Dashboard ThingSpeak

![Dashboard ThingSpeak](docs/dashboard_thingspeak.png)

Les graphiques suivent la puissance (W) de la cuisine, du salon, de la chambre, de la salle de bain, des toilettes et de la buanderie. Les pics les plus élevés sont en cuisine (~2 kW), salle de bain (~1,5 kW) et salon (~1,4 kW), tandis que la chambre et les toilettes restent peu consommatrices.

## Contenu du dépôt

| Fichier | Rôle |
|---|---|
| `energie_bilan.py` | Simule la consommation, envoie les données aux 2 canaux ThingSpeak, génère `data/journal.csv`, `data/bilan_equipements.csv` et `docs/bilan.png` |
| `alerte-automatique.py` | Analyse les exports ThingSpeak, détecte les dépassements du seuil (3000 W) et génère `docs/analyse_thingspeak.png` |
| `data/` | Exports ThingSpeak (`feeds_*.csv`), journal, bilan par équipement, alertes |
| `docs/` | Captures et graphiques produits |

## Utilisation

```bash
pip install -r requirements.txt

# 1. (optionnel) envoi vers ThingSpeak : définir les Write API Keys
export THINGSPEAK_KEY_GENERAL=8CV3G5IHNUQCTTMY   # canal A : compteur + pièces
export THINGSPEAK_KEY_EQUIP=CLVMXN9EY6UULDK2   # canal B : équipements
python energie_bilan.py                  # sans clés : simulation locale uniquement

# 2. analyse des exports et alertes
python alerte-automatique.py
```

Dashboard public :

Canal A : Consommation d’énergie par pièces de la maison :https://thingspeak.mathworks.com/channels/3550172

Canal B : Consommation d’ énergie par équipements : https://thingspeak.mathworks.com/channels/3550188


## Résultats

![Bilan](docs/bilan.png)
![Analyse ThingSpeak](docs/analyse_thingspeak.png)
![Notification des Alertes par Email](docs/Notification_Alerte_par_Email.png)