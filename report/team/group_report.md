# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm:
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`):

## 2. Mục tiêu và cách tiếp cận

Nhóm hiểu bài toán thế nào, chia việc ra sao, thứ tự làm bốn shape.

...

## 3. Giải pháp

Mô tả ba shape nhóm viết (workflow, single, orchestrator): mỗi shape đọc gì, quyết định gì, gọi host ra sao. Chỉ rõ ranh giới code / model (tham khảo [docs/architecture.md](../../docs/architecture.md)), cách handoff được sanitize và trace ghi những event nào.

...

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

### 4.3. Phần cần bổ sung khi tích hợp

Kết quả trên mới là benchmark riêng D. Cần chạy benchmark đủ A/B/C/D trong cùng điều kiện để tạo `src/reports/benchmark.json`, bổ sung bảng so sánh, crash safety từ `src/reports/crash.json`, rồi mới chốt kiến trúc. Chưa có cơ sở kết luận swarm tốt hơn các shape khác hoặc suy rộng kết quả này sang model thực tế.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

Lỗi gặp phải (kèm lệnh, output hoặc ảnh chụp) và cách nhóm xử lý.

...

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Nêu thêm giới hạn của nhóm và điều kiện làm kết luận thay đổi.

Kết quả riêng D mới bao phủ 14 claim public và 5 seed. Qua 62 test có sẵn không bảo đảm đúng mọi claim và mọi seed: benchmark vẫn ghi nhận T02 sai ở seed 55. Chi phí là VND mô phỏng, không phải hóa đơn API; chưa đo latency thực tế. Hướng cải thiện về thiết kế là giữ nguyên dữ liệu order làm căn cứ tính tiền, kiểm chứng khi ticket mâu thuẫn với order; chưa áp dụng thay đổi này vào swarm tham chiếu. Cần bổ sung kết quả A/B/C, crash suite và thí nghiệm đối chứng trước khi kết luận chung.

## 8. Tài liệu tham khảo

...
