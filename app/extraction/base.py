from __future__ import annotations

from abc import ABC, abstractmethod

from app.extraction.models import NormativeFacts


class FactExtractor(ABC):
    mode: str

    @abstractmethod
    def extract(self, user_text: str) -> tuple[NormativeFacts, str | None]:
        """
        Returns:
            (facts, raw_model_output)
        """
        raise NotImplementedError
