import json
import os

import pytest

from app import labeling


@pytest.fixture
def datasets_root(tmp_path, monkeypatch):
    monkeypatch.setattr(labeling, "DATASETS_PATH", str(tmp_path))
    return tmp_path


def _make_dataset(name, annotations):
    labeling.create_dataset(name)
    with open(labeling._annotations_path(name), "w", encoding="utf-8") as f:
        json.dump(annotations, f)
    # Raw-Dateien, die save_annotation normalerweise anlegt
    for entry in annotations:
        stem = labeling._frame_stem(entry["match_id"], entry["frame_index"])
        with open(os.path.join(labeling._dataset_images_dir(name), stem + ".jpg"), "wb") as f:
            f.write(b"\xff\xd8fake")
        with open(os.path.join(labeling._dataset_labels_dir(name), stem + ".txt"), "w", encoding="utf-8") as f:
            for bbox in entry.get("bboxes") or []:
                f.write(f"0 {bbox[0]:.6f} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f}\n")


# ---------------------------------------------------------------------------
# Datensatz-Namen (Path-Traversal-Schutz)
# ---------------------------------------------------------------------------

class TestValidateDatasetName:
    def test_valid_names(self):
        for name in ("v1-ml-training", "abc", "a1_b2", "x" * 64):
            assert labeling.validate_dataset_name(name) == name

    def test_rejects_invalid_names(self):
        for name in ("../escape", "..", "Upper", "mit leerzeichen", "äöü", "", "x" * 65, "-nofirst", "_nofirst", "a/b"):
            with pytest.raises(ValueError):
                labeling.validate_dataset_name(name)


# ---------------------------------------------------------------------------
# BBox-Validierung
# ---------------------------------------------------------------------------

class TestValidateBbox:
    def test_valid_bbox(self):
        labeling._validate_bbox([0.5, 0.5, 0.2, 0.2])

    def test_wrong_length(self):
        with pytest.raises(ValueError):
            labeling._validate_bbox([0.5, 0.5, 0.2])

    def test_out_of_range(self):
        with pytest.raises(ValueError):
            labeling._validate_bbox([1.5, 0.5, 0.2, 0.2])
        with pytest.raises(ValueError):
            labeling._validate_bbox([0.5, -0.1, 0.2, 0.2])

    def test_too_small(self):
        with pytest.raises(ValueError):
            labeling._validate_bbox([0.5, 0.5, 0.001, 0.001])

    def test_overhangs_image_edge(self):
        # Box ragt über den linken/rand hinaus (cx - w/2 < 0)
        with pytest.raises(ValueError):
            labeling._validate_bbox([0.05, 0.5, 0.2, 0.2])
        # ... und rechts (cx + w/2 > 1)
        with pytest.raises(ValueError):
            labeling._validate_bbox([0.95, 0.5, 0.2, 0.2])

    def test_non_numeric(self):
        with pytest.raises(ValueError):
            labeling._validate_bbox([0.5, 0.5, "a", 0.2])


# ---------------------------------------------------------------------------
# Altformat-Migration + BOM + defekte Dateien
# ---------------------------------------------------------------------------

class TestReadAnnotations:
    def test_legacy_single_bbox_migrated(self, datasets_root):
        _make_dataset("ds", [
            {"match_id": 2, "frame_index": 10, "bbox": [0.4, 0.4, 0.1, 0.1]},
        ])
        annotations = labeling._read_annotations("ds")
        assert annotations[0]["bboxes"] == [[0.4, 0.4, 0.1, 0.1]]
        assert "bbox" not in annotations[0]
        assert annotations[0]["has_ball"] is True

    def test_legacy_none_bboxes(self, datasets_root):
        _make_dataset("ds", [
            {"match_id": 2, "frame_index": 10, "bboxes": None, "has_ball": True},
        ])
        annotations = labeling._read_annotations("ds")
        assert annotations[0]["bboxes"] == []
        # has_ball wird aus den tatsächlichen Boxen abgeleitet
        assert annotations[0]["has_ball"] is False

    def test_bom_tolerated(self, datasets_root):
        labeling.create_dataset("ds")
        payload = [{"match_id": 2, "frame_index": 1, "bboxes": [[0.5, 0.5, 0.1, 0.1]]}]
        with open(labeling._annotations_path("ds"), "w", encoding="utf-8-sig") as f:
            json.dump(payload, f)
        annotations = labeling._read_annotations("ds")
        assert len(annotations) == 1

    def test_corrupted_json_returns_empty(self, datasets_root):
        _make_dataset("ds", [])
        with open(labeling._annotations_path("ds"), "w", encoding="utf-8") as f:
            f.write("{kein gueltiges json")
        assert labeling._read_annotations("ds") == []

    def test_missing_file_returns_empty(self, datasets_root):
        assert labeling._read_annotations("gibtsnicht") == []


