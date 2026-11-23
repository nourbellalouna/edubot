
from fastapi import FastAPI, HTTPException
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


@app.post("/calculer-moyenne", response_model=CalculResponse)
def calculer(request: CalculRequest):
    try:
        moyenne = calculer_moyenne(request.notes, request.coefficients)
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
