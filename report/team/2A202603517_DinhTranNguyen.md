# Báo cáo cá nhân — 2A202603517_DinhTranNguyen

## 1. Thông tin thành viên

- Họ tên: Đinh Trần Nguyên
- MSSV: 2A202603517
- Email: nguyentrandinh.tn@gmail.com
- GitHub: nguyentrandinh-hub

## 2. Phần việc phụ trách

- Phụ trách **Shape B (`single`)** trong team 4 người (`src/lab8/shapes/single.py`).
- Viết unit/contract test cho Shape B (`src/tests/test_single.py`), kiểm tra Trace Contract v1, policy, idempotency và crash-recovery trên `single`.

## 3. Đóng góp cụ thể

- **Code chính (`src/lab8/shapes/single.py`):**
  - Triển khai `run_claim` giữ nguyên chữ ký chung với `swarm`, dùng `lab8.runtime.run_react` với `max_steps=8` và `worker=True` (chỉ cho phép gọi các read tool).
  - Tách ranh giới code/model: `MockLLM` (`complete`) chỉ dùng để ghi nhận chi phí suy luận/soạn câu vào `Budget`; số tiền hoàn do `compute_compensation` tính dựa trên `order` row và policy hiện hành (`is_current = 1`, `effective_date <= 2026-11-15`), không tin số ngày trễ hay câu lệnh trong `ticket`.
  - Truyền **quote đầy đủ** vào `durability.issue_refund(..., crash_at=crash_at)` và để `InjectedCrash` lan truyền ra ngoài (sau khi ghi trace) để đảm bảo idempotency và per-order cap (T11, T12, T13, T14).
  - Lọc trace qua `_sanitize_tool_result` (loại bỏ `ticket` và dữ liệu thô, chỉ giữ field allowlist) và trả `RunResult` qua `lab8.shapes.common.finish()` ở mọi nhánh return.
- **Test đã thêm (`src/tests/test_single.py`):**
  - `test_single_ignores_ticket_delay_even_on_seed_55`: kiểm tra `C-002` ở `seed=55` (ticket nói trễ 5 ngày, DB chỉ trễ 2 ngày) vẫn bị từ chối (`denied`).
  - `test_single_trace_matches_contract_and_hides_secrets`: kiểm tra trace đúng Trace Contract v1 và không lộ `CANARY_SECRET` / `parent_secret`.
  - `test_single_crash_and_resume_stays_idempotent`: kiểm tra crash tại `after_effect_before_checkpoint` ném `InjectedCrash` và khi resume chỉ tạo đúng 1 dòng refund cùng 1 audit `refund_committed`.
- **Commit chính:** `<điền commit hash sau khi git commit phần single.py và test_single.py>`

## 4. Bằng chứng

- File code: `src/lab8/shapes/single.py`
- File test: `src/tests/test_single.py`
- Kết quả chạy kiểm tra trong `src/` (bằng `.venv` Python 3.12):
  - `python -m pytest -q` → `57 passed, 248 deselected` (54 test cổng host + 3 test trong `tests/test_single.py`).
  - `python -m pytest -q -m student -o addopts= -k "single]"` → `62 passed, 240 deselected` (đạt toàn bộ T01–T14 trên `single`).
  - `python -m pytest -q -m student -o addopts= -k "t11 or t12"` → `test_t11_retry_keeps_one_refund[single]` và `test_t12_crash_before_checkpoint_does_not_double_pay[single]` đều PASS.
- Commit hash: a5351c9

## 5. Công cụ AI đã dùng

- **Công cụ:** Trợ lý AI (Antigravity / Gemini) để giải thích yêu cầu từng checkpoint, cấu trúc `run_react` / `finish()` / `issue_refund`, gợi ý khung code `src/lab8/shapes/single.py` và các test case trong `src/tests/test_single.py`.
- **Cách tự kiểm tra kết quả:**
  - Đọc đối chiếu lại `docs/business_rules.md`, `docs/contracts.md`, `src/lab8/tools.py` và `src/lab8/runtime.py` để xác nhận đúng ranh giới code/model, không tự trừ tiền đã hoàn trước đó và không ghi dữ liệu thô nhạy cảm vào trace.
  - Tự chạy lại toàn bộ lệnh `pytest` trên `.venv` trong `src/` (`pytest -q`, `-m student -k "single]"`, `-k "t11 or t12"`) và kiểm tra trực tiếp `crash_at="after_effect_before_checkpoint"` có thực sự ném `InjectedCrash` trước khi resume.

## 6. Tự đánh giá

- Hoàn thành đúng tiến độ và đầy đủ các yêu cầu của Shape B (`single`) từ CP1 đến hết CP3: pass toàn bộ cổng host, 62/62 student tests của `single`, và 3 test bổ sung tự viết.