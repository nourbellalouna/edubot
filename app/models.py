
import unicodedata
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator


class Statut(str, Enum):
    REPONDU = "repondu"
    REFUS = "refus"
    VERIFICATION_HUMAINE = "verification_humaine"


class TypeDemande(str, Enum):
    ATTESTATION = "attestation de scolarite"
    STAGE = "demande de stage"
    RELEVE = "releve de notes"


class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000,
        description="Question posée par l'étudiant"
    )

    @field_validator("question")
    @classmethod
    def verifier_question(cls, valeur):
        if not valeur.strip():
            raise ValueError("La question ne peut pas être vide.")
        return valeur.strip()


class CalculRequest(BaseModel):
    notes: list[Annotated[float, Field(ge=0, le=20)]] = Field(
        min_length=1
    )
    coefficients: list[Annotated[float, Field(gt=0)]] = Field(
        min_length=1
    )

    @model_validator(mode="after")
    def verifier_listes(self):
        if len(self.notes) != len(self.coefficients):
            raise ValueError(
                "Le nombre de notes doit être égal au nombre de coefficients."
            )
        return self


class CalculResponse(BaseModel):
    moyenne: float = Field(ge=0, le=20)


class DemandeRequest(BaseModel):
    nom: str = Field(min_length=2, max_length=100)
    type_demande: TypeDemande
    description: str = Field(min_length=5, max_length=500)

    @field_validator("nom", "description")
    @classmethod
    def nettoyer_texte(cls, valeur):
        valeur = valeur.strip()
        if not valeur:
            raise ValueError("Ce champ ne peut pas être vide.")
        return valeur

    @field_validator("type_demande", mode="before")
    @classmethod
    def normaliser_type(cls, valeur):
        if isinstance(valeur, str):
            valeur = unicodedata.normalize("NFD", valeur.lower())
            valeur = "".join(
                caractere
                for caractere in valeur
                if unicodedata.category(caractere) != "Mn"
            ).strip()
        return valeur


class DemandeResponse(BaseModel):
    id: int
    nom: str
    type_demande: str
    description: str
    date: str
    statut: str


class ReponseResponse(BaseModel):
    answer: str = Field(max_length=2000)
    status: Statut
    sources: list[str] = Field(default_factory=list)
