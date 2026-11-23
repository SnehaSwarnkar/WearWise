"""
WearWise Anthropometry Evaluation Port Implementation
Provides candidate anthropometric measurements to BICE solver without leaking geometry internals.
"""

from dataclasses import asdict
from typing import List, Dict, Optional
from app.domain.entities.avatar import AvatarShapeSpec
from app.domain.interfaces.avatar import AvatarEngine
from app.domain.interfaces.anthropometry import AnthropometryEvaluationPort
from app.anthropometry.engine import AnthropometryEngine
from app.anthropometry.exceptions import AnthropometryError


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
        Explicitly raises AnthropometryError if any requested measurement fails or is missing.
        """
        mesh = self._avatar_engine.generate_avatar(shape_spec)
        # Explicitly associate landmark provider with the generated candidate mesh
        lp = self._avatar_engine.get_landmark_provider(mesh=mesh)
        res = self._anthropometry_engine.extract_all(
            mesh, lp, avatar_id="bice_candidate", measurement_codes=measurement_codes
        )
        results: Dict[str, float] = {}
        failed_codes: List[str] = []

        for code in measurement_codes:
            rec = res.records.get(code)
            if rec is None or rec.measurement is None or rec.diagnostic.status_code != "SUCCESS":
                failed_codes.append(code)
            else:
                results[code] = float(rec.measurement.value_cm)

        if failed_codes:
            raise AnthropometryError(
                f"Candidate anthropometry evaluation failed for requested measurement code(s): {failed_codes}",
                details={"failed_codes": failed_codes, "shape_spec": asdict(shape_spec)},
            )

        return results
