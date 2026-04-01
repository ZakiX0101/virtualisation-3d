from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent

ASSETS_DIR = PROJECT_DIR / "assets"
TEXTURES_DIR = ASSETS_DIR / "textures"
ICONS_DIR = ASSETS_DIR / "icons"
BLENDER_DIR = PROJECT_DIR / "blender"
BLENDER_FILE = BLENDER_DIR / "oud2.blend"

WINDOW_TITLE = "Smart Heritage AR - Detection"
OUD_WINDOW_TITLE = "Oud Composition View"

CAMERA_INDEX = 0
CONFIDENCE = 0.75

MODEL_CANDIDATES = [
    PROJECT_DIR / "models" / "best.pt",
    PROJECT_DIR / "best.pt",
    PROJECT_DIR / "runs" / "detect" / "train" / "weights" / "best.pt",
    PROJECT_DIR / "runs" / "detect" / "backup" / "best.pt",
]

TEXTURE_PROFILES = {
    "light_brown": TEXTURES_DIR / "wood_light.jpg",
    "classic_brown": TEXTURES_DIR / "wood_classic.jpg",
    "reddish_brown": TEXTURES_DIR / "wood_reddish.jpg",
    "dark_brown": TEXTURES_DIR / "wood_dark.jpg",
}

def find_model_path() -> Path:
    for path in MODEL_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError(
        "Aucun modèle YOLO trouvé.\n"
        "Place ton fichier best.pt dans models/best.pt\n"
        "ou garde-le dans runs/detect/train/weights/best.pt"
    )