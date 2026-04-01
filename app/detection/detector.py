from ultralytics import YOLO


class InstrumentDetector:
    def __init__(self, model_path: str, conf: float = 0.75):
        self.model = YOLO(model_path)
        self.conf = conf
        self.names = self.model.names

    def detect(self, frame):
        return self.model(frame, conf=self.conf, verbose=False)[0]

    def get_label(self, cls_idx: int) -> str:
        if isinstance(self.names, dict):
            return str(self.names.get(cls_idx, cls_idx))
        return str(self.names[cls_idx])