import os
import sys

# Set HADOOP_HOME so PySpark can find winutils.exe
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['HADOOP_HOME'] = os.path.join(current_dir, 'hadoop')

# Set JAVA_HOME so PySpark uses the local JDK 17
os.environ['JAVA_HOME'] = os.path.join(current_dir, 'jdk-17')

from pyspark.sql import SparkSession

def main():
    print("Initializing SparkSession...")
    spark = SparkSession.builder \
        .appName("TestSparkSetup") \
        .getOrCreate()
    
    print("SparkSession created successfully!")
    
    # Create a small DataFrame to test
    data = [("Alice", 25), ("Bob", 30), ("Charlie", 35)]
    columns = ["Name", "Age"]
    
    print("Creating DataFrame...")
    df = spark.createDataFrame(data, columns)
    
    print("Showing DataFrame:")
    df.show()
    
    print("Stopping SparkSession...")
    spark.stop()
    print("Spark test completed successfully.")

if __name__ == "__main__":
    main()
