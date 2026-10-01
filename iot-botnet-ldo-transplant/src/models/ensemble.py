"""Prototype ensemble for the IoT botnet detection project."""

from sklearn.ensemble import (
    ExtraTreesClassifier,
    GradientBoostingClassifier,
    RandomForestClassifier,
    VotingClassifier,
)


def build_ensemble(random_state=42):
    """Create a soft-voting ensemble of three classifiers."""

    random_forest = RandomForestClassifier(
        n_estimators=50,
        random_state=random_state,
        n_jobs=-1,
    )

    extra_trees = ExtraTreesClassifier(
        n_estimators=50,
        random_state=random_state,
        n_jobs=-1,
    )

    gradient_boosting = GradientBoostingClassifier(
        n_estimators=50,
        max_depth=5,
        random_state=random_state,
    )

    model = VotingClassifier(
        estimators=[
            ("random_forest", random_forest),
            ("extra_trees", extra_trees),
            ("gradient_boosting", gradient_boosting),
        ],
        voting="soft",
    )

    return model