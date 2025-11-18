# AiNote Frontend - React + Vite

## 📁 Cấu trúc thư mục

```
frontend/
├── index.html
├── vite.config.ts               # Cấu hình Vite
├── package.json                 # Scripts & dependencies
├── tsconfig*.json               # Cấu hình TypeScript
├── public/
└── src/
    ├── main.tsx                 # Entry React
    ├── App.tsx                  # Shell ứng dụng
    ├── App.css / index.css      # Global styles
    │
    ├── components/              # UI components chính
    │   ├── Login.tsx
    │   ├── Register.tsx
    │   ├── Notes.tsx
    │   ├── CreateNote.tsx
    │   ├── UpdateNote.tsx
    │   └── ChatWidget.tsx
    │
    ├── contexts/                # React Context
    │   ├── AuthContext.ts
    │   └── AuthContext.tsx
    │
    ├── hooks/
    │   └── useAuth.ts
    │
    └── services/
        └── api.ts               # Axios client & API methods
```

## 🔧 Cấu hình API

- Mặc định frontend gọi backend tại `http://localhost:8000/api` (được cố định trong `src/services/api.ts`).
- Muốn thay đổi:
  - Sửa hằng `API_BASE_URL` trong `src/services/api.ts`, ví dụ:
    ```ts
    const API_BASE_URL = 'http://127.0.0.1:8000/api';
    ```
  - Hoặc bạn có thể refactor để đọc từ biến môi trường Vite (VD: `import.meta.env.VITE_API_URL`).

## ▶️ Chạy dự án (Windows PowerShell)

```powershell
# Cài dependencies
npm install

# Chạy dev server (mặc định Vite chạy cổng 5173)
npm run dev

# Mở trình duyệt (ví dụ)
Start-Process http://localhost:5173
```

## 🏗️ Build & Preview

```powershell
# Build production
npm run build

# Xem thử bản build
npm run preview
```

## 🔒 Auth & Token Refresh

- `services/api.ts` thêm `Authorization: Bearer <access_token>` tự động từ `localStorage`.
- Nếu gặp 401, client sẽ gọi `/auth/refresh` (yêu cầu backend hoạt động đúng và còn `refresh_token`).
- Khi refresh thất bại, người dùng sẽ được chuyển về trang đăng nhập.

## 🧩 Scripts trong package.json

- `dev`: chạy Vite dev server
- `build`: build TypeScript + bundle với Vite
- `preview`: phục vụ bản build để kiểm tra nhanh
- `lint`: chạy ESLint

## ❗ Lưu ý khi kết nối Backend

- Đảm bảo backend chạy tại cùng host/port như `API_BASE_URL`.
- CORS đã được bật phía backend ở `app/main.py` (mặc định `allow_origins=["*"]`).
- Nếu đổi port/backend host, nhớ cập nhật `API_BASE_URL` để tránh lỗi 404/Network Error.
