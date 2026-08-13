from tars_core.application.classify_statement import ClassifyStatementUseCase
from tars_core.domain.connection import Engine
from tars_core.infrastructure.sql_classifier import SqlglotClassifier


def test_delegates_to_the_configured_classifier() -> None:
    use_case = ClassifyStatementUseCase(classifier=SqlglotClassifier())

    assert use_case.execute("SELECT * FROM film", engine=Engine.POSTGRESQL) is False
    assert use_case.execute("DELETE FROM film", engine=Engine.POSTGRESQL) is True
