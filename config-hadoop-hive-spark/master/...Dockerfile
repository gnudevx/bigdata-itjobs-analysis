
# Base Image
FROM hadoop-base1

USER hadoopducdung
WORKDIR /home/hadoopducdung

# Copy Hadoop configuration files
COPY config/core-site.xml /home/hadoopducdung/hadoop/etc/hadoop/core-site.xml
COPY config/hdfs-site.xml /home/hadoopducdung/hadoop/etc/hadoop/hdfs-site.xml
COPY config/mapred-site.xml /home/hadoopducdung/hadoop/etc/hadoop/mapred-site.xml
COPY config/yarn-site.xml /home/hadoopducdung/hadoop/etc/hadoop/yarn-site.xml
COPY config/workers /home/hadoopducdung/hadoop/etc/hadoop/workers

USER root
# Convert files to Unix format
RUN dos2unix /home/hadoopducdung/hadoop/etc/hadoop/core-site.xml && \
    dos2unix /home/hadoopducdung/hadoop/etc/hadoop/hdfs-site.xml && \
    dos2unix /home/hadoopducdung/hadoop/etc/hadoop/yarn-site.xml && \
    dos2unix /home/hadoopducdung/hadoop/etc/hadoop/mapred-site.xml && \
    dos2unix /home/hadoopducdung/hadoop/etc/hadoop/workers

# Cấu hình biến môi trường
ENV HIVE_HOME=/opt/hive
ENV PATH=$PATH:$HIVE_HOME/bin

# Tạo thư mục warehouse
RUN mkdir -p /user/hive/warehouse && chmod -R 777 /user/hive/warehouse

# Format HDFS
USER hadoopducdung
RUN hdfs namenode -format

USER root
# Start SSH and Hadoop services
CMD ["/usr/sbin/sshd", "-D"]