# Hệ Thống Thiết Kế UI/UX (Cognitive Flow Design System)

## 1. Triết Lý Thiết Kế (Design Philosophy)
Hệ thống thiết kế **Cognitive Flow** được xây dựng dựa trên nguyên tắc: **Kết hợp giữa tính chuẩn xác của công cụ năng suất (SaaS Precision) với sự hứng khởi của cơ chế game hóa xúc giác (Tactile Gamification)**.

Mục tiêu cốt lõi:
- Xóa bỏ cảm giác ngột ngạt, nhàm chán khi phải học hàng nghìn thẻ flashcard.
- Giữ được sự tập trung cao độ (Deep Focus) trong phiên học thông qua việc tinh giản các yếu tố gây xao nhãng.
- **Quy tắc thẩm mỹ chuyên nghiệp**: Tuyệt đối **không sử dụng biểu tượng cảm xúc (emoji) kiểu AI-slop** (như 🚀, 🎉, 🤖, 💡, 🔥 trong các nhãn giao diện). Thay vào đó, toàn bộ biểu tượng được chuẩn hóa bằng hệ thống icon vector **Google Material Symbols Outlined**, mang lại cảm giác chỉn chu, hiện đại và cao cấp.

---

## 2. Bảng Màu Chuẩn (Color Architecture)

Hệ thống màu sắc sử dụng chuẩn Tailwind CSS kết hợp CSS Custom Properties, được định nghĩa từ `DESIGN.md`:

```css
:root {
  /* Nền và Bề mặt (Canvas & Surfaces) */
  --color-surface: #faf8ff;
  --color-surface-dim: #d2d9f4;
  --color-surface-bright: #faf8ff;
  --color-surface-container-lowest: #ffffff;
  --color-surface-container-low: #f2f3ff;
  --color-surface-container: #eaedff;
  --color-surface-container-high: #e2e7ff;
  --color-surface-container-highest: #dae2fd;
  --color-on-surface: #131b2e;
  --color-on-surface-variant: #464555;
  --color-outline: #777587;
  --color-outline-variant: #c7c4d8;

  /* Màu Chủ Đạo (Primary - Deep Cognitive Indigo) */
  --color-primary: #3525cd;
  --color-on-primary: #ffffff;
  --color-primary-container: #4f46e5;
  --color-on-primary-container: #dad7ff;
  --color-primary-fixed: #e2dfff;
  --color-on-primary-fixed: #0f0069;

  /* Màu Thứ Cấp (Secondary - Emerald Retention Mastery) */
  --color-secondary: #006c49;
  --color-on-secondary: #ffffff;
  --color-secondary-container: #6cf8bb;
  --color-on-secondary-container: #00714d;
  --color-secondary-fixed: #6ffbbe;
  --color-on-secondary-fixed: #002113;

  /* Màu Kích Hoạt Game (Tertiary - Amber Flame & Streaks) */
  --color-tertiary: #684000;
  --color-on-tertiary: #ffffff;
  --color-tertiary-container: #885500;
  --color-on-tertiary-container: #ffd4a4;
  --color-tertiary-fixed: #ffddb8;
  --color-on-tertiary-fixed: #2a1700;

  /* Màu Báo Lỗi / Cảnh Báo (Error / Lapse Crimson) */
  --color-error: #ba1a1a;
  --color-on-error: #ffffff;
  --color-error-container: #ffdad6;
  --color-on-error-container: #93000a;
}
```

### Ý nghĩa ứng dụng của màu sắc:
- **Primary (`#3525CD` / `#4F46E5`)**: Màu đại diện thương hiệu, các nút hành động chính (Primary CTA), trạng thái đang học (Active Learning).
- **Secondary (`#006C49` / `#10B981`)**: Đại diện cho sự ghi nhớ thành công (Mastery), câu trả lời đúng trong Quiz, nút Good/Easy, và thanh tiến độ đạt chuẩn.
- **Tertiary (`#684000` / `#F59E0B`)**: Dành riêng cho các thành tố game hóa: ngọn lửa chuỗi học liên tục (Streak Flame), thanh điểm kinh nghiệm (XP bar), số lượng thẻ học dở dang.
- **Error (`#BA1A1A` / `#EF4444`)**: Dành cho nút Again (quên thẻ), đáp án sai trong Quiz, cảnh báo thẻ Leech.

---

## 3. Hệ Thống Kiểu Chữ (Typography)

Sử dụng duy nhất phông chữ **Plus Jakarta Sans** cho toàn bộ hệ thống để đảm bảo sự liền mạch:

