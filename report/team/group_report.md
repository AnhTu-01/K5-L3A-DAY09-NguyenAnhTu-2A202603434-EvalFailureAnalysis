# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: potato
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-TenNhom-FromWorkflowsToAgents` (xem [SUBMISSION.md](../../SUBMISSION.md))
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): 52c67ea

## 2. Mục tiêu và cách tiếp cận

Bài toán LogiX-VN yêu cầu xây dựng hệ thống xử lý khiếu nại bồi thường logistics tự động, đảm bảo an toàn tài chính, tính đúng đắn theo chính sách bồi thường và khả năng chịu lỗi sự cố (crash recovery).

Nhóm tiếp cận theo nguyên tắc "Least Autonomy": trao quyền tự chủ tối thiểu cho mô hình trí tuệ nhân tạo (LLM) và giữ toàn quyền tính toán số tiền và ghi sổ cái ở tầng mã nguồn có cấu trúc và máy chủ (host).

Phân công công việc nhóm 4 người:
1. Nguyễn Huy Thứ (`Teddyy1101`): Triển khai Shape A (Workflow tuần tự) và tích hợp hệ thống (Integration runner).
2. Đinh Trần Nguyên (`nguyentrandinh-hub`): Triển khai Shape B (Single ReAct agent) với vòng lặp ReAct tối đa 8 bước.
3. Nguyễn Anh Tú (`AnhTu-01`): Triển khai Shape C (Orchestrator + read-only investigator) với cơ chế lọc handoff nghiêm ngặt.
4. Nguyễn Đức Trung (`NguyenDucTrung999`): Phụ trách sổ cái (ledger), chính sách bồi thường, an toàn sập nguồn (crash durability) và đánh giá so sánh (evaluation/benchmark).

## 3. Giải pháp

### 3.1. Ranh giới Code và Model
- **Tầng tính toán tiền**: Hàm `compute_compensation` xác định quyền lợi bồi thường dựa trên thông tin đơn hàng và bảng chính sách hiện hành (`is_current = True`). Tuyệt đối không để LLM tự quyết định số tiền.
- **Tầng Host duy nhất ghi dữ liệu**: Hàm `durability.issue_refund` là cổng duy nhất có quyền ghi vào `refund_ledger` và `audit_events`. Host tự động áp mức trần đơn hàng (`per-order cap`), ràng buộc mã phê duyệt (`approval_binding`) và khấu trừ các khoản bồi thường trước đó cho cùng đơn hàng (T13, T14).

### 3.2. Cơ chế lọc Handoff và bảo vệ bí mật
- Dữ liệu chuyển giao giữa các tác tử (`handoff`) bắt buộc phải đi qua hàm làm sạch `make_handoff` với danh sách trường cho phép (`FACT_KEYS`).
- Tác tử điều tra (investigator) chỉ được cấp các công cụ đọc (`lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`), không bao giờ có công cụ ghi bồi thường.
- Không ghi thông tin nhạy cảm (PII: số điện thoại, địa chỉ, canary token) vào tệp nhật ký `trace`.

### 3.3. Độ bền bỉ và Tính lũy nghiệm (Durability & Idempotency)
- Sử dụng khóa lũy nghiệm duy nhất `idempotency_key = f"refund:{claim_id}"`.
- Thao tác ghi sổ cái và sự kiện kiểm toán nằm trong cùng một transaction SQLite nguyên tử (`BEGIN IMMEDIATE`).
- Khi gặp sự cố sập nguồn (`InjectedCrash` tại điểm `after_effect_before_checkpoint`), hệ thống kiểm tra sổ cái khi khởi động lại và xử lý an toàn theo cơ chế phát lại lũy nghiệm (`idempotent_replay`), đảm bảo không chi tiền hai lần.

## 4. Kết quả

### 4.1. Bảng so sánh 4 kiến trúc trên bộ public (src/reports/benchmark.json)

| Shape | Pass rate | Pass^5 | Seed min-max | Variance | Cost / success (VND) | Mean steps |
|---|---|---|---|---|---|---|
| **workflow** | **1.000** | **1.000** | 1.000 - 1.000 | **0.000000** | **27.86** | 4.43 |
| **single** | **1.000** | **1.000** | 1.000 - 1.000 | **0.000000** | 46.29 | 6.14 |
| **orchestrator** | **1.000** | **1.000** | 1.000 - 1.000 | **0.000000** | 57.51 | 3.43 |
| **swarm** | 0.986 | 0.929 | 0.929 - 1.000 | 0.000816 | 49.57 | 2.80 |

### 4.2. Độ an toàn sự cố (Crash safety)
- Kiểm thử sập nguồn ngẫu nhiên qua 20 kịch bản đạt kết quả tuyệt đối **20/20** (`src/reports/crash.json`).
- Không phát hiện bất kỳ trường hợp nào bị rò rỉ token bí mật hoặc vượt rào phê duyệt (Secret leak: 0, Approval bypass: 0).

### 4.3. Quyết định kiến trúc
Nhóm chọn **Shape A (Workflow)** làm kiến trúc nộp bài chính thức. Chi tiết quyết định xem tại `report/team/decision_adr.md`. Nghiên cứu mở rộng và ablation xem tại `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

