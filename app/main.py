
import os
import tempfile
from pathlib import Path
from functools import lru_cache

import whisper

from fastapi import FastAPI, HTTPException, UploadFile, File

from app.models import (
    QuestionRequest,
    ReponseResponse,
    Statut,
    CalculRequest,
    CalculResponse,
    DemandeRequest,
    DemandeResponse
)

from app.agent import generate_answer
from app.tools.calcul import calculer_moyenne
from app.rag import repondre_avec_documents
from app.tools.demande import creer_demande


app = FastAPI(
    title="EduBot",
    description="Assistant intelligent pour étudiants",
    version="1.0.0"
)


@lru_cache(maxsize=1)
def charger_modele_whisper():
    return whisper.load_model("base")


@app.get("/")
def accueil():
    return {
        "message": "Bienvenue sur EduBot",
        "status": "API en fonctionnement"
    }


@app.post("/question", response_model=ReponseResponse)
def poser_question(request: QuestionRequest):
    try:
        resultat = generate_answer(request.question)

        return ReponseResponse(
            answer=resultat["answer"],
            status=Statut(resultat["status"]),
            sources=resultat.get("sources", [])
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Une erreur est survenue lors du traitement de la question."
        )


@app.post("/audio")
async def poser_question_audio(file: UploadFile = File(...)):
    extensions_autorisees = [
        ".wav", ".mp3", ".m4a", ".mp4",
        ".mpeg", ".mpga", ".webm", ".ogg", ".flac"
    ]

    extension = Path(file.filename or "").suffix.lower()

    if extension not in extensions_autorisees:
        raise HTTPException(
            status_code=400,
            detail="Format audio non autorisé."
        )

    contenu = await file.read()

    if not contenu:
        raise HTTPException(
            status_code=400,
            detail="Le fichier audio est vide."
        )

    if len(contenu) > 15 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Le fichier audio ne doit pas dépasser 15 Mo."
        )

    chemin_temporaire = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False
        ) as fichier:
            fichier.write(contenu)
            chemin_temporaire = fichier.name

        modele = charger_modele_whisper()

        resultat_audio = modele.transcribe(
            chemin_temporaire,
            language="fr"
        )

        transcription = resultat_audio["text"].strip()

        if not transcription:
            raise HTTPException(
                status_code=400,
                detail="Aucune question n'a été détectée."
            )

        resultat = generate_answer(transcription)

        return {
            "transcription": transcription,
            "answer": resultat["answer"],
            "status": resultat["status"],
            "sources": resultat.get("sources", [])
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Une erreur est survenue lors du traitement audio."
        )

    finally:
        if chemin_temporaire and os.path.exists(chemin_temporaire):
            os.remove(chemin_temporaire)


@app.post("/calculer-moyenne", response_model=CalculResponse)
def calculer(request: CalculRequest):
    try:
        moyenne = calculer_moyenne(
            request.notes,
            request.coefficients
        )

        return CalculResponse(moyenne=moyenne)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/rechercher-document", response_model=ReponseResponse)
def rechercher_document(request: QuestionRequest):
    try:
        resultat = repondre_avec_documents(request.question)

        return ReponseResponse(
            answer=resultat["answer"],
            status=Statut(resultat["status"]),
            sources=resultat["sources"]
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Une erreur est survenue lors de la recherche."
        )


@app.post("/demandes", response_model=DemandeResponse)
def ajouter_demande(request: DemandeRequest):
    try:
        resultat = creer_demande(
            request.nom,
            request.type_demande,
            request.description
        )

        return DemandeResponse(**resultat)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
