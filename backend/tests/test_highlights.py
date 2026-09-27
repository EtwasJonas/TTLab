import pytest

from app.rally_detection import RallyDetector


@pytest.fixture
def detector():
    return RallyDetector()


class TestClassifyHighlight:
    def test_exactly_min_duration_is_highlight(self, detector):
        is_hl, score = detector.classify_highlight(duration=10.0, impact_count=5, score=0.5, max_score=1.0)
        assert is_hl is True
        assert score == pytest.approx(10.0 / 15.0, abs=1e-3)

    def test_just_below_min_duration(self, detector):
        is_hl, _ = detector.classify_highlight(duration=9.99, impact_count=5, score=0.5, max_score=1.0)
        assert is_hl is False

    def test_exactly_min_impacts_is_highlight(self, detector):
        is_hl, score = detector.classify_highlight(duration=5.0, impact_count=24, score=0.5, max_score=1.0)
        assert is_hl is True
        assert score == pytest.approx(24.0 / 30.0, abs=1e-3)

    def test_just_below_min_impacts(self, detector):
        is_hl, _ = detector.classify_highlight(duration=5.0, impact_count=23, score=0.5, max_score=1.0)
        assert is_hl is False

    def test_exactly_score_ratio_is_highlight(self, detector):
        # score == 0.9 * max_score (Grenzwert inklusive)
        is_hl, score = detector.classify_highlight(duration=5.0, impact_count=5, score=0.90, max_score=1.0)
        assert is_hl is True
        assert score == pytest.approx(0.9, abs=1e-3)

    def test_just_below_score_ratio(self, detector):
        is_hl, _ = detector.classify_highlight(duration=5.0, impact_count=5, score=0.89, max_score=1.0)
        assert is_hl is False

    def test_zero_max_score_never_triggers_ratio(self, detector):
        # max_score = 0 (z.B. einziges, schwaches Rally) darf keinen
        # Highlight-Status erzeugen
        is_hl, score = detector.classify_highlight(duration=5.0, impact_count=5, score=0.0, max_score=0.0)
        assert is_hl is False
        assert score == 0.0

    def test_highlight_score_capped_at_1(self, detector):
        is_hl, score = detector.classify_highlight(duration=60.0, impact_count=5, score=0.5, max_score=1.0)
        assert is_hl is True
        assert score == 1.0

    def test_best_rally_of_video_is_highlight(self, detector):
        # Das beste Rally eines Videos liegt per Definition bei score == max_score
        is_hl, _ = detector.classify_highlight(duration=5.0, impact_count=5, score=0.7, max_score=0.7)
        assert is_hl is True

    def test_boring_rally(self, detector):
        is_hl, score = detector.classify_highlight(duration=3.0, impact_count=6, score=0.2, max_score=1.0)
        assert is_hl is False
        assert score == 0.0
