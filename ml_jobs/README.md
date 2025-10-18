ml_jobs/
├── code/
│   ├── cleaning/
│   ├── training/
│   ├── evaluation/
│   └── utils/
│
├── data/
│   ├── raw/
│   ├── processed/
│   ├── prepared/
│   └── feature_columns.json
│
├── model_store/
│   ├── 2025-10-17/
│   ├── latest/
│   └── training_history.csv
│
├── logs/
├── configs/
│   └── paths.yaml
└── README.md


1️⃣ /code/ – nơi chứa toàn bộ logic xử lý của bạn 🧠
👉 Đây là trái tim của hệ thống ML.
Tất cả các script (code Python) bạn viết đều nằm ở đây.
📁 cleaning/

Chứa các file xử lý dữ liệu thô từ spark thành dữ liệu sạch.

Ví dụ:

cleaning/
 ├── clean_skills.py          # từ JSON raw → CSV sạch
 ├── preprocess.py            # từ CSV sạch → dữ liệu ML-ready


👉 Tức là:
Bước 1: Làm sạch dữ liệu (remove lỗi, normalize text, xử lý kỹ năng, lương, v.v.)
Bước 2: Chuẩn hóa để mô hình có thể đọc (biến category thành one-hot, kỹ năng thành vector)

📁 training/

Chứa các script liên quan đến việc huấn luyện mô hình ML.

Ví dụ:

training/
 ├── train_model.py           # huấn luyện model mới
 ├── incremental_train.py     # cập nhật model cũ bằng dữ liệu mới
 ├── evaluate_model.py        # đánh giá model
 └── visualize_feature.py     # vẽ biểu đồ feature importance


👉 Nghĩ đơn giản:

train_model → dạy mô hình mới

incremental_train → dạy thêm (từ model cũ)

evaluate_model → kiểm tra xem nó đoán có tốt không

visualize_feature → xem yếu tố nào ảnh hưởng đến dự đoán nhiều nhất

📁 utils/

Chứa các hàm dùng chung cho nhiều file.

Ví dụ:

utils/
 ├── io_utils.py          # load/save dữ liệu, tạo đường dẫn, timestamp
 ├── model_utils.py       # load model latest, copy version
 ├── date_utils.py        # hàm lấy ngày giờ chuẩn


👉 Đây là nơi gom những đoạn code lặp lại để đỡ phải copy đi copy lại.

2️⃣ /data/ – nơi chứa tất cả dữ liệu đầu vào & trung gian 📦

Mục tiêu: bạn biết dữ liệu đang ở bước nào.

Cấu trúc:

data/
├── raw/
├── processed/
├── prepared/
└── feature_columns.json

📁 raw/

Dữ liệu thô bạn crawl từ web hoặc nhận từ HDFS.
Ví dụ:

cleaned_data_2025-10-17.json

📁 processed/

Sau khi chạy bước clean_skills_main(), dữ liệu được chuẩn hóa và làm sạch.
Ví dụ:

cleaned_extended_2025-10-17.csv


🟢 Dữ liệu ở đây thường có: group, title, salary, location, skills_clean...

📁 prepared/

Sau khi preprocess_main() chạy, file này chứa toàn bộ đặc trưng để train mô hình:

prepared_dataset_2025-10-17.csv


Ví dụ:

experience_num	loc_hcm	sen_junior	grp_Data Engineer	skill__python	skill__spark	salary
2	1	0	0	1	1	25000000
📄 feature_columns.json

Chứa danh sách các feature (cột) mà mô hình đã dùng để train.
→ Khi load model, bạn sẽ biết đúng feature nào tương ứng.

3️⃣ /model_store/ – nơi lưu mô hình đã huấn luyện 🎯

Đây là nơi bạn lưu kết quả trí tuệ của mình — mô hình đã học xong.

Cấu trúc:

model_store/
├── 2025-10-17/
│   ├── rf_salary_model.pkl
│   ├── xgb_salary_model.json
│   ├── metrics.json
│   └── pred_vs_actual.png
├── latest/
│   ├── rf_salary_model.pkl
│   ├── xgb_salary_model.json
│   ├── metrics.json
│   └── feature_importance.png
└── training_history.csv

📁 2025-10-17/

Là bản model version được train hôm đó.
Ví dụ:

rf_salary_model.pkl → mô hình RandomForest đã học

xgb_salary_model.json → mô hình XGBoost dạng JSON

metrics.json → kết quả đo lường (MAE, RMSE, R²)

pred_vs_actual.png → biểu đồ kiểm chứng kết quả

👉 Mỗi ngày train 1 lần → 1 folder riêng biệt → bạn có thể quay lại model ngày trước đó nếu model mới bị lỗi.

📁 latest/

Bản mới nhất hiện tại — luôn được pipeline hoặc API sử dụng.

Các file trong latest/ được copy từ version mới nhất.

Dùng cho:

evaluate_main()

visualize_main()

incremental_train()

→ Tức là mọi code inference hoặc đánh giá đều chỉ cần quan tâm “latest”, không phải tìm theo ngày.

📄 training_history.csv

Ghi lại lịch sử tất cả lần huấn luyện.
Ví dụ:

timestamp	model	mae	rmse	r2
20251017_0930	rf	3.2e6	5.5e6	0.82
20251017_0930	xgb	2.8e6	4.9e6	0.85

→ Dễ dàng xem xu hướng model tốt hơn hay tệ đi theo thời gian.

4️⃣ /logs/ – nơi lưu log khi chạy pipeline 🧾

Bạn có thể ghi log ở đây để kiểm tra lỗi từng bước.

Ví dụ:

logs/
├── clean_skills.log
├── preprocess.log
├── train_model.log
└── evaluate_model.log


Khi có lỗi, chỉ cần mở đúng file log ra là biết step nào hỏng.

5️⃣ /configs/ – nơi chứa cấu hình hệ thống ⚙️

Để không hardcode đường dẫn hay tham số vào code.

Ví dụ file paths.yaml:

data_root: "/opt/airflow/ml_jobs/data"
model_root: "/opt/airflow/ml_jobs/model_store"
log_root: "/opt/airflow/ml_jobs/logs"

folders:
  processed: "processed"
  prepared: "prepared"
  latest_model: "latest"


Sau đó trong code:

import yaml
with open("/opt/airflow/ml_jobs/configs/paths.yaml") as f:
    cfg = yaml.safe_load(f)
DATA_PATH = Path(cfg["data_root"]) / cfg["folders"]["prepared"]


→ Dễ bảo trì, dễ deploy qua môi trường khác (local, server, docker).