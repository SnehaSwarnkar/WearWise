"""
WearWise Anthropometry Evaluation Port Protocol
Abstract domain port for extracting physical anthropometric measurements from candidate AvatarShapeSpecs.
"""

from typing import Protocol, List, Dict
from app.domain.entities.avatar import AvatarShapeSpec


class AnthropometryEvaluationPort(Protocol):
    """
    Abstract domain port for extracting physical anthropometric measurements
    from a candidate AvatarShapeSpec.
    
    Used by BICE regularized solver to evaluate measurement residuals without
    coupling to 3D geometry processing internals.
    """
    def extract_candidate_measurements(
        self,
        shape_spec: AvatarShapeSpec,
        measurement_codes: List[str]
    ) -> Dict[str, float]:
        """
        Computes physical dimensions in CENTIMETERS for the requested canonical codes.
        """
        ...
