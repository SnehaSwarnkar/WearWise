"""
WearWise Anthropometry Evaluation Port Implementation
Provides candidate anthropometric measurements to BICE solver without leaking geometry internals.
"""

from typing import List, Dict, Optional
from app.domain.entities.avatar import AvatarShapeSpec
from app.domain.interfaces.avatar import AvatarEngine
from app.domain.interfaces.anthropometry import AnthropometryEvaluationPort
from app.anthropometry.engine import AnthropometryEngine


class DefaultAnthropometryEvaluationPort(AnthropometryEvaluationPort):
    """
    Concrete evaluation adapter implementing AnthropometryEvaluationPort.
    Coordinates between AvatarEngine and AnthropometryEngine.
    """
    def __init__(
        self,
        avatar_engine: AvatarEngine,
        anthropometry_engine: Optional[AnthropometryEngine] = None,
    ) -> None:
        self._avatar_engine = avatar_engine
        self._anthropometry_engine = anthropometry_engine or AnthropometryEngine()

    def extract_candidate_measurements(
        self,
        shape_spec: AvatarShapeSpec,
        measurement_codes: List[str]
    ) -> Dict[str, float]:
        """
        Generates 3D mesh for shape_spec, extracts candidate physical measurements
        in CENTIMETERS, and returns dictionary mapping code -> value_cm.
        """
        mesh = self._avatar_engine.generate_avatar(shape_spec)
        lp = self._avatar_engine.get_landmark_provider()
        res = self._anthropometry_engine.extract_all(
            mesh, lp, avatar_id="bice_candidate", measurement_codes=measurement_codes
        )
        return {
            code: float(rec.measurement.value_cm)
            for code, rec in res.records.items()
            if rec.diagnostic.status_code == "SUCCESS"
        }
