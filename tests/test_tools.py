
import pytest

from app.tools.calcul import calculer_moyenne, verifier_validation_semestre
from app.tools.demande import creer_demande
from app.tools.recherche import rechercher_information
from app.agent import generate_answer


def test_calculer_moyenne():
    resultat = calculer_moyenne([12, 15, 16], [2, 3, 1])
    assert resultat == 14.17


def test_calculer_moyenne_notes_invalides():
    with pytest.raises(ValueError):
        calculer_moyenne([25, 12], [1, 1])


def test_calculer_moyenne_coefficients_invalides():
    with pytest.raises(ValueError):
        calculer_moyenne([12, 15], [1, 0])


def test_verifier_validation_semestre():
    assert verifier_validation_semestre(12) == "semestre valide"
    assert verifier_validation_semestre(8.2) == "semestre non valide"


def test_verifier_validation_semestre_moyenne_invalide():
    with pytest.raises(ValueError):
        verifier_validation_semestre(25)


def test_creer_demande(tmp_path, monkeypatch):
    fichier = tmp_path / "demandes.json"

    monkeypatch.setattr(
        "app.tools.demande.FICHIER_DEMANDES",
        str(fichier)
    )

    resultat = creer_demande(
        "Ahmed Ben Ali",
        "attestation de scolarité",
        "Je souhaite obtenir une attestation."
    )

    assert resultat["id"] == 1
    assert resultat["nom"] == "Ahmed Ben Ali"
    assert resultat["statut"] == "en attente"


def test_creer_demande_type_invalide():
    with pytest.raises(ValueError):
        creer_demande(
            "Ahmed Ben Ali",
            "demande invalide",
            "Description de la demande."
        )


def test_rechercher_information(tmp_path, monkeypatch):
    document = tmp_path / "reglement.txt"

    document.write_text(
        "1. INSCRIPTION\n\n"
        "Pour effectuer une inscription, "
        "l'etudiant doit fournir une carte d'identite.",
        encoding="utf-8"
    )

    monkeypatch.setattr(
        "app.tools.recherche.DOSSIER_DOCUMENTS",
        str(tmp_path)
    )

    resultat = rechercher_information(
        "Quels documents fournir pour une inscription ?"
    )

    assert len(resultat) > 0
    assert resultat[0]["source"] == "reglement.txt"


def test_agent_recherche_inscription(monkeypatch):
    monkeypatch.setattr("app.agent.APP_MODE", "simulation")

    resultat = generate_answer(
        "Quels documents faut-il fournir pour une inscription ?"
    )

    assert resultat["status"] == "repondu"
    assert "inscription" in resultat["answer"].lower()
    assert "demande de stage" not in resultat["answer"].lower()
    assert resultat["sources"] == ["reglement.txt"]


def test_agent_information_introuvable(monkeypatch):
    monkeypatch.setattr("app.agent.APP_MODE", "simulation")

    resultat = generate_answer(
        "Quelle est la date de rentrée universitaire ?"
    )

    assert resultat["status"] == "verification_humaine"
    assert resultat["sources"] == []


def test_agent_demande_sans_creation(monkeypatch):
    monkeypatch.setattr("app.agent.APP_MODE", "simulation")

    def creation_interdite(*args, **kwargs):
        raise AssertionError("Aucune demande ne doit être créée.")

    monkeypatch.setattr("app.agent.creer_demande", creation_interdite)

    resultat = generate_answer(
        "Je souhaite obtenir une attestation de scolarité."
    )

    assert resultat["status"] == "repondu"
    assert "simulation" in resultat["answer"].lower()


def test_agent_reconnait_demande_calcul(monkeypatch):
    monkeypatch.setattr("app.agent.APP_MODE", "simulation")

    resultat = generate_answer(
        "Calcule ma moyenne avec mes notes et coefficients."
    )

    assert resultat["status"] == "repondu"
    assert "calcul" in resultat["answer"].lower()
