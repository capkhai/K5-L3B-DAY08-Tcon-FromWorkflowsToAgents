# Team

## Thông tin nhóm

- Tên nhóm:
- Lớp: L3B
- Repo nhóm: `K5-L3A-DAY08-TenNhom-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/capkhai/K5-L3B-DAY08-Tcon-FromWorkflowsToAgents ; `main` ; `d1e745d`

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Vũ Văn Trường | 2A202603910 | tini.vu.0@gmail.com | Sz3RO | Shape C (orchestrator + handoff) |
|   2 | Vũ Văn Bình | 2A202603831 | binhvuvan2004@gmail.com | hnib1908 | Shape D (swarm: kiểm thử, benchmark và phân tích lỗi) |
|   3 | Lê Hiền Hiếu | 2A202603940 | hieulh.work@gmail.com | hieulhaiwork | Shape A (deterministic workflow) |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Vũ Văn Trường | Shape C (orchestrator + handoff) | `51b0383`: cài `orchestrator.py` và thêm lưới an toàn exception | `src/tests/test_orchestrator_shape.py` (17 test: unknown claim, handoff/trace sạch secret, injection 5 seed, trần theo đơn, 3 điểm crash, needs_info, denied, replay, lưới an toàn) |
| Vũ Văn Bình | D — swarm: test có sẵn 62 passed; benchmark 69/70 trial; phân tích T02 seed 55; tổng hợp báo cáo | `1c61baa`: thêm test trace và báo cáo đánh giá swarm | `src/tests/test_swarm_delay_evidence.py::test_swarm_t02_trace_explains_seed_dependent_delay_override` (AI hỗ trợ; 1 passed) |
| Lê Hiền Hiếu | Shape A (workflow) | `02659b9`: Hoàn thiện `workflow.py` xử lý 8 bước deterministic, tích hợp tool_cost và fix lỗi nuốt InjectedCrash; pass test các testcases yêu cầu | `src/tests/test_public_matrix.py::test_t12_crash_before_checkpoint_does_not_double_pay[workflow]` (Đã fix khối try/except thành try/finally để pass test kiểm định crash, 62/62 passed) |

## Cá nhân

Phần D đã có bản báo cáo tại `report/team/2A202603831_VuVanBinh.md`. Bằng chứng hiện có: `src/reports/swarm_benchmark.json`, run ID `R-swarm-C-002-s55` (sai) và `R-swarm-C-002-s11` (đúng). Đã thêm test đối chiếu trace với hỗ trợ AI, commit kỹ thuật `1c61baa`; cần tự đọc hiểu test trước khi nộp.

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## MSSV_HoTen

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-

## 2A202603910_VuVanTruong

Báo cáo đầy đủ: [report/team/2A202603910_VuVanTruong.md](report/team/2A202603910_VuVanTruong.md)

### Phần việc phụ trách

- Shape C (`orchestrator`) tại `src/lab8/shapes/orchestrator.py`: handoff `handoff.v1` với tool chỉ đọc, investigator chỉ đọc, trace contract v1 sạch secret/PII, truyền `crash_at` và quote đầy đủ vào `durability.issue_refund`.
- Bộ test bổ sung cho Shape C tại `src/tests/test_orchestrator_shape.py`.

### Đóng góp cụ thể

- Cài Shape C: mọi quyết định (tiền, từ chối, escalate) do code quyết, không đọc nội dung ticket; model chỉ soạn chữ. Quote đầy đủ từ `compute_compensation` được truyền vào host (T13, T14); `InjectedCrash` được ghi trace rồi ném lại.
- Thêm lưới an toàn exception: `run_claim` không ném exception ra ngoài (trả `failed` / `internal_error` với trace hợp lệ), trừ `InjectedCrash` để T12 vẫn kiểm được crash thật.
- Thêm 17 test cho Shape C.

### Bằng chứng

- Cổng host `python -m pytest -q`: 71 passed (54 test sẵn có + 17 test mới).
- Ma trận student `python -m pytest -q -m student -o addopts= -k orchestrator`: 62/62 passed.
- Benchmark public (orchestrator, 5 seed): pass rate 1.000, pass^5 1.000, variance 0, cost/success 57.25 VND mô phỏng, 4.71 bước. Chưa chạy bộ hidden.
- Crash suite của host `crash_safety 20/20` (suite này không chạy qua Shape C; bằng chứng crash của Shape C là T12 và 3 test crash trên C-012).
- Commit: `51b0383`.

## 2A202603831_VuVanBinh

Bổ sung tích hợp (AI hỗ trợ, commit `d1e745d`): kiểm thử A/B/C/D, sửa workflow nuốt crash (`except` → `finally`), benchmark chung, crash suite, thí nghiệm R2 và test `src/tests/test_research_r2.py`. Kết quả: 73 test mặc định và 248 test student đạt; crash safety 20/20. Hash bản tích hợp là `d1e745d`; `1c61baa` bên dưới vẫn là commit kỹ thuật phần D ban đầu.

Báo cáo đầy đủ: [report/team/2A202603831_VuVanBinh.md](report/team/2A202603831_VuVanBinh.md)

### Phần việc phụ trách

- Shape D — swarm tham chiếu: đọc code, chạy kiểm thử và benchmark; đối chiếu trace để giải thích lỗi T02 ở seed 55.

### Đóng góp cụ thể

- Chạy bộ test student riêng swarm: 62 passed.
- Chạy benchmark 14 claim public với seed 11, 22, 33, 44, 55; tổng hợp kết quả vào báo cáo nhóm.
- Phân tích C-002: seed 55 ghi đè dữ liệu order từ 2 thành 5 ngày theo ticket, dẫn tới quyết định sai.
- Thêm test `test_swarm_t02_trace_explains_seed_dependent_delay_override` với hỗ trợ AI; đối chiếu trace, quote, trạng thái và xác nhận dữ liệu order gốc vẫn giữ nguyên.

### Bằng chứng

- Commit kỹ thuật: `1c61baa`.
- Test: `src/tests/test_swarm_delay_evidence.py`; kết quả riêng: 1 passed.
- Benchmark: `src/reports/swarm_benchmark.json`; đạt 69/70 trial, pass rate 98,57%, pass^5 92,86%, variance 0,0008163265, cost/success 49,57 VND mô phỏng, mean/p95 steps 2,80/3,00.
- Run ID đối chiếu: `R-swarm-C-002-s11` và `R-swarm-C-002-s55`. Trace chỉ dùng cục bộ, không commit.

## 2A202603940_LeHienHieu

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-


