# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

## Case của nhóm (Nguyễn Anh Tú, 2A202603434)

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, run ID `R-seeded_regression-C-002-s11` |
| Triệu chứng | Grader Lab 8 `trial_pass` fail ("status resolved != denied"). Reply #6 nói "LogiX đã hoàn 20.000đ cho đơn O-202" và ledger đúng là 20.000đ, nhưng nhãn là 0 (khách ghi trễ 5 ngày, DB chỉ 2 ngày). |
| Bước sai đầu tiên | Event #3 `model_override {"delay_days": 5}`: agent đè số ngày của DB (2) bằng số trong ticket (5). |
| Vì sao là bước *đầu tiên* | Event #1 `handoff` đúng (chỉ tool đọc) và event #2 `investigator` trả đúng `delay_days: 2` từ DB. Từ event #3 trở đi mọi thứ sai theo: quote #4 tính 20.000đ, rồi reply #6 báo đúng số sai. |
| Failure mode | FM-03 ticket_trust (`docs/failure_taxonomy.md`) |
| Đối chứng | `fixed C-002@11`: không có event `model_override`; quote #3 `amount_vnd 0, no_entitlement`; reply "chưa đủ điều kiện hoàn"; ledger=0. |
| Regression test | `tests/test_lab9_trace_case_anhtu.py::test_ticket_trust_is_caught_on_seeded_regression_and_not_on_fixed`: trên `seeded_regression` thì `DbFactKept` và `RefundAmountCorrect` đều False; trên `fixed` đều True. |
| Chưa chắc chắn | Trace không cho biết **vì sao** agent chọn số trong ticket (MockLLM không có lý do để đọc). Chỉ chứng minh được rằng số trong ticket thắng số của DB. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
