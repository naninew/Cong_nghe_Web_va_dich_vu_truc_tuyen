# Tài Liệu API RESTful (API Reference)

## 1. Quy chuẩn chung (API Conventions)
- **Base URL**: `/api/v1`
- **Định dạng dữ liệu**: `application/json` (trừ endpoint upload sử dụng `multipart/form-data`)
- **Mã hóa ký tự**: `UTF-8`
- **Xác thực**: Chuẩn HTTP Bearer Token qua header: `Authorization: Bearer <access_token>`
- **Định dạng phản hồi thành công**:
  ```json
  {
    "success": true,
    "data": { ... },
    "message": "Operation completed successfully"
  }
  ```
- **Định dạng phản hồi lỗi (Error Format)**:
  ```json
  {
    "detail": "Resource not found or authentication failed"
  }
  ```

---

## 2. Nhóm Endpoint Xác Thực (Authentication Endpoints)

### 2.1. Đăng nhập bằng Google OAuth 2.0
- **Endpoint**: `POST /api/v1/auth/google`
- **Mô tả**: Tiếp nhận ID Token từ Google Sign-In SDK, xác thực với Google và cấp phát cặp JWT.
- **Request Body**:
  ```json
  {
    "id_token": "eyJhbGciOiJSUzI1NiIs..."
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "data": {
      "access_token": "eyJhbGciOiJIUzI1Ni...",
      "refresh_token": "eyJhbGciOiJIUzI1Ni...",
      "token_type": "bearer",
      "user": {
        "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "email": "user@example.com",
        "display_name": "Alex Rivera",
        "avatar_url": "https://lh3.googleusercontent.com/...",
        "xp": 320,
        "streak_days": 14
      }
    }
  }
  ```

### 2.2. Đăng nhập môi trường phát triển (Dev / Mock Login)
- **Endpoint**: `POST /api/v1/auth/dev-login`
- **Mô tả**: Dùng cho phát triển cục bộ và kiểm thử khi chưa kết nối Google OAuth Console. Hoạt động khi `ENABLE_DEV_LOGIN=true`.
- **Request Body**:
  ```json
  {
    "email": "dev@memora.local",
    "display_name": "Dev Scholar"
  }
  ```
- **Response (200 OK)**: Cấp phát JWT tương tự endpoint Google.

### 2.3. Làm mới Access Token (Token Refresh)
- **Endpoint**: `POST /api/v1/auth/refresh`
- **Request Body**:
  ```json
  {
    "refresh_token": "eyJhbGciOiJIUzI1Ni..."
  }
  ```
- **Response (200 OK)**: Cấp phát `access_token` mới.

### 2.4. Thông tin tài khoản hiện tại (Get Current User Profile)
- **Endpoint**: `GET /api/v1/auth/me`
- **Headers**: `Authorization: Bearer <token>`
- **Response (200 OK)**: Trả về thông tin user, chuỗi streak, tổng XP, cấp độ.

---

## 3. Nhóm Endpoint Bộ Thẻ (Decks Endpoints)

