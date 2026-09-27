"""Tests für die Spielzonen-Erweiterung (play_zone_polygon).

V0.6 offene Masken-Frage: Die Tischplatten-Maske erfasst den Ball nur bei
Abpunkten - im Flug ist er im Luftraum ÜBER der Platte. play_zone_polygon()
erweitert das Polygon nach oben (faktor × Polygonhöhe) als konvexe Hülle
mit einer nach oben verschobenen Kopie - das folgt der Perspektive des
Tisches und verbreitert die Zone nicht über die Tischkanten hinaus.
"""
import numpy as np
import pytest

from app.rally_detection import play_zone_polygon


def poly(points):
    return np.array(points, dtype=np.int32)


class TestPlayZonePolygon:
    def test_factor_zero_is_identity(self):
        # TTLAB_PLAY_ZONE=0.0 (Default) muss bit-identisch bleiben -
        # exakt dasselbe Array, keine Kopie, keine Umformung.
        polygon = poly([[100, 200], [500, 180], [520, 400], [80, 420]])
        result = play_zone_polygon(polygon, 0.0)
        assert result is polygon

    def test_factor_one_contains_airspace_above_center(self):
        polygon = poly([[100, 200], [500, 200], [500, 400], [100, 400]])
        hull = play_zone_polygon(polygon, 1.0)
        # Punkt eine halbe Tischhöhe über der Plattenmitte muss drin liegen
        above = poly([[300, 100]])
        inside = cv2_point_in_hull(above, hull)
        assert inside

    def test_factor_zero_excludes_airspace(self):
        polygon = poly([[100, 200], [500, 200], [500, 400], [100, 400]])
        hull = play_zone_polygon(polygon, 0.0)
        above = poly([[300, 100]])
        assert not cv2_point_in_hull(above, hull)

    def test_original_corners_still_inside(self):
        polygon = poly([[100, 200], [500, 200], [500, 400], [100, 400]])
        hull = play_zone_polygon(polygon, 1.0)
        for corner in polygon:
            assert cv2_point_in_hull(corner.reshape(1, 2), hull)

    def test_follows_table_tilt(self):
        # Schief gestellter Tisch (Perspektive): rechte Seite höher.
        # Der Luftraum über der HÖHEREN rechten Kante muss enthalten sein,
        # nicht nur der über der linken.
        polygon = poly([[100, 400], [500, 180], [520, 260], [120, 470]])
        hull = play_zone_polygon(polygon, 1.0)
        poly_height = 470 - 180  # 290
        # Punkt direkt über der Mitte der rechten (hohen) Kante, ~0.5 Höhen
        above_right_edge = poly([[505, 180 - poly_height * 0.5]])
        assert cv2_point_in_hull(above_right_edge, hull)

    def test_no_sideways_widening(self):
        polygon = poly([[100, 200], [500, 200], [500, 400], [100, 400]])
        hull = play_zone_polygon(polygon, 1.5)
        # Punkte seitlich neben den Tischkanten (auch in grosser Hoehe)
        # muessen AUSSERHALB bleiben - die Zone ist eine Saeule ueber dem
        # Tisch, kein Trichter.
        assert not cv2_point_in_hull(poly([[50, 100]]), hull)
        assert not cv2_point_in_hull(poly([[550, 100]]), hull)

    def test_negative_and_huge_factors_clamped(self):
        polygon = poly([[0, 0], [10, 0], [10, 10], [0, 10]])
        # Negativ -> 0 -> Identitaet
        assert play_zone_polygon(polygon, -1.0) is polygon
        # > 3 wird auf 3 geklemmt (nimmt zu, bleibt endlich)
        hull3 = play_zone_polygon(polygon, 3.0)
        hull9 = play_zone_polygon(polygon, 9.0)
        assert hull3.shape == hull9.shape
        assert np.array_equal(hull3, hull9)

    def test_result_is_valid_polygon(self):
        polygon = poly([[100, 200], [500, 180], [520, 400], [80, 420]])
        hull = play_zone_polygon(polygon, 1.0)
        assert hull.ndim == 2
        assert hull.shape[1] == 2
        assert len(hull) >= 4  # Huelle eines gestapelten Quads


def cv2_point_in_hull(point, hull):
    """Punkt-in-Polygon via cv2 (konsistent mit der Masken-Nutzung)."""
    import cv2
    mask = np.zeros((600, 700), dtype=np.uint8)
    cv2.fillPoly(mask, [np.asarray(hull, dtype=np.int32)], 255)
    x, y = int(point[0][0]), int(point[0][1])
    return 0 <= x < 700 and 0 <= y < 600 and mask[y, x] == 255
