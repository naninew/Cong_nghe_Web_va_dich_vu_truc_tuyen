# Đặc Tả Module Lõi Anki (Anki Core Specification)

## 1. Giới thiệu tổng quan
Module `anki_core` là phần lõi logic của hệ thống, được đóng gói độc lập từ logic của Anki chính thức (`anki`). Module này đảm nhiệm toàn bộ các phép tính toán thuật toán, kết xuất mẫu thẻ, và xử lý tập tin dữ liệu `.apkg`, hoàn toàn độc lập với các thư viện bên ngoài như giao diện PyQt hay trình biên dịch Rust lúc chạy (runtime).

Vị trí mã nguồn: `backend/app/anki_core/`

---

## 2. Các trạng thái thẻ và hàng đợi (Card States & Queues)

Mỗi thẻ flashcard trong hệ thống tuân thủ nghiêm ngặt mô hình trạng thái của Anki:

### 2.1. Phân loại kiểu thẻ (`type` - Card Type)
- `0` - **New**: Thẻ mới được tạo hoặc nhập từ bộ thẻ, chưa từng được người dùng học.
- `1` - **Learning**: Thẻ đang trong giai đoạn học ban đầu (chưa hoàn thành các bước học - learning steps).
- `2` - **Review**: Thẻ đã tốt nghiệp (graduated) và chuyển sang chu kỳ ôn tập tính theo ngày.
- `3` - **Relearning**: Thẻ review nhưng bị trả lời sai (Lapse) và phải quay lại học các bước học lại.

### 2.2. Phân loại hàng đợi thẻ (`queue` - Card Queue)
- `0` - **New Queue**: Danh sách thẻ mới chờ học.
- `1` - **Learning Queue**: Danh sách thẻ đang trong các bước học trong ngày (tính theo phút).
- `2` - **Review Queue**: Danh sách thẻ đã đến ngày cần ôn tập (`due <= today`).
- `3` - **Day-learn Queue**: Danh sách thẻ đang học có bước học chuyển tiếp qua ngày hôm sau.
- `-1` - **Suspended**: Thẻ bị tạm ngưng thủ công hoặc do đạt ngưỡng khó (Leech). Thẻ sẽ không xuất hiện trong phiên học.
- `-2` - **User Buried**: Thẻ bị người dùng tạm ẩn trong ngày hôm nay. Tự động mở lại vào ngày mai.
- `-3` - **Sibling Buried**: Thẻ anh em (sinh từ cùng 1 Note) bị tạm ẩn tự động để tránh lộ gợi ý trong cùng một ngày.

---

## 3. Thuật toán Spaced Repetition (SRS)

Module `anki_core` hỗ trợ cả 2 thuật toán: **SM-2 (Anki v2/v3)** và **FSRS v4.5**.

### 3.1. Thuật toán SM-2 (Anki v2/v3 Algorithm)

#### A. Cấu hình mặc định (Deck Config Defaults)
- Các bước học ban đầu (`learning_steps`): `[1, 10]` (1 phút, 10 phút).
- Các bước học lại khi quên (`relearning_steps`): `[10]` (10 phút).
- Khoảng cách tốt nghiệp (`graduating_interval`): 1 ngày.
- Khoảng cách dễ (`easy_interval`): 4 ngày.
- Hệ số dễ ban đầu (`starting_ease`): 2500 (tức 250%).
- Ngưỡng tối thiểu của hệ số dễ (`minimum_ease`): 1300 (tức 130%).
- Hệ số phạt khi khó (`hard_factor`): 1.2.
- Hệ số thưởng khi dễ (`easy_bonus`): 1.3.
- Hệ số điều chỉnh khoảng cách (`interval_modifier`): 1.0.

#### B. Quy tắc tính toán chuyển đổi trạng thái khi đánh giá thẻ

Khi người dùng đánh giá thẻ bằng 1 trong 4 nút:
1. **Button 1: Again (Sai / Quên)**
   - Thẻ chuyển sang trạng thái `Learning` hoặc `Relearning`.
   - Đặt lại bước học: chuyển về bước đầu tiên (ví dụ 1 phút).
   - Tăng bộ đếm quên: `lapses = lapses + 1`.
   - Giảm hệ số dễ: `factor = max(1300, factor - 200)` (-20%).
   - Nếu `lapses >= leech_threshold` (mặc định 8): gắn tag `leech`, và tùy chọn tạm ngưng thẻ (`suspend`).
