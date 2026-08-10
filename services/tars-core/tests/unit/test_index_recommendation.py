from tars_core.domain.index_recommendation import IndexRecommendation, IndexRecommendationKind
from tars_core.domain.severity import Severity


def test_missing_recommendation_has_no_existing_index_name() -> None:
    rec = IndexRecommendation(
        kind=IndexRecommendationKind.MISSING,
        severity=Severity.WARNING,
        schema_name="public",
        table="film",
        columns=["rating"],
        rationale="frequent filter with no supporting index",
    )

    assert rec.existing_index_name is None


def test_unused_recommendation_names_the_existing_index() -> None:
    rec = IndexRecommendation(
        kind=IndexRecommendationKind.UNUSED,
        severity=Severity.INFO,
        schema_name="public",
        table="film",
        columns=["release_year"],
        existing_index_name="film_release_year_idx",
        rationale="never selected by the planner in the observed workload",
    )

    assert rec.existing_index_name == "film_release_year_idx"
    assert rec.kind is IndexRecommendationKind.UNUSED