### 3.1. Lấy danh sách cây bộ thẻ (Get Decks Hierarchy)
- **Endpoint**: `GET /api/v1/decks`
- **Mô tả**: Trả về toàn bộ danh sách bộ thẻ kèm cấu trúc cây cha con (tách bởi `::`), số thẻ New, Learn, Due trong ngày.
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1785785949998,
      "name": "Tiếng Nhật Tổng Hợp",
      "total_cards": 59378,
      "counts": { "new": 120, "learning": 15, "due": 28 },
      "children": [
        {
          "id": 1785785949997,
          "name": "01. Từ vựng",
          "counts": { "new": 50, "learning": 8, "due": 14 },
          "children": []
        }
      ]
    }
  ]
  ```

### 3.2. Tạo mới bộ thẻ
- **Endpoint**: `POST /api/v1/decks`
- **Request Body**:
  ```json
  {
    "name": "Tiếng Nhật Tổng Hợp::06. Hội thoại",
    "description": "Từ vựng và mẫu câu giao tiếp đời sống",
    "config_id": null
  }
  ```

### 3.3. Xem chi tiết bộ thẻ
- **Endpoint**: `GET /api/v1/decks/{deck_id}`
- **Response (200 OK)**: Trả về ID, tên bộ thẻ, mô tả, và ID cấu hình áp dụng.

### 3.4. Cập nhật bộ thẻ
- **Endpoint**: `PATCH /api/v1/decks/{deck_id}`
- **Request Body**:
  ```json
  {
    "name": "Tên bộ thẻ mới",
    "description": "Mô tả mới",
    "config_id": 1
  }
  ```

### 3.5. Xóa bộ thẻ
- **Endpoint**: `DELETE /api/v1/decks/{deck_id}`
- **Mô tả**: Xóa bộ thẻ và xóa toàn bộ thẻ flashcard trực thuộc bộ thẻ đó.

---

## 4. Nhóm Endpoint Ôn Tập Flashcard (Study Endpoints)

### 4.1. Lấy thẻ học tiếp theo trong hàng đợi (Get Queued Card)
- **Endpoint**: `GET /api/v1/study/queue`
- **Query Params**:
  - `deck_id` (long, optional): Giới hạn trong bộ thẻ (gồm cả các bộ thẻ con).
  - `filter_mode` (string, default `"all"`): `"all"` (ưu tiên Learning -> Due -> New), hoặc lọc riêng `"due"`, `"learning"`, `"new"`.
- **Response (200 OK)**:
  ```json
  {
    "card": {
      "id": 1785785855719,
      "deck_id": 1785785950001,
      "deck_name": "Tiếng Nhật Tổng Hợp::01. Từ vựng::N3",
      "note_id": 1785785855700,
      "ord": 0,
      "type": 2,
      "queue": 2,
      "due": 19825,
      "ivl": 1,
      "factor": 2500,
      "reps": 3,
      "lapses": 0,
      "fields": {
        "Expression": "躊躇う",
        "Reading": "ためらう",
        "Meaning": "ngập ngừng; do dự; chần chừ"
      },
      "tags": ["JLPT_N3", "Vocab"],
      "rendered": {
        "front_html": "<div class=\"card-front\">...</div>",
        "back_html": "<div class=\"card-back\">...</div>",
        "css": ".card-front { ... }"
      },
      "next_intervals": {
        "again": "< 1m",
        "hard": "12h",
        "good": "1d",
        "easy": "4d"
      }
    },
    "remaining_counts": {
      "new": 19,
      "learning": 3,
      "due": 27
    }
  }
  ```

### 4.2. Gửi kết quả đánh giá thẻ (Submit Card Answer)
- **Endpoint**: `POST /api/v1/study/answer`
- **Request Body**:
  ```json
  {
    "card_id": 1785785855719,
    "rating": 3,
    "time_taken_ms": 2840
  }
  ```
  *(Rating: 1=Again, 2=Hard, 3=Good, 4=Easy)*
- **Response (200 OK)**:
  ```json
  {
    "card_id": 1785785855719,
    "rating": 3,
    "new_interval": 1,
    "due": 19826,
    "xp_awarded": 15,
    "streak_days": 14
  }
  ```

### 4.3. Tăng hạn mức thẻ mới học trong ngày (Custom Increase)
- **Endpoint**: `POST /api/v1/study/custom-increase`
- **Mô tả**: Cho phép người học nới rộng chỉ tiêu thẻ mới trong ngày khi đã hoàn thành hạn mức mặc định.
- **Request Body**:
  ```json
  {
    "deck_id": 1785785950001,
    "amount": 10
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "added_cards": 10,
    "remaining_new": 10
  }
  ```

---

## 5. Nhóm Endpoint Quản Lý & Duyệt Thẻ (Cards & Browser Endpoints)

### 5.1. Duyệt và Tìm kiếm thẻ (Browse Cards)
- **Endpoint**: `GET /api/v1/cards/browse`
- **Query Params**:
  - `deck_id` (long, optional): Lọc theo bộ thẻ và các bộ thẻ con.
  - `state` (string, default `"all"`): Lọc trạng thái (`"all"`, `"lapsed"`, `"due"`, `"learning"`, `"new"`, `"suspended"`).
  - `search` (string, optional): Từ khóa tìm kiếm trong nội dung các trường hoặc nhãn tags.
  - `page` (int, ge=1, default `1`): Số trang.
  - `page_size` (int, ge=1, le=100, default `20`): Số lượng thẻ mỗi trang.
- **Response (200 OK)**:
  ```json
  {
    "total": 59378,
    "page": 1,
    "page_size": 20,
    "total_pages": 2969,
    "items": [
      {
        "id": 1785785855719,
        "deck_id": 1785785950001,
        "deck_name": "Tiếng Nhật Tổng Hợp::01. Từ vựng::N3",
        "note_id": 1785785855700,
        "ord": 0,
        "type": 2,
        "queue": 2,
        "state_label": "Due",
        "due": 19825,
        "ivl": 1,
        "factor": 2500,
        "reps": 3,
        "lapses": 0,
        "fields": {
          "Expression": "躊躇う",
          "Reading": "ためらう",
          "Meaning": "ngập ngừng; do dự"
        },
        "tags": ["JLPT_N3"]
      }
    ]
  }
  ```

### 5.2. Xem chi tiết thẻ & Lịch sử ôn tập
- **Endpoint**: `GET /api/v1/cards/{card_id}`
- **Response (200 OK)**: Trả về thông tin thẻ, rendered preview HTML/CSS, và 10 bản ghi nhật ký ôn tập gần nhất (`revlogs`).

### 5.3. Chỉnh sửa thẻ & ghi chú
- **Endpoint**: `PATCH /api/v1/cards/{card_id}`
- **Request Body**:
  ```json
  {
    "fields": {
      "Expression": "躊躇う",
      "Meaning": "do dự, chần chừ"
    },
    "tags": ["JLPT_N3", "Verbs"],
    "is_suspended": false
  }
  ```
- **Response (200 OK)**:
  ```json
  { "success": true, "message": "Card updated successfully" }
  ```

### 5.4. Đặt lại tiến trình thẻ về mới (Reset Card Progress)
- **Endpoint**: `POST /api/v1/cards/{card_id}/reset`
- **Mô tả**: Đặt lại toàn bộ chỉ số SRS (`queue=0, due=0, ivl=0, reps=0, lapses=0, fsrs=null`) về trạng thái New.
- **Response (200 OK)**:
  ```json
  { "success": true, "message": "Card progress reset to New successfully" }
  ```

### 5.5. Lấy danh sách mẫu thẻ (List Notetypes)
- **Endpoint**: `GET /api/v1/cards/notetypes/list`
- **Response (200 OK)**: Danh sách mẫu thẻ của user kèm danh sách các trường (`fields`) và template (`templates`).

### 5.6. Tạo mới thẻ và ghi chú (Create Card)
- **Endpoint**: `POST /api/v1/cards`
- **Request Body**:
  ```json
  {
    "deck_id": 1785785950001,
    "notetype_id": 1785785940001,
    "fields": {
      "Expression": "気兼ね",
      "Reading": "きがね",
      "Meaning": "khách khí, gượng gạo"
    },
    "tags": ["JLPT_N1"]
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "note_id": 1785785999999,
    "created_cards": [1785785999991],
    "message": "Successfully created note with 1 cards"
  }
  ```

### 5.7. Xóa thẻ
- **Endpoint**: `DELETE /api/v1/cards/{card_id}`
- **Mô tả**: Xóa thẻ và tự động xóa ghi chú cha nếu ghi chú không còn thẻ nào khác.

---

## 6. Nhóm Endpoint Thống Kê & Phân Tích (Analytics & Statistics Endpoints)

### 6.1. Thống kê tổng quan Bento Dashboard
- **Endpoint**: `GET /api/v1/stats/overview`
- **Response (200 OK)**:
  ```json
  {
    "user": {
      "name": "Dev Scholar",
      "email": "dev@memora.local",
      "avatar_url": null,
      "streak_days": 5,
      "xp": 450
    },
    "daily_goal": {
      "completed": 28,
      "target": 50
    },
    "due_count": 35,
    "total_cards": 59378,
    "mature_cards": 1200,
    "learning_cards": 85,
    "new_cards": 58093,
    "retention_rate": 94.2
  }
  ```

### 6.2. Thống kê chi tiết từng bộ thẻ (Hizashi Dashboard)
- **Endpoint**: `GET /api/v1/stats/deck/{deck_id}`
- **Mô tả**: Cung cấp 4 thẻ chỉ số chính, phân bố 6 trạng thái thẻ và ma trận 5 cấp độ ổn định trí nhớ:
  1. *Tier 1*: Mới nhớ (`ivl < 1d`)
  2. *Tier 2*: Đang nhớ (`1d <= ivl <= 7d`)
  3. *Tier 3*: Khá vững (`7d < ivl <= 21d`)
  4. *Tier 4*: Vững (`21d < ivl <= 60d`)
  5. *Tier 5*: Nhớ lâu (`ivl > 60d`)
- **Response (200 OK)**:
  ```json
  {
    "deck": { "id": 1785785949997, "name": "01. Từ vựng", "description": "" },
    "overview": {
      "total_cards": 12500,
      "studied_cards": 450,
      "progress_percent": 3.6,
      "retention_rate": 93.8,
      "success_reviews": 1200,
      "fail_reviews": 80,
      "total_reviews": 1280,
      "avg_reviews_per_card": 2.8
    },
    "distribution": {
      "new": 12050,
      "learning": 50,
      "review": 380,
      "relearning": 20,
      "leeches": 5,
      "starred": 12
    },
    "learned": {
      "total_learned": 450,
      "total_cards": 12500,
      "tier_counts": { "tier1": 50, "tier2": 120, "tier3": 150, "tier4": 90, "tier5": 40 },
      "cards": [
        { "card_id": 1785785855719, "front_text": "躊躇う", "ivl": 14, "reps": 4, "lapses": 0, "tier": 3 }
      ]
    }
  }
  ```

---

## 7. Nhóm Endpoint Game Học Tập (Quiz Game Endpoints)

### 7.1. Khởi tạo phiên Game 4 lựa chọn (Start Quiz Session)
- **Endpoint**: `POST /api/v1/games/start`
- **Request Body**:
  ```json
  {
    "deck_id": 1785785950001,
    "mode": "classic",
    "direction": "front_to_back",
    "total_questions": 10,
    "question_type": "vocab",
    "srs_sync": true,
    "timer_seconds": 15,
    "question_field": null,
    "answer_field": null,
    "hint_field": null
  }
  ```
  *(Các chế độ `mode`: `"classic"`, `"speed_blitz"`, `"survival"`, `"lapsed_only"`)*
  *(Các hướng `direction`: `"front_to_back"`, `"back_to_front"`, `"audio_listening"`, `"custom"`)*
- **Response (200 OK)**: Trả về `session_id`, `deck_id`, `total_questions`, và mảng danh sách câu hỏi `questions`.

### 7.2. Gửi câu trả lời trong Game (Submit Quiz Answer)
- **Endpoint**: `POST /api/v1/games/answer`
- **Request Body**:
  ```json
  {
    "session_id": "4b5e6f...",
    "card_id": 1785785855719,
    "selected_key": "B",
    "response_time_ms": 3200
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "is_correct": true,
    "correct_key": "B",
    "points_earned": 100,
    "combo_xp": 25,
    "current_combo": 4,
    "explanation": "Chính xác!",
    "srs_updated": true,
    "srs_grade": "Good"
  }
  ```

### 7.3. Kết thúc ván game & Xem bảng tổng kết (Finish Game Session)
- **Endpoint**: `POST /api/v1/games/finish`
- **Request Body**:
  ```json
  { "session_id": "4b5e6f..." }
  ```
- **Response (200 OK)**:
  ```json
  {
    "session_id": "4b5e6f...",
    "score": 1250,
    "xp_earned": 210,
    "total_questions": 10,
    "correct_count": 9,
    "accuracy_percent": 90.0,
    "duration_seconds": 45
  }
  ```

---

## 8. Nhóm Endpoint Nạp Dữ Liệu & Xuất File (Import & Export Endpoints)

### 8.1. Tải lên tập tin APKG (Upload & Process APKG)
- **Endpoint**: `POST /api/v1/import/apkg`
- **Content-Type**: `multipart/form-data`
- **Form Data**:
  - `file`: File nhị phân `.apkg`
  - `with_scheduling`: Boolean (default `true`)
- **Response (202 Accepted)**:
  ```json
  {
    "success": true,
    "job_id": "job_9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "status": "processing",
    "message": "File received. Import task initiated in background."
  }
  ```

### 8.2. Kiểm tra tiến trình nạp dữ liệu (Get Import Job Status)
- **Endpoint**: `GET /api/v1/import/status/{job_id}`
- **Response (200 OK)**:
  ```json
  {
    "job_id": "job_9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "status": "completed",
    "progress_percent": 100,
    "total_cards": 59378,
    "imported_cards": 59378,
    "imported_decks": 47,
    "imported_notetypes": 3,
    "error_message": null
  }
  ```

### 8.3. Xuất bộ thẻ thành file APKG (Export Deck to APKG)
- **Endpoint**: `GET /api/v1/export/deck/{deck_id}`
- **Response**: Trả về binary stream file `.apkg` chuẩn có thể import vào Anki Desktop.
