#!/bin/bash
set -e

ROLE=${ROLE:-datanode}   # ROLE=master cho master service trong compose
HADOOP_HOME=/home/hadoopducdung/hadoop
SPARK_HOME=/usr/local/spark
DATA_ROOT=/home/hadoopducdung/hadoop/hadoop_data
NN_DIR=${DATA_ROOT}/hdfs/namenode
DN_DIR=${DATA_ROOT}/hdfs/datanode

# ensure dirs and ownership
mkdir -p "${NN_DIR}" "${DN_DIR}" "${HADOOP_HOME}/logs"
chown -R hadoopducdung:hadoopducdung "${DATA_ROOT}" "${HADOOP_HOME}/logs" || true

# 🔹 Dọn dẹp tiến trình cũ (nếu còn)
echo "=> Cleaning up old Hadoop/Spark processes and pid files..."
pkill -f 'DataNode' || true
pkill -f 'NodeManager' || true
pkill -f 'NameNode' || true
pkill -f 'ResourceManager' || true
pkill -f 'Master' || true
pkill -f 'Worker' || true
rm -f /tmp/hadoop-*.pid

# 🔹 Format HDFS nếu là master (chỉ 1 lần đầu)
if [ "$ROLE" = "master" ]; then
  if [ ! -f "${NN_DIR}/current/VERSION" ]; then
    echo "=> Formatting NameNode (first-time only)..."
    su - hadoopducdung -c "${HADOOP_HOME}/bin/hdfs namenode -format -nonInteractive" || true
  else
    echo "=> NameNode already formatted, skipping format."
  fi
fi

# 🔹 Start SSH
service ssh start

# 🔹 Start Hadoop daemons theo role
if [ "$ROLE" = "master" ]; then
  echo "=> Starting HDFS and YARN on master..."
  su - hadoopducdung -c "${HADOOP_HOME}/sbin/start-dfs.sh"
  su - hadoopducdung -c "${HADOOP_HOME}/sbin/start-yarn.sh"
  mkdir -p "${SPARK_HOME}/logs"
  mkdir -p "${SPARK_HOME}/work"
  chmod -R 777 "${SPARK_HOME}/logs"
  chmod -R 777 "${SPARK_HOME}/work"
  # 🔹 Start Spark Master
  echo "=> Starting Spark Master..."
  su - hadoopducdung -c "${SPARK_HOME}/sbin/start-master.sh"

  # 🔹 Start Spark Worker trên chính master (nếu muốn)
  echo "=> Starting Spark Worker on master..."
  su - hadoopducdung -c "${SPARK_HOME}/sbin/start-worker.sh spark://ducdung-master:7077"
  # ✅🔹 Tự động tạo HDFS thư mục airflow (chỉ trên master)
  echo "=> Checking HDFS directory /user/hadoopducdung/airflow ..."
  su - hadoopducdung -c "
    ${HADOOP_HOME}/bin/hdfs dfs -test -d /user/hadoopducdung/airflow || (
      echo '📁 Creating /user/hadoopducdung/airflow in HDFS...';
      ${HADOOP_HOME}/bin/hdfs dfs -mkdir -p /user/hadoopducdung/airflow &&
      ${HADOOP_HOME}/bin/hdfs dfs -chown -R hadoopducdung:supergroup /user/hadoopducdung/airflow &&
      ${HADOOP_HOME}/bin/hdfs dfs -chmod 775 /user/hadoopducdung/airflow
    )
  "
  echo "✅ HDFS airflow directory ready."
elif [ "$ROLE" = "datanode" ]; then
  echo "=> Starting datanode and nodemanager on worker..."
  su - hadoopducdung -c "${HADOOP_HOME}/sbin/hadoop-daemon.sh start datanode"
  su - hadoopducdung -c "${HADOOP_HOME}/sbin/yarn-daemon.sh start nodemanager"

  # 🔹 Start Spark Worker trên node phụ (nếu muốn)
  echo "=> Starting Spark Worker on slave..."
  su - hadoopducdung -c "${SPARK_HOME}/sbin/start-worker.sh spark://ducdung-master:7077"
fi

# 🔹 Giữ container sống
tail -f /dev/null
