
import json
import unicodedata
from datetime import datetime
from pathlib import Path

DOSSIER_PROJET = Path(__file__).resolve().parents[2]
FICHIER_DEMANDES = DOSSIER_PROJET / "data" / "demandes.json"


def normaliser_texte(texte):
    texte = unicodedata.normalize("NFD", texte.lower().strip())

    texte = "".join(
        caractere
        for caractere in texte
        if unicodedata.category(caractere) != "Mn"
    )

    return " ".join(texte.split())


def creer_demande(nom: str, type_demande: str, description: str):

    types_autorises = [
        "attestation de scolarite",
        "demande de stage",
        "releve de notes"
    ]

    nom = nom.strip()
    description = description.strip()
    type_demande = " ".join(type_demande.strip().split())

    type_normalise = normaliser_texte(type_demande)

    if type_normalise not in types_autorises:
        raise ValueError("Type de demande non autorisé.")

    if len(nom) < 2:
        raise ValueError("Le nom est obligatoire.")

    if len(description) < 5:
        raise ValueError("La description est trop courte.")

    fichier_demandes = Path(FICHIER_DEMANDES)

    fichier_demandes.parent.mkdir(parents=True, exist_ok=True)

    if fichier_demandes.exists():
        try:
            with open(fichier_demandes, "r", encoding="utf-8") as fichier:
                demandes = json.load(fichier)
        except json.JSONDecodeError:
            raise ValueError(
                "Le fichier des demandes contient des données invalides."
            )
    else:
        demandes = []

    if not isinstance(demandes, list):
        raise ValueError("Le contenu du fichier des demandes est invalide.")

    ids = [
        demande.get("id", 0)
        for demande in demandes
        if isinstance(demande, dict)
        and isinstance(demande.get("id"), int)
    ]

    nouvel_id = max(ids, default=0) + 1

    nouvelle_demande = {
        "id": nouvel_id,
        "nom": nom,
        "type_demande": type_demande,
        "description": description,
        "date": datetime.now().isoformat(),
        "statut": "en attente"
    }

    demandes.append(nouvelle_demande)

    fichier_temporaire = fichier_demandes.with_suffix(".tmp")

    with open(fichier_temporaire, "w", encoding="utf-8") as fichier:
        json.dump(demandes, fichier, ensure_ascii=False, indent=4)

    fichier_temporaire.replace(fichier_demandes)

    return nouvelle_demande
