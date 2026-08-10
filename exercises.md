# Phiếu Phản Ánh — K4 Ngày 12

> Họ và tên: Phạm Minh Hiếu Mã học viên: 2A202601562

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `api_token` không có giá trị mặc định nên app chết ngay khi
khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà việc
"chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Lúc deploy lên Render, tôi tạo Blueprint xong nhưng quên điền giá trị cho
> `API_TOKEN` (biến này khai `sync: false` nên Render không tự lấy từ repo,
> phải nhập tay). App vẫn khởi động, `/healthz` vẫn 200 bình thường, nhưng
> `/readyz` trả về `500` với traceback rõ ràng: `ValidationError: api_token
Field required`. Nhờ vậy tôi biết ngay là thiếu biến môi trường và vào
> đúng chỗ để sửa. Nếu `api_token` có mặc định kiểu `"changeme"`, app sẽ
> khởi động và chạy "bình thường" — chỉ có điều bất kỳ ai gõ đúng
> `Bearer changeme` cũng gọi được `/chat` miễn phí, và tôi sẽ không biết
> chuyện đó xảy ra cho tới khi nhìn hóa đơn LLM hoặc log request lạ, tức là
> đã trễ.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/chat` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Một dòng log thật lấy từ lúc tôi gọi `/chat` (client `sv-test`, tin nhắn
> thứ hai trong cùng hội thoại):
>
> ```json
> {
>     "event": "chat_completed",
>     "severity": "INFO",
>     "ts": "2026-08-10T09:06:12+00:00",
>     "client_id": "sv-test",
>     "prompt_tokens": 41,
>     "completion_tokens": 43,
>     "usd_cost": 3.195e-5
> }
> ```
>
> Hai việc làm được mà `print("đã trả lời xong")` không làm được:
>
> 1. **Lọc/gộp theo trường** — vì là JSON có `client_id` và `usd_cost` là
>    khóa riêng biệt, tôi có thể `jq` hoặc đưa vào log platform để hỏi
>    "client nào tiêu nhiều tiền nhất hôm nay", cộng dồn `usd_cost` theo
>    `client_id`. Chuỗi text tự do thì phải viết regex đoán mò mới lấy được
>    số tiền ra.
> 2. **Cảnh báo tự động theo `severity`** — Google Cloud Logging (và hầu
>    hết log platform) đọc đúng khóa `severity` viết hoa để tô màu, lọc, và
>    bật cảnh báo khi có dòng `ERROR`. `print()` không có khái niệm mức độ
>    nên không thể tự động phân biệt "log tường thuật" với "log cần báo
>    động ai đó".

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t chat:single .
docker build -t chat:multi .
docker images | grep chat
```

| Bản               | Dung lượng        |
| ----------------- | ----------------- |
| 1 stage (bản đầu) | 1730 MB (1.73 GB) |
| Multi-stage       | 270 MB            |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Số đo lấy từ `docker images` thật trên máy tôi (build cả hai bản từ cùng
> `requirements.txt`). Chênh lệch ~1.46GB gồm ba phần chính:
>
> 1. **Base image đầy đủ vs slim** — `python:3.11` mang theo toàn bộ
>    compiler, dev headers, tài liệu... trong khi `python:3.11-slim` chỉ có
>    runtime tối thiểu.
> 2. **Build tool bị bỏ lại** — bản 1-stage `pip install` trực tiếp trên
>    image cuối cùng nên mọi công cụ build (nếu package nào cần biên dịch)
>    và pip cache đều nằm luôn trong image. Bản multi-stage cài dependency
>    ở stage `builder` riêng rồi chỉ `COPY --from=builder /install
/usr/local` — chỉ mang kết quả cài đặt sang, vứt bỏ toàn bộ builder.
> 3. **Source code thừa** — bản 1-stage `COPY . .` copy nguyên thư mục repo
>    (kể cả file không cần cho runtime), còn bản multi-stage chỉ `COPY app`
>    và `COPY utils`.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Dockerfile của tôi tách hai bước: `COPY requirements.txt .` +
> `RUN pip install ...` ở stage `builder`, rồi mới `COPY app ./app` +
> `COPY utils ./utils` ở stage `runtime`. Khi sửa một ký tự trong
> `app/main.py` rồi build lại: layer `COPY requirements.txt .` và
> `RUN pip install` ở stage builder **được dùng lại từ cache** hoàn toàn
> (Docker so hash `requirements.txt`, không đổi thì không chạy lại); chỉ
> layer `COPY app ./app` trở đi ở stage runtime phải chạy lại. Kết quả:
> build lại chỉ mất vài giây thay vì tải lại hết dependency.
>
> Nếu đặt `COPY . .` lên trước `RUN pip install` thì mọi lần sửa dù chỉ một
> dấu phẩy trong code cũng làm layer `COPY . .` đổi hash → Docker coi mọi
> layer phía sau (kể cả `pip install`) là "không còn hợp lệ" và chạy lại từ
> đó — cài lại toàn bộ thư viện mỗi lần build, dù chẳng có thư viện nào
> thay đổi.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Chuỗi sự kiện: (1) một dependency Python trong `requirements.txt` có lỗ
> hổng thực thi mã từ xa (RCE), hoặc code tự viết xử lý input không an
> toàn → (2) kẻ tấn công lợi dụng lỗ hổng đó để chạy lệnh shell bên trong
> container → (3) nếu process đang chạy bằng root, lệnh shell đó có toàn
> quyền root **trong container** — đọc/ghi mọi file, cài thêm phần mềm độc
> hại, đọc secret trong biến môi trường của process khác → (4) nếu container
> đó có lỗ hổng thoát container (kernel exploit) hoặc bị mount nhầm thứ
> nhạy cảm từ host (ví dụ `/var/run/docker.sock`), root-trong-container dễ
> dàng leo thang thành root-trên-host.
>
> `USER appuser` cắt đứt chuỗi ngay ở bước (3): kẻ tấn công vẫn thực thi
> được mã (bước 2 vẫn xảy ra), nhưng process chạy dưới quyền `appuser`
> (uid 10001) không có quyền ghi ra ngoài những gì `appuser` được cấp —
> không cài được package hệ thống, không đụng được file thuộc root, không
> tự leo thang lên root trong chính container. Thiệt hại bị giới hạn lại
> ngay từ bước đầu, dù lỗ hổng ở bước (1) vẫn tồn tại.

