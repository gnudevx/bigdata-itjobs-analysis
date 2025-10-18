from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("Spark Connection Test")
    .config("spark.master", "spark://hadoop-master:7077")
    .getOrCreate()
)

data = [("Hello",), ("Spark",), ("from",), ("Airflow",)]
df = spark.createDataFrame(data, ["word"])
df.show()

spark.stop()
