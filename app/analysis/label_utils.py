def normalize_label(label: str) -> str:
    """
    Normalise le nom de classe renvoyé par YOLO.
    Exemple : outar -> loutar
    """
    label = label.lower().strip()

    mapping = {
        "outar": "loutar",
    }

    return mapping.get(label, label)