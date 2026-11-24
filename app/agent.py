
import os
import json
import re
import unicodedata

from dotenv import load_dotenv
from groq import Groq

from app.tools.calcul import calculer_moyenne, verifier_validation_semestre
from app.tools.recherche import rechercher_information
from app.tools.demande import creer_demande


load_dotenv()

APP_MODE = os.getenv("APP_MODE", "simulation")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-oss-20b")
MAX_TOURS = 3

demande_en_attente = None


PROMPTS = {
    "A": (
        "Tu es EduBot, un assistant intelligent destiné aux étudiants. "
        "Réponds clairement et simplement. "
        "Utilise les outils disponibles lorsque cela est nécessaire. "
        "Pour toute question administrative ou concernant le règlement, "
        "utilise obligatoirement rechercher_information. "
        "Réponds uniquement à partir des résultats de cet outil. "
        "N'invente aucune information. "
        "Si aucun résultat n'est trouvé, demande une vérification humaine. "
        "Ne crée une demande administrative que si l'étudiant le demande explicitement."
    ),

    "B": (
        "Tu es un assistant universitaire nommé EduBot. "
        "Aide les étudiants à obtenir des informations fiables. "
        "Utilise les outils pour les calculs, les recherches et les demandes. "
        "Pour toute question administrative ou concernant le règlement, "
        "utilise obligatoirement rechercher_information. "
        "Ne donne jamais une information non confirmée. "
        "Si la recherche ne retourne aucun résultat, demande une vérification humaine. "
        "Ne crée une demande administrative que si l'étudiant le demande explicitement."
    )
}


outils = [
    {
        "type": "function",
        "function": {
            "name": "calculer_moyenne",
            "description": (
                "Calcule une moyenne pondérée et indique si le semestre "
                "est validé selon le seuil de 10 sur 20."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "notes": {
                        "type": "array",
                        "items": {"type": "number"}
                    },
                    "coefficients": {
                        "type": "array",
                        "items": {"type": "number"}
                    }
                },
                "required": ["notes", "coefficients"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rechercher_information",
            "description": "Recherche une information dans les documents de l'établissement.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "creer_demande",
            "description": "Crée une demande administrative uniquement si l'étudiant le demande explicitement.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nom": {"type": "string"},
                    "type_demande": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["nom", "type_demande", "description"]
            }
        }
    }
]


def executer_outil(nom_outil, arguments):

    if nom_outil == "calculer_moyenne":
        moyenne = calculer_moyenne(
            arguments["notes"],
            arguments["coefficients"]
        )

        decision = verifier_validation_semestre(moyenne)

        return {
            "moyenne": moyenne,
            "decision_semestre": decision
        }

    if nom_outil == "rechercher_information":
        return rechercher_information(arguments["question"])

    if nom_outil == "creer_demande":
        return creer_demande(
            arguments["nom"],
            arguments["type_demande"],
            arguments["description"]
        )

    raise ValueError("Outil inconnu.")


def formuler_reponse_calcul(moyenne, decision):

    if decision == "semestre valide":
        decision_formulee = "semestre validé"
    else:
        decision_formulee = "semestre non validé"

    return {
        "answer": (
            f"Votre moyenne pondérée est de {moyenne}/20.\n"
            f"Décision : {decision_formulee}."
        ),
        "status": "repondu",
        "sources": []
    }


def normaliser_question(texte):

    texte = unicodedata.normalize("NFD", texte.lower())

    return "".join(
        caractere
        for caractere in texte
        if unicodedata.category(caractere) != "Mn"
    )


def detecter_type_demande(question):

    texte = normaliser_question(question)

    types = {
        "attestation de scolarite": [
            "attestation de scolarite",
            "attestation scolaire"
        ],
        "demande de stage": [
            "demande de stage",
            "attestation de stage"
        ],
        "releve de notes": [
            "releve de notes",
            "bulletin de notes"
        ]
    }

    for type_demande, expressions in types.items():
        if any(expression in texte for expression in expressions):
            return type_demande

    return None


def est_demande_explicite(question):

    texte = normaliser_question(question)

    expressions = [
        "je souhaite obtenir",
        "je veux obtenir",
        "je voudrais obtenir",
        "je souhaite faire une demande",
        "je veux faire une demande",
        "je voudrais faire une demande",
        "je souhaite demander",
        "je veux demander",
        "creer une demande",
        "creer ma demande",
        "deposer une demande",
        "faire une demande de"
    ]

    return any(expression in texte for expression in expressions)


def est_type_demande_non_autorise(question):

    texte = normaliser_question(question)

    motifs = [
        r"\bdemande\s+de\s+([a-z]+)",
        r"\bdemande\s+d[' ]([a-z]+)",
        r"\bdemande\s+du\s+([a-z]+)",
        r"\bdemande\s+des\s+([a-z]+)"
    ]

    for motif in motifs:
        resultat = re.search(motif, texte)

        if resultat:
            return True

    return False


