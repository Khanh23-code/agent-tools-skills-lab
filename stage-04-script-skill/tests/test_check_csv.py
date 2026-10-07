"""csv-quality script: thống kê fixture, quá tải theo người, lỗi input/schema/parse exit khác 0, lỗi dữ liệu exit 0."""

import json
import subprocess
import sys

import pytest

import paths

SCRIPT = paths.FIXTURES_DIR / "skills" / "csv-quality" / "scripts" / "check_csv.py"


def run(path, max_hours: float | str | None = 8):
    cmd = [sys.executable, str(SCRIPT), "--input", str(path)]
    if max_hours is not None:
        cmd.extend(["--max-hours", str(max_hours)])
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=10)


def write_csv(tmp_path, text):
    path = tmp_path / "t.csv"
    path.write_text(text, encoding="utf-8")
    return path


def test_fixture_statistics():
    result = run(paths.FIXTURES_DIR / "data" / "tasks.csv", max_hours=8)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["row_count"] == 6
    assert data["missing_owner_count"] == 1
    assert data["invalid_hours_count"] == 1
    assert data["duplicate_id_count"] == 1
    assert data["duplicate_ids"] == ["T02"]
    assert [(i["line"], i["column"], i["type"]) for i in data["issues"]] == [
        (4, "owner", "missing_owner"),
        (5, "hours", "invalid_hours"),
        (6, "task_id", "duplicate_id"),
    ]
    assert "total_hours" not in data
    assert data["max_hours"] == 8
    assert "hours_by_owner" in data
    assert "overloaded_owners" in data
    assert "excluded_rows" in data


@pytest.mark.parametrize("hours", ["NaN", "nan", "Infinity", "-inf", "-1", ""])
def test_non_finite_negative_or_empty_hours_rejected(tmp_path, hours):
    data = json.loads(run(write_csv(tmp_path, f"task_id,owner,hours\nT01,Lan,{hours}\n"), max_hours=8).stdout)
    assert data["invalid_hours_count"] == 1
    assert data["issues"][0]["line"] == 2


def test_clean_data_exit_0_without_issues(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,4\nT02,Minh,2.5\n"), max_hours=8)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["issues"] == []
    assert data["hours_by_owner"] == {"Lan": 4, "Minh": 2.5}
    assert data["overloaded_owners"] == []
    assert data["excluded_rows"] == []


def test_missing_max_hours_exit_nonzero(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,4\n"), max_hours=None)
    assert result.returncode != 0
    assert result.stdout == ""


@pytest.mark.parametrize("bad_max_hours", ["-1", "-0.1", "abc", "NaN", "nan", "Infinity", "-inf"])
def test_invalid_max_hours_exit_nonzero(tmp_path, bad_max_hours):
    result = run(write_csv(tmp_path, "task_id,owner,hours\nT01,Lan,4\n"), max_hours=bad_max_hours)
    assert result.returncode != 0
    assert result.stdout == ""
    assert "max-hours" in result.stderr


def test_missing_file_exit_1(tmp_path):
    result = run(tmp_path / "khong-co.csv", max_hours=8)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "Không đọc được file" in result.stderr


def test_missing_column_exit_1(tmp_path):
    result = run(write_csv(tmp_path, "task_id,owner\nT01,Lan\n"), max_hours=8)
    assert result.returncode == 1
    assert "Thiếu cột bắt buộc: hours" in result.stderr


def test_parse_error_exit_1(tmp_path):
    result = run(write_csv(tmp_path, 'task_id,owner,hours\nT01,"La"n,4\n'), max_hours=8)
    assert result.returncode == 1
    assert "Lỗi parse CSV" in result.stderr


def test_script_does_not_modify_input():
    source = paths.FIXTURES_DIR / "data" / "tasks.csv"
    before = source.read_bytes()
    run(source, max_hours=8)
    assert source.read_bytes() == before


def test_workload_threshold_8_and_9():
    workload_path = paths.FIXTURES_DIR / "data" / "workload.csv"
    # Ngưỡng 8: Lan 9h (quá tải), Minh 3h (không quá tải)
    res8 = run(workload_path, max_hours=8)
    assert res8.returncode == 0, res8.stderr
    data8 = json.loads(res8.stdout)
    assert data8["hours_by_owner"] == {"Lan": 9, "Minh": 3}
    assert data8["overloaded_owners"] == [{"owner": "Lan", "total_hours": 9}]
    assert data8["excluded_rows"] == [
        {"line": 5, "task_id": "T04", "reasons": ["invalid_hours"]},
        {"line": 6, "task_id": "T02", "reasons": ["duplicate_id"]},
        {"line": 7, "task_id": "T05", "reasons": ["missing_owner"]},
    ]

    # Ngưỡng 9: Lan 9h (bằng ngưỡng -> không quá tải), Minh 3h
    res9 = run(workload_path, max_hours=9)
    assert res9.returncode == 0, res9.stderr
    data9 = json.loads(res9.stdout)
    assert data9["hours_by_owner"] == {"Lan": 9, "Minh": 3}
    assert data9["overloaded_owners"] == []
    assert data9["excluded_rows"] == data8["excluded_rows"]


def test_first_occurrence_invalid_hours_not_replaced_by_later_occurrence():
    """Trường hợp đặc biệt: lần xuất hiện đầu tiên của ID có hours không hợp lệ.
    Dòng 2: E01,Lan,abc -> loại vì invalid_hours.
    Dòng 3: E01,Lan,5   -> loại vì duplicate_id.
    Dòng 4: E02,Minh,0  -> hợp lệ (0 giờ).
    Chỉ Minh có 0 giờ; Lan không được tính; không ai quá tải với ngưỡng 0.
    """
    edge_path = paths.FIXTURES_DIR / "data" / "workload-edge.csv"
    res = run(edge_path, max_hours=0)
    assert res.returncode == 0, res.stderr
    data = json.loads(res.stdout)
    assert data["max_hours"] == 0
    assert data["hours_by_owner"] == {"Minh": 0}
    assert "Lan" not in data["hours_by_owner"]
    assert data["overloaded_owners"] == []
    assert data["excluded_rows"] == [
        {"line": 2, "task_id": "E01", "reasons": ["invalid_hours"]},
        {"line": 3, "task_id": "E01", "reasons": ["duplicate_id"]},
    ]
