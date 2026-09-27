"""Szenarien für _strip_bounce_tail (Bounce-Decay-Filter, V0.5).

Konfiguration (RallyDetector.__init__):
    bounce_height_decay=0.95, bounce_interval_decay=0.85, bounce_entry_ratio=0.9

Muster:
- Ausklingender Ball (aufheben/über den Tisch werfen): Lautstärke UND
  Abstände schrumpfen mit jedem Aufprall -> Ende wird abgeschnitten.
- Echte Rally: gleichbleibende Abstände, alternierende Lautstärke
  (Schlag laut, Platten-Bounce leise) -> wird nie beschnitten.
"""
import pytest

from app.rally_detection import RallyDetector


@pytest.fixture
def detector():
    return RallyDetector()


def check_unchanged(detector, times, heights):
    t, h, trimmed = detector._strip_bounce_tail(list(times), list(heights))
    return t == list(times) and h == list(heights) and trimmed is False


class TestStripBounceTail:
    def test_pure_bounce_discards_whole_group(self, detector):
        # Ball fällt aus: Lautstärke 1.0 -> 0.8 -> 0.6 -> 0.4, Abstände schrumpfen
        times = [10.0, 10.5, 10.9, 11.2, 11.4]
        heights = [1.0, 0.8, 0.6, 0.4, 0.2]
        t, h, trimmed = detector._strip_bounce_tail(times, heights)
        assert trimmed is True
        assert t == [] and h == []

    def test_rally_with_bounce_tail_is_trimmed(self, detector):
        # 4 echte Schläge (gleichbleibend laut), danach fällt der Ball aus
        times = [0.0, 0.8, 1.6, 2.4, 3.0, 3.35, 3.6, 3.75]
        heights = [1.0, 0.9, 1.0, 0.9, 0.5, 0.4, 0.3, 0.2]
        t, h, trimmed = detector._strip_bounce_tail(times, heights)
        assert trimmed is True
        # Der 4. Schlag (0.9) liegt genau auf der Entry-Ratio-Grenze
        # (0.9 <= 0.9 * 1.0) und wird schon als Bounce-Ende gewertet
        assert t == [0.0, 0.8, 1.6]
        assert h == [1.0, 0.9, 1.0]

    def test_loud_hit_before_tail_is_kept(self, detector):
        # Der letzte LAUTE Schlag gehört noch zur Rally, nur die Bounces
        # danach werden abgeschnitten
        times = [0.0, 0.8, 1.6, 2.4, 2.9, 3.25, 3.5]
        heights = [1.0, 0.9, 1.0, 1.0, 0.5, 0.4, 0.3]
        t, h, trimmed = detector._strip_bounce_tail(times, heights)
        assert trimmed is True
        # Mindestens die ersten Schläge + optional der letzte laute Schlag
        assert t[:3] == [0.0, 0.8, 1.6]
        assert len(t) in (3, 4)

    def test_real_rally_not_trimmed(self, detector):
        # Gleichbleibende Abstände, alternierende Lautstärke
        times = [0.0, 0.8, 1.6, 2.4, 3.2, 4.0]
        heights = [1.0, 0.5, 1.0, 0.5, 1.0, 0.5]
        assert check_unchanged(detector, times, heights)

    def test_steady_gaps_growing_loudness_not_trimmed(self, detector):
        # Lauter werdende Schläge (Spieler kommt näher) sind kein Bounce
        times = [0.0, 0.5, 1.0, 1.5, 2.0]
        heights = [0.3, 0.5, 0.7, 0.9, 1.0]
        assert check_unchanged(detector, times, heights)

    def test_short_group_not_trimmed(self, detector):
        # < 3 Impacts = kein Bounce-Muster möglich
        assert check_unchanged(detector, [0.0, 0.5], [1.0, 0.1])
        assert check_unchanged(detector, [0.0], [1.0])

    def test_constant_loudness_not_trimmed(self, detector):
        # Schrumpfende Abstände, aber GLEICHE Lautstärke -> kein Bounce
        # (Höhen-Decay 0.95 verlangt striktes Schrumpfen)
        times = [0.0, 0.8, 1.4, 1.8, 2.1]
        heights = [0.5, 0.5, 0.5, 0.5, 0.5]
        assert check_unchanged(detector, times, heights)

    def test_input_lists_not_mutated(self, detector):
        times = [10.0, 10.5, 10.9, 11.2]
        heights = [1.0, 0.8, 0.6, 0.4]
        t_in, h_in = list(times), list(heights)
        detector._strip_bounce_tail(times, heights)
        assert times == t_in and heights == h_in
