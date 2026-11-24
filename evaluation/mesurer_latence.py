import sys
from pathlib import Path

RACINE_PROJET = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE_PROJET))

import json
import time
import statistics
from datetime import datetime

from app.agent import generate_answer, APP_MODE, MODEL_NAME

NOMBRE_APPELS = 20

QUESTION = (
    "Quelles sont les règles concernant la justification d'une absence ?"
)

FICHIER_RESULTATS = RACINE_PROJET / "evaluation" / "resultats_latence.json"


def mesurer_latence():

    if APP_MODE != "real":
        print("ERREUR : le projet doit être en mode real.")
        print("Vérifiez APP_MODE dans votre fichier .env.")
        return

    latences = []
    erreurs = 0

    print("EDUBOT - MESURE DE LATENCE")
    print("Modèle :", MODEL_NAME)
    print("Nombre d'appels :", NOMBRE_APPELS)
    print("--------------------------------")

    for numero in range(1, NOMBRE_APPELS + 1):

        debut = time.perf_counter()

        try:
            generate_answer(QUESTION)
            statut = "reussi"

        except Exception as erreur:
            statut = "erreur"
            erreurs += 1
            print("Erreur :", str(erreur))

        duree = time.perf_counter() - debut
        latences.append(duree)

        print(
            f"Appel {numero:02d}/{NOMBRE_APPELS} : "
            f"{duree:.3f} secondes - {statut}"
        )

    minimum = min(latences)
    mediane = statistics.median(latences)
    maximum = max(latences)
    moyenne = statistics.mean(latences)

    resultats = {
        "date": datetime.now().isoformat(),
        "mode": APP_MODE,
        "modele": MODEL_NAME,
        "nombre_appels": NOMBRE_APPELS,
        "appels_reussis": NOMBRE_APPELS - erreurs,
        "appels_en_erreur": erreurs,
        "latence_minimale_secondes": round(minimum, 3),
        "latence_mediane_secondes": round(mediane, 3),
        "latence_maximale_secondes": round(maximum, 3),
        "latence_moyenne_secondes": round(moyenne, 3)
    }

    with open(FICHIER_RESULTATS, "w", encoding="utf-8") as fichier:
        json.dump(resultats, fichier, ensure_ascii=False, indent=4)

    print("--------------------------------")
    print("RÉSULTATS SUR 20 APPELS")
    print("Minimum :", round(minimum, 3), "secondes")
    print("Médiane :", round(mediane, 3), "secondes")
    print("Maximum :", round(maximum, 3), "secondes")
    print("Moyenne :", round(moyenne, 3), "secondes")
    print("Appels réussis :", NOMBRE_APPELS - erreurs)
    print("Erreurs :", erreurs)
    print("Résultats enregistrés dans :", FICHIER_RESULTATS)


if __name__ == "__main__":
    mesurer_latence()
