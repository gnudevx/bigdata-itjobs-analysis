FROM openjdk:8-jdk

ENV HIVE_VERSION=3.1.3
ENV HIVE_HOME=/opt/hive
ENV PATH=$PATH:$HIVE_HOME/bin
ENV HADOOP_HOME=/opt/hadoop
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

# Install utils
RUN apt-get update && apt-get install -y wget curl tar procps net-tools && rm -rf /var/lib/apt/lists/*

# Install Hadoop
COPY config/hadoop-3.3.6.tar.gz /tmp/
RUN tar -xzf /tmp/hadoop-3.3.6.tar.gz -C /opt/ \
    && ln -s /opt/hadoop-3.3.6 /opt/hadoop \
    && rm /tmp/hadoop-3.3.6.tar.gz

# ARG HADOOP_VERSION=3.3.6 
# RUN wget https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz && \ 
#     tar -xzf hadoop-${HADOOP_VERSION}.tar.gz -C /opt/ && \ 
#     ln -s /opt/hadoop-${HADOOP_VERSION} /opt/hadoop && \ 
#     rm hadoop-${HADOOP_VERSION}.tar.gz

# Install Hive
COPY config/apache-hive-${HIVE_VERSION}-bin.tar.gz /tmp/
RUN tar -xzf /tmp/apache-hive-${HIVE_VERSION}-bin.tar.gz -C /opt/ && \
    ln -s /opt/apache-hive-${HIVE_VERSION}-bin /opt/hive && \
    rm /tmp/apache-hive-${HIVE_VERSION}-bin.tar.gz

# RUN wget https://archive.apache.org/dist/hive/hive-${HIVE_VERSION}/apache-hive-${HIVE_VERSION}-bin.tar.gz && \
#     tar -xzf apache-hive-${HIVE_VERSION}-bin.tar.gz -C /opt/ && \
#     ln -s /opt/apache-hive-${HIVE_VERSION}-bin /opt/hive && \
#     rm apache-hive-${HIVE_VERSION}-bin.tar.gz

# Install MySQL JDBC driver
RUN curl -fSL https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/8.0.33/mysql-connector-j-8.0.33.jar -o $HIVE_HOME/lib/mysql-connector-j-8.0.33.jar

# RUN mkdir -p $HIVE_HOME/logs $HIVE_HOME/tmp && \
#     chown -R hadoopducdung:hadoopducdung $HIVE_HOME/logs $HIVE_HOME/tmp

WORKDIR $HIVE_HOME
COPY config/hive-site.xml $HIVE_HOME/conf/hive-site.xml

# Tạo user hadoopducdung
RUN groupadd -g 1000 hadoopducdung && \
    useradd -m -u 1000 -g 1000 hadoopducdung && \
    chown -R hadoopducdung:hadoopducdung /opt/hive /opt/hadoop
RUN mkdir -p $HIVE_HOME/logs $HIVE_HOME/tmp && \
    chown -R hadoopducdung:hadoopducdung $HIVE_HOME/logs $HIVE_HOME/tmp && \
    chown -R hadoopducdung:hadoopducdung /opt/hive /opt/hadoop

COPY config/core-site.xml /opt/hadoop/etc/hadoop/core-site.xml
COPY config/hdfs-site.xml /opt/hadoop/etc/hadoop/hdfs-site.xml
ENV HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
ENV HIVE_CONF_DIR=/opt/hive/conf
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

USER hadoopducdung
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["hive", "--service", "hiveserver2"]
