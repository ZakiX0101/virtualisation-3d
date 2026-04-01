from threading import Lock
from copy import deepcopy

DEFAULT_STATE = {
    "visible": False,
    "instrument": None,
    "history": "",
    "wood_tone": "classic_brown",
    "texture_name": "wood_classic.jpg",
    "texture_url": "/assets/textures/wood_classic.jpg",
    "model_url": "/assets/models/oud.glb",
    "parts": [
        {
            "name": "Table",
            "role": "Partie principale visible du oud. Dans ton modèle actuel, elle regroupe le corps principal et le manche."
        },
        {
            "name": "Chevilles",
            "role": "Éléments utilisés pour tendre et accorder les cordes."
        },
        {
            "name": "Strings",
            "role": "Cordes de l’instrument, responsables de la production du son."
        },
    ],
}

_STATE = deepcopy(DEFAULT_STATE)
_LOCK = Lock()


def update_state(**kwargs):
    with _LOCK:
        _STATE.update(kwargs)


def get_state():
    with _LOCK:
        return deepcopy(_STATE)


def reset_state():
    with _LOCK:
        _STATE.clear()
        _STATE.update(deepcopy(DEFAULT_STATE))