---

### Câu 6 — Bearer token (CP3)

Vì sao 401 phải kèm header `WWW-Authenticate: Bearer`? Và vì sao ta trả **cùng
một** thông báo lỗi cho cả ba trường hợp (thiếu header, sai scheme, sai token)
thay vì nói rõ sai ở đâu cho người dùng dễ sửa?

> `WWW-Authenticate: Bearer` là bắt buộc theo chuẩn HTTP (RFC 7235/6750):
> đây là cách server nói cho client biết **kiểu xác thực nào được chấp
> nhận**. Không có header này, một client/thư viện HTTP tự động (ví dụ
> trình duyệt hoặc SDK) không biết phải gửi lại request kèm scheme gì —
> nó chỉ thấy "401" trơn mà không biết phải làm gì tiếp theo.
>
> Trả cùng một thông báo cho cả ba trường hợp (thiếu header, sai scheme,
> sai token) là để không tặng thông tin cho kẻ đang dò token. Nếu tôi trả
> lỗi khác nhau kiểu "thiếu header" vs "token sai" vs "scheme sai", kẻ tấn
> công có thể dùng phản hồi đó như một "oracle": họ thử hàng loạt giá trị,
> hễ thông báo đổi từ "thiếu header" sang "token sai" là biết họ đã đoán
> đúng _cấu trúc_ request, chỉ còn phải dò đúng token — thu hẹp không gian
> tấn công. Trả chung một câu, cộng với so token bằng `secrets.compare_digest`
> (không rò rỉ qua thời gian phản hồi), đảm bảo request sai ở đâu cũng chỉ
> nhận đúng một loại phản hồi, không có manh mối nào để khai thác.

---

### Câu 7 — Token bucket (CP3)

Với `capacity=10`, `refill_per_minute=10`: một client im lặng 10 phút rồi gửi
liên tiếp. Nó gửi được bao nhiêu request trước khi bị 429? Nếu bỏ đoạn
`min(capacity, ...)` trong `available()` thì con số đó thành bao nhiêu, và tại sao?

> Với `capacity=10`, `refill_per_minute=10`, xô đầy tối đa là 10 token dù
> im lặng bao lâu (nhờ `min(self.capacity, tokens)`). Vậy im lặng 10 phút
> rồi gửi liên tiếp: client được **10 request** đi qua, request thứ 11 bị
> chặn 429 — tôi đã tự kiểm chứng đúng con số này trên bản deploy thật
> (spam 15 request liên tiếp: 10 request đầu trả 200, từ request 11 trở đi
> trả 429).
>
> Nếu bỏ `min(capacity, ...)`: sau 10 phút im lặng, token tích được là
> `10 phút × 10 token/phút = 100 token`, nên client bắn được **100 request**
> liên tiếp trước khi bị chặn — gấp 10 lần capacity danh nghĩa. Lý do: xô
> không còn giới hạn trên, số token cứ cộng dồn tuyến tính theo thời gian
> im lặng, im lặng càng lâu thì được phép bắn càng nhiều trong một giây,
> đánh mất hoàn toàn mục đích "làm mượt" lưu lượng của token bucket.

---

