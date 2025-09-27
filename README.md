# 🚀 Big Data IT Jobs Analysis
**Project Structure**
<pre> ```bash
bigdata-itjobs-analysis/
│
├── config-hadoop-hive-spark/   # All for docker-compose + config cho Hadoop, Spark, Hive
│   ├── compose.yaml            # Docker Compose file để dựng cluster Big Data
│   ├── hadoop-base/            # Dockerfile & config Hadoop/Spark
│   ├── hive/                   # Dockerfile & config Hive Metastore
│   ├── master/                 # Config master node (NameNode, ResourceManager)
│   ├── slave/                  # Config slave node (DataNode, NodeManager)
│   └── .devcontainer/          # VSCode devcontainer config
│
├── crawler/                    # crawl collection data + clean data for IT jobs (TopCV, VietnamWorks, ...)
│   ├── source_code/            # Script crawl & insert to DB
│   │   ├── crawl_topcv.py
│   │   ├── crawl_vnwork.py
│   │   ├── convert_csv.py
│   │   ├── SaoLuu_PhucHoi.py
│   │   └── Analysis_Data/      # SSAS project (DW, cube, dimensions)
│   │
│   ├── Handel_Data_Windows/    # SQL scripts, PowerBI dashboard, data cleaning scripts
│   │   ├── Script_Create_Table.sql
│   │   ├── TrucQuanHoa.pbix
│   │   └── CleanData/          # clean data (train model NER)
│   │
│   └── my_streamlit_app/       # Web visualization bằng Streamlit
│       ├── Home.py
│       ├── page_mapreduce.py
│       ├── page_mysql.py
│       └── mapreduce_jobs/     # Job MapReduce demo (Top10CV, Lương TB, Kỹ năng...)
│
├── hive_scripts/               # folder save HiveQL scripts
│
├── notebooks/                  # Jupyter notebooks (EDA, Spark SQL test, ML pipeline demo)
│
└── spark_jobs/                 # Spark jobs (ETL, data processing)
    ├── Code/
    ├── Log/
    └── Output/ 
``` </pre>
**How to Run the Project**
1️⃣ Build & Start Containers
# Go to config folder
cd config-hadoop-hive-spark/

# Build images
docker-compose build --no-cache

# Start cluster
docker compose up -d

# Check running containers
docker ps

2️⃣ Hadoop (HDFS) – Basic Commands
- you can entry for docker master and run basic commands
# Put file into HDFS
hdfs dfs -put /tmp/local.csv /user/hadoop/

# List files
hdfs dfs -ls /user/hadoop/

# Read file
hdfs dfs -cat /user/hadoop/local.csv

3️⃣ Spark – Run Jobs
# Run Python job
docker exec -it spark-master spark-submit \
  --master yarn /spark_jobs/job.py

# Run Scala/Java JAR
docker exec -it spark-master spark-submit \
  --master yarn /spark_jobs/app.jar

4️⃣ Hive – Query Data
docker exec -it hive-server hive

CREATE DATABASE demo;
USE demo;
CREATE TABLE users(id INT, name STRING);
LOAD DATA INPATH '/user/hadoop/users.csv' INTO TABLE users;
SELECT * FROM users;
