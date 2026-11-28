"""
WearWise Body Intelligence & Calibration Engine (BICE) Package
Transforms body measurements and semantic controls into engine-neutral AvatarShapeSpec.
Enforces deterministic normalization, regional bounds, and geometric locality evaluation.
"""

from app.bice.config import (
    BICE_SPEC_VERSION,
    MAPPING_VERSION,
    METRIC_VERSION,
    NEUTRAL_CONTROL_VALUE,
    NEUTRAL_NORMALIZED_OFFSET,
    MIN_STATURE_CM,
    MAX_STATURE_CM,
    SEMANTIC_CONTROL_SAFE_RANGES,
    PROVISIONAL_REGIONAL_BOUNDS,
    DEFAULT_REGIONAL_BOUNDS,
    IS_PROVISIONAL_BOUNDS,
    BOUNDS_PROVISIONAL_NOTICE,
    TARGET_SIGNAL_THRESHOLD_M,
    MAXIMAL_LOCALITY_PENALTY,
)

from app.bice.exceptions import (
    BICEError,
    BICEValidationError,
    BICEBoundsExceededError,
    BICEInsufficientSignalError,
    BICEConvergenceError,
    BICEConfigurationError,
)

from app.bice.normalizer import (
    normalize_control,
    denormalize_control,
    normalize_controls,
    denormalize_controls,
)

from app.bice.bounds import (
    RegionalBoundsDiagnostic,
    BoundsCheckReport,
    get_regional_axis_bounds,
    check_axis_bound,
    evaluate_regional_bounds,
    validate_regional_bounds,
)

from app.bice.mapping import (
    SemanticMappingRule,
    SEMANTIC_MAPPING_RULES,
    ALL_TARGET_REGIONS,
    map_normalized_to_regional_scales,
    map_regional_scales_to_normalized,
    map_controls_to_regional_scales,
)

from app.bice.validator import (
    VALID_PRESENTATIONS,
    validate_presentation,
    validate_stature,
    validate_controls_input,
    validate_measurements_input,
)

from app.bice.locality import (
    LocalityLossEvaluation,
    compute_rmsr,
    evaluate_locality_from_result,
    LocalityEvaluator,
)

from app.bice.solver import (
    SolverCandidateDiagnostic,
    SolverObjectiveProtocol,
    build_avatar_shape_spec,
    BICEShapeSolver,
)

__all__ = [
    # Config
    "BICE_SPEC_VERSION",
    "MAPPING_VERSION",
    "METRIC_VERSION",
    "NEUTRAL_CONTROL_VALUE",
    "NEUTRAL_NORMALIZED_OFFSET",
    "MIN_STATURE_CM",
    "MAX_STATURE_CM",
    "SEMANTIC_CONTROL_SAFE_RANGES",
    "PROVISIONAL_REGIONAL_BOUNDS",
    "DEFAULT_REGIONAL_BOUNDS",
    "IS_PROVISIONAL_BOUNDS",
    "BOUNDS_PROVISIONAL_NOTICE",
    "TARGET_SIGNAL_THRESHOLD_M",
    "MAXIMAL_LOCALITY_PENALTY",
    # Exceptions
    "BICEError",
    "BICEValidationError",
    "BICEBoundsExceededError",
    "BICEInsufficientSignalError",
    "BICEConvergenceError",
    "BICEConfigurationError",
    # Normalizer
    "normalize_control",
    "denormalize_control",
    "normalize_controls",
    "denormalize_controls",
    # Bounds
    "RegionalBoundsDiagnostic",
    "BoundsCheckReport",
    "get_regional_axis_bounds",
    "check_axis_bound",
    "evaluate_regional_bounds",
    "validate_regional_bounds",
    # Mapping
    "SemanticMappingRule",
    "SEMANTIC_MAPPING_RULES",
    "ALL_TARGET_REGIONS",
    "map_normalized_to_regional_scales",
    "map_regional_scales_to_normalized",
    "map_controls_to_regional_scales",
    # Validator
    "VALID_PRESENTATIONS",
    "validate_presentation",
    "validate_stature",
    "validate_controls_input",
    "validate_measurements_input",
    # Locality
    "LocalityLossEvaluation",
    "compute_rmsr",
    "evaluate_locality_from_result",
    "LocalityEvaluator",
    # Solver
    "SolverCandidateDiagnostic",
    "SolverObjectiveProtocol",
    "build_avatar_shape_spec",
    "BICEShapeSolver",
]
