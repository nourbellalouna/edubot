
def calculer_moyenne(notes: list[float], coefficients: list[float]):

    if len(notes) == 0 or len(notes) != len(coefficients):
        raise ValueError("Les notes et les coefficients sont obligatoires.")

    if any(note < 0 or note > 20 for note in notes):
        raise ValueError("Les notes doivent être comprises entre 0 et 20.")

    if any(coef <= 0 for coef in coefficients):
        raise ValueError("Les coefficients doivent être positifs.")

    somme_coefficients = sum(coefficients)

    moyenne = sum(
        note * coef
        for note, coef in zip(notes, coefficients)
    ) / somme_coefficients

    return round(moyenne, 2)
