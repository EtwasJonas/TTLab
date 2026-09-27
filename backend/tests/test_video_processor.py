"""Unit-Tests für video_processor: _parse_frame_rate + rotate_frame.

get_display_rotation braucht ffprobe + eine echte Videodatei und wird über
die Phase-2-Verifikationsskripte (tests/phase2_verification/) gegen echte
Videos geprüft - hier nur die reinen Funktionen ohne I/O.
"""
import numpy as np
import pytest

from app.video_processor import _parse_frame_rate, rotate_frame


class TestParseFrameRate:
    def test_ntsc_fraction(self):
        assert _parse_frame_rate("30000/1001") == pytest.approx(30000 / 1001, abs=1e-9)
        assert _parse_frame_rate("30000/1001") == pytest.approx(29.97, abs=1e-3)

    def test_simple_integer(self):
        assert _parse_frame_rate("30") == 30.0

    def test_simple_float(self):
        assert _parse_frame_rate("29.97") == pytest.approx(29.97)

    def test_zero_denominator_falls_back(self):
        assert _parse_frame_rate("30/0") == 30.0

    def test_invalid_falls_back(self):
        assert _parse_frame_rate("not_a_rate") == 30.0
        assert _parse_frame_rate("") == 30.0
        assert _parse_frame_rate("abc/def") == 30.0

    def test_no_eval_injection(self):
        # Der alte Code nutzte eval() - hiermit stellt sich die sichere
        # Variante quer: es darf kein Code ausgeführt werden
        assert _parse_frame_rate("__import__('os').system('')") == 30.0


class TestRotateFrame:
    def test_zero_degrees_is_noop_same_object(self):
        frame = np.zeros((4, 6, 3), dtype=np.uint8)
        result = rotate_frame(frame, 0)
        assert result is frame  # keine Kopie -> Bit-Identität garantiert

    def test_90_clockwise(self):
        # Eindeutiges Muster: oben links heller Punkt
        frame = np.zeros((2, 4, 3), dtype=np.uint8)
        frame[0, 0] = 255
        result = rotate_frame(frame, 90)
        assert result.shape == (4, 2, 3)
        # Bei 90° im Uhrzeigersinn wandert der Punkt nach oben rechts
        assert result[0, 1, 0] == 255

    def test_180(self):
        frame = np.zeros((2, 4, 3), dtype=np.uint8)
        frame[0, 0] = 255
        result = rotate_frame(frame, 180)
        assert result.shape == (2, 4, 3)
        assert result[1, 3, 0] == 255

    def test_270(self):
        frame = np.zeros((2, 4, 3), dtype=np.uint8)
        frame[0, 0] = 255
        result = rotate_frame(frame, 270)
        assert result.shape == (4, 2, 3)
        # 270° im Uhrzeigersinn = 90° gegen den Uhrzeigersinn: Punkt nach unten links
        assert result[3, 0, 0] == 255

    def test_full_rotation_roundtrip(self):
        rng = np.random.default_rng(42)
        frame = rng.integers(0, 255, size=(8, 12, 3), dtype=np.uint8)
        out = rotate_frame(rotate_frame(rotate_frame(rotate_frame(frame, 90), 90), 90), 90)
        assert np.array_equal(out, frame)

    def test_360_via_two_180(self):
        rng = np.random.default_rng(7)
        frame = rng.integers(0, 255, size=(5, 9, 3), dtype=np.uint8)
        assert np.array_equal(rotate_frame(rotate_frame(frame, 180), 180), frame)
