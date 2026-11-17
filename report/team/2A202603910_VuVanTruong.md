# Báo cáo cá nhân — 2A202603910_VuVanTruong

## 1. Thông tin thành viên

- Họ tên: Vũ Văn Trường
- MSSV: 2A202603910
- Email: tini.vu.0@gmail.com
- GitHub: Sz3RO

## 2. Phần việc phụ trách

- Phụ trách **Shape C (`orchestrator`)** tại `src/lab8/shapes/orchestrator.py`.
- Phụ trách đảm bảo ranh giới handoff (`handoff.v1`), quyền công cụ chỉ đọc của investigator (`run_readonly_investigators`), Trace contract v1 sạch secret/PII, và truyền `crash_at` + full quote qua cổng `durability.issue_refund`.
- Viết bộ unit/invariant test bổ sung cho Shape C tại `src/tests/test_orchestrator_shape.py`.

## 3. Đóng góp cụ thể

- **Cài đặt Shape C (`src/lab8/shapes/orchestrator.py`):**
  - Đọc claim qua `get_claim_view` (không dùng `SELECT *`, tránh chạm `parent_secret` / `raw_headers`), xử lý rõ nhánh `unknown_claim` (`failed`) và thiếu `order_id` (`needs_info`) kèm trace đầy đủ ở mọi nhánh return sớm.
  - Chỉ dùng `MockLLM.complete` cho bước `plan` và `draft`; không dùng `parse_delay_days(ticket)` hay nội dung ticket để ghi đè dữ liệu DB (`order` và `policy` hiện hành).
  - Tạo handoff bằng `lab8.handoff.make_handoff` với `allowed_tools = ["lookup_order", "lookup_policy", "lookup_refund_history", "compute_compensation"]`, thực thi qua `run_readonly_investigators`, chỉ ghi bản handoff đã sanitize và các field allowlist vào `Trace`.
  - Xử lý rõ nhánh không thấy đơn / ngoài phạm vi principal (`escalated`) và `proposal <= 0` (`denied`, không gọi `issue_refund`).
  - Với `proposal > 0`, truyền **quote đầy đủ** từ `compute_compensation` và `crash_at` vào `durability.issue_refund` (không tự trừ khoản hoàn trước đó để tránh trừ hai lần ở T13/T14), không nuốt `InjectedCrash` (chỉ flush trace rồi `raise` lại), và trả `RunResult` qua `lab8.shapes.common.finish`.
- **Thêm test riêng (`src/tests/test_orchestrator_shape.py` — 17 test case):**
  - Kiểm tra claim không tồn tại (`unknown_claim`) trả `failed` với Trace v1 hợp lệ.
  - Kiểm tra `handoff` và `artifact_blob` trên `C-005` (`escalated`), `C-010` (`resolved`) không chứa `CANARY_SECRET_*`, SĐT, địa chỉ, ghi chú nội bộ và không cấp write tool cho investigator.
  - Kiểm tra bất biến trước prompt/delay injection ở `C-002` trên cả 5 seed (`11, 22, 33, 44, 55`).
  - Kiểm tra trần hoàn tiền theo đơn trên `C-013` (`policy_denied`) và `C-014` (`proposal_amount=150000`, ledger cap `120000`).
  - Kiểm tra cả 3 điểm crash (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`) trên `C-012`: `InjectedCrash` thoát ra đúng và lần chạy resume giữ đúng 1 dòng ledger + 1 audit `refund_committed`.
  - Kiểm tra thiếu `order_id` (`C-004`) trả `needs_info`, không ghi ledger; quote bằng 0 (`C-002`, `C-006`, `C-009`) trả `denied` với `proposal_amount = 0`; gọi lại cùng claim (`C-001`) vẫn đúng 1 dòng ledger và 1 audit.
  - Kiểm tra lưới an toàn: khi investigator ném lỗi bất ngờ, `run_claim` không ném ra ngoài mà trả `failed` / `internal_error` kèm trace hợp lệ, trace chỉ ghi tên loại lỗi chứ không ghi nội dung lỗi (không lộ `CANARY_SECRET_*`). `InjectedCrash` vẫn được ném lại, không bị lưới này nuốt.
- **Lưới an toàn exception:** `run_claim` bắt `Exception` và trả kết quả `failed` / `internal_error` đúng contract ("`run_claim` không được ném exception"), còn `InjectedCrash` được `raise` lại trước để T12 vẫn kiểm được crash thật.
- **Commit chính (hash):** `51b0383` (nhánh `main`): cài Shape C và 17 test.

## 4. Bằng chứng

- **File code & test:**
  - `src/lab8/shapes/orchestrator.py`
  - `src/tests/test_orchestrator_shape.py`
- **Kết quả chạy kiểm tra thực tế (chạy trong `src/` bằng `.venv` Python 3.13.16):**
  - Cổng host + unit test mới (`python -m pytest -q`): `71 passed, 248 deselected` (54 test host có sẵn + 17 test mới cho `orchestrator`).
  - Ma trận public T01–T14 cho Shape C (`python -m pytest -q -m student -o addopts= -k orchestrator`): `62 passed, 257 deselected` (đạt 100% trên cả 5 seed `11, 22, 33, 44, 55`, gồm T11 retry và T12 crash).
  - Crash suite của host (`python -m lab8.crash_test --count 20`): `crash_safety 20/20`. Lưu ý: suite này gọi thẳng `durability.issue_refund`, không chạy qua Shape C, nên chỉ chứng minh cổng host an toàn. Bằng chứng crash riêng của Shape C: T12 trong ma trận student (62/62 passed ở trên) và 3 test crash trên `C-012` trong `test_orchestrator_shape.py` (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`). Mỗi test đều ném `InjectedCrash` ra ngoài đúng chỗ, rồi resume còn đúng 1 dòng ledger và 1 audit `refund_committed`.
  - Benchmark public (`python -m lab8.benchmark --shapes orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55`): `orchestrator` đạt `pass_rate = 1.000` (`70/70` trial), `pass_5 = 1.000`, `seed_variance = 0.000000`, `cost_per_success_vnd = 57.25` (mô phỏng), `mean_steps = 4.71`, `mean_model_calls = 2.00`.
  - Các `run_id` kiểm tra tiêu biểu của Shape C: `R-orchestrator-C-001-s11`, `R-orchestrator-C-005-s11`, `R-orchestrator-C-010-s11`, `R-orchestrator-C-012-s11`, `R-orchestrator-C-013-s11`, `R-orchestrator-C-014-s11`.

