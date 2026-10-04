"""Tests für das Rally-Gate (rally_gate_flag, V0.6).

Erkennt reine Ball-Behandlung (Hüpfen/Drosseln vor dem Aufschlag, Ball über
den Tisch werfen) über die ML-Ballpositionen: echte Rallys bewegen den Ball
über den ganzen Tisch, Handling hält ihn lokal. thresholds aus der
Ground-Truth-Messung (Matches 2/5/7, siehe PROJEKTUEBERGABE).
"""
import pytest

from app.ball_detector import HeuristicBallDetector
from app.rally_detection import RallyDetector, rally_gate_flag


def pos(xs):
    return [(x, 0.5) for x in xs]


class TestRallyGateFlag:
    def test_no_positions_never_flags(self):
        # Heuristik: keine Positionen -> Gate inaktiv (Bit-Identität)
        assert rally_gate_flag([0.0, 0.5, 1.0], None) is False

    def test_local_ball_high_hit_ratio_flags(self):
        # Hüpfen: Ball bewegt sich kaum (x_range < 0.12), wird bei vielen
        # Peaks gefunden (ratio >= 0.4)
        positions = pos([0.50, 0.52, 0.51, 0.50, 0.53])
        times = [0.0, 0.5, 1.0, 1.5, 2.0]
        assert rally_gate_flag(times, positions) is True

    def test_wide_ball_flight_does_not_flag(self):
        # Echte Rally: Ball kreuzt den Tisch
        positions = pos([0.2, 0.6, 0.25, 0.65, 0.3])
        times = [0.0, 0.5, 1.0, 1.5, 2.0]
        assert rally_gate_flag(times, positions) is False

    def test_local_ball_but_low_hit_ratio_does_not_flag(self):
        # Ball kaum gefunden (Ball meist bei den Spielern außerhalb der
        # Platte) -> keine Evidenz, nicht flaggen
        positions = pos([0.50, 0.51, 0.50])
        times = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
        assert rally_gate_flag(times, positions) is False

    def test_zero_positions_short_group_flags(self):
        # Regel B: gar keine Ballposition über der Platte in einer kurzen
        # Gruppe -> verdächtig (Wurf-/Hüpf-Segment neben dem Tisch)
        times = [0.0, 0.5, 1.0, 1.5]
        assert rally_gate_flag(times, []) is True

    def test_zero_positions_long_group_does_not_flag(self):
        # Regel B: >= 10 Peaks ohne Ballposition -> zu riskant, nicht flaggen
        times = [float(i) * 0.5 for i in range(12)]
        assert rally_gate_flag(times, []) is False

    def test_few_positions_does_not_flag(self):
        # 1-2 Positionen: zu wenig Evidenz
        assert rally_gate_flag([0.0, 0.5, 1.0], pos([0.5, 0.51])) is False

    def test_boundary_values(self):
        # Range knapp unter 0.12 -> True (schwelle inklusiv gedacht), drüber -> False
        positions = pos([0.441, 0.56, 0.50])  # range 0.119, ratio 1.0
        assert rally_gate_flag([0.0, 0.5, 1.0], positions) is True
        positions = pos([0.40, 0.56, 0.50])  # range 0.16
        assert rally_gate_flag([0.0, 0.5, 1.0], positions) is False

    def test_empty_group(self):
        assert rally_gate_flag([], []) is False


class TestGateConfig:
    def test_default_mode_is_review(self, monkeypatch):
        monkeypatch.delenv("TTLAB_RALLY_GATE", raising=False)
        detector = RallyDetector()
        assert detector.rally_gate_mode == "review"

    def test_modes_and_invalid(self, monkeypatch):
        monkeypatch.setenv("TTLAB_RALLY_GATE", "reject")
        assert RallyDetector().rally_gate_mode == "reject"
        monkeypatch.setenv("TTLAB_RALLY_GATE", "off")
        assert RallyDetector().rally_gate_mode == "off"
        monkeypatch.setenv("TTLAB_RALLY_GATE", "quatsch")
        assert RallyDetector().rally_gate_mode == "review"


class TestDetectorCapabilities:
    def test_heuristic_provides_no_positions(self):
        assert HeuristicBallDetector.provides_positions is False
