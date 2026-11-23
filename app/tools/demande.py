
import json
import os
import unicodedata
from datetime import datetime

FICHIER_DEMANDES = "data/demandes.json"


def normaliser_texte(texte):
    texte = unicodedata.normalize("NFD", texte.lower())
    return "".join(
        caractere
        for caractere in texte
        if unicodedata.category(caractere) != "Mn"
    )


def creer_demande(nom: str, type_demande: str, description: str):
    types_autorises = [
        "attestation de scolarite",
        "demande de stage",
        "releve de notes"
    ]

    type_normalise = normaliser_texte(type_demande)

    if type_normalise not in types_autorises:
        raise ValueError("Type de demande non autorisé.")

    if len(nom.strip()) < 2:
        raise ValueError("Le nom est obligatoire.")

    if len(description.strip()) < 5:
        raise ValueError("La description est trop courte.")

    os.makedirs("data", exist_ok=True)

    if os.path.exists(FICHIER_DEMANDES):
        with open(FICHIER_DEMANDES, "r", encoding="utf-8") as f:
            demandes = json.load(f)
    else:
        demandes = []

    nouvelle_demande = {
        "id": len(demandes) + 1,
        "nom": nom,
        "type_demande": type_demande,
        "description": description,
        "date": datetime.now().isoformat(),
        "statut": "en attente"
    }

    demandes.append(nouvelle_demande)

    with open(FICHIER_DEMANDES, "w", encoding="utf-8") as f:
        json.dump(demandes, f, ensure_ascii=False, indent=4)

    return nouvelle_demande
