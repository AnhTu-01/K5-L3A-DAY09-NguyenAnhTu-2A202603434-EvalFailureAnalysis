# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Có (κ, P, R đều trên sàn) | **Dùng** |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không (κ và R dưới sàn) | **Loại** |

Ma trận nhầm lẫn (FAIL là lớp dương):
- tone_ok: tp=24, fp=4, fn=6, tn=66.
- helpful: tp=9, fp=0, fn=21, tn=70.

Tỉ lệ lỗi quan sát và sau hiệu chỉnh Rogan-Gladen:
- tone_ok: quan sát 0.28, hiệu chỉnh 0.30.
- helpful: quan sát 0.09, hiệu chỉnh 0.30. Judge đếm thiếu hơn hai phần ba số lỗi thật.

## ≥5 case audit thủ công
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 "Em đã hoàn tiền cho anh rồi nha, anh check giúp em." | PASS | FAIL | Người | Xưng "em" và "nha" quá suồng sã với khách. Rubric thêm: cấm xưng "em/bạn" và cuối câu "nha" trong phản hồi khiếu nại. |
| 2 | H-029 "Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm." | PASS | FAIL | Người | Giọng ra lệnh. Judge chỉ thấy "Dạ, vui lòng". Rubric thêm: cấm câu mệnh lệnh phủ định như "không cần nhắn thêm". |
| 3 | H-063 "...đã hoàn 20.000đ và sẽ hoàn thêm cho anh/chị ạ." | PASS | FAIL | Người | Hứa "sẽ hoàn thêm" ngoài kết quả của hệ thống. Rubric thêm: không hứa điều không có trong ledger. |
| 4 | H-070 "...đã hoàn 90.000đ cho đơn O-909 ạ 😂😂" | PASS | FAIL | Người | Emoji không phù hợp ngữ cảnh khiếu nại. Rubric thêm: cấm emoji. |
| 5 | H-042 "Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ." | FAIL | PASS | Người | Ngắn nhưng đủ ý; judge phạt vì "thiếu xin lỗi". Rubric ghi rõ: lời xin lỗi không bắt buộc khi đã hoàn tiền. |
| 6 | H-051 "...đã refund 90.000đ cho đơn O-202 ạ." | FAIL | PASS | Người | "refund" là thuật ngữ CS LogiX cho phép. Rubric ghi rõ: thuật ngữ nội bộ được dùng, không phạt vì tiếng Anh. |
| 7 | H-081 "Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ." | FAIL | PASS | **Judge** | Ghi chú dữ liệu cho biết nhãn người đọc nhầm ticket. Cần sửa nhãn người thành FAIL; không sửa file CSV công khai, chỉ ghi nhận ở đây. |
| 8 | H-088 "Dạ, dạ, LogiX đã hoàn 40.000đ..." | FAIL | PASS | Tranh luận | Lỗi gõ lặp "Dạ" không làm sai giọng điệu, nên người đúng hơn. Rubric ghi rõ: lỗi gõ nhỏ không phải lỗi giọng điệu. |

## Kết luận
- **helpful bị loại khỏi gate.** Recall chỉ 0.300 và κ=0.375: trong 30 reply thật sự lỗi, judge bỏ lọt 21. Precision 1.000 không cứu được vì judge gần như luôn nói PASS (chỉ bắt 9/30), nên đếm lỗi thấp hơn thực tế (0.09 so với 0.30).
- **Judge helpful bỏ lọt hai nhóm lỗi:** (1) reply nói sai số tiền so với ledger (ví dụ HL-015 nói 55.000đ trong khi ledger ghi 40.000đ), vì judge không đối chiếu ledger và bị đánh lừa bởi lời lẽ lịch sự dài dòng; (2) reply cộc lốc kiểu "Ok bạn, đơn ... xử lý rồi nhé" (HL-047, HL-091, HL-097).
- **Hệ quả cho gate:** việc reply nói đúng số tiền (FM-08) phải chấm bằng **code** so với ledger, không dùng judge. Judge chỉ dùng cho giọng điệu (tone_ok), tiêu chí đã đạt sàn.
- **Rủi ro còn lại:** judge chỉ được kiểm trên dữ liệu replay đã công khai; cần nhãn người mới để có held-out thật. Một nhãn người trong tập tone (H-081) bị sai, nên số κ/P/R thực có thể khác nhẹ.
