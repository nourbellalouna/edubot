
from app.tools.recherche import rechercher_information
from app.agent import APP_MODE, MODEL_NAME
from groq import Groq
import os


def repondre_avec_documents(question: str):

    resultats = rechercher_information(question)

    if not resultats:
        return {
            "answer": (
                "Je ne trouve pas cette information dans les documents "
                "disponibles. Veuillez contacter l'administration."
            ),
            "status": "verification_humaine",
            "sources": []
        }

    if APP_MODE == "simulation":
        meilleur_resultat = resultats[0]

        return {
            "answer": meilleur_resultat["texte"],
            "status": "repondu",
            "sources": [meilleur_resultat["source"]]
        }

    contexte = "\n\n".join(
        resultat["texte"]
        for resultat in resultats
    )

    sources = list(set(
        resultat["source"]
        for resultat in resultats
    ))

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("La clé API Groq est manquante.")

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "Tu es EduBot. Réponds uniquement à partir "
                    "du contexte fourni. N'invente aucune information. "
                    "Si le contexte ne permet pas de répondre, "
                    "indique que l'information est indisponible."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Contexte :\n{contexte}\n\n"
                    f"Question : {question}"
                )
            }
        ],
        temperature=0,
        max_completion_tokens=500
    )

    answer = response.choices[0].message.content or ""

    return {
        "answer": answer,
        "status": "repondu",
        "sources": sources
    }
