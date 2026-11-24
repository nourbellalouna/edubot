# EduBot – Assistant intelligent pour étudiants

## 1. Présentation du projet

EduBot est un assistant intelligent destiné aux étudiants. Il permet de répondre aux questions liées à la vie universitaire, de rechercher des informations dans les documents de l'établissement, de calculer des moyennes et de créer des demandes administratives.

Le projet utilise un modèle de langage accessible via l'API Groq, avec une architecture basée sur FastAPI.

L'étudiant peut poser ses questions par écrit ou envoyer un enregistrement audio. Dans ce dernier cas, le système utilise Whisper pour convertir la question vocale en texte et générer une réponse écrite.

## 2. Objectifs

- Répondre aux questions des étudiants.
- Fournir des informations à partir des documents disponibles.
- Calculer les moyennes pondérées.
- Accompagner les étudiants dans leurs demandes administratives.
- Traiter les questions audio et fournir des réponses écrites.
- Refuser ou transmettre à une vérification humaine les questions auxquelles le système ne peut pas répondre de manière fiable.

## 3. Technologies utilisées

- Python
- FastAPI
- Pydantic
- Groq API
- Uvicorn
- Pytest
- JSON
- OpenAI Whisper
- FFmpeg
- RAG (Retrieval-Augmented Generation)

## 4. Architecture du projet