2. **Button 2: Hard (Khó)**
   - Nếu thẻ đang học: Lấy trung bình cộng giữa bước hiện tại và bước tiếp theo.
   - Nếu thẻ đang ở chu kỳ Review:
     - `new_interval = max(previous_interval + 1, round(previous_interval * hard_factor * interval_modifier))`.
     - Giảm hệ số dễ: `factor = max(1300, factor - 150)` (-15%).
3. **Button 3: Good (Tốt / Đúng tiêu chuẩn)**
   - Nếu thẻ đang học và chưa phải bước cuối: Chuyển sang bước học tiếp theo (ví dụ từ 1m sang 10m).
   - Nếu thẻ đang ở bước học cuối cùng: Thẻ chính thức tốt nghiệp (Graduate), chuyển sang chu kỳ Review với `new_interval = graduating_interval` (1 ngày).
   - Nếu thẻ đang ở chu kỳ Review:
     - `new_interval = max(previous_interval + 1, round(previous_interval * (factor / 1000.0) * interval_modifier))`.
     - Hệ số `factor` giữ nguyên.
4. **Button 4: Easy (Rất dễ)**
   - Nếu thẻ đang học: Thẻ tốt nghiệp ngay lập tức không cần qua các bước sau, chuyển thẳng sang Review với `new_interval = easy_interval` (4 ngày).
   - Nếu thẻ đang ở chu kỳ Review:
     - `new_interval = max(previous_interval + 1, round(previous_interval * (factor / 1000.0) * easy_bonus * interval_modifier))`.
     - Tăng hệ số dễ: `factor = factor + 150` (+15%).

---

### 3.2. Thuật toán FSRS v4.5 (Free Spaced Repetition Scheduler)

FSRS mô phỏng trực tiếp đường cong trí nhớ con người thông qua 3 tham số:
1. **Stability ($S$)**: Độ ổn định của trí nhớ (tính theo ngày). Sau $S$ ngày, xác suất nhớ lại của người dùng giảm xuống còn 90%.
2. **Difficulty ($D$)**: Độ khó nội tại của thông tin trên thẻ (thang điểm từ 1 đến 10).
3. **Retrievability ($R$)**: Khả năng truy xuất lại thông tin tại thời điểm hiện tại:
   $$R(t, S) = \left(1 + \text{factor} \cdot \frac{t}{S}\right)^{\text{decay}}$$
   với $\text{factor} = 19/81$ và $\text{decay} = -0.5$.

#### Công thức tính khoảng cách ôn tập tiếp theo:
Dựa trên tỷ lệ duy trì mong muốn $R_{\text{target}}$ (Requested Retention, mặc định 0.90):
$$I = S \cdot \frac{\ln(R_{\text{target}})}{\ln(0.90)}$$

