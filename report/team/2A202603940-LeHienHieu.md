# Báo cáo cá nhân — MSSV_HoTen

## 1. Thông tin thành viên

- Họ tên: Lê Hiền Hiếu
- MSSV: 2A202603940
- Email: 26ai.hieulh@vinuni.edu.vn
- GitHub: hieulhaiwork

## 2. Phần việc phụ trách
- Phụ trách thiết kế và lập trình kiến trúc Shape A — Deterministic Workflow trong [file](../../src/lab8/shapes/workflow.py).
- Đảm bảo luồng xử lý đền bù hoàn toàn bằng code (hard-coded logic) để loại bỏ rủi ro ảo giác từ LLM.
- Xử lý cơ chế tiêm lỗi (Crash Injection) để vượt qua bài kiểm tra độ bền hệ thống.

## 3. Đóng góp cụ thể
- Commit chính: `02659b9`
- Hoàn thành Checkpoint 2 (CP2): Xây dựng luồng thực thi 8 bước tuần tự cho workflow. Đã cấu hình để hệ thống tự động bóc tách thông tin từ get_claim_view, xác thực bằng lookup_order, tính toán số tiền đền bù bằng hàm compute_compensation thay vì dùng AI.
- Hoàn thành Checkpoint 3 (CP3): Xử lý cơ chế Crash Injection. Đảm bảo hệ thống vẫn ghi nhận dấu vết (trace log) hợp lệ ngay cả khi tiến trình bị đánh sập ngay trước/sau khi gọi issue_refund.
- Quyết định kỹ thuật:
    - Áp dụng nguyên tắc "Draft then Commit": Đặt hàm gọi LLM API `complete()` ngay sau khi tính toán xong proposal và trước khi gọi lệnh ghi cơ sở dữ liệu issue_refund. Việc này giúp tối ưu hóa code (tránh lặp ở các nhánh điều kiện) và đảm bảo an toàn giao dịch nếu API của LLM bị gián đoạn.
    - Quản lý chặt chẽ ngân sách (Budget) bằng cách gọi thủ công budget.add_tool(tool_cost()) trước mỗi công cụ đọc (read tools).

## 4. Bằng chứng
- Vượt qua 100% kiểm thử Benchmark: Báo cáo tại [benchmark_workflow](../../src/reports/benchmark_workflow.json) (chạy trên các public claims) cho thấy:
    - pass_rate: 1.0 (70/70 lượt chạy thành công).
    - seed_variance: 0.0 (Không dao động kết quả dù chạy với seed 11, 22, 33, 44 hay 55).
    - mean_model_calls: Đúng 1.0 lần gọi model cho mỗi kịch bản.
- Vượt qua 100% kiểm định độ bền: Báo cáo tại [benchmark_workflow_crash](../../src/reports/benchmark_workflow_crash.json) ghi nhận crash_safety: 20/20 (vượt qua tất cả các kịch bản đứt gãy giao dịch).
- Ngoài ra code đã pass các bài pytest của CP1+CP2 và CP3:
```(python)
python -m pytest -q -m student -o addopts= -k workflow
..............................................................
62 passed, 240 deselected in 4.83s
```
và
```(python)
python -m pytest -q
..............................................................
72 passed, 248 deselected in 6.98s

```

## 5. Công cụ AI đã dùng

Công cụ, dùng vào việc gì, và bạn đã tự kiểm tra kết quả thế nào (xem [RULES.md](../../RULES.md)).
- Công cụ: Google Gemini (Mô hình hội thoại).
- Dùng vào việc gì:
    - Tóm tắt chủ đề của bài và nội dung cần làm
    - Gợi ý các bước cần thực hiện trong luồng 8 bước trong workflow.py.
    - Giải thích ý nghĩa của các file báo cáo benchmark và hệ thống cổng kiểm duyệt (gates).
- Tự kiểm tra kết quả: Tôi đã không chép code một cách mù quáng mà đã xác thực lại bằng cách yêu cầu AI giải thích rõ từng bước làm, lí do làm vậy, đặt các câu hỏi phản biện "Vì sao không làm ...?". Tiếp đó chạy thực tế toàn bộ các lệnh kiểm định nội bộ (python -m pytest -q -m student -o addopts= -k workflow; python -m lab8.smoke, python -m pytest -q, lab8.benchmark, lab8.crash_test) trên máy cá nhân để bảo đảm code chạy đúng 100% không báo lỗi.


## 6. Tự đánh giá
- Hoàn thành tốt nhiệm vụ được giao.
- Đã hiểu được ranh giới bảo mật giữa việc cho AI tự quyết định so với việc dùng AI như một công cụ hỗ trợ giao tiếp trong khi logic lõi bị kiểm soát bằng Code truyền thống (Workflow).
- Nắm vững cách xây dựng hệ thống đủ sức khỏe trong giao dịch cơ sở dữ liệu khi đối mặt với sự cố hệ thống giả lập.
...
