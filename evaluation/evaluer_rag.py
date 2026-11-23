
import os
import sys
import json

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from app.tools.recherche import rechercher_information


JEU_TEST = [
    {
        "question": "Quels documents faut-il fournir pour une inscription ?",
        "document_attendu": "reglement.txt"
    },
    {
        "question": "Quelle est la moyenne minimale pour valider le semestre ?",
        "document_attendu": "reglement.txt"
    },
    {
        "question": "Quels documents sont nécessaires pour une demande de stage ?",
        "document_attendu": "reglement.txt"
    },
    {
        "question": "Comment justifier une absence ?",
        "document_attendu": "reglement.txt"
    }
]


def calculer_recall(k):
    total = 0

    for exemple in JEU_TEST:
        resultats = rechercher_information(exemple["question"])
        premiers_resultats = resultats[:k]

        document_trouve = any(
            resultat["source"] == exemple["document_attendu"]
            for resultat in premiers_resultats
        )

        if document_trouve:
            total += 1

        print(
            f"{'REUSSI' if document_trouve else 'ECHEC'} "
            f"| Recall@{k} "
            f"| {exemple['question']}"
        )

    return total / len(JEU_TEST) if JEU_TEST else 0


print("\n========== EVALUATION RAG ==========")

resultats = {}

for k in [1, 2, 3]:
    recall = calculer_recall(k)

    resultats[f"Recall@{k}"] = round(recall * 100, 2)

    print(f"\nRecall@{k} : {recall * 100:.2f}%")


with open(
    "evaluation/resultats_rag.json",
    "w",
    encoding="utf-8"
) as fichier:
    json.dump(
        resultats,
        fichier,
        ensure_ascii=False,
        indent=4
    )

print("\nRésultats enregistrés dans evaluation/resultats_rag.json")
