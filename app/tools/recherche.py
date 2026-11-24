
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
    "aux", "qui", "que", "quoi", "inscrire",
    "obtenir", "necessaires", "necessaire",
    "elements", "permet", "estce", "doit",
    "effectuer", "aupres", "universitaire"
}

SYNONYMES = {
    "inscrire": "inscription",
    "inscriptions": "inscription",
    "documents": "fournir",
    "document": "fournir",
    "justifier": "justifiee",
    "justification": "justifiee",
    "valider": "validation",
    "valide": "validation",
    "minimale": "moyenne"
}

SUJETS_SPECIFIQUES = {
    "bourse": {"bourse"},
    "logement": {"logement"},
    "frais": {"frais", "prix", "cout", "montant", "tarif"},
    "prix": {"frais", "prix", "cout", "montant", "tarif"},
    "montant": {"frais", "prix", "cout", "montant", "tarif"},
    "cout": {"frais", "prix", "cout", "montant", "tarif"},
    "commence": {"date", "debut", "commence", "calendrier"},
    "debut": {"date", "debut", "commence", "calendrier"},
    "date": {"date", "debut", "commence", "calendrier"}
}


def normaliser_texte(texte):
    texte = texte.lower()
    texte = unicodedata.normalize("NFD", texte)

    return "".join(
        caractere
        for caractere in texte
        if unicodedata.category(caractere) != "Mn"
    )


def extraire_mots(texte):
    texte = normaliser_texte(texte)
    mots = re.findall(r"\w+", texte)

    resultat = set()

    for mot in mots:
        mot = SYNONYMES.get(mot, mot)

        if mot not in MOTS_INUTILES and len(mot) > 2:
            resultat.add(mot)

    return resultat


def sujet_non_couvert(mots_question, mots_paragraphe):

    for mot in mots_question:
        if mot in SUJETS_SPECIFIQUES:
            mots_attendus = SUJETS_SPECIFIQUES[mot]

            if not mots_attendus.intersection(mots_paragraphe):
                return True

    return False


def rechercher_information(question: str):
    resultats = []

    mots_question = extraire_mots(question)

    if not mots_question:
        return []

    if not os.path.isdir(DOSSIER_DOCUMENTS):
        return []

    for fichier in os.listdir(DOSSIER_DOCUMENTS):

        if not fichier.endswith(".txt"):
            continue

        chemin = os.path.join(DOSSIER_DOCUMENTS, fichier)

        with open(chemin, "r", encoding="utf-8") as f:
            contenu = f.read()

        paragraphes = contenu.split("\n\n")

        for paragraphe in paragraphes:

            paragraphe = paragraphe.strip()

            if not paragraphe:
                continue

            mots_paragraphe = extraire_mots(paragraphe)

            if sujet_non_couvert(mots_question, mots_paragraphe):
                continue

            correspondances = mots_question.intersection(
                mots_paragraphe
            )

            score = len(correspondances)

            if score > 0:
                resultats.append({
                    "texte": paragraphe,
                    "source": fichier,
                    "score": score
                })

    resultats.sort(
        key=lambda resultat: resultat["score"],
        reverse=True
    )

    return resultats[:3]