1. **Khách hàng khai khống độ trễ trong ticket (Ca T02)**:
   - *Khó khăn*: Khách hàng ghi trễ 5 ngày trong ticket nhưng cơ sở dữ liệu chỉ ghi nhận trễ 2 ngày. Kiến trúc Swarm bị mắc bẫy ở seed 55 và bồi thường sai.
   - *Xử lý*: Thiết lập quy tắc xem dòng dữ liệu `orders` trong database là nguồn sự thật duy nhất (ground truth), hoàn toàn bỏ qua câu chữ trong ticket khi tính quote.
2. **Quy tắc gộp quyền lợi và trần bồi thường theo đơn (Ca T13, T14)**:
   - *Khó khăn*: Đơn hàng đã được bồi thường trước đó nếu không kiểm tra sẽ dẫn đến chi thừa ngân sách.
   - *Xử lý*: Shape truyền toàn bộ quyền lợi vào `issue_refund`, tầng Host chịu trách nhiệm trừ đi số tiền đã nhận của đơn hàng và áp trần bồi thường an toàn.
3. **Phục hồi sau sự cố sập nguồn (Ca T12)**:
   - *Khó khăn*: Sập nguồn ngay sau khi ghi sổ cái nhưng chưa kịp lưu checkpoint làm mất đồng bộ trạng thái.
   - *Xử lý*: Thay vì chỉ tin vào bảng checkpoint, hệ thống kiểm tra trực tiếp sự tồn tại của bản ghi trong `refund_ledger` khi khởi động lại.

## 6. Tổng hợp đóng góp

| Thành viên | MSSV | Vai trò | Test chính phụ trách |
|---|---|---|---|
| Nguyễn Huy Thứ | 2A202603356 | workflow + integration | `tests/test_workflow.py` |
| Đinh Trần Nguyên | 2A202603517 | single agent | `tests/test_single.py` |
| Nguyễn Anh Tú | 2A202603434 | orchestrator + handoff | `tests/test_orchestrator_handoff_anhtu.py` |
| Nguyễn Đức Trung | 2A202603423 | ledger + evaluation | `tests/test_ledger_trung.py` |

Chi tiết đóng góp và bằng chứng cụ thể của từng thành viên xem tại `report/team/MSSV_HoTen.md` và `TEAM.md`.

## 7. Hạn chế và hướng cải thiện

1. **Mô hình mô phỏng (MockLLM)**: MockLLM là môi trường mô phỏng cục bộ dựa trên seed, chưa phản ánh hết tính bất định và độ trễ mạng thực tế của LLM thương mại (như GPT-4 hoặc Gemini Pro).
2. **Đo lường độ trễ (Latency)**: Hệ thống chạy giả lập nên độ trễ ghi nhận là `unavailable`. Cần bổ sung benchmark đo thời gian phản hồi thực tế (p95 latency) trên môi trường production.
3. **Mở rộng chính sách**: Cần xây dựng giao diện phân tích động để hỗ trợ các chính sách bồi thường đa điều kiện phức tạp hơn trong tương lai.

## 8. Tài liệu tham khảo

1. Google Research (2026), *Towards a Science of Scaling Agent Systems*.
2. MAST, NeurIPS (2025), *Why Do Multi-Agent LLM Systems Fail?*
3. AgentArch, AACL (2026), *Empirical Evaluation of Multi-Agent Architectures*.
4. Tài liệu bài lab LogiX-VN: `docs/architecture.md`, `docs/business_rules.md`, `docs/contracts.md`.