```text
edubot/
│
├── app/
│   ├── main.py
│   ├── agent.py
│   ├── models.py
│   ├── rag.py
│   │
│   └── tools/
│       ├── calcul.py
│       ├── demande.py
│       └── recherche.py
│
├── data/
│   └── demandes.json
│
├── documents/
│   └── reglement.txt
│
├── evaluation/
│   ├── dataset.json
│   ├── evaluer.py
│   ├── evaluer_rag.py
│   ├── diagnostiquer.py
│   ├── comparer_prompts.py
│   ├── resultats.json
│   ├── resultats_rag.json
│   └── comparaison_prompts.json
│
├── tests/
│   └── test_tools.py
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## 5. Installation

### Cloner le projet

```bash
git clone URL_DU_DEPOT
cd edubot
```

Remplacer `URL_DU_DEPOT` par l'adresse réelle du dépôt Git.

### Créer un environnement virtuel

```bash
python -m venv .venv
```

### Activer l'environnement virtuel

Sous Linux / WSL :

```bash
source .venv/bin/activate
```

### Installer les dépendances

```bash
pip install -r requirements.txt
```

### Installer FFmpeg

FFmpeg est nécessaire au traitement des fichiers audio avec Whisper.

Sous Ubuntu / WSL :

```bash
sudo apt update
sudo apt install ffmpeg
```

## 6. Configuration

Créer un fichier `.env` à la racine du projet.

Ajouter les paramètres suivants :

```env
GROQ_API_KEY=votre_cle_api
MODEL_NAME=openai/gpt-oss-20b
APP_MODE=real
```

Remplacer `votre_cle_api` par une clé API Groq valide.

Pour utiliser le mode simulation :

```env
APP_MODE=simulation
```

Ne jamais publier le fichier `.env` ou sa clé API sur GitHub.

## 7. Lancement de l'application

Depuis le dossier principal :

```bash
uvicorn app.main:app --reload
```

L'API sera accessible à l'adresse :

http://127.0.0.1:8000

Documentation interactive Swagger :

http://127.0.0.1:8000/docs

Les différentes fonctionnalités peuvent être testées directement depuis Swagger.

## 8. Fonctionnalités de l'API

### 8.1 Accueil

**Méthode :** GET

**Route :** `/`

Vérifie que l'API fonctionne.

### 8.2 Poser une question écrite

**Méthode :** POST

**Route :** `/question`

Exemple :

```json
{
  "question": "Quels documents faut-il fournir pour une inscription ?"
}
```

L'agent analyse la question et utilise les outils disponibles si nécessaire.

### 8.3 Poser une question audio

**Méthode :** POST

**Route :** `/audio`

L'étudiant peut envoyer un fichier audio contenant sa question.

Le système utilise Whisper pour convertir l'enregistrement en texte, puis transmet la question à l'agent.

La réponse est retournée sous forme écrite avec :

- La transcription de la question.
- La réponse générée.
- Le statut de la réponse.
- Les sources utilisées.

Les formats audio acceptés comprennent WAV, MP3, M4A, MP4, WebM, OGG et FLAC.

### 8.4 Calculer une moyenne

**Méthode :** POST

**Route :** `/calculer-moyenne`

Exemple :

```json
{
  "notes": [14, 16, 12],
  "coefficients": [2, 3, 1]
}
```

Le système calcule la moyenne pondérée et vérifie la validité des données.

### 8.5 Rechercher dans les documents

**Méthode :** POST

**Route :** `/rechercher-document`

Exemple :

```json
{
  "question": "Quelle est la moyenne minimale pour valider le semestre ?"
}
```

Le système recherche les informations pertinentes dans les documents disponibles et fournit les sources utilisées.

### 8.6 Créer une demande administrative

**Méthode :** POST

**Route :** `/demandes`

Exemple :

```json
{
  "nom": "Ahmed Ben Ali",
  "type_demande": "demande de stage",
  "description": "Demande de stage pour le semestre prochain."
}
```

La demande est enregistrée dans le fichier JSON après validation des informations.

## 9. Agent intelligent et outils

EduBot dispose de trois outils :

- `calculer_moyenne` : calcule une moyenne pondérée et vérifie les valeurs.
- `rechercher_information` : recherche des informations dans les documents disponibles.
- `creer_demande` : enregistre une demande administrative après une demande explicite de l'étudiant.

Les outils sont décrits avec JSON Schema.

L'agent utilise une boucle limitée à trois tours afin de contrôler les appels aux outils et d'éviter les actions non demandées.

## 10. RAG et recherche documentaire

Le système utilise une approche RAG (Retrieval-Augmented Generation).

Le fonctionnement repose sur trois étapes :

1. Recherche des passages pertinents dans les documents.
2. Transmission du contexte récupéré au modèle.
3. Génération d'une réponse fondée sur les informations disponibles, avec indication des sources.

Si aucune information pertinente n'est trouvée, EduBot peut demander une vérification humaine.

## 11. Évaluation du projet

Le projet dispose d'un dataset de 28 exemples couvrant les questions documentaires, les calculs et les cas nécessitant une vérification humaine.

### Exécution des évaluations

Évaluation générale :

```bash
python evaluation/evaluer.py
```

Évaluation RAG :

```bash
python evaluation/evaluer_rag.py
```

Comparaison des prompts :

```bash
python evaluation/comparer_prompts.py
```

Diagnostic des erreurs :

```bash
python evaluation/diagnostiquer.py
```

### Résultats obtenus

**Évaluation générale :**
- 28 exemples dans le dataset.
- 27 exemples exécutés avec succès.
- 1 exemple ignoré volontairement pour éviter la création réelle d'une demande administrative.
- Taux de réussite : 100 %.

**Temps d'exécution :**
- Moyenne : 1,09 seconde.
- Minimum : 0 seconde.
- Médiane : 0,97 seconde.
- Maximum : 3,57 secondes.

**Évaluation RAG :**
- Recall@1 : 100 %.
- Recall@2 : 100 %.
- Recall@3 : 100 %.

**Comparaison des prompts :**
- Prompt A : 26/26 réussites, soit 100 %.
- Prompt B : 25/26 réussites, soit 96,15 %.

Le Prompt A présente de meilleures réponses et limite davantage les informations non présentes dans les documents.

**Tests automatisés :**
- 12 tests réussis.
- 0 échec.

Les résultats dépendent du dataset et des documents utilisés. Ils ne garantissent pas les mêmes performances sur toutes les questions.

## 12. Tests automatisés

Pour exécuter les tests :

```bash
python -m pytest -v
```

Les tests vérifient notamment le calcul des moyennes, la validation des demandes, la recherche documentaire et le comportement de l'agent.

## 13. Conclusion

EduBot met en pratique plusieurs concepts du Machine Learning appliqué : utilisation d'une API de modèle, validation des réponses, agent avec outils, traitement audio, évaluation sur un dataset et recherche documentaire avec RAG.

Le projet vise à proposer un assistant universitaire capable d'aider les étudiants tout en limitant les réponses non fiables.