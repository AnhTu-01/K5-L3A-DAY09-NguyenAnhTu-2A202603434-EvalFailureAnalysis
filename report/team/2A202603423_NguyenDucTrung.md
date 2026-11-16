# Báo cáo cá nhân — 2A202603423_NguyenDucTrung

## 1. Thông tin thành viên

- Họ tên: Nguyễn Đức Trung
- MSSV: 2A202603423
- Email: trungducnguyen2k@gmail.com
- GitHub: NguyenDucTrung999

## 2. Phần việc phụ trách

Ledger, cơ chế ghi sổ cái tài chính, chính sách bảo đảm tính lũy nghiệm (idempotency) và xử lý sự cố sập nguồn (crash recovery): `src/lab8/durability.py`, `src/lab8/db.py`. Nhánh làm việc: `trung2`.

## 3. Đóng góp cụ thể

- Đảm bảo tính nguyên tử và toàn vẹn của sổ cái bồi thường `refund_ledger`: mỗi giao dịch bồi thường thành công được ghi kèm đúng 1 sự kiện kiểm toán `refund_committed` trong `audit_events` dưới cùng một transaction SQLite (`BEGIN IMMEDIATE`).
- Thiết lập và kiểm chứng khóa lũy nghiệm duy nhất `idempotency_key = f"refund:{claim_id}"` để ngăn chặn việc bồi thường trùng lặp khi một claim được phát lại nhiều lần (`idempotent_replay`).
- Kiểm soát và thực thi cơ chế chặn trần bồi thường theo đơn hàng (`per-order cap`): tự động trừ đi số tiền đã bồi thường ở các claim trước, từ chối với lý do `order_already_refunded` nếu đơn hàng đã được hoàn đủ.
- Xử lý các kịch bản sập nguồn (`crash_at`) tại ranh giới checkpoint (`after_effect_before_checkpoint`): bảo đảm hệ thống khôi phục an toàn mà không làm mất mát hoặc ghi đè sai lệch dữ liệu tài chính.
- Tích hợp thành công mã nguồn của 3 thành viên (`workflow.py` của Thu, `single.py` của Nguyên, `orchestrator.py` của Anh Tú).
- Viết file kiểm thử chuyên biệt: `src/tests/test_ledger_trung.py` (4 test kiểm tra tính duy nhất của dòng sổ cái, chống xung đột số tiền, khôi phục sau sập nguồn và kiểm soát hạn mức đơn hàng).

## 4. Bằng chứng

- Lệnh `python -m pytest -q tests/test_ledger_trung.py`: 4 passed.
- Lệnh `python -m lab8.crash_test --count 20 --out reports/crash.json`: `crash_safety 20/20` trên toàn bộ 20 kịch bản sự cố.
- Lệnh `python -m pytest -q`: toàn bộ 70 test cổng host xanh.
- Lệnh `python -m pytest -q -m student -o addopts=`: 248 passed trên cả 3 shape được tích hợp.

## 5. Công cụ AI đã dùng

Antigravity (Google DeepMind): hỗ trợ rà soát logic giao dịch SQLite, tích hợp các nhánh độc lập của thành viên và xây dựng kịch bản kiểm thử crash recovery. Tôi tự kiểm tra, chạy lại toàn bộ test suite trên môi trường cục bộ và xác thực tính toàn vẹn của sổ cái trước khi commit. Tôi chịu trách nhiệm về nội dung đã nộp.

## 6. Tự đánh giá

Hoàn thành đầy đủ phần việc sổ cái (ledger), chính sách và xử lý sập nguồn theo yêu cầu CP3 và CP4. Đạt 20/20 điểm crash safety. Lưu ý: phần đánh giá so sánh (evaluation CP5) sẽ được thực hiện ở bước sau theo kế hoạch của nhóm.
