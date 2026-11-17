# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm:
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`): `c1bbc3b`

## 2. Mục tiêu và cách tiếp cận

Nhóm xử lý cùng bài toán hoàn phí vận chuyển bằng workflow, single agent, orchestrator và swarm. Mục tiêu là chọn mức tự chủ thấp nhất vẫn đáp ứng luật nghiệp vụ, approval, chống hoàn trùng và bảo vệ dữ liệu. A/B/C được triển khai riêng; D dùng swarm tham chiếu để đối chứng. Sau tích hợp, nhóm chạy cùng 14 claim public và 5 seed, mỗi trial có database mới.

## 3. Giải pháp

| Shape | Cách xử lý | Ranh giới code / model |
| --- | --- | --- |
| A — workflow | Đọc claim, kiểm quyền truy cập order, tính quote, gọi host theo thứ tự cố định | Model chỉ soạn phản hồi; code tính tiền và gọi host |
| B — single | Vòng `run_react`, tối đa 8 bước; đọc order và tính quote, sau đó code gọi host | Quyết định tool đọc theo trạng thái; model không được ghi refund |
| C — orchestrator | Tạo handoff cho investigator chỉ đọc, nhận quote rồi gọi host | Handoff qua `make_handoff`, field/tool theo allowlist; trace qua `safe_dump` |
| D — swarm | Peer đọc ticket, investigator kiểm đơn; nhánh tham chiếu có thể tin số ngày khách khai | Giữ nguyên điểm yếu để đo độ dao động; host vẫn kiểm approval và chống hoàn trùng |

Cả bốn shape dùng `compute_compensation` và truyền quote đầy đủ vào `durability.issue_refund`; host áp approval và trần theo đơn. Trace không ghi ticket thô, secret, SĐT, địa chỉ hoặc ghi chú nội bộ. Workflow ghi `quote`, `decision`, `error`, `crash`; orchestrator có thêm `handoff` và `investigator`.

## 4. Kết quả

Bảng so sánh 4 shape trên bộ public (từ `src/reports/benchmark.json`): pass rate, pass^5, seed min–max, variance, cost/success, mean/p95 steps. Kèm crash safety (`src/reports/crash.json`) và, nếu có, kết quả tự kiểm trên `student_drop/`.

### 4.1. Kết quả hiện có của D — Swarm

Nguồn số liệu: `src/reports/swarm_benchmark.json`, chạy trên 14 claim public với 5 seed `11,22,33,44,55` (70 trial). Backend là MockLLM; mỗi trial dùng SQLite mới; mốc policy `as_of=2026-11-15`.

| Chỉ số | Swarm |
| --- | ---: |
| Trial đạt | 69/70 |
| Pass rate | 98,57% |
| pass^5 (claim đạt cả 5 seed) | 92,86% (13/14 claim) |
| Pass rate seed 11, 22, 33, 44 | 100% mỗi seed |
| Pass rate seed 55 | 92,86% |
| Seed min–max | 92,86–100% |
| Seed variance | 0,0008163265 |
| Cost/success | 49,57 VND mô phỏng |
| Mean / p95 steps | 2,80 / 3,00 |
| Latency | `unavailable` |

Kiểm thử riêng swarm bằng lệnh sau trong `src/` đạt `62 passed, 240 deselected` khi kiểm tra lại ngày 17/11/2026:

```powershell
python -m pytest -q -m student -o addopts= -k swarm
```

Lệnh tạo benchmark riêng đã thực hiện trong `src/`:

```powershell
python -m lab8.benchmark --shapes swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/swarm_benchmark.json
```

### 4.2. Phân tích trường hợp T02 — C-002

Benchmark chỉ có một trial sai: `R-swarm-C-002-s55`, lý do `status resolved != denied`. Dữ liệu đơn O-202 xác nhận giao trễ 2 ngày, không có hỏng hàng được xác minh; ticket khách khai trễ 5 ngày. Theo `docs/business_rules.md`, nguồn sự thật là dữ liệu order và policy hiện hành; đơn này phải bị từ chối vì chưa đạt ngưỡng trễ 3 ngày.

Đối chiếu hai trace cục bộ cho cùng claim:

| Bằng chứng | Seed 11 | Seed 55 |
| --- | --- | --- |
| Run ID | `R-swarm-C-002-s11` | `R-swarm-C-002-s55` |
| `investigator`: số ngày trễ từ order | 2 | 2 |
| Event `model_override` | Không có | Ghi đè thành 5 ngày |
| `quote.amount_vnd` | 0 | 20.000 |
| Trạng thái trong benchmark | `denied` — đúng | `resolved` — sai |

Nguyên nhân nằm ở nhánh `REFERENCE_WEAKNESS` trong `src/lab8/shapes/swarm_reference.py`: nếu số ngày đọc từ ticket khác dữ liệu order và `seed % 5 == 0`, swarm ghi đè `order["delay_days"]` bằng số ngày từ ticket rồi tính lại quote. Trong 5 seed được dùng, chỉ seed 55 kích hoạt điều kiện này. Điều kiện chia hết cho 5 áp dụng cho seed, độc lập với ngưỡng nghiệp vụ trễ ít nhất 3 ngày.

Kết luận: phép tính tiền bằng code vẫn có thể sai nghiệp vụ khi đầu vào từ nguồn đáng tin cậy bị thay bằng thông tin khách tự khai. Đây là điểm yếu có sẵn của swarm tham chiếu; nhóm giữ nguyên để đối chứng. Trace dùng để đối chiếu tại `src/traces/<run_id>.json`, không đưa vào commit.

### 4.3. Kết quả tích hợp bốn shape

Nguồn: `src/reports/benchmark.json`; cùng 14 claim × 5 seed, 70 trial/shape. Số bước là số event trong trace theo bộ đo của lab, không phải thời gian xử lý.

| Shape | Pass | pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean/p95 steps |
| --- | ---: | ---: | --- | ---: | ---: | --- |
| workflow | 100% | 100% | 100–100% | 0 | 28,79 | 1,86 / 2 |
| single | 100% | 100% | 100–100% | 0 | 29,94 | 5,57 / 6 |
| orchestrator | 100% | 100% | 100–100% | 0 | 57,25 | 4,71 / 5 |
| swarm | 98,57% | 92,86% | 92,86–100% | 0,0008163265 | 49,57 | 2,80 / 3 |

Sau sửa lỗi bắt crash ở workflow (mục 5), ma trận student đạt 248/248 test; bộ test mặc định sau thêm test R2 đạt 73/73. Crash suite đạt `20/20` trong `src/reports/crash.json`; suite này chủ yếu kiểm host, còn bằng chứng crash theo từng shape là test student T12. Chưa có kết quả hidden, không khẳng định đã qua ngưỡng hidden.

Đề xuất chọn workflow: cùng độ đúng public với single và orchestrator, mức tự chủ thấp và cost/success được bộ đo ghi nhận thấp nhất. Đây là so sánh các implementation hiện có; khác biệt prompt, hạch toán Budget và event trace cũng có thể ảnh hưởng cost/steps, chưa chứng minh topology là nguyên nhân duy nhất.

### 4.4. Thí nghiệm R2 — tắt ticket override

Giữ nguyên model, prompts, tool, corpus, seed, giá và evaluator; chỉ tắt quyền ghi đè số ngày từ ticket trong bản thử nghiệm `src/research/swarm_verified.py`. Swarm tham chiếu không bị sửa. Metadata shape/run ID đổi để tách trace, không đổi nghiệp vụ khác. Kết quả từ `src/reports/research_r2.json`: pass rate 98,57% → 100%, pass^5 92,86% → 100%, variance 0,0008163265 → 0; cost/success 49,57 → 48,72 VND mô phỏng. C-002 seed 55 được sửa đúng, số model call trung bình vẫn là 3. Chi tiết phương pháp và giới hạn xem research card.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

Khi tích hợp, lệnh `python -m pytest -q -m student -o addopts=` cho `1 failed, 247 passed`. Test lỗi là `test_t12_crash_before_checkpoint_does_not_double_pay[workflow]`, thông báo `crash did not fire`. Nguyên nhân: hàm `run_claim` ngoài cùng dùng `except:` để đóng connection nên nuốt luôn `InjectedCrash` được ném lại từ `_run`. Đổi thành `finally:` để luôn đóng connection và cho crash truyền ra đúng contract; chạy lại đạt `248 passed`. Không sửa host, policy, dữ liệu, evaluator hay swarm tham chiếu.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Nêu thêm giới hạn của nhóm và điều kiện làm kết luận thay đổi.

Kết quả chỉ bao phủ 14 claim public và 5 seed, không thay thế chấm hidden. MockLLM và lỗi cố ý không mô phỏng đầy đủ model thực tế. Cost là giá mô phỏng trên Budget được code ghi nhận, steps phụ thuộc mức chi tiết trace; không suy ra latency hay hiệu quả topology thuần túy. R2 chỉ loại bỏ một nhánh lỗi đã biết, không chứng minh verifier tổng quát xử lý được mọi mâu thuẫn. Cần đánh giá trên dữ liệu mới và model thực khi mở rộng bài toán.

## 8. Tài liệu tham khảo

- Tài liệu lab: `docs/business_rules.md`, `docs/contracts.md`, `docs/metrics.md`, `RULES.md`, `RUBRIC.md`.
- Cemri và cộng sự (2025), [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657), NeurIPS 2025. Dùng taxonomy để diễn giải R2; số liệu lab do công cụ tạo, không lấy từ paper.
