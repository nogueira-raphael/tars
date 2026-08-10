from datetime import UTC, datetime

from tars_core.domain.locks import BlockingSession, LockTree, SessionState


def test_session_with_no_blockers_has_an_empty_blocked_by_list() -> None:
    session = BlockingSession(session_id="1", state=SessionState.ACTIVE)

    assert session.blocked_by == []


def test_blocking_chain_is_expressed_as_edges_not_a_nested_tree() -> None:
    blocker = BlockingSession(session_id="1", state=SessionState.ACTIVE)
    blocked = BlockingSession(
        session_id="2",
        state=SessionState.ACTIVE,
        wait_type="Lock:transactionid",
        blocked_by=["1"],
    )
    tree = LockTree(
        connection_id="conn-1", sessions=[blocker, blocked], captured_at=datetime.now(UTC)
    )

    blocked_ids = {s.session_id for s in tree.sessions if s.blocked_by}

    assert blocked_ids == {"2"}
    assert tree.sessions[1].blocked_by == ["1"]


def test_a_session_can_be_blocked_by_more_than_one_other_session() -> None:
    # A flat edge list — unlike a literal tree — doesn't break on this case.
    session = BlockingSession(session_id="3", state=SessionState.ACTIVE, blocked_by=["1", "2"])

    assert session.blocked_by == ["1", "2"]
