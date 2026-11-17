# Báo cáo cá nhân — 2A202603883_CaoPhamTanKhai

## 1. Thông tin thành viên

- Họ tên: Cao Phạm Tân Khải
- MSSV: 2A202603883
- Email: cptkhai@gmail.com
- GitHub: cptkhai

## 2. Phần việc phụ trách

- Phụ trách **Shape B (`single`)** tại `src/lab8/shapes/single.py`.
- Thiết kế và triển khai máy trạng thái vòng lặp ReAct bounded tối đa 8 bước qua `lab8.runtime.run_react`.
- Đảm bảo các ranh giới an toàn và quy tắc cốt lõi của bài lab:
  - Chỉ cấp tool đọc (`lookup_order`, `compute_compensation`) cho agent; model không được cấp quyền ghi tiền.
  - Tiền do code `lab8.tools.compute_compensation` tính toán dựa trên policy có hiệu lực, không để MockLLM tự sinh số tiền bồi thường.
  - Nguồn sự thật khách quan là thuộc tính đơn hàng từ DB (`lookup_order`), hoàn toàn miễn nhiễm với việc khách hàng khai khống ngày trễ hay tấn công prompt injection qua nội dung ticket (khắc phục điểm yếu của Swarm ở seed 55).
  - Tuân thủ Trace contract v1: flush trace và ghi nhận sự kiện crash trước khi re-raise `InjectedCrash`.
  - Chuyển giao toàn bộ quote bồi thường vào cổng host `durability.issue_refund`, tuân thủ kiểm tra approval, trần hoàn tiền theo đơn (T13, T14) và chống ghi trùng lặp (idempotency).
- Viết bộ unit/invariant test độc lập bổ sung cho Shape B tại `src/tests/test_single_shape.py`.

## 3. Đóng góp cụ thể

- **Cài đặt Shape B (`src/lab8/shapes/single.py`):**
  - Đọc claim an toàn qua `get_claim_view(conn, claim_id)`: chỉ lấy các trường trong allowlist (`claim_id`, `principal_id`, `order_id`, `ticket`), không đọc `parent_secret` hay `raw_headers_json`. Xử lý trường hợp claim không tồn tại (`failed`, `unknown_claim`) kèm trace hợp lệ.
  - Xây dựng hàm suy luận `decide(seen)` cho vòng lặp ReAct:
    - Bước 0: Kiểm tra `order_id`. Nếu đơn hàng không có mã đơn (`order_id == None`), dừng ngay với `needs_info` mà không cố đoán mã đơn từ câu chữ trong ticket. Nếu có `order_id`, triệu gọi tool `lookup_order`.
    - Bước 1: Tiếp nhận kết quả `lookup_order`. Nếu `not order_view["visible"]` (đơn không tồn tại hoặc sai principal), dừng ngay với `escalated`. Nếu hợp lệ, đưa thông tin đơn hàng vào `compute_compensation`.
    - Bước 2: Đọc kết quả tính tiền. Nếu `amount_vnd <= 0`, dừng với `denied` (không gọi `issue_refund`). Nếu `amount_vnd > 0`, đưa ra đề xuất bồi thường `proposal = amount_vnd`.
  - Lớp bọc `_Trace`: Cho phép ghi nhận sự kiện crash và chủ động flush trace xuống đĩa trước khi re-raise `InjectedCrash`, bảo đảm không vi phạm lỗi `missing_trace` khi crash.
  - Tương tác cổng Host: Với đề xuất hợp lệ, truyền **toàn bộ quote** vào `durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)` để host tự động kiểm tra approval và trừ trần các khoản đã hoàn trước đó cùng đơn. Đóng gói kết quả bằng `lab8.shapes.common.finish`.