### Câu 8 — Ngân sách theo ngày (CP3)

So sánh hạn mức $30/tháng với hạn mức $1/ngày cho cùng một client. Giả sử có sự
cố khiến một client gọi liên tục từ 2h sáng. Với mỗi cách, thiệt hại tối đa là
bao nhiêu và service tự hồi phục khi nào?

> **Hạn mức $30/tháng:** sự cố lúc 2h sáng có thể chạy tới khi tiêu hết
> $30 rồi mới bị chặn — thiệt hại tối đa cả **$30**, và nếu $30 đó bị tiêu
> hết ngay trong đêm đầu tiên thì client bị khóa cho đến khi sang tháng
> sau mới tự hồi phục (có thể là vài chục ngày sau).
>
> **Hạn mức $1/ngày (cách lab dùng, key `spend:<client>:<YYYY-MM-DD>`):**
> thiệt hại tối đa chỉ **$1** cho lần sự cố đó, vì `check()` chặn ngay khi
> tổng chi trong ngày UTC hiện tại vượt ngưỡng. Đến 00:00 UTC hôm sau, khóa
> Redis đổi sang ngày mới (key khác) nên `spent()` tự trả về `0.0` — service
> tự hồi phục hoàn toàn không cần ai can thiệp, sớm nhất là vài giờ sau
> (tùy sự cố xảy ra lúc mấy giờ), không phải chờ hết cả tháng.
>
> Tóm lại: hạn mức ngày giới hạn thiệt hại xuống còn 1/30 so với hạn mức
> tháng, và thời gian tự hồi phục ngắn hơn rất nhiều.

---

### Câu 9 — /healthz khác /readyz (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Nếu gộp `/healthz` và `/readyz` thành một endpoint kiểm tra cả Redis:
>
> 1. `t = 0s` — Redis rớt kết nối.
> 2. `t = 0s → ~10s` (lần liveness probe kế tiếp) — cả 3 container gọi
>    `store.ping()` bên trong `/healthz`, cả 3 đều nhận `False` (do
>    `ping()` bắt exception và trả `False`) → cả 3 endpoint trả `503`.
> 3. Orchestrator đọc `/healthz` là **liveness** probe, thấy `503` liên
>    tiếp vượt ngưỡng `retries` → hiểu nhầm là "process chết, cần khởi động
>    lại" → **restart cả 3 container cùng lúc**, dù process Python của cả 3
>    vẫn đang chạy tốt, chỉ là Redis tạm mất kết nối.
> 4. `t = 30s` — Redis hồi phục. Nhưng lúc này cả 3 container đang trong
>    quá trình restart (dừng, khởi động lại, load lại app) — quá trình đó
>    tốn thêm vài giây tới vài chục giây tùy tốc độ boot.
> 5. Kết quả: một sự cố Redis 30 giây (đáng lẽ chỉ cần `/readyz` báo
>    "not ready" để load balancer tạm ngừng đẩy traffic, còn container vẫn
>    sống) biến thành **downtime toàn cụm** kéo dài hơn 30 giây — vì
>    liveness probe không nên phụ thuộc dependency ngoài, đúng nguyên tắc
>    tách `/healthz` (process còn sống không) khỏi `/readyz` (đã sẵn sàng
>    nhận traffic chưa) mà CP4 yêu cầu.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> Deploy lên Render qua Blueprint (`render.yaml`) xong, `/healthz` trả
> `200` bình thường nhưng `/readyz` trả về **`500 Internal Server Error`**
> thay vì `503` như mong đợi khi Redis chưa sẵn sàng.
>
> Tìm nguyên nhân: mở tab **Logs** trên dashboard Render, đọc traceback
> đầy đủ. Dòng cuối cùng là:
> `pydantic_core._pydantic_core.ValidationError: 1 validation error for
Settings — api_token: Field required`, với stack trace trỏ đúng vào
> `get_store()` → `get_redis_client()` → `get_settings()` → `Settings()`.
> Từ đó suy ra: biến môi trường `API_TOKEN` chưa thực sự được gán trên
> service, dù đã tạo Blueprint xong (vì `API_TOKEN` khai `sync: false` nên
> Render bắt buộc nhập tay, và bước đó bị bỏ sót lúc setup). `/chat` vẫn
> trả `401` bình thường vì code chỉ đọc `Settings` **sau khi** có header
> `Authorization` hợp lệ — nên lỗi chỉ lộ qua `/readyz` (đọc Settings ngay
> từ đầu request).
>
> Cách sửa: vào đúng service `day12-chat` (không phải service Redis) →
> tab **Environment** → điền giá trị cho `API_TOKEN` → **Save Changes** →
> Render tự động redeploy. Gọi lại `/readyz` sau khi build xong, nhận về
> `200 {"status":"ready","redis":true}`.
