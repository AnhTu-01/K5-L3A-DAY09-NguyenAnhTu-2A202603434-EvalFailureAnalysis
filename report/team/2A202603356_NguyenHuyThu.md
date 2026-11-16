# Báo cáo cá nhân — 2A202603356_NguyenHuyThu

## 1. Thông tin thành viên

- Họ tên: Nguyễn Huy Thứ
- MSSV: 2A202603356
- Email: nguyenhuythu111@gmail.com
- GitHub: [Teddyy1101](https://github.com/Teddyy1101)
- Vai trò: Workflow + integration
- Nhánh làm việc: [thu](https://github.com/NguyenDucTrung999/K5-L3A-Day08-potato-FromWorkflowstoAgents/tree/thu)
- Ngày cập nhật bằng chứng: 16/11/2026

## 2. Phần việc phụ trách

Phụ trách triển khai shape A `workflow` ở CP2 và CP3, thêm test cho workflow, sau đó thực hiện Bước 4: review, tích hợp code single/orchestrator của đồng đội và kiểm tra regression qua runner chung.

Các file thuộc phần triển khai và test của tôi:

- [src/lab8/shapes/workflow.py](../../src/lab8/shapes/workflow.py).
- [src/tests/test_workflow.py](../../src/tests/test_workflow.py).
- [src/tests/test_shapes_integration.py](../../src/tests/test_shapes_integration.py).

Bước 5 (chạy benchmark, tạo bằng chứng đánh giá và tổng hợp số liệu) thuộc người phụ trách ledger + evaluation. `TEAM.md`, báo cáo nhóm, ADR và research card được nhóm tổng hợp chung trên một máy. Báo cáo này ghi phần workflow và integration đã thực hiện; code single/orchestrator được ghi nhận là đóng góp của tác giả tương ứng.

## 3. Đóng góp cụ thể

### 3.1. Triển khai workflow — CP2

Thay stub `not_implemented` trong `workflow.py` bằng pipeline Python cố định, giữ nguyên chữ ký `run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult`:

1. Mở SQLite bằng `connect(store_path)`; đọc claim qua `get_claim_view`.
2. Claim không tồn tại trả `failed`; thiếu `order_id` trả `needs_info`.
3. Tra đơn qua `lookup_order` với principal của claim. Không tìm thấy đơn hoặc không có quyền xem trả `escalated`.
4. Tính quote bằng `compute_compensation` từ structured order và policy hiệu lực. Không lấy số ngày trễ, mã đơn hoặc chỉ dẫn trong ticket làm nguồn quyết định nghiệp vụ.
5. Quote bằng 0 trả `denied` và không gọi thao tác ghi tiền. Quote dương được truyền đầy đủ vào `durability.issue_refund` để host kiểm approval, trần theo đơn và idempotency.
6. Host chấp nhận trả `resolved`; host từ chối trả `denied`; amount conflict trả `failed`. `proposal_amount` vẫn giữ quote gốc.

Workflow không gọi model. Số tiền do code tính; approval, refund effect và audit do host xử lý. Ví dụ, ở T14, workflow gửi quote 150.000 VND; host tự trừ 30.000 VND đã hoàn và chỉ ghi thêm 120.000 VND. Workflow không tự trừ lịch sử trước khi gọi host.

Khởi tạo `Budget`, `Trace` và `make_run_id`; ghi nhận các tool đọc được gọi chủ động. Helper nội bộ `finish_result()` gọi `common.finish()` ở mọi nhánh trả kết quả, để effect/audit được lấy từ ledger và trace được ghi trong lần chạy hiện tại.

Trace ghi các event `claim_read`, `order_lookup`, `quote`, `refund_outcome`, `decision`. Chỉ ghi các field được chọn; không dump nguyên claim/ticket hoặc order thô, không ghi parent secret, headers, phone, address, tên hàng hay internal note.

### 3.2. Crash/resume và test workflow — CP3

Truyền `crash_at` vào `issue_refund`, để `InjectedCrash` truyền ra runner/test và luôn đóng connection trong `finally`. Không dùng exception handler để biến crash thành kết quả nghiệp vụ bình thường. Tính an toàn khi retry dựa vào ledger và transaction có sẵn của host.

Thêm `test_workflow.py` với ba hàm test, tương ứng năm trường hợp chạy:

| Test | Số trường hợp | Nội dung kiểm tra |
| --- | ---: | --- |
| `test_unknown_claim_returns_failed_with_fresh_trace` | 1 | Claim không tồn tại trả `failed`, proposal 0, không refund/audit committed và có trace mới đúng contract |
| `test_crash_resume_commits_refund_once` | 3 | Ba điểm crash: `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`; kiểm trạng thái trước resume và một refund/một audit sau resume |
| `test_retry_with_changed_quote_preserves_committed_refund` | 1 | Thay quote trong DB tạm rồi retry: `amount_conflict`, giữ effect 35.000 VND cũ và một audit committed |

Fixture bổ sung và việc thay đổi shipping fee chỉ diễn ra trong DB tạm của test. Không sửa dữ liệu public hoặc các file host/thước đo.

Commit workflow và năm trường hợp test: [`1c5e253`](https://github.com/NguyenDucTrung999/K5-L3A-Day08-potato-FromWorkflowstoAgents/commit/1c5e2535a19ebddc47e0204720a13ff64eebe444), `feat(workflow): implement claims processing and crash recovery`.

### 3.3. Tích hợp ba shape — Bước 4

Review code và test của đồng đội, sau đó tích hợp vào `thu` bằng `git cherry-pick -x`, giữ tác giả và tham chiếu commit nguồn:

| Tác giả / phần việc | Commit nguồn | Commit trên nhánh thu |
| --- | --- | --- |
| Đinh Trần Nguyên — code single | `7c8b00e25e31ed2bb880655dfa94ceadf66866ac` | `f31e0da` |
| Đinh Trần Nguyên — ba test single | `a5351c934bb44bf3a15d711bef132cbdce9b33a2` | `1253312` |
| Nguyễn Anh Tú — code orchestrator và bốn test handoff | `8fb4a71e30d553058a7b0f578fc56b7010c4cab9` | `f0638ae` |

Commit cuối của nhánh orchestrator được cung cấp là `6a96cea392e51f9b490d9767c0e2fe6fafdeaea9`, chỉ sửa tài liệu. Đã đối chiếu lịch sử để lấy commit code/test `8fb4a71`, giữ phần `TEAM.md` và báo cáo cho nhóm tổng hợp chung.

Các điểm đã review khi tích hợp:

- Cả ba shape giữ nguyên chữ ký và sử dụng `RunResult`/`finish()`; không sửa registry, runner hoặc host để bù lỗi shape.
- Single gọi `run_react` với `max_steps=8`, `worker=True`; tool trong vòng lặp chỉ đọc, thao tác ghi tiền nằm ngoài vòng lặp và đi qua host.
- Orchestrator tạo handoff bằng `make_handoff`; investigator chỉ có tool đọc; trace ghi handoff đã sanitize.
- Cả ba truyền quote đầy đủ, đóng connection và truyền crash đúng. Single/orchestrator bắt riêng `InjectedCrash` để ghi trace rồi raise lại, không nuốt crash.

Không cần chỉnh code single/orchestrator sau review và kiểm tra regression.

Thêm `test_shapes_integration.py`, gọi qua `lab8.app.run_shape` với **ba shape × ba điểm crash = chín trường hợp**. Test kiểm crash thực sự xảy ra; mở connection mới để đối chiếu ledger/audit/checkpoint trước resume; resume trên cùng DB; đối chiếu kết quả và trace bằng `trial_pass`. Sau resume, mỗi claim có đúng một refund 35.000 VND, một audit `refund_committed` và checkpoint hợp lệ. Test có marker `student`.

Commit test integration: [`3b8dbc6`](https://github.com/NguyenDucTrung999/K5-L3A-Day08-potato-FromWorkflowstoAgents/commit/3b8dbc62c8e974ab2b01ffaab621c93bff70c345), `test(integration): verify crash recovery across student shapes`. Các commit code/test đã được push lên `origin/thu`.

## 4. Bằng chứng

Các kết quả dưới đây lấy từ output terminal của các lượt kiểm tra đã thực hiện trong phiên làm việc. Mọi lệnh chạy trong thư mục `src/`, sử dụng `.venv` ở gốc repo.

| Lượt kiểm tra | Lệnh đã chạy | Kết quả |
| --- | --- | --- |
| Workflow sau CP2 + CP3 | `..\.venv\Scripts\python.exe -m pytest -q -o addopts= tests/test_workflow.py tests/test_public_matrix.py -k workflow` | **67 passed, 186 deselected** — 62 test chuẩn của workflow và 5 trường hợp bổ sung |
| Integration riêng sau nhận đủ code | `..\.venv\Scripts\python.exe -m pytest -q -m student -o addopts= tests/test_shapes_integration.py` | **9 passed** |
| Regression toàn bộ sau tích hợp | `..\.venv\Scripts\python.exe -m pytest -q -o addopts=` | **323 passed** — gồm host, ma trận student và test bổ sung |

Lượt regression toàn bộ được chạy trên code sau khi tích hợp ba commit của đồng đội; nội dung test integration sau đó được ghi trong commit `3b8dbc6`. `git diff --check` không báo lỗi.

T11/T12 đã nằm trong lượt kiểm workflow đầy đủ; test integration bổ sung cả ba cửa sổ crash qua runner chung. Kết quả `323 passed` là kết quả test, không phải pass rate benchmark hay điểm hidden. Trong student suite, lỗi tham chiếu của swarm ở C-002/seed 55 được kiểm là lỗi mong đợi theo test chuẩn.

Phần việc này chưa tạo `benchmark.json`, `crash.json` hoặc run id dẫn chứng benchmark. Bằng chứng benchmark/hidden và quyết định kiến trúc được bàn giao cho người phụ trách evaluation và nhóm tổng hợp.

## 5. Công cụ AI đã dùng

Công cụ sử dụng: **Codex/ChatGPT** trong workspace của nhóm.

AI đã hỗ trợ đọc README, contract và luật nghiệp vụ; lập kế hoạch theo vai trò; sinh và chỉnh sửa code workflow/test; review commit của đồng đội; thực hiện cherry-pick, và tổng hợp báo cáo này từ code.

Kết quả do AI hỗ trợ được kiểm chứng bằng cách đối chiếu với `docs/business_rules.md`, `docs/contracts.md` và API host; kiểm ledger/audit/checkpoint trong DB tạm; dùng `check_trace`/`trial_pass`; chạy ma trận public và regression toàn bộ. Hash commit được lấy từ Git, số test lấy từ output lệnh đã chạy. Các lệnh kiểm chứng trong phiên này do Codex thực thi; không ghi nhận đây là một lượt thành viên tự chạy độc lập.

Không sử dụng API model thật trong code lab. Không sinh số liệu benchmark, run id hoặc điểm hidden khi chưa có bằng chứng. Thành viên cần tự đọc và chạy lại các lệnh trên để xác nhận khả năng giải thích code khi báo cáo.

## 6. Tự đánh giá

Đối chiếu theo bằng chứng thực hiện, phần workflow CP2/CP3 và integration Bước 4 đã hoàn thành: có hai commit kỹ thuật của cá nhân, 14 trường hợp test bổ sung (5 workflow + 9 integration) và regression toàn bộ xanh sau khi nhận code đồng đội.

Các giới hạn cần ghi nhận:

- Các tình huống integration crash dùng claim public C-001 và seed 11; ma trận public chuẩn kiểm thêm các claim/seed quy định. Kết quả này chưa chứng minh pass rate hoặc must-pass trên hidden.
- Chưa có số liệu benchmark/cost/variance hay kết luận chọn kiến trúc thuộc phần evaluation. Không suy ra các kết quả đó từ số test pass.

Nhận xét chủ quan về mức độ hiểu bài, điểm mạnh và điểm cần cải thiện do thành viên tự bổ sung sau khi tự review và chạy lại. Báo cáo này chỉ tổng hợp phần việc và kết quả có thể đối chiếu.
