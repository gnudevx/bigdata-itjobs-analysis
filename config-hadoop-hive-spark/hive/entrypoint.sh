#!/bin/bash
set -e

echo "=> Kiểm tra HDFS đã sẵn sàng..."
until hdfs dfs -ls / >/dev/null 2>&1; do
  echo "   HDFS chưa sẵn sàng, đợi 3s..."
  sleep 3
done

# Thoát safe mode nếu cần
hdfs dfsadmin -safemode leave || true

# Thư mục cho Hive
hdfs dfs -mkdir -p /tmp /tmp/hive /user/hive/warehouse || true
hdfs dfs -chmod -R 777 /tmp /tmp/hive /user/hive/warehouse || true

# Init schema nếu chưa có
echo "=> Kiểm tra schema Hive Metastore..."
schematool -dbType mysql -info > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "=> Chưa có schema, init..."
  schematool -dbType mysql -initSchema
else
  echo "=> Schema đã tồn tại, bỏ qua bước init."
fi

# Start metastore
echo "=> Start Hive Metastore..."
nohup hive --service metastore > $HIVE_HOME/logs/metastore.log 2>&1 &
sleep 10

# Start HiveServer2 (giữ foreground để container sống)
echo "=> Start HiveServer2..."
exec hive --service hiveserver2
