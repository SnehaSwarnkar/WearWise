"""
Test Suite: BICE Shape Spec Builder & Solver Framework
Verifies shape spec construction, measurement preservation, candidate generation,
diagnostics generation, bounds rejection, and solver candidate admissibility.
"""

from decimal import Decimal
import pytest
from app.bice.solver import (
    build_avatar_shape_spec,
    BICEShapeSolver,
    SolverCandidateDiagnostic,
)
from app.bice.exceptions import (
    BICEValidationError,
    BICEBoundsExceededError,
)
from app.domain.entities.avatar import AvatarShapeSpec, RegionalShapeScale
from app.domain.entities.body import BodyShapeControls, BodyMeasurement
from tests.bice.test_locality import MockDeterministicEvaluationPort


def test_build_avatar_shape_spec_success():
    """Verify build_avatar_shape_spec builds a valid AvatarShapeSpec with default mapping."""
    spec = build_avatar_shape_spec(
        presentation="feminine",
        stature_cm=165.5,
        measurements={
            "stature": 165.5,
            "chest_circumference": 92.0,
            "waist_circumference": 70.0,
            "hip_circumference": 96.0,
        },
        controls=BodyShapeControls(
            shoulder_width=0.45,
            waist_definition=0.70,
            hip_fullness=0.60,
        ),
    )
    assert isinstance(spec, AvatarShapeSpec)
    assert spec.presentation == "feminine"
    assert spec.target_stature_cm == 165.5
    assert spec.target_measurements["chest_circumference"] == 92.0
    assert spec.target_measurements["stature"] == 165.5

    # Check that regional_scales were automatically mapped
    assert "waist_abdomen" in spec.regional_scales
    # waist_definition 0.70 > 0.50 -> negative scale_x in waist_abdomen
    assert spec.regional_scales["waist_abdomen"].scale_x < 0.0


def test_build_avatar_shape_spec_stature_rejection():
    """Verify stature outside [100.0, 230.0] is rejected."""
    with pytest.raises(BICEValidationError):
        build_avatar_shape_spec(
            presentation="neutral",
            stature_cm=95.0,  # Below 100 cm
            measurements={},
            controls=BodyShapeControls(),
        )

    with pytest.raises(BICEValidationError):
        build_avatar_shape_spec(
            presentation="neutral",
            stature_cm=235.0,  # Above 230 cm
            measurements={},
            controls=BodyShapeControls(),
        )


def test_build_avatar_shape_spec_implausible_measurements():
    """Verify anatomically implausible proportions are rejected."""
    # Waist 200 cm, Hip 70 cm -> waist > 2.5 * hip
    with pytest.raises(BICEValidationError):
        build_avatar_shape_spec(
            presentation="masculine",
            stature_cm=175.0,
            measurements={
                "waist_circumference": 200.0,
                "hip_circumference": 70.0,
            },
            controls=BodyShapeControls(),
        )


def test_solver_generate_candidate_valid():
    """Verify BICEShapeSolver generates an accepted candidate for valid inputs."""
    solver = BICEShapeSolver()
    candidate = solver.generate_candidate(
        presentation="masculine",
        stature_cm=180.0,
        measurements={"chest_circumference": 102.0},
        controls={"shoulder_width": 0.55, "thigh_fullness": 0.50},
    )

    assert isinstance(candidate, SolverCandidateDiagnostic)
    assert candidate.is_accepted is True
    assert candidate.rejection_reason is None
    assert candidate.bounds_report.is_valid is True
    assert candidate.shape_spec.target_stature_cm == 180.0


def test_solver_rejects_candidate_exceeding_provisional_bounds():
    """
    Verify candidate is rejected when mapped regional scales violate provisional bounds.
    E.g. thigh_fullness safe range is [0.20, 0.80]. At 0.80, normalized is +1.0.
    With direct mapping, thighs.scale_x is 1.0, but provisional bound for thighs is [-0.50, +0.50]!
    Candidate should be rejected by bounds check!
    """
    solver = BICEShapeSolver()
    candidate = solver.generate_candidate(
        presentation="neutral",
        stature_cm=170.0,
        measurements={},
        controls={"thigh_fullness": 0.80},  # normalized = 1.0, exceeds provisional bound 0.50
    )

    assert candidate.is_accepted is False
    assert "Bounds violation" in candidate.rejection_reason
    assert candidate.bounds_report.is_valid is False
    assert candidate.bounds_report.violations_count >= 1


def test_solver_with_locality_port_rejection():
    """Verify candidate is rejected when injected port returns insufficient target signal."""
    mock_port = MockDeterministicEvaluationPort(
        target_displacement_m=1e-5,  # 0.01 mm (< 0.1 mm)
        non_target_displacements_m={},
        status="insufficient_target_signal",
    )
    solver = BICEShapeSolver(evaluation_port=mock_port)

    candidate = solver.generate_candidate(
        presentation="neutral",
        stature_cm=172.0,
        measurements={},
        controls={"shoulder_width": 0.50},
        target_region="shoulders",
    )

    assert candidate.is_accepted is False
    assert "Locality violation" in candidate.rejection_reason
    assert candidate.locality_evaluation.status == "insufficient_target_signal"
