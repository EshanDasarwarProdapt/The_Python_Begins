import os
import sys

# Set HADOOP_HOME and JAVA_HOME to our local setup
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['HADOOP_HOME'] = os.path.join(current_dir, 'hadoop')
os.environ['JAVA_HOME'] = os.path.join(current_dir, 'jdk-17')

from pyspark.sql import SparkSession

def main():
    # Initialize Spark Session
    spark = SparkSession.builder \
        .appName("SparkSQLTempTables") \
        .master("local[*]") \
        .getOrCreate()
        
    print("--- Spark Session Initialized ---\n")

    # 1. Load the CSV files from Sep_1 into DataFrames
    print("Loading datasets...")
    customers_df = spark.read.csv("Sep_1/customers_dataset.csv", header=True, inferSchema=True)
    orders_df = spark.read.csv("Sep_1/orders_dataset.csv", header=True, inferSchema=True)
    products_df = spark.read.csv("Sep_1/products_dataset.csv", header=True, inferSchema=True)

    # 2. Create Temporary Tables (Views)
    customers_df.createOrReplaceTempView("customers")
    orders_df.createOrReplaceTempView("orders")
    products_df.createOrReplaceTempView("products")
    
    print("Successfully created Temp Tables: 'customers', 'orders', 'products'\n")

    # 3. Perform Spark SQL Queries to View Tables
    # print("--- Customers Table ---")
    # spark.sql("SELECT * FROM customers LIMIT 5").show()

    print("--- Products Table ---")
    spark.sql("SELECT * FROM products LIMIT 5").show()

    # print("--- Orders Table ---")
    # spark.sql("SELECT * FROM orders LIMIT 5").show()

    spark.sql("SELECT * product_id, product_name, category, price, stock_quantity FROM products Where price >50000 AND stock_quantity < 20").show()
    
    spark.sql("select customer_id, SUM(sales_amount) AS total_sales FROM orders group by customer_id").show()
    spark.stop()

if __name__ == "__main__":
    main()
