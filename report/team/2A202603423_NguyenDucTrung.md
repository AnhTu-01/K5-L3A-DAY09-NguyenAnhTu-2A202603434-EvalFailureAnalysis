# Báo cáo cá nhân — 2A202603423_NguyenDucTrung

## 1. Thông tin thành viên

- Họ tên: Nguyễn Đức Trung
- MSSV: 2A202603423
- Email: trungducnguyen2k@gmail.com
- GitHub: NguyenDucTrung999
- Vai trò: Ledger + evaluation
- Nhánh làm việc: trung2

## 2. Phần việc phụ trách

- **Ledger & Durability**: Quản lý cơ chế ghi sổ cái tài chính, chính sách bảo đảm tính lũy nghiệm (idempotency) và xử lý sự cố sập nguồn (crash recovery): `src/lab8/durability.py`, `src/lab8/db.py`.
- **Evaluation & Reporting**: Chạy benchmark đánh giá định lượng 4 kiến trúc qua 5 seed, xây dựng báo cáo quyết định kiến trúc (`report/team/decision_adr.md`), phiếu nghiên cứu ablation (`report/team/research_card.md`) và tổng hợp báo cáo nhóm (`report/team/group_report.md`).

## 3. Đóng góp cụ thể

- Đảm bảo tính nguyên tử và toàn vẹn của sổ cái bồi thường `refund_ledger`: mỗi giao dịch bồi thường thành công được ghi kèm đúng 1 sự kiện kiểm toán `refund_committed` trong `audit_events` dưới cùng một transaction SQLite (`BEGIN IMMEDIATE`).
- Thiết lập và kiểm chứng khóa lũy nghiệm duy nhất `idempotency_key = f"refund:{claim_id}"` để ngăn chặn việc bồi thường trùng lặp khi một claim được phát lại nhiều lần (`idempotent_replay`).
- Kiểm soát và thực thi cơ chế chặn trần bồi thường theo đơn hàng (`per-order cap`): tự động trừ đi số tiền đã bồi thường ở các claim trước, từ chối với lý do `order_already_refunded` nếu đơn hàng đã được hoàn đủ.
- Xử lý các kịch bản sập nguồn (`crash_at`) tại ranh giới checkpoint (`after_effect_before_checkpoint`): bảo đảm hệ thống khôi phục an toàn mà không làm mất mát hoặc ghi đè sai lệch dữ liệu tài chính.
- Viết file kiểm thử chuyên biệt cho sổ cái: `src/tests/test_ledger_trung.py` (4 test kiểm tra tính duy nhất của dòng sổ cái, chống xung đột số tiền, khôi phục sau sập nguồn và kiểm soát hạn mức đơn hàng).
- Thực thi benchmark toàn diện 4 shape qua 5 seed (70 trial mỗi shape), thu thập các chỉ số pass rate, pass^5, variance, chi phí trên mỗi ca thành công để đưa ra cơ sở định lượng chọn shape `workflow`.
- Hoàn thiện hồ sơ nộp bài nhóm bao gồm `decision_adr.md`, `research_card.md` và `group_report.md`.

## 4. Bằng chứng

- File test riêng: `src/tests/test_ledger_trung.py` (4/4 test pass).
- Kết quả kiểm thử an toàn sự cố: `src/reports/crash.json` đạt `crash_safety: 20/20`.
- Báo cáo benchmark: `src/reports/benchmark.json` (workflow đạt pass rate 1.000, pass^5 1.000, variance 0.000000, chi phí 27.86 VND).
- Lệnh `python -m pytest -q`: 70 passed (cổng host xanh).
- Lệnh `python -m pytest -q -m student -o addopts=`: 257 passed trên toàn bộ các shape và bài test tích hợp.
- Lệnh `python -m lab8.check_submission`: đạt chuẩn 0 FAIL, 0 WARN.

## 5. Công cụ AI đã dùng

- **Công cụ**: Antigravity (Google DeepMind).
- **Mục đích**: Hỗ trợ phân tích luồng giao dịch SQLite, tích hợp các nhánh độc lập của thành viên và xây dựng kịch bản kiểm thử crash recovery.
- **Cách tự kiểm tra**: Tự chạy lại toàn bộ test suite trên môi trường cục bộ, đối chiếu dữ liệu sổ cái và benchmark trước khi commit. Tôi chịu hoàn toàn trách nhiệm về nội dung đã nộp.

## 6. Tự đánh giá

Hoàn thành xuất sắc và đúng hạn cả hai phần việc phụ trách: bảo đảm 100% an toàn sổ cái tài chính trước mọi kịch bản sự cố sập nguồn (20/20 crash safety) và hoàn thành đầy đủ các báo cáo đánh giá định lượng theo chuẩn yêu cầu của môn học.