| Tên Style | Cỡ chữ / Dòng | Trọng số (Weight) | Ứng Dụng |
| :--- | :--- | :--- | :--- |
| `display` | 36px / 44px | 800 (ExtraBold) | Tiêu đề lớn trang chủ, con số thống kê chính |
| `display-mobile`| 30px / 38px | 800 (ExtraBold) | Tiêu đề lớn trên màn hình di động |
| `headline-lg` | 28px / 36px | 700 (Bold) | Tiêu đề các mục lớn, tên bộ thẻ chính |
| `headline-md` | 22px / 28px | 600 (SemiBold) | Tiêu đề Card, mặt thẻ Flashcard |
| `headline-sm` | 18px / 24px | 600 (SemiBold) | Tiêu đề nhỏ, tên các phương án trắc nghiệm |
| `body-lg` | 16px / 24px | 400 (Regular) | Nội dung giải thích chi tiết, câu ví dụ dài |
| `body-md` | 14px / 20px | 400 (Regular) | Văn bản chuẩn toàn trang web |
| `body-bold` | 14px / 20px | 600 (SemiBold) | Nhãn cần nhấn mạnh trong bảng hoặc form |
| `label-md` | 13px / 18px | 600 (SemiBold) | Nhãn nút bấm, tab điều hướng |
| `label-sm` | 12px / 16px | 600 (SemiBold) | Thẻ trạng thái (Status Pills), phím tắt bàn phím |
| `caption` | 11px / 14px | 500 (Medium) | Chú thích phụ, thông số thuật toán |

> [!TIP]
> Tất cả các con số đếm thời gian, điểm XP, số thẻ đáo hạn đều được áp dụng thuộc tính `font-variant-numeric: tabular-nums` để số không bị co giật khi thay đổi liên tục.

---

## 4. Các Thành Phần Giao Diện Xúc Giác (Tactile Components)

### 4.1. Nút Bấm Xúc Giác 3D (3D Tactile Buttons)
Khác với các nút phẳng mờ nhạt, nút bấm trong Memora có độ nổi vật lý với bóng đổ đáy đặc trưng:
- Trạng thái nghỉ (Resting): `box-shadow: 0 3px 0 0 #tinted-darker-color;`
- Trạng thái di chuột (Hover): Tăng độ sáng hoặc đổ bóng nổi hơn nhẹ.
- Trạng thái nhấn (Active/Pressed): `transform: translateY(2px); box-shadow: none;` mang lại cảm giác lún phím thật như nhấn nút bàn phím cơ.

### 4.2. Khối Lật Thẻ Flashcard 3D (3D Perspective Flip Card)
- Sử dụng hiệu ứng CSS 3D Transforms: `perspective: 1000px`, `transform-style: preserve-3d`.
- Chiều cao tối thiểu 360px trên Desktop, có hiệu ứng các lớp thẻ xếp chồng bên dưới (Card Stack Layers) thể hiện số lượng thẻ còn lại trong xấp.
- Tự động hiển thị nút nghe phát âm (`R`), nút xem gợi ý ngữ cảnh (`H`), và nút cắm cờ ghi nhớ (`F`).

### 4.3. Thanh Đánh Giá 4 Nút Lặp Lại Ngắt Quãng (SRS Rating Bar)
Cố định ở chân khung học:
1. **[1] Again**: Nền trắng viền đỏ, phím tắt `[1]`, nhãn `< 1m`.
2. **[2] Hard**: Nền trắng viền cam, phím tắt `[2]`, nhãn `12h`.
3. **[3] Good**: Nền xanh Indigo đặc sắc, phím tắt `[3]`, nhãn `1d`.
4. **[4] Easy**: Nền trắng viền xanh Emerald, phím tắt `[4]`, nhãn `4d`.

### 4.4. Thẻ Trắc Nghiệm 4 Phương Án (Quiz Option Tiles)
- Trạng thái thường: Viền xám `border-slate-200`, chữ cái A, B, C, D nằm trong khung tròn xám, góc phải hiển thị phím tắt số tương ứng (`1`, `2`, `3`, `4`).
- Trạng thái chọn đúng (Success): Viền xanh đậm `#006C49`, nền xanh pastel `#ECFDF5`, dấu tích xanh, huy hiệu `CORRECT`.
- Trạng thái chọn sai (Error): Viền đỏ `#EF4444`, nền đỏ pastel `#FEF2F2`, biểu tượng gạch chéo.

---

## 5. Quy Chuẩn Đáp Ứng Thiết Bị (Responsive Breakpoints)

- **Màn hình lớn / Desktop (> 1024px)**:
  - Sidebar điều hướng cố định bên trái rộng 260px.
  - Vùng nội dung tối đa 1280px (Dashboard) hoặc tập trung 680px (Study Session).
  - Lưới hiển thị Bento Grid 4 cột.
- **Máy tính bảng / Tablet (640px – 1024px)**:
  - Sidebar có thể thu gọn lại thành thanh biểu tượng (Icon Rail 72px).
  - Lưới Bento chuyển thành 2 cột.
- **Điện thoại di động / Mobile (< 640px)**:
  - Sidebar biến mất hoàn toàn, thay thế bằng **Thanh điều hướng dưới đáy (Bottom Navigation Dock)** với 4 nút chính: Dashboard, Library, Study, Profile.
  - Màn hình học tập thẻ tràn viền màn hình (Full width, margins 1rem), các nút đánh giá 1-4 phóng to vừa vặn tầm với của ngón tay cái người dùng.
