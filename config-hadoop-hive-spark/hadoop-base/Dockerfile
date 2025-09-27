FROM ubuntu:22.04

LABEL maintainer="DOCUTEE <work.docutee@outlook.com>"

# Prepare ssh
RUN mkdir -p /run/sshd && echo "root:root" | chpasswd

# Install base packages + Java
RUN apt-get update && \
    apt-get install -y wget ssh openssh-server dos2unix vim sudo telnet iputils-ping && \
    apt-get install -y openjdk-8-jdk openjdk-17-jdk && \
    apt-get install -y libc6 libzstd1 libncurses5 libtinfo5 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Setup Java alternatives (Java 17 default)
RUN update-alternatives --install /usr/bin/java java /usr/lib/jvm/java-8-openjdk-amd64/bin/java 1 && \
    update-alternatives --install /usr/bin/java java /usr/lib/jvm/java-17-openjdk-amd64/bin/java 2 && \
    update-alternatives --set java /usr/lib/jvm/java-17-openjdk-amd64/bin/java && \
    update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-8-openjdk-amd64/bin/javac 1 && \
    update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-17-openjdk-amd64/bin/javac 2 && \
    update-alternatives --set javac /usr/lib/jvm/java-17-openjdk-amd64/bin/javac
# RUN wget https://downloads.apache.org/spark/spark-4.0.1/spark-4.0.1-bin-hadoop3.tgz \ 
# && tar -xvzf spark-4.0.1-bin-hadoop3.tgz -C /usr/local/ \ 
# && mv /usr/local/spark-4.0.1-bin-hadoop3 /usr/local/spark \ 
# && rm spark-4.0.1-bin-hadoop3.tgz
# Spark
COPY spark-config/spark-4.0.1-bin-hadoop3.tgz /tmp/
RUN tar -xzf /tmp/spark-4.0.1-bin-hadoop3.tgz -C /usr/local/ && \
    mv /usr/local/spark-4.0.1-bin-hadoop3 /usr/local/spark && \
    rm /tmp/spark-4.0.1-bin-hadoop3.tgz

# Set environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV HADOOP_JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
ENV HADOOP_HOME=/home/hadoopducdung/hadoop
ENV SPARK_HOME=/usr/local/spark
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$SPARK_HOME/bin:$JAVA_HOME/bin

# Create Hadoop user
RUN adduser --disabled-password --gecos "" hadoopducdung && \
    echo "hadoopducdung:hadoopducdung" | chpasswd && \
    usermod -aG sudo hadoopducdung && \
    echo "hadoopducdung ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers
# RUN wget https://dlcdn.apache.org/hadoop/common/hadoop-3.4.1/hadoop-3.4.1.tar.gz && \ 
# tar -xzf hadoop-3.4.1.tar.gz && \ 
# mv hadoop-3.4.1 hadoop && \ # rm hadoop-3.4.1.tar.gz
# Hadoop
COPY hadoop-config/hadoop-3.4.1.tar.gz /tmp/
RUN mkdir -p /home/hadoopducdung && \
    tar -xzf /tmp/hadoop-3.4.1.tar.gz -C /home/hadoopducdung/ && \
    mv /home/hadoopducdung/hadoop-3.4.1 /home/hadoopducdung/hadoop && \
    rm /tmp/hadoop-3.4.1.tar.gz && \
    chown -R hadoopducdung:hadoopducdung /home/hadoopducdung/hadoop

COPY .bashrc /home/hadoopducdung/.bashrc
RUN dos2unix /home/hadoopducdung/.bashrc && \
    chown hadoopducdung:hadoopducdung /home/hadoopducdung/.bashrc

COPY --chown=hadoopducdung:hadoopducdung spark-config/spark-env.sh $SPARK_HOME/conf/spark-env.sh
COPY --chown=hadoopducdung:hadoopducdung spark-config/spark-defaults.conf $SPARK_HOME/conf/spark-defaults.conf

RUN dos2unix $SPARK_HOME/conf/*

USER hadoopducdung
WORKDIR /home/hadoopducdung

# Fix JAVA_HOME for Hadoop
RUN echo "export JAVA_HOME=$HADOOP_JAVA_HOME" >> /home/hadoopducdung/hadoop/etc/hadoop/hadoop-env.sh

# # Copy configs
# COPY .bashrc /home/hadoopducdung/.bashrc
# RUN dos2unix /home/hadoopducdung/.bashrc

# SSH setup
RUN mkdir -p /home/hadoopducdung/.ssh && \
    ssh-keygen -t rsa -P '' -f /home/hadoopducdung/.ssh/id_rsa && \
    cat /home/hadoopducdung/.ssh/id_rsa.pub >> /home/hadoopducdung/.ssh/authorized_keys && \
    chmod 600 /home/hadoopducdung/.ssh/authorized_keys

USER root

# # Ports
# EXPOSE 9000 9870 9864 8088 8042 4040
# Expose ports
EXPOSE 9000 50070 9001 9002 9003 9004 9005 9006 9870 9864 8088 8042
# Start sshd
# CMD ["/usr/sbin/sshd", "-D"]
