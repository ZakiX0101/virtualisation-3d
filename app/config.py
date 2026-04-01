from pathlib import Path
import os

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent

ASSETS_DIR = PROJECT_DIR / "assets"
TEXTURES_DIR = ASSETS_DIR / "textures"
ICONS_DIR = ASSETS_DIR / "icons"

BLENDER_DIR = PROJECT_DIR / "blender"
BLENDER_FILE = BLENDER_DIR / "oud2.blend"

WINDOW_TITLE = "Smart Heritage AR - Detection"
CAMERA_INDEX = 0
CONFIDENCE = 0.75

# Le modèle explicitement voulu en priorité
MODEL_CANDIDATES = [
    PROJECT_DIR / "runs" / "detect" / "train" / "weights" / "best.pt",
]

TEXTURE_PROFILES = {
    "wood_classic": TEXTURES_DIR / "wood_classic.jpg",
    "wood_dark": TEXTURES_DIR / "wood_dark.jpg",
    "wood_honey": TEXTURES_DIR / "wood_honey.jpg",
    "wood_light": TEXTURES_DIR / "wood_light.jpg",
    "wood_reddish": TEXTURES_DIR / "wood_reddish.jpg",
    "wood_walnut": TEXTURES_DIR / "wood_walnut.jpg",
}


def find_model_path() -> Path:
    env_path = os.environ.get("YOLO_MODEL_PATH", "").strip()
    if env_path:
        candidate = Path(env_path).expanduser().resolve()
        if candidate.exists() and candidate.is_file():
            return candidate
        raise FileNotFoundError(
            f"YOLO_MODEL_PATH pointe vers un fichier introuvable : {candidate}"
        )

    for path in MODEL_CANDIDATES:
        if path.exists() and path.is_file():
            return path.resolve()

    raise FileNotFoundError(
        "Aucun modèle YOLO trouvé.\n"
        "Attendu par défaut : runs/detect/train/weights/best.pt\n"
        "Ou définis YOLO_MODEL_PATH vers le bon fichier .pt"
    )