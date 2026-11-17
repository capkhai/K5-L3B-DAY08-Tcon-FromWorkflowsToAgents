# Team

## Thông tin nhóm

- Tên nhóm:
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-TenNhom-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt:

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Vũ Văn Trường | 2A202603910 | tini.vu.0@gmail.com | Sz3RO | Shape C (orchestrator + handoff) |
|   2 |        |      |       |        |         |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Vũ Văn Trường | Shape C (orchestrator + handoff) | `51b0383`: cài `orchestrator.py` và thêm lưới an toàn exception | `src/tests/test_orchestrator_shape.py` (17 test: unknown claim, handoff/trace sạch secret, injection 5 seed, trần theo đơn, 3 điểm crash, needs_info, denied, replay, lưới an toàn) |

## Cá nhân

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
