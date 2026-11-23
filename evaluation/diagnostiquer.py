
import json
import os
import sys

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from app.agent import generate_answer


with open("evaluation/dataset.json", "r", encoding="utf-8") as fichier:
    dataset = json.load(fichier)

with open("evaluation/resultats.json", "r", encoding="utf-8") as fichier:
    anciens_resultats = json.load(fichier)


echecs = [
    resultat for resultat in anciens_resultats
    if not resultat["reussi"]
]

if not echecs:
    print("Aucune erreur détectée dans les résultats de l'évaluation.")
    sys.exit(0)


for resultat in echecs:
    exemple = next(
        (
            item for item in dataset
            if item["question"] == resultat["question"]
        ),
        None
    )

    if exemple is None:
        print("\nQuestion introuvable dans le dataset :", resultat["question"])
        continue

    print("\n" + "=" * 60)
    print("QUESTION :", exemple["question"])
    print("REPONSE ATTENDUE :", exemple["reponse_attendue"])

    try:
        reponse = generate_answer(exemple["question"])

        print("REPONSE EDUBOT :", reponse["answer"])
        print("STATUT :", reponse["status"])
        print("SOURCES :", reponse.get("sources", []))

    except Exception as erreur:
        print("ERREUR :", erreur)
