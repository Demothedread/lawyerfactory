from lawyerfactory.compose.maestro.prewriting_packets import (
    PREWRITING_DELIVERABLE_IDS,
    to_user_review_packet,
)


def test_prewriting_review_packet_has_three_deliverables():
    packet = to_user_review_packet()

    assert packet["deliverable_count"] == 3
    assert packet["ready_for_user_review"] is True
    ids = [item["deliverable_id"] for item in packet["deliverables"]]
    assert tuple(ids) == PREWRITING_DELIVERABLE_IDS
