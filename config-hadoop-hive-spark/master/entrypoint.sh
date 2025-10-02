#!/bin/bash
set -e

ROLE=${ROLE:-datanode}   # set ROLE=master cho master service trong compose
HADOOP_HOME=/home/hadoopducdung/hadoop
DATA_ROOT=/home/hadoopducdung/hadoop/hadoop_data
NN_DIR=${DATA_ROOT}/hdfs/namenode
DN_DIR=${DATA_ROOT}/hdfs/datanode

# ensure dirs and ownership
mkdir -p "${NN_DIR}" "${DN_DIR}" "${HADOOP_HOME}/logs"
chown -R hadoopducdung:hadoopducdung "${DATA_ROOT}" "${HADOOP_HOME}/logs" || true

# 🔹 Dọn dẹp tiến trình cũ (nếu còn) + xóa pid file
echo "=> Cleaning up old Hadoop processes and pid files..."
pkill -f 'DataNode' || true
pkill -f 'NodeManager' || true
pkill -f 'NameNode' || true
pkill -f 'ResourceManager' || true
rm -f /tmp/hadoop-*.pid

# Format only on master and only if not formatted yet
if [ "$ROLE" = "master" ]; then
  if [ ! -f "${NN_DIR}/current/VERSION" ]; then
    echo "=> Formatting NameNode (first-time only)..."
    su - hadoopducdung -c "${HADOOP_HOME}/bin/hdfs namenode -format -nonInteractive" || true
  else
    echo "=> NameNode already formatted, skipping format."
  fi
fi

# start ssh (so other nodes can connect)
service ssh start

# start Hadoop daemons according to role
if [ "$ROLE" = "master" ]; then
  echo "=> Starting HDFS and YARN on master..."
  su - hadoopducdung -c "${HADOOP_HOME}/sbin/start-dfs.sh"
  su - hadoopducdung -c "${HADOOP_HOME}/sbin/start-yarn.sh"
else
  echo "=> Starting datanode and nodemanager on worker..."
  su - hadoopducdung -c "${HADOOP_HOME}/sbin/hadoop-daemon.sh start datanode"
  su - hadoopducdung -c "${HADOOP_HOME}/sbin/yarn-daemon.sh start nodemanager"
fi

# keep container alive
tail -f /dev/null
