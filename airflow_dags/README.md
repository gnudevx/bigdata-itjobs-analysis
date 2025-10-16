docker compose run airflow-cli airflow config list
docker compose up -d airflow-init 
docker compose up -d --build

--- lỗi kết nối với spark ở airflow:
Dùng file Python bên trong container (nếu muốn làm qua CLI)

Vào trong container:

docker compose exec airflow-webserver bash


Rồi trong shell của container, chạy lệnh này (ở Linux shell, không còn PowerShell nữa):

airflow connections delete spark_default

airflow connections add spark_default \
  --conn-type 'spark' \
  --conn-extra '{"master": "spark://hadoop-master:7077", "spark_binary": "/opt/spark/bin/spark-submit"}'
airflow connections add spark_default \
  --conn-type 'spark' \
  --conn-extra '{"master": "spark://hadoop-master:7077", "spark_binary": "/opt/spark/bin/spark-submit"}'



Kiểm tra lại:

airflow connections get spark_default


Nếu thấy dòng:

extra_dejson | {"master": "spark://hadoop-master:7077", "spark_binary": "/opt/spark/bin/spark-submit"}


→ Là OK 🎯