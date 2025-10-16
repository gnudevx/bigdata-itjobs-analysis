from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("arrow-spark").getOrCreate()
print("🔥 Spark connected successfully!")
spark.stop()