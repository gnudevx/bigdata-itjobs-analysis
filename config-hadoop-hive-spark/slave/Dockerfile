# Base Image
FROM hadoop-base1

USER hadoopducdung
WORKDIR /home/hadoopducdung


# Copy Hadoop configuration files
COPY config/core-site.xml /home/hadoopducdung/hadoop/etc/hadoop/core-site.xml
COPY config/hdfs-site.xml /home/hadoopducdung/hadoop/etc/hadoop/hdfs-site.xml
COPY config/yarn-site.xml /home/hadoopducdung/hadoop/etc/hadoop/yarn-site.xml

USER root
# Convert files to Unix format
RUN dos2unix /home/hadoopducdung/hadoop/etc/hadoop/core-site.xml && \
    dos2unix /home/hadoopducdung/hadoop/etc/hadoop/hdfs-site.xml && \
    dos2unix /home/hadoopducdung/hadoop/etc/hadoop/yarn-site.xml

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh && dos2unix /usr/local/bin/entrypoint.sh
# Format HDFS
# USER hadoopducdung


USER root
# Start SSH and Hadoop services at runtime
# CMD ["/usr/sbin/sshd", "-D"]
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/bin/bash"]