def extraire_informations_demande(question):

    nom = None
    description = None

    nom_match = re.search(
        r"\bnom\s*:\s*(.*?)(?=;\s*description\s*:|$)",
        question,
        re.IGNORECASE
    )

    description_match = re.search(
        r"\bdescription\s*:\s*(.*)",
        question,
        re.IGNORECASE
    )

    if nom_match:
        nom = nom_match.group(1).strip().strip(";")

    if description_match:
        description = description_match.group(1).strip()

    if not nom:
        nom_match = re.search(
            r"\bje m'appelle\s+(.+?)(?=\s+et\s+|\s*,|[.;]|$)",
            question,
            re.IGNORECASE
        )

        if nom_match:
            nom = nom_match.group(1).strip()

    if not description and nom:
        description_match = re.search(
            r"\bje m'appelle\s+.+?\s+et\s+(.+)",
            question,
            re.IGNORECASE
        )

        if description_match:
            description = description_match.group(1).strip().strip(" .")

    return nom, description


def reponse_creation_demande(resultat):

    return {
        "answer": (
            "Votre demande a été créée avec succès.\n"
            f"Numéro de demande : {resultat['id']}.\n"
            f"Statut : {resultat['statut']}."
        ),
        "status": "repondu",
        "sources": []
    }


def reponse_type_non_autorise():

    return {
        "answer": (
            "Ce type de demande n'est pas autorisé. "
            "Les demandes disponibles sont : attestation de scolarité, "
            "demande de stage et relevé de notes."
        ),
        "status": "refus",
        "sources": []
    }


def traiter_demande(question):

    global demande_en_attente

    type_demande = detecter_type_demande(question)

    contient_nom = re.search(
        r"\bnom\s*:",
        question,
        re.IGNORECASE
    )

    contient_description = re.search(
        r"\bdescription\s*:",
        question,
        re.IGNORECASE
    )

    contient_identite = re.search(
        r"\bje m'appelle\s+",
        question,
        re.IGNORECASE
    )

    if (
        demande_en_attente is None
        and est_demande_explicite(question)
        and type_demande is None
        and est_type_demande_non_autorise(question)
    ):
        return reponse_type_non_autorise()

    if (
        demande_en_attente is not None
        and est_demande_explicite(question)
        and type_demande is None
        and est_type_demande_non_autorise(question)
    ):
        demande_en_attente = None
        return reponse_type_non_autorise()

    if demande_en_attente is None:

        if not type_demande or not est_demande_explicite(question):
            return None

        demande_en_attente = {
            "type_demande": type_demande
        }

    elif type_demande and est_demande_explicite(question):
        demande_en_attente = {
            "type_demande": type_demande
        }

    elif not contient_nom and not contient_description and not contient_identite:
        return None

    nom, description = extraire_informations_demande(question)

    if not nom or not description:

        message = (
            f"Pour créer votre demande de {demande_en_attente['type_demande']}, "
            "veuillez fournir votre nom complet et une courte description.\n"
            "Exemple : Nom : Ahmed Ben Ali ; "
            "Description : Je souhaite obtenir ce document."
        )

        if APP_MODE == "simulation":
            message = "Le mode simulation est activé. " + message

        return {
            "answer": message,
            "status": "repondu",
            "sources": []
        }

    try:
        resultat = creer_demande(
            nom,
            demande_en_attente["type_demande"],
            description
        )

        demande_en_attente = None

        return reponse_creation_demande(resultat)

    except ValueError as erreur:
        demande_en_attente = None

        return {
            "answer": str(erreur),
            "status": "refus",
            "sources": []
        }


def verifier_calcul_invalide(question):

    question_minuscule = question.lower()

    mots_calcul = [
        "calculer ma moyenne",
        "calcule ma moyenne",
        "calcul de ma moyenne",
        "mes notes",
        "notes et coefficients"
    ]

    if not any(mot in question_minuscule for mot in mots_calcul):
        return None

    parties = re.split(
        r"\bcoefficients?\b",
        question_minuscule,
        maxsplit=1
    )

    if len(parties) != 2:
        return None

    notes = [
        float(nombre.replace(",", "."))
        for nombre in re.findall(r"\d+(?:[.,]\d+)?", parties[0])
    ]

    coefficients = [
        float(nombre.replace(",", "."))
        for nombre in re.findall(r"\d+(?:[.,]\d+)?", parties[1])
    ]

    if not notes or not coefficients:
        return None

    try:
        calculer_moyenne(notes, coefficients)

    except ValueError as erreur:
        return {
            "answer": str(erreur),
            "status": "refus",
            "sources": []
        }

    return None


