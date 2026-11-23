
import sys
import os
import json
import time
import re
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent import generate_answer


FICHIER_DATASET = "evaluation/dataset.json"
FICHIER_RESULTATS = "evaluation/comparaison_prompts.json"


def normaliser(texte):
    texte = unicodedata.normalize("NFD", texte.lower())
    return "".join(
        c for c in texte
        if unicodedata.category(c) != "Mn"
    )


def verifier_reponse(exemple, resultat):
    categorie = exemple["categorie"]
    reponse = normaliser(resultat["answer"])

    if categorie == "document":

        attendu = normaliser(exemple["reponse_attendue"])

        mots_importants = re.findall(r"\w+", attendu)
        mots_obtenus = set(re.findall(r"\w+", reponse))

        mots_importants = [
            mot for mot in mots_importants
            if mot not in ["il", "faut", "une", "la", "le", "de", "du", "sur"]
        ]

        if not mots_importants:
            return False

        presents = sum(
            1 for mot in mots_importants
            if mot in mots_obtenus
        )

        return presents / len(mots_importants) >= 0.6

    if categorie == "calcul":

        attendus = re.findall(
            r"\d+(?:[.,]\d+)?",
            exemple["reponse_attendue"]
        )

        obtenus = re.findall(
            r"\d+(?:[.,]\d+)?",
            reponse
        )

        if not attendus or not obtenus:
            return False

        valeur_attendue = float(attendus[0].replace(",", "."))

        return any(
            abs(float(n.replace(",", ".")) - valeur_attendue) <= 0.01
            for n in obtenus
        )

    return False


with open(FICHIER_DATASET, "r", encoding="utf-8") as fichier:
    dataset = json.load(fichier)


resultats_comparaison = {}

for version in ["A", "B"]:

    reussites = 0
    total = 0
    temps_total = 0
    details = []

    print(f"\nEvaluation du prompt {version}")

    for exemple in dataset:

        if exemple["categorie"] == "demande":
            print("IGNORE | demande | Création réelle non testée")
            continue

        debut = time.time()

        try:
            resultat = generate_answer(exemple["question"], version)
            duree = time.time() - debut

            correct = verifier_reponse(exemple, resultat)

            total += 1
            temps_total += duree

            if correct:
                reussites += 1

            details.append({
                "question": exemple["question"],
                "categorie": exemple["categorie"],
                "correct": correct,
                "temps": round(duree, 2)
            })

            statut = "REUSSI" if correct else "ECHEC"
            print(f"{statut} | {exemple['categorie']} | {duree:.2f}s")

        except Exception as erreur:

            total += 1

            details.append({
                "question": exemple["question"],
                "categorie": exemple["categorie"],
                "correct": False,
                "erreur": str(erreur)
            })

            print(f"ERREUR | {exemple['categorie']} | {erreur}")

    taux = round(reussites / total * 100, 2) if total else 0
    temps_moyen = round(temps_total / total, 2) if total else 0

    resultats_comparaison[version] = {
        "reussites": reussites,
        "total": total,
        "taux_reussite": taux,
        "temps_moyen": temps_moyen,
        "details": details
    }

    print(f"Résultat : {reussites}/{total}")
    print(f"Taux de réussite : {taux}%")
    print(f"Temps moyen : {temps_moyen}s")


with open(FICHIER_RESULTATS, "w", encoding="utf-8") as fichier:
    json.dump(
        resultats_comparaison,
        fichier,
        ensure_ascii=False,
        indent=4
    )


print("\nComparaison terminée.")
