# Copyright 2026 Wladimir Esposito (OmniAI / Omni Tech Consulting)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
