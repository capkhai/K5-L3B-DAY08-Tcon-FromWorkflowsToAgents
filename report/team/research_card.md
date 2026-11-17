# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 — Failure taxonomy |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Cemri và cộng sự, Why Do Multi-Agent LLM Systems Fail?, NeurIPS 2025; https://arxiv.org/abs/2503.13657 ; nghiên cứu thực nghiệm trên execution traces, không phải production report |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | MAST phân loại lỗi MAS thành các nhóm thiết kế hệ thống, lệch phối hợp giữa agent và kiểm chứng tác vụ. Taxonomy giúp phân tích nguyên nhân vượt ra ngoài tỷ lệ thành công tổng hợp. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Paper phân tích 1600+ trace từ 7 framework, với các tác vụ code, toán và agent tổng quát. Lab này chỉ dùng MockLLM, 14 claim giả lập và lỗi cố ý; phân loại T02 là diễn giải của nhóm, không phải kết luận paper về LogiX-VN. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Nếu tắt quyền cho ticket ghi đè delay từ order, C-002 seed 55 sẽ chuyển về denied; dự kiến sửa 1/70 trial, pass rate tăng khoảng 1,43 điểm phần trăm và pass^5 tăng 7,14 điểm phần trăm. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Dùng snapshot swarm trong research/swarm_verified.py; chỉ làm điều kiện REFERENCE_WEAKNESS luôn False. Giữ MockLLM, prompt, tools, giá, corpus, 5 seed và evaluator. Chỉ đổi metadata shape/run ID để tách trace. Không sửa swarm tham chiếu hoặc dữ liệu; mỗi trial dùng database mới. |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Diễn giải T02 là lỗi kiểm chứng: không giữ order làm căn cứ khi ticket mâu thuẫn. Đo trial sai, pass rate, pass^5, seed variance, cost/success và model calls bằng lab8.benchmark. |

## Kết quả ablation

- Lệnh đã chạy trong `src/` bằng Python của venv (cùng module/lệnh có thể chạy sau khi activate):

```powershell
.\.venv\Scripts\python.exe -m lab8.benchmark --shapes swarm,swarm_verified --extra-shape swarm_verified=research.swarm_verified:run_claim --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/research_r2.json
```

- Run id / file report: `src/reports/research_r2.json`; `R-swarm-C-002-s55` và `R-swarm_verified-C-002-s55`.
- Kết quả ủng hộ hypothesis trong bộ public đã kiểm:

| Metric | Swarm gốc | Tắt override |
| --- | ---: | ---: |
| Trial đạt | 69/70 | 70/70 |
| Pass rate | 98,57% | 100% |
| pass^5 | 92,86% | 100% |
| Seed variance | 0,0008163265 | 0 |
| Cost/success (VND mô phỏng) | 49,57 | 48,72 |
| Tổng chi phí mô phỏng | 3420,12 | 3410,10 |
| Model calls trung bình | 3 | 3 |

C-002 seed 55 chuyển từ `resolved` sang `denied`. Bản gốc có thêm một lần tính lại quote, nên tổng chi phí giảm 10,02; cost/success còn chịu ảnh hưởng của mẫu số tăng từ 69 lên 70. Test `tests/test_research_r2.py` kiểm bản thử nghiệm qua evaluator, giữ nguyên điểm yếu của reference và giữ 3 model calls ở C-002. Bản thử nghiệm là can thiệp bỏ nhánh lỗi đã biết, không cài thêm agent verifier hay chứng minh lợi ích topology.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
