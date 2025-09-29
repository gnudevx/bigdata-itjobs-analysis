#!/bin/bash
set -e

ROLE=${ROLE:-datanode}
HADOOP_HOME=/home/hadoopducdung/hadoop
DATA_ROOT=/home/hadoopducdung/hadoop/hadoop_data
NN_DIR=${DATA_ROOT}/hdfs/namenode
DN_DIR=${DATA_ROOT}/hdfs/datanode

# Tạo key ssh để start-dfs.sh không bị treo
if [ ! -f /home/hadoopducdung/.ssh/id_rsa ]; then
  ssh-keygen -t rsa -P "" -f /home/hadoopducdung/.ssh/id_rsa
  cat /home/hadoopducdung/.ssh/id_rsa.pub >> /home/hadoopducdung/.ssh/authorized_keys
fi

# ensure dirs and ownership
mkdir -p "${NN_DIR}" "${DN_DIR}" "${HADOOP_HOME}/logs"
chown -R hadoopducdung:hadoopducdung "${DATA_ROOT}" "${HADOOP_HOME}/logs" || true

# Format only on master
if [ "$ROLE" = "master" ]; then
  if [ ! -d "${NN_DIR}/current" ]; then
    echo "=> Formatting NameNode (first-time only)..."
    su - hadoopducdung -c "${HADOOP_HOME}/bin/hdfs namenode -format -nonInteractive"
  else
    echo "=> NameNode already formatted, skipping."
  fi
fi

# start ssh
service ssh start
rm -f /tmp/hadoop-*/hadoop-*.pid

if [ "$ROLE" = "master" ]; then
  echo "=> Starting HDFS + YARN on master..."
  su - hadoopducdung -c "${HADOOP_HOME}/sbin/start-dfs.sh"
  su - hadoopducdung -c "${HADOOP_HOME}/sbin/start-yarn.sh"
else
  echo "=> Starting datanode + nodemanager..."
  su - hadoopducdung -c "${HADOOP_HOME}/sbin/hadoop-daemon.sh start datanode"
  su - hadoopducdung -c "${HADOOP_HOME}/sbin/yarn-daemon.sh start nodemanager"
fi

# giữ container chạy
tail -f /dev/null