- **Viết bộ test riêng cho Shape B (`src/tests/test_single_shape.py` — 6 test case lớn):**
  - `test_single_unknown_claim_returns_failed_with_valid_trace`: Kiểm tra claim không tồn tại trả `failed` với Trace contract v1 hợp lệ.
  - `test_single_trace_omits_secrets_and_pii`: Kiểm tra trace trên `C-005` (`escalated`) và `C-010` (`resolved`) không chứa bất kỳ token `CANARY_SECRET_*`, số điện thoại, địa chỉ hay ghi chú nội bộ nào.
  - `test_single_ignores_ticket_delay_override_across_all_seeds`: Chứng minh bất biến trên `C-002` qua cả 5 seed (`11, 22, 33, 44, 55`): Agent luôn từ chối vì DB ghi trễ 2 ngày, không bị lừa bởi câu chữ "trễ 5 ngày" trong ticket (trong khi Swarm fail ở seed 55).
  - `test_single_respects_per_order_caps_t13_and_t14`: Kiểm tra trần theo đơn trên `C-013` (`policy_denied`) và `C-014` (`proposal_amount=150000`, ledger cap đúng phần chênh `120000`).
  - `test_single_crash_points_and_resume_keeps_one_refund`: Kiểm tra toàn diện 3 điểm crash (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`) trên `C-012`: `InjectedCrash` thoát ra đúng và lần chạy resume giữ đúng 1 dòng ledger + 1 audit `refund_committed`.
  - `test_single_missing_order_and_zero_quote_rules`: Kiểm tra thiếu `order_id` (`C-004`) trả `needs_info`, quote bằng 0 / prompt injection "ignore policy" (`C-009`) trả `denied`.
- **Commit chính:** `f171f3a` (cài đặt `single.py`) và commit bổ sung `src/tests/test_single_shape.py`.

## 4. Bằng chứng

- **File code & test:**
  - `src/lab8/shapes/single.py`
  - `src/tests/test_single_shape.py`
- **Kết quả chạy kiểm tra thực tế (chạy trong `src/` trên `.venv` Python 3.11):**
  - Cổng host + toàn bộ unit test (`python -m pytest -q`): **`77 passed, 248 deselected`** (54 test host gốc + 17 test Shape C + 6 test Shape B mới).
  - Ma trận public T01–T14 cho riêng Shape B (`python -m pytest -q -m student -o addopts= -k "single and not workflow and not orchestrator"`): **`122 passed`** (toàn bộ 62/62 test cases của Shape B xanh 100%, gồm 12 claim public × 5 seed, T11 retry và T12 crash).
  - Format kiểm tra nộp bài (`python -m lab8.check_submission`):
    ```text
    [ OK ] shape single: format đúng, 12/12 claim public pass ở seed 11
    ```
  - Benchmark public (`python -m lab8.benchmark --shapes single,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55`):
    - `single`: đạt `pass_rate = 1.000` (70/70 trials), `pass_5 = 1.000`, `seed_variance = 0.000000`, `cost_per_success_vnd = 29.94` (mô phỏng), `mean_steps = 5.57`.
    - So sánh với `swarm`: `swarm` chỉ đạt pass rate `0.986`, `pass^5 = 0.929`, bị biến thiên `var = 0.000816`, và chi phí cao hơn gần 40% (`49.57 VND`).

## 5. Công cụ AI đã dùng

- **Công cụ:** Antigravity (Google DeepMind Agentic AI Assistant).
- **Mục đích sử dụng:**
  - Hỗ trợ phân tích tài liệu đặc tả nghiệp vụ (`docs/business_rules.md`), Trace contract v1 (`docs/contracts.md`), và cơ chế ReAct loop trong `lab8/runtime.py`.
  - Tham vấn thiết kế luồng quyết định trong `decide()` và cấu trúc xử lý flush trace an toàn khi gặp ngoại lệ `InjectedCrash`.
  - Hỗ trợ xây dựng bộ test ma trận biên trong `src/tests/test_single_shape.py` và tổng hợp số liệu benchmark.
- **Cách tự kiểm tra kết quả:**
  - Chạy kiểm thử tự động trực tiếp trên terminal với `smoke`, `pytest`, `check_submission`, và script `benchmark`.
  - Tự rà soát code để đảm bảo: không chỉnh sửa các file lõi bị cấm (`metrics.py`, `durability.py`, `policy.py`, `config/`), không dùng câu lệnh `SELECT *`, không đưa secret/PII vào trace, và tuân thủ nghiêm ngặt ranh giới quyền hạn giữa model và host.

## 6. Tự đánh giá

- Hoàn thành đầy đủ 100% mục tiêu của Shape B (Single ReAct Agent), vượt qua toàn bộ 62 test student và các tiêu chí must-pass (không lộ secret, không bypass approval, crash an toàn tuyệt đối).
- Bài học rút ra & Đánh giá kiến trúc:
  - Shape B ReAct cho thấy tính hiệu quả vượt trội so với Swarm: độ chính xác cao hơn (1.000 vs 0.986), không bị phương sai (variance = 0), và tiết kiệm chi phí gọi model hơn đáng kể (29.94 VND vs 49.57 VND).
  - Khẳng định định hướng bài học: Khi nghiệp vụ đòi hỏi tính chính xác và bảo mật cao, việc kết hợp vòng lặp suy luận ReAct có kiểm soát với ranh giới Host nghiêm ngặt mang lại kết quả tin cậy hơn việc phân tán quyền hạn cho các cụm multi-agent tự do.
