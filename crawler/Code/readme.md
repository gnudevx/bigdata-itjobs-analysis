crawler/
├── __init__.py
├── config/ 
│   ├── __init__.py
│   └── settings.py          ← cấu hình chung (đường dẫn, logging, driver,...)
│
├── core/
│   ├── __init__.py
│   ├── driver.py            ← khởi tạo Chrome driver (ẩn danh, stealth)
│   ├── utils.py             ← log, delay, scroll...
│
├── modules/
│   ├── __init__.py
│   └── topcv_crawler.py     ← crawler chính (TopCV)
│   └── vnwork_crawler.py     ← crawler chính (vnwork)
│
└── main.py                  ← entry point để chạy crawler

config/settings.py: nơi chứa tất cả cấu hình có thể thay đổi — đường dẫn lưu file, tên file, chế độ headless, path chromedriver, số trang tối đa, các hằng số chung.
core/driver.py: khởi tạo và trả về một WebDriver (ở đây dùng undetected_chromedriver) với các option chuẩn, stealth, user-agent random, headless toggle.
core/utils.py: 
- gom các hàm tiện ích dùng chung:

- setup_logger(name) → chuẩn hóa file log / format.

- log_and_print(logger, msg) → print + write log.

- human_delay(...) → delay ngẫu nhiên để giả hành vi người dùng.

- human_scroll(driver) → scroll nhẹ để kích lazy-load.

- save_json(obj, path) → ghi file theo kiểu append/merge an toàn.
