# Team

## Thông tin nhóm

- Tên nhóm: potato
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-potato-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/NguyenDucTrung999/K5-Day8-From-Workflows-to-Agents, nhánh trung2, commit 37ed8c2

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Nguyễn Anh Tú | 2A202603434 | minhhong2061@gmail.com | AnhTu-01 | orchestrator + handoff |
|   2 | Đinh Trần Nguyên | 2A202603517 | nguyentrandinh.tn@gmail.com | nguyentrandinh-hub | single agent |
|   3 | Nguyễn Huy Thứ | 2A202603356 | nguyenhuythu111@gmail.com | Teddyy1101 | workflow + integration |
|   4 | Nguyễn Đức Trung | 2A202603423 | trungducnguyen2k@gmail.com | NguyenDucTrung999 | ledger + evaluation |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Nguyễn Anh Tú - 2A202603434 | orchestrator + handoff | 8fb4a71 | tests/test_orchestrator_handoff_anhtu.py |
| Đinh Trần Nguyên - 2A202603517 | single agent | a5351c9 | tests/test_single.py |
| Nguyễn Huy Thứ - 2A202603356 | workflow + integration | 1c5e253 | tests/test_workflow.py |
| Nguyen Duc Trung - 2A202603423 | ledger + evaluation | 37ed8c2 | tests/test_ledger_trung.py |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603434_NguyenAnhTu

### Phần việc phụ trách

- Shape C (orchestrator) và phần handoff: `src/lab8/shapes/orchestrator.py`. Nhánh làm việc: `anhtu`.

### Đóng góp cụ thể

- Triển khai shape orchestrator: đọc claim qua `get_claim_view`, xây dựng handoff bằng `make_handoff` với allowlist bảo vệ, giao nhiệm vụ cho investigator chỉ có công cụ đọc (`lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`).
- Gửi quote đầy đủ từ order row vào `durability.issue_refund`, truyền `crash_at` xuống host và không bắt `InjectedCrash`.
- Lọc trace chỉ ghi các trường cho phép, loại bỏ `CANARY_SECRET_*`, PII và thông tin ticket.
- Viết file test: `src/tests/test_orchestrator_handoff_anhtu.py`.

### Bằng chứng

- `python -m pytest -q tests/test_orchestrator_handoff_anhtu.py`: 4 passed.
- `python -m pytest -q -m student -o addopts= -k orchestrator`: 62 passed.
- Commit: `8fb4a71`.

## 2A202603517_DinhTranNguyen

### Phần việc phụ trách

- Shape B (single ReAct agent): `src/lab8/shapes/single.py`. Nhánh làm việc: `nguyen`.

### Đóng góp cụ thể

- Triển khai `run_claim` qua `lab8.runtime.run_react` với `max_steps=8`, worker chỉ gọi các read tools.
- Đảm bảo ranh giới code/model: MockLLM chỉ ghi nhận chi phí, số tiền hoàn toàn do `compute_compensation` tính toán từ bảng đơn hàng.
- Truyền quote đầy đủ vào `durability.issue_refund`, hỗ trợ xử lý sập nguồn an toàn.
- Lọc trace qua allowlist và hoàn tất qua `finish()`.
- Viết file test: `src/tests/test_single.py`.

### Bằng chứng

- `python -m pytest -q tests/test_single.py`: 3 passed.
- `python -m pytest -q -m student -o addopts= -k "single]"`: 62 passed.
- Commit: `a5351c9`.

## 2A202603356_NguyenHuyThu

### Phần việc phụ trách

- Shape A (workflow) và tích hợp hệ thống (integration): `src/lab8/shapes/workflow.py`, `src/tests/test_workflow.py`, `src/tests/test_shapes_integration.py`. Nhánh làm việc: `thu`.

### Đóng góp cụ thể

- Triển khai workflow tuần tự 8 bước hoàn toàn bằng code Python, không gọi model, đảm bảo tính tất định và an toàn trước prompt injection.
- Kiểm tra các nhánh `needs_info`, `escalated`, `denied`, `resolved`, truyền quote đầy đủ vào host.
- Tích hợp và kiểm tra chéo các shape của thành viên trong nhóm qua test runner chung.
- Viết file test: `src/tests/test_workflow.py` và `src/tests/test_shapes_integration.py`.

### Bằng chứng

- `python -m pytest -q tests/test_workflow.py`: 4 passed.
- `python -m pytest -q tests/test_shapes_integration.py`: 4 passed.
- `python -m pytest -q -m student -o addopts= -k workflow`: 62 passed.
- Commit: `1c5e253`.

## 2A202603423_NguyenDucTrung

### Phần việc phụ trách

- Sổ cái (ledger), chính sách bồi thường, an toàn sập nguồn (crash durability) và đánh giá kiến trúc (evaluation): `src/lab8/durability.py`, `src/lab8/db.py`, `src/reports/`. Nhánh làm việc: `trung2`.

### Đóng góp cụ thể

- Bảo đảm tính nguyên tử của giao dịch SQLite sổ cái `refund_ledger` và sự kiện `refund_committed` (`BEGIN IMMEDIATE`).
- Thiết lập khóa lũy nghiệm duy nhất `idempotency_key = f"refund:{claim_id}"` chống chi trả trùng lặp khi replay.
- Kiểm soát và thực thi cơ chế chặn trần đơn hàng (`per-order cap`).
- Khôi phục an toàn sau sự cố sập nguồn `crash_at` tại ranh giới checkpoint.
- Viết file test chuyên biệt cho sổ cái: `src/tests/test_ledger_trung.py`.
- Thực thi benchmark 4 shape qua 5 seed (70 trial/shape), hoàn thiện `decision_adr.md`, `research_card.md` và `group_report.md`.

### Bằng chứng

- `python -m pytest -q tests/test_ledger_trung.py`: 4 passed.
- `python -m lab8.crash_test --count 20 --out reports/crash.json`: `crash_safety 20/20`.
- `src/reports/benchmark.json`: Workflow pass rate 1.000, chi phí 27.86 VND.
- Commit: `37ed8c2`.
