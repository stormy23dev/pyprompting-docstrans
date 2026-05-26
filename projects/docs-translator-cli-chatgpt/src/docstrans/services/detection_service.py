from __future__ import annotations

from docstrans.api.client import LibreTranslateClient


class DetectionService:
    def __init__(self, client: LibreTranslateClient) -> None:
        self.client = client

    def detect(self, text: str) -> dict:
        detections, _, _ = self.client.detect(text)
        best = detections[0] if detections else {"language": "unknown", "confidence": 0.0}
        return {"best": best, "detections": detections}
