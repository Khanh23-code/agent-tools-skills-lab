#!/usr/bin/env python3
"""Kiểm tra chất lượng CSV công việc (task_id, owner, hours) và kiểm tra quá tải theo người.

Cách chạy (cwd là workspace):
    python skills/csv-quality/scripts/check_csv.py --input data/workload.csv --max-hours 8

Exit 0: phân tích thành công, kể cả khi dữ liệu có dòng lỗi hoặc người quá tải.
Exit khác 0: file không tồn tại/không đọc được, thiếu cột bắt buộc, lỗi parse CSV, thiếu/sai --max-hours.
Script chỉ đọc, không sửa CSV đầu vào.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys

REQUIRED_COLUMNS = ("task_id", "owner", "hours")


class InputError(Exception):
    pass


def parse_hours(raw: str | None) -> float | None:
    """Số giờ hợp lệ: số hữu hạn, không âm. Trả None nếu không hợp lệ."""
    if raw is None or not raw.strip():
        return None
    try:
        value = float(raw.strip())
    except ValueError:
        return None
    if not math.isfinite(value) or value < 0:
        return None
    return value


def parse_max_hours(raw: str | None) -> float:
    """Kiểm tra giá trị --max-hours: số hữu hạn, không âm (>= 0)."""
    if raw is None or not str(raw).strip():
        raise InputError("Thiếu tham số bắt buộc --max-hours.")
    try:
        value = float(str(raw).strip())
    except ValueError:
        raise InputError(f"Giá trị --max-hours không hợp lệ: '{raw}' không phải là số.")
    if not math.isfinite(value) or value < 0:
        raise InputError(f"Giá trị --max-hours không hợp lệ: '{raw}' phải là số hữu hạn không âm (>= 0).")
    return value


def format_num(val: float) -> int | float:
    """Chuyển float thành int nếu nguyên, giữ float nếu có phần thập phân."""
    return int(val) if val.is_integer() else round(val, 4)


def analyze(path: str, max_hours: float) -> dict:
    if max_hours is None or not math.isfinite(max_hours) or max_hours < 0:
        raise InputError(f"Ngưỡng max_hours không hợp lệ: {max_hours}")

    try:
        handle = open(path, encoding="utf-8-sig", newline="")
    except OSError as exc:
        raise InputError(f"Không đọc được file {path}: {exc.strerror or exc}") from exc

    with handle:
        reader = csv.reader(handle, strict=True)
        try:
            header = next(reader, None)
            if header is None:
                raise InputError(f"File {path} rỗng, không có header.")
            columns = [c.strip() for c in header]
            missing = [c for c in REQUIRED_COLUMNS if c not in columns]
            if missing:
                raise InputError(f"Thiếu cột bắt buộc: {', '.join(missing)}. Header hiện có: {', '.join(columns)}")
            index = {name: columns.index(name) for name in REQUIRED_COLUMNS}

            row_count = 0
            missing_owner = 0
            invalid_hours = 0
            first_seen: dict[str, int] = {}
            duplicate_ids: list[str] = []
            issues: list[dict] = []

            owner_hours: dict[str, float] = {}
            excluded_rows: list[dict] = []

            for row in reader:
                line = reader.line_num
                if not any(cell.strip() for cell in row):
                    continue  # bỏ qua dòng trống
                row_count += 1

                def cell(name: str) -> str:
                    position = index[name]
                    return row[position].strip() if position < len(row) else ""

                task_id, owner, hours = cell("task_id"), cell("owner"), cell("hours")

                # Kiểm tra trùng lặp ID (chỉ ID không rỗng mới theo dõi)
                is_duplicate = False
                if task_id:
                    if task_id in first_seen:
                        is_duplicate = True
                        if task_id not in duplicate_ids:
                            duplicate_ids.append(task_id)
                    else:
                        first_seen[task_id] = line

                # Thống kê chất lượng cũ (issues)
                if len(row) != len(columns):
                    issues.append({"line": line, "column": None, "type": "wrong_field_count", "task_id": task_id or None,
                                   "message": f"Có {len(row)} trường, header có {len(columns)} cột."})
                if not task_id:
                    issues.append({"line": line, "column": "task_id", "type": "missing_task_id", "task_id": None,
                                   "message": "task_id trống."})
                elif is_duplicate:
                    issues.append({"line": line, "column": "task_id", "type": "duplicate_id", "task_id": task_id,
                                   "message": f"task_id {task_id} đã xuất hiện ở line {first_seen[task_id]}."})
                if not owner:
                    missing_owner += 1
                    issues.append({"line": line, "column": "owner", "type": "missing_owner", "task_id": task_id or None,
                                   "message": "owner trống."})
                parsed_h = parse_hours(hours)
                if parsed_h is None:
                    invalid_hours += 1
                    issues.append({"line": line, "column": "hours", "type": "invalid_hours", "task_id": task_id or None,
                                   "value": hours, "message": f"hours '{hours}' không phải số hữu hạn không âm."})

                # Lý do loại dòng khỏi tính tổng giờ (thứ tự cố định)
                reasons: list[str] = []
                if len(row) != len(columns):
                    reasons.append("wrong_field_count")
                if not task_id:
                    reasons.append("missing_task_id")
                elif is_duplicate:
                    reasons.append("duplicate_id")
                if not owner:
                    reasons.append("missing_owner")
                if parsed_h is None:
                    reasons.append("invalid_hours")

                if reasons:
                    excluded_rows.append({
                        "line": line,
                        "task_id": task_id if task_id else None,
                        "reasons": reasons,
                    })
                else:
                    owner_hours[owner] = owner_hours.get(owner, 0.0) + parsed_h

        except csv.Error as exc:
            raise InputError(f"Lỗi parse CSV ở line {reader.line_num}: {exc}") from exc
        except UnicodeDecodeError as exc:
            raise InputError(f"File {path} không phải UTF-8: {exc}") from exc

    hours_by_owner = {
        owner: format_num(hours_sum)
        for owner, hours_sum in owner_hours.items()
    }

    overloaded_owners = [
        {"owner": owner, "total_hours": format_num(owner_hours[owner])}
        for owner in sorted(owner_hours.keys())
        if owner_hours[owner] > max_hours
    ]

    return {
        "input": path,
        "max_hours": format_num(max_hours),
        "row_count": row_count,
        "missing_owner_count": missing_owner,
        "invalid_hours_count": invalid_hours,
        "duplicate_id_count": len(duplicate_ids),
        "duplicate_ids": duplicate_ids,
        "issues": sorted(issues, key=lambda item: item["line"]),
        "hours_by_owner": hours_by_owner,
        "overloaded_owners": overloaded_owners,
        "excluded_rows": excluded_rows,
    }


def main(argv: list[str] | None = None) -> int:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
        try:
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Kiểm tra chất lượng CSV công việc và quá tải theo người.")
    parser.add_argument("--input", required=True, help="Đường dẫn CSV, ví dụ data/workload.csv")
    parser.add_argument("--max-hours", required=True, help="Ngưỡng giờ tối đa (số hữu hạn không âm, ví dụ 8)")

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) and exc.code != 0 else 2

    try:
        max_h = parse_max_hours(args.max_hours)
        result = analyze(args.input, max_hours=max_h)
    except InputError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
