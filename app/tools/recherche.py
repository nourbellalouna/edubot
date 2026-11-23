
import os
import re
import unicodedata

DOSSIER_DOCUMENTS = "documents"

MOTS_INUTILES = {
    "comment", "quelle", "quelles", "quel", "quels",
    "est", "sont", "une", "des", "les", "la", "le",
    "un", "de", "du", "dans", "pour", "avec", "sur",
    "je", "dois", "mon", "ma", "mes", "me", "faire",
    "faut", "il", "elle", "et", "ou", "a", "au",
    "aux", "qui", "que", "quoi", "ou", "inscrire"
}

SYNONYMES = {
    "inscrire": "inscription",
    "inscriptions": "inscription",
    "documents": "fournir",
    "document": "fournir"
}


def normaliser_texte(texte):
    texte = texte.lower()
    texte = unicodedata.normalize("NFD", texte)

    texte = "".join(
        caractere
        for caractere in texte
        if unicodedata.category(caractere) != "Mn"
    )

    return texte


def extraire_mots(texte):
    texte = normaliser_texte(texte)
    mots = re.findall(r"\w+", texte)

    resultat = set()

    for mot in mots:
        mot = SYNONYMES.get(mot, mot)

        if mot not in MOTS_INUTILES and len(mot) > 2:
            resultat.add(mot)

    return resultat


def rechercher_information(question: str):
    resultats = []

    mots_question = extraire_mots(question)

    for fichier in os.listdir(DOSSIER_DOCUMENTS):

        if fichier.endswith(".txt"):

            chemin = os.path.join(DOSSIER_DOCUMENTS, fichier)

            with open(chemin, "r", encoding="utf-8") as f:
                contenu = f.read()

            paragraphes = contenu.split("\n\n")

            i = 0

            while i < len(paragraphes):

                paragraphe = paragraphes[i].strip()

                if re.match(r"^\d+\.", paragraphe) and i + 1 < len(paragraphes):
                    paragraphe += "\n" + paragraphes[i + 1].strip()
                    i += 1

                mots_paragraphe = extraire_mots(paragraphe)
                score = len(mots_question & mots_paragraphe)

                if score > 0:
                    resultats.append({
                        "texte": paragraphe,
                        "source": fichier,
                        "score": score
                    })

                i += 1

    resultats.sort(
        key=lambda resultat: resultat["score"],
        reverse=True
    )

    return resultats[:3]
