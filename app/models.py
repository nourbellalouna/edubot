
from enum import Enum
from pydantic import BaseModel, Field


class Statut(str, Enum):
    REPONDU = "repondu"
    REFUS = "refus"
    VERIFICATION_HUMAINE = "verification_humaine"


class QuestionRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000,
        description="Question posée par l'étudiant"
    )


class CalculRequest(BaseModel):
    notes: list[float]
    coefficients: list[float]


class CalculResponse(BaseModel):
    moyenne: float


class DemandeRequest(BaseModel):
    nom: str = Field(min_length=2)
    type_demande: str
    description: str = Field(min_length=5)


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
    sources: list[str] = []
