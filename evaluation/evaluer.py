
import os
import sys
import json
import time
import re
import unicodedata
import statistics

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from app.agent import generate_answer


def normaliser_texte(texte):
    texte = texte.lower()
    texte = unicodedata.normalize("NFD", texte)

    texte = "".join(
        caractere
        for caractere in texte
        if unicodedata.category(caractere) != "Mn"
    )

    texte = texte.replace(
        "au moins",
        "superieure ou egale"
    )

    return texte


def extraire_nombres(texte):
    nombres = re.findall(r"\d+(?:[.,]\d+)?", texte)
    return [float(nombre.replace(",", ".")) for nombre in nombres]


SYNONYMES_EVALUATION = {
    "justifier": "declarer",
    "justifiee": "declaree",
    "justifie": "declare",
    "administration": "administration",
    "etablissement": "etablissement"
}


def extraire_mots(texte):
    mots = re.findall(r"\w+", normaliser_texte(texte))

    return {
        SYNONYMES_EVALUATION.get(mot, mot)
        for mot in mots
        if len(mot) > 3 or mot.isdigit()
    }


with open("evaluation/dataset.json", "r", encoding="utf-8") as fichier:
    dataset = json.load(fichier)


resultats = []
temps_total = 0
tests_ignores = 0

for exemple in dataset:
    question = exemple["question"]
    categorie = exemple["categorie"]
    statut_attendu = exemple.get("statut_attendu")

    if categorie == "demande" and "Ahmed Ben Ali" in question:
        print("IGNORE | demande | Création réelle non exécutée")
        tests_ignores += 1
        continue

    debut = time.time()

    try:
        resultat = generate_answer(question)
        duree = time.time() - debut

        reponse = normaliser_texte(resultat["answer"])
        statut_obtenu = resultat["status"]

        if statut_attendu:
            reussi = statut_obtenu == statut_attendu

        elif categorie == "calcul":
            nombres_reponse = extraire_nombres(reponse)
            nombres_attendus = extraire_nombres(
                exemple["reponse_attendue"]
            )

            reussi = (
                len(nombres_attendus) == 1
                and any(
                    abs(nombre - nombres_attendus[0]) < 0.01
                    for nombre in nombres_reponse
                )
            )

        elif categorie == "demande":
            reussi = (
                statut_obtenu == "repondu"
                and "cree avec succes" not in reponse
            )

        else:
            mots_attendus = extraire_mots(
                exemple["reponse_attendue"]
            )
            mots_reponse = extraire_mots(reponse)

            mots_trouves = len(mots_attendus & mots_reponse)

            reussi = (
                mots_trouves / len(mots_attendus) >= 0.6
                if mots_attendus else False
            )

    except Exception as erreur:
        duree = time.time() - debut
        reussi = False
        reponse = str(erreur)
        statut_obtenu = "erreur"

        print("ERREUR DETAILLEE :", repr(erreur))

    temps_total += duree

    resultats.append({
        "question": question,
        "categorie": categorie,
        "statut_attendu": statut_attendu,
        "statut_obtenu": statut_obtenu,
        "reussi": reussi,
        "temps": round(duree, 2)
    })

    print(
        f"{'REUSSI' if reussi else 'ECHEC'} | "
        f"{categorie} | {statut_obtenu} | {duree:.2f}s"
    )


nombre_tests = len(resultats)
nombre_reussis = sum(1 for r in resultats if r["reussi"])

print("\n========== RESULTATS ==========")
print("Exemples dans le dataset :", len(dataset))
print("Tests exécutés :", nombre_tests)
print("Tests ignorés :", tests_ignores)
print("Réussites :", nombre_reussis)
print("Échecs :", nombre_tests - nombre_reussis)

taux_reussite = (
    nombre_reussis / nombre_tests * 100
    if nombre_tests else 0
)

temps_moyen = temps_total / nombre_tests if nombre_tests else 0

print(f"Taux de réussite : {taux_reussite:.2f}%")
print(f"Temps moyen : {temps_moyen:.2f}s")

temps = [r["temps"] for r in resultats]

if temps:
    print(f"Temps minimum : {min(temps):.2f}s")
    print(f"Temps médian : {statistics.median(temps):.2f}s")
    print(f"Temps maximum : {max(temps):.2f}s")


print("\nRésultats par catégorie :")

for categorie in ["document", "calcul", "demande"]:
    tests = [r for r in resultats if r["categorie"] == categorie]

    if tests:
        reussites = sum(1 for r in tests if r["reussi"])
        taux = reussites / len(tests) * 100

        print(
            f"{categorie} : {reussites}/{len(tests)} "
            f"({taux:.2f}%)"
        )


with open("evaluation/resultats.json", "w", encoding="utf-8") as fichier:
    json.dump(resultats, fichier, ensure_ascii=False, indent=4)