def repondre_simulation(question):

    resultat_demande = traiter_demande(question)

    if resultat_demande is not None:
        return resultat_demande

    question_minuscule = question.lower()

    mots_calcul = [
        "calculer ma moyenne",
        "calcule ma moyenne",
        "calcul de ma moyenne",
        "mes notes",
        "notes et coefficients"
    ]

    if any(mot in question_minuscule for mot in mots_calcul):

        parties = re.split(
            r"\bcoefficients?\b",
            question_minuscule,
            maxsplit=1
        )

        if len(parties) != 2:
            return {
                "answer": (
                    "Veuillez fournir les notes et leurs coefficients "
                    "pour calculer votre moyenne."
                ),
                "status": "repondu",
                "sources": []
            }

        notes = [
            float(nombre.replace(",", "."))
            for nombre in re.findall(r"\d+(?:[.,]\d+)?", parties[0])
        ]

        coefficients = [
            float(nombre.replace(",", "."))
            for nombre in re.findall(r"\d+(?:[.,]\d+)?", parties[1])
        ]

        if not notes or not coefficients:
            return {
                "answer": (
                    "Veuillez fournir vos notes et leurs coefficients "
                    "pour calculer votre moyenne."
                ),
                "status": "repondu",
                "sources": []
            }

        try:
            moyenne = calculer_moyenne(notes, coefficients)
            decision = verifier_validation_semestre(moyenne)

            return formuler_reponse_calcul(moyenne, decision)

        except ValueError as erreur:
            return {
                "answer": str(erreur),
                "status": "refus",
                "sources": []
            }

    resultats = rechercher_information(question)

    if resultats:
        meilleur_resultat = resultats[0]

        return {
            "answer": meilleur_resultat["texte"],
            "status": "repondu",
            "sources": [meilleur_resultat["source"]]
        }

    return {
        "answer": (
            "Je ne trouve pas cette information dans les documents "
            "disponibles. Veuillez contacter l'administration."
        ),
        "status": "verification_humaine",
        "sources": []
    }


def generate_answer(question: str, version_prompt="A"):

    if version_prompt not in PROMPTS:
        raise ValueError("Version de prompt inconnue.")

    if APP_MODE == "simulation":
        return repondre_simulation(question)

    resultat_demande = traiter_demande(question)

    if resultat_demande is not None:
        return resultat_demande

    resultat_validation = verifier_calcul_invalide(question)

    if resultat_validation:
        return resultat_validation

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("La clé API Groq est manquante.")

    client = Groq(api_key=api_key)

    messages = [
        {
            "role": "system",
            "content": PROMPTS[version_prompt]
        },
        {
            "role": "user",
            "content": question
        }
    ]

    sources = []

    for tour in range(MAX_TOURS):

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=outils,
            tool_choice="auto",
            temperature=0,
            max_completion_tokens=1000
        )

        message = response.choices[0].message

        if not message.tool_calls:

            reponse = message.content or (
                "Je ne peux pas répondre à cette question."
            )

            mots_introuvables = [
                "je n'ai pas trouvé",
                "je n’ai pas trouvé",
                "je ne trouve pas",
                "information introuvable",
                "informations disponibles",
                "vérifier auprès de l'administration",
                "vérification auprès de l'administration"
            ]

            statut = "repondu"

            if any(
                mot in reponse.lower()
                for mot in mots_introuvables
            ):
                statut = "verification_humaine"

            return {
                "answer": reponse,
                "status": statut,
                "sources": list(set(sources))
            }

        messages.append(message.model_dump(exclude_none=True))

        for tool_call in message.tool_calls:

            nom_outil = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            if nom_outil == "creer_demande" and not est_demande_explicite(question):
                contenu_resultat = json.dumps(
                    {
                        "erreur": (
                            "La création d'une demande n'est autorisée "
                            "que si l'étudiant la demande explicitement."
                        )
                    },
                    ensure_ascii=False
                )

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": contenu_resultat
                })

                continue

            try:
                resultat = executer_outil(nom_outil, arguments)

                if nom_outil == "calculer_moyenne":
                    return formuler_reponse_calcul(
                        resultat["moyenne"],
                        resultat["decision_semestre"]
                    )

                if nom_outil == "creer_demande":
                    return reponse_creation_demande(resultat)

                if nom_outil == "rechercher_information":

                    if not resultat:
                        return {
                            "answer": (
                                "Je ne trouve pas cette information dans "
                                "les documents disponibles. "
                                "Veuillez contacter l'administration."
                            ),
                            "status": "verification_humaine",
                            "sources": []
                        }

                    sources.extend(
                        element["source"]
                        for element in resultat
                    )

                contenu_resultat = json.dumps(
                    resultat,
                    ensure_ascii=False
                )

            except ValueError as erreur:

                if nom_outil == "calculer_moyenne":
                    return {
                        "answer": str(erreur),
                        "status": "refus",
                        "sources": []
                    }

                contenu_resultat = json.dumps(
                    {"erreur": str(erreur)},
                    ensure_ascii=False
                )

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": contenu_resultat
            })

    return {
        "answer": (
            "Je n'ai pas pu obtenir une réponse suffisamment fiable. "
            "Veuillez contacter l'administration."
        ),
        "status": "verification_humaine",
        "sources": list(set(sources))
    }
