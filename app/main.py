import cv2

from app.config import CAMERA_INDEX, CONFIDENCE, WINDOW_TITLE, find_model_path
from app.data.instrument_info import INSTRUMENT_INFO
from app.analysis.label_utils import normalize_label
from app.analysis.appearance import (
    crop_from_box,
    extract_dominant_color,
    classify_wood_tone,
    choose_texture_profile,
)
from app.detection.detector import InstrumentDetector
from app.ar.overlay import draw_detection_overlay
from app.rendering.oud_renderer import (
    show_oud_composition_view,
    close_oud_window,
    try_open_blender_file,
)


def main():
    try:
        model_path = find_model_path()
    except FileNotFoundError as e:
        print(e)
        return

    print(f"[INFO] Modèle utilisé : {model_path}")

    detector = InstrumentDetector(str(model_path), conf=CONFIDENCE)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("Erreur : impossible d’ouvrir la caméra.")
        return

    print("[INFO] Appuie sur 'q' pour quitter.")
    print("[INFO] Appuie sur 'b' pour ouvrir le fichier Blender du oud.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erreur : impossible de lire l’image caméra.")
            break

        raw_frame = frame.copy()
        results = detector.detect(raw_frame)

        oud_found = False

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])

            raw_label = detector.get_label(cls)
            label = normalize_label(raw_label)
            info_text = INSTRUMENT_INFO.get(label, "Description non disponible.")

            wood_tone = None
            texture_profile = None
            dominant_color = None

            if label == "oud":
                crop = crop_from_box(raw_frame, x1, y1, x2, y2)
                dominant_color = extract_dominant_color(crop)
                wood_tone = classify_wood_tone(dominant_color)
                texture_profile = choose_texture_profile(wood_tone)

                show_oud_composition_view(wood_tone, texture_profile, dominant_color)
                oud_found = True

            frame = draw_detection_overlay(
                frame=frame,
                label=label,
                info_text=info_text,
                box=(x1, y1, x2, y2),
                wood_tone=wood_tone,
                texture_name=texture_profile["name"] if texture_profile else None,
                dominant_color=dominant_color,
            )

        if not oud_found:
            close_oud_window()

        cv2.imshow(WINDOW_TITLE, frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break
        elif key == ord("b"):
            try_open_blender_file()

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()