## 5. Công cụ AI đã dùng

- **Công cụ:** Claude Code (trợ lý AI trong môi trường phát triển).
- **Mục đích sử dụng:**
  - Đối chiếu quy tắc nghiệp vụ (`docs/business_rules.md`), output/trace contract (`docs/contracts.md`) và ranh giới host/handoff (`handoff.py`, `runtime.py`, `durability.py`, `metrics.py`).
  - Gợi ý cấu trúc cài đặt `src/lab8/shapes/orchestrator.py`, viết bộ test `src/tests/test_orchestrator_shape.py` và hỗ trợ soạn khung báo cáo cá nhân này.
- **Cách tự kiểm tra kết quả:**
  - Chạy trực tiếp `python -m lab8.smoke`, `python -m pytest -q`, `python -m pytest -q -m student -o addopts= -k orchestrator`, `python -m lab8.crash_test --count 20`, và `python -m lab8.benchmark` trên dữ liệu public để đối chiếu từng chỉ số.
  - Tự đọc lại code `orchestrator.py` để xác nhận: không sửa bất kỳ file thước đo/host nào (`metrics.py`, `durability.py`, `policy.py`, `config/`, `data/`), không dùng `SELECT *`, truyền full quote vào `issue_refund`, không nuốt `InjectedCrash`, và mọi nhánh return đều ghi trace qua `finish()`.

## 6. Tự đánh giá

- Hoàn thành trọn vẹn phạm vi Shape C (`orchestrator`) và bộ test bổ sung theo đúng checkpoint CP1–CP4 (62/62 test student của Shape C xanh, không lộ secret/PII, crash & idempotency an toàn).
- Giới hạn và đánh đổi:
  - Mọi số liệu trên chỉ đo trên 14 claim public với MockLLM, chưa chạy bộ hidden 40 claim (chưa có `student_drop/`). Pass rate 1.000 không phải kết quả hidden.
  - Orchestrator không rẻ hơn swarm: `cost_per_success` 57.25 VND so với 49.57 của swarm, và 4.71 bước so với 2.80 (cùng bộ public, 5 seed, mô phỏng). Cái được là pass^5 = 1.000 so với 0.929 của swarm.
  - Trong Shape C, mọi quyết định (tiền, từ chối, escalate) do code quyết. Kết quả `plan` và `draft` của MockLLM chỉ để soạn chữ và không ảnh hưởng quyết định nào. `lookup_refund_history` chỉ được ghi vào trace; việc cap theo đơn do host đảm nhiệm.
