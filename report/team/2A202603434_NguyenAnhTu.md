# Báo cáo cá nhân — 2A202603434_NguyenAnhTu

## 1. Thông tin thành viên

- Họ tên: Nguyễn Anh Tú
- MSSV: 2A202603434
- Email: minhhong2061@gmail.com
- GitHub: AnhTu-01

## 2. Phần việc phụ trách

Shape C (orchestrator) và phần handoff: `src/lab8/shapes/orchestrator.py`. Nhánh làm việc: `anhtu`.

## 3. Đóng góp cụ thể

- Viết shape orchestrator: orchestrator đọc claim bằng `get_claim_view`, tạo handoff bằng `make_handoff` (allowlist trong code), giao cho một investigator chỉ có tool đọc (`lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`).
- Orchestrator lấy quote từ order row (bỏ qua số ngày trong ticket) và là bên duy nhất gọi `durability.issue_refund` với quote đầy đủ để host tự trừ số đã hoàn.
- Truyền `crash_at` xuống host, không bắt `InjectedCrash`; mọi lỗi khác trả về `failed` nên `run_claim` không raise.
- Trace chỉ ghi handoff đã sanitize và các field đơn hàng thuộc allowlist, không ghi ticket hay parent context.
- Commit chính: `a1b2c3d`.
- Test đã thêm: `src/tests/test_orchestrator_handoff_anhtu.py` (4 test: tool của investigator chỉ đọc, handoff từ chối tool ghi, handoff loại bỏ secret và field lạ, trace có sự kiện handoff và không lộ `CANARY_SECRET_`).

## 4. Bằng chứng

- Lệnh `python -m pytest -q -m student -o addopts= -k orchestrator`: 62 passed (chạy trên máy tôi).
- Lệnh `python -m pytest -q`: cổng host xanh.
- Lệnh `python -m pytest -q tests/test_orchestrator_handoff_anhtu.py`: 4 passed.
- Benchmark riêng shape orchestrator trên bộ public (14 claim x 5 seed) cho pass rate 1.000 (chạy trong quá trình phát triển, chưa phải số liệu chính thức của nhóm).

## 5. Công cụ AI đã dùng

Claude (Anthropic): hỗ trợ đọc tài liệu lab, viết bản đầu của `orchestrator.py` và file test. Tôi tự kiểm tra bằng cách chạy lại các lệnh pytest ở mục 4 trên máy của mình và đọc lại logic của file trước khi commit. Tôi chịu trách nhiệm về nội dung đã nộp.

## 6. Tự đánh giá

Phần orchestrator và handoff chạy đúng các test public và test riêng. Hạn chế: chưa chạy thử trên bộ hidden; MockLLM không phải model sản xuất; chưa có số liệu crash 20/20 chính thức của cả nhóm.
