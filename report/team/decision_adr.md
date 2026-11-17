# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: d1e745d
- Run id dẫn chứng: R-workflow-C-001-s11; đối chiếu R-swarm-C-002-s55; src/reports/benchmark.json
- Pass rate / pass^5 / seed min-max / variance: 1,000 / 1,000 / 1,000–1,000 / 0 (70/70 trial public)
- Cost per success (mô phỏng, VND): 28,79
- Crash safety: 20/20 (src/reports/crash.json, suite host); T12 workflow đạt trong ma trận student 248/248
- Secret leak / approval bypass: Không có trial workflow bị evaluator public ghi nhận lỗi leak/bypass; các test student tương ứng đạt. Chưa có số đếm hidden, không suy rộng sang hidden.

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Đề xuất workflow vì task có luật nghiệp vụ và luồng đọc–tính–ghi rõ ràng. Trên cùng 14 claim và seed 11,22,33,44,55, workflow, single và orchestrator đều đạt 70/70 trial. Workflow có mức tự chủ thấp nhất, cost/success 28,79 so với 29,94 của single và 57,25 của orchestrator. Swarm có 69/70 trial và cost/success 49,57. Số liệu lấy từ file benchmark do công cụ sinh.

Bản code và bằng chứng đánh giá được chốt tại commit `d1e745d`, bao gồm bản sửa workflow để crash truyền ra đúng contract.

## Có đáng đổi lấy multi-agent không

Hiện chưa có lợi ích public đủ để chấp nhận thêm điều phối và chi phí. Chỉ xem xét đổi khi task có nhánh điều tra độc lập hoặc thiếu dữ liệu mà workflow không xử lý được, và benchmark mới cho thấy cải thiện độ đúng/độ bền đủ bù chi phí. Không kết luận mọi bài toán đều nên dùng workflow.

## Trace và bằng chứng

Workflow ghi `quote`, `decision`, `error`, `crash` và trả `trace_path` theo contract v1. Không ghi ticket thô, parent secret, SĐT, địa chỉ, tên hàng hoặc internal note. Các trace nằm trong `src/traces/`, chỉ dùng cục bộ và không commit. Benchmark kiểm contract và các dấu hiệu lộ dữ liệu qua evaluator chính thức; không tự tuyên bố đã kiểm mọi kênh ngoài phạm vi scanner.

## Giới hạn

MockLLM không phải model sản xuất; latency là `unavailable`. Giá mô phỏng phụ thuộc Budget được implementation ghi nhận; steps là số event, không phải latency. Khác biệt prompt, số lần gọi tool/model và mức chi tiết trace là yếu tố gây nhiễu khi quy kết lợi ích cho topology. Chưa chạy hidden nên chưa xác nhận ngưỡng 0,75. JSON giữ nguyên do công cụ sinh. Quyết định cần nhóm rà soát trước khi nộp.