#### Cập nhật Độ khó ($D$) và Độ ổn định ($S$):
Khi người dùng chấm điểm $G \in \{1: \text{Again}, 2: \text{Hard}, 3: \text{Good}, 4: \text{Easy}\}$:
- Độ khó mới được tính toán bằng cách bù trừ độ khó hiện tại và phản hồi của người dùng, kết hợp hiệu ứng hoàn nguyên về giá trị trung bình (mean reversion).
- Độ ổn định mới:
  - Nếu trả lời đúng ($G > 1$): Độ ổn định tăng theo cấp số nhân dựa trên khả năng gợi nhớ và độ khó ($S'_{\text{success}} = S \cdot (1 + \text{factor} \cdot \dots)$).
  - Nếu trả lời sai ($G = 1$): Độ ổn định bị sụt giảm mạnh ($S'_{\text{fail}} = \text{stability\_after\_lapse}$).

---

## 4. Công cụ dựng mẫu thẻ (Template & Rendering Engine)

Thư mục: `backend/app/anki_core/template/`

Hệ thống hỗ trợ dựng cả 2 mặt thẻ: Mặt trước (`qfmt`) và Mặt sau (`afmt`), áp dụng mã CSS từ Notetype.

### 4.1. Thay thế trường dữ liệu (Mustache Replacements)
- `{{FieldName}}`: Thay thế bằng nội dung của trường dữ liệu tương ứng trong Note.
- `{{#FieldName}} ... {{/FieldName}}`: Khối điều kiện hiển thị: chỉ hiển thị nội dung bên trong nếu trường `FieldName` có dữ liệu (không rỗng).
- `{{^FieldName}} ... {{/FieldName}}`: Khối điều kiện nghịch đảo: chỉ hiển thị nội dung bên trong nếu trường `FieldName` rỗng.

### 4.2. Các bộ lọc đặc biệt (Built-in Filters)
- `{{text:FieldName}}`: Loại bỏ hoàn toàn các thẻ HTML, chỉ giữ lại chuỗi văn bản thuần túy.
- `{{hint:FieldName}}`: Tạo nút bấm dạng HTML tương tác: khi chưa bấm hiện nút `Show Hint`, khi người dùng bấm vào sẽ mở rộng hiển thị nội dung gợi ý.
- `{{FrontSide}}`: Sử dụng trong mặt sau (`afmt`), tự động đưa toàn bộ HTML của mặt trước vào mặt sau, đồng thời tự động loại bỏ các thẻ âm thanh để không bị phát lặp lại hai lần.

### 4.3. Xử lý Thẻ Điền Vào Chỗ Trống (Cloze Deletion)
Cú pháp: `{{c1::đáp án::gợi ý}}`
- Ở mặt trước của thẻ số 1 (Card 1): Hiển thị `[...]` hoặc `[gợi ý]`.
- Ở mặt sau của thẻ số 1: Hiển thị `<span class="cloze">đáp án</span>`.
- Các thẻ cloze khác (ví dụ `c2`, `c3`) hiển thị nguyên văn nội dung đáp án của chúng mà không ẩn.

### 4.4. Xử lý Phát Âm & Đa Phương Tiện
Cú pháp trong Anki: `[sound:mazii_v_N1_139713.mp3]`
- Trình dựng tự động chuyển cú pháp trên thành thẻ Audio HTML5:
  ```html
  <div class="audio-player" data-src="/media/user_id/mazii_v_N1_139713.mp3">
    <button class="play-btn" onclick="playAudio(this)">
      <span class="material-symbols-outlined">volume_up</span>
    </button>
  </div>
  ```
- Nếu tập tin âm thanh không tồn tại cục bộ (như trường hợp bộ thẻ mẫu Mazii), hệ thống kích hoạt Web Speech API (Japanese Speech Synthesis) đọc trực tiếp từ vựng/câu ví dụ.

---

## 5. Cấu trúc và Cơ chế Xử Lý Tập Tin APKG

Tập tin `.apkg` là một file nén ZIP chuẩn chứa:
1. `collection.anki21` (hoặc `collection.anki2`): Tập tin CSDL SQLite chứa toàn bộ cấu trúc:
   - `col`: Chứa 1 bản ghi lưu cấu hình chung, danh mục Decks (JSON), danh mục Notetypes (JSON), Deck Configurations (JSON).
   - `notes`: Chứa các bản ghi ghi chú. Các trường dữ liệu được nối với nhau bằng ký tự phân tách đặc biệt `\x1f` (Unit Separator, mã ASCII 31).
   - `cards`: Chứa các bản ghi thẻ học (liên kết tới `nid` - note ID và `did` - deck ID).
   - `revlog`: Chứa lịch sử các lần ôn tập thẻ trước đây.
2. `media`: File JSON ánh xạ số thứ tự tập tin nén (`"0"`, `"1"`, `"2"`) sang tên file thực tế (ví dụ `{"0": "image.png", "1": "audio.mp3"}`).
3. Các file đa phương tiện được lưu trực tiếp dưới dạng các file có tên là các con số tương ứng trong file zip.

### Quy trình Nhập (Import) Tốc Độ Cao
Đối với các bộ dữ liệu lớn như `Tieng_Nhat_Tong_hop_N1_to_N5.apkg` (gần 60,000 thẻ):
1. Giải nén SQLite vào vùng nhớ tạm thời.
2. Đọc và tạo cây bộ thẻ (Decks) theo quan hệ cha con (phân cách bởi `::`).
3. Đọc và tạo Notetypes kèm trường (Fields) và mẫu thẻ (Templates).
4. Sử dụng con trỏ SQLite duyệt từng batch 5,000 notes và cards.
5. Thực hiện Bulk Insert vào PostgreSQL bằng câu lệnh `COPY` hoặc `executemany` trên một kết nối duy nhất trong 1 Transaction.
6. Thời gian xử lý toàn bộ 59,378 thẻ: **3 đến 5 giây**.
