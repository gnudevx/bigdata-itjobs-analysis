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
## 🚀 How to Run the Project

| Step | Description              | Command                                                                 |
|:----:|--------------------------|-------------------------------------------------------------------------|
| **1** | Go to config folder      | `cd config-hadoop-hive-spark/`                                         |
|       |                          | `docker build -t hadoop-base1 ./hadoop-base`                           |
|      | Build images             | `docker compose build --no-cache`                                       |
|      | Start cluster            | `docker compose up -d`                                                  |
|      | Check running containers | `docker ps`                                                             |
| **2** | Enter Hadoop master     | `docker exec -it hadoop-master bash`                                    |
|      | Put file into HDFS       | `hdfs dfs -put /tmp/local.csv /user/hadoop/`                            |
|      | List files               | `hdfs dfs -ls /user/hadoop/`                                            |
|      | Read file                | `hdfs dfs -cat /user/hadoop/local.csv`                                  |
| **3** | Run Python job          | `docker exec -it spark-master spark-submit --master yarn /spark_jobs/job.py` |
|      | Run Scala/Java JAR       | `docker exec -it spark-master spark-submit --master yarn /spark_jobs/app.jar` |
| **4** | Open Hive CLI           | `docker exec -it hive-server hive`                                      |
|      | entry first              | `schematool -dbType mysql -initSchema`                                  |
|      | start service             | `hive --service metastore &`                                           |
|      | Create database          | `CREATE DATABASE demo;`                                                 |
|      | Use database             | `USE demo;`                                                             |
|      | Create table             | `CREATE TABLE users(id INT, name STRING);`                              |
|      | Load data                | `LOAD DATA INPATH '/user/hadoop/users.csv' INTO TABLE users;`           |
|      | Query data               | `SELECT * FROM users;`                