# ---------------------------------------------------------------------------
# Export-Determinismus + Multi-Box
# ---------------------------------------------------------------------------

class TestExportDataset:
    def test_deterministic_split(self, datasets_root):
        annotations = [
            {"match_id": 2, "frame_index": i, "bboxes": [[0.5, 0.5, 0.1, 0.1]]}
            for i in range(20)
        ]
        _make_dataset("ds", annotations)

        result1 = labeling.export_dataset("ds", val_ratio=0.2, seed=42)
        val1 = sorted(os.listdir(os.path.join(labeling.dataset_dir("ds"), "yolo", "images", "val")))
        train1 = sorted(os.listdir(os.path.join(labeling.dataset_dir("ds"), "yolo", "images", "train")))

        result2 = labeling.export_dataset("ds", val_ratio=0.2, seed=42)
        val2 = sorted(os.listdir(os.path.join(labeling.dataset_dir("ds"), "yolo", "images", "val")))
        train2 = sorted(os.listdir(os.path.join(labeling.dataset_dir("ds"), "yolo", "images", "train")))

        assert val1 == val2
        assert train1 == train2
        assert result1["val_frames"] == result2["val_frames"]
        # 20 Frames, val_ratio 0.2 -> 4 val / 16 train, kein Frame in beiden Splits
        assert len(val1) == 4
        assert len(train1) == 16
        assert not set(val1) & set(train1)

    def test_data_yaml_portable(self, datasets_root):
        _make_dataset("ds", [
            {"match_id": 2, "frame_index": 0, "bboxes": [[0.5, 0.5, 0.1, 0.1]]},
            {"match_id": 2, "frame_index": 1, "bboxes": [[0.4, 0.4, 0.1, 0.1]]},
        ])
        labeling.export_dataset("ds")
        with open(os.path.join(labeling.dataset_dir("ds"), "yolo", "data.yaml"), encoding="utf-8") as f:
            yaml_text = f.read()
        assert "path: ." in yaml_text
        assert "nc: 1" in yaml_text
        assert "names: ['ball']" in yaml_text

    def test_multi_box_label_files_copied(self, datasets_root):
        _make_dataset("ds", [
            {"match_id": 2, "frame_index": 0, "bboxes": [
                [0.5, 0.5, 0.1, 0.1],
                [0.2, 0.8, 0.05, 0.05],
            ]},
            {"match_id": 2, "frame_index": 1, "bboxes": []},  # Negativ-Sample
        ])
        labeling.export_dataset("ds")

        yolo_labels = os.path.join(labeling.dataset_dir("ds"), "yolo", "labels")
        contents = {}
        for split in ("train", "val"):
            for fn in os.listdir(os.path.join(yolo_labels, split)):
                with open(os.path.join(yolo_labels, split, fn), encoding="utf-8") as f:
                    contents[fn] = f.read()

        multi = contents["m2_f0.txt"]
        assert multi.count("\n") == 2  # eine Zeile pro Ball
        negativ = contents["m2_f1.txt"]
        assert negativ == ""  # leere Datei = Hintergrund-Bild

    def test_requires_two_frames(self, datasets_root):
        _make_dataset("ds", [
            {"match_id": 2, "frame_index": 0, "bboxes": [[0.5, 0.5, 0.1, 0.1]]},
        ])
        with pytest.raises(ValueError):
            labeling.export_dataset("ds")


class TestDatasetStats:
    def test_stats_counts(self, datasets_root):
        _make_dataset("ds", [
            {"match_id": 2, "frame_index": 0, "bboxes": [[0.5, 0.5, 0.1, 0.1]]},
            {"match_id": 2, "frame_index": 1, "bboxes": []},
            {"match_id": 3, "frame_index": 5, "bboxes": [[0.3, 0.3, 0.1, 0.1]]},
        ])
        stats = labeling.dataset_stats("ds")
        assert stats["total_frames"] == 3
        assert stats["frames_with_ball"] == 2
        assert stats["frames_without_ball"] == 1
        assert stats["exported"] is False
