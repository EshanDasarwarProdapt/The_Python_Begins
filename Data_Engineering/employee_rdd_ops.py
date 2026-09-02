import os
import sys

# Set HADOOP_HOME and JAVA_HOME to our local setup
current_dir = os.path.dirname(os.path.abspath(__file__))
os.environ['HADOOP_HOME'] = os.path.join(current_dir, 'hadoop')
os.environ['JAVA_HOME'] = os.path.join(current_dir, 'jdk-17')

from pyspark.sql import SparkSession

def main():
    # Initialize SparkSession and get SparkContext
    spark = SparkSession.builder \
        .appName("EmployeeRDDOperations") \
        .master("local[*]") \
        .getOrCreate()
        
    sc = spark.sparkContext
    
    print("--- Spark Session Initialized ---\n")

    # 1. Load the CSV file into an RDD
    rdd = sc.textFile("employees_records.csv")

    # 2. Extract and remove the header
    header = rdd.first()
    data_rdd = rdd.filter(lambda row: row != header)

    # 3. Parse the data
    # format: emp_id,name,department,city,age,salary,experience,gender,joining_year
    # Indices: 0:emp_id, 1:name, 2:department, 3:city, 4:age, 5:salary, 6:experience, 7:gender, 8:joining_year
    parsed_rdd = data_rdd.map(lambda row: row.split(","))

    # --- OPERATION 0: View Data as a Table ---
    # Convert RDD to DataFrame to view it in a tabular format
    header_cols = header.split(",")
    df = parsed_rdd.toDF(header_cols)
    print("--- Employee Records Table (First 5 Rows) ---")
    df.show(5)

    # --- OPERATION 1: Total Salary per Department ---
    # Map to (department, salary) and reduceByKey
    dept_salary_rdd = parsed_rdd.map(lambda x: (x[2], int(x[5])))
    total_salary_per_dept = dept_salary_rdd.reduceByKey(lambda a, b: a + b)
    
    print("1. Total Salary per Department:")
    for dept, total_salary in total_salary_per_dept.collect():
        print(f"   {dept}: Rs {total_salary}")
    print("-" * 40)

    # --- OPERATION 2: Count of Employees per City ---
    # Map to (city, 1) and reduceByKey
    city_count_rdd = parsed_rdd.map(lambda x: (x[3], 1))
    employees_per_city = city_count_rdd.reduceByKey(lambda a, b: a + b)

    print("2. Number of Employees per City:")
    for city, count in employees_per_city.collect():
        print(f"   {city}: {count}")
    print("-" * 40)

    # --- OPERATION 3: Top 3 Highest Paid Employees ---
    # Sort by salary (index 5) in descending order
    # Note: sortBy takes a key function and ascending=False
    top_3_paid = parsed_rdd.sortBy(lambda x: int(x[5]), ascending=False).take(3)
    
    print("3. Top 3 Highest Paid Employees:")
    for emp in top_3_paid:
        print(f"   {emp[1]} from {emp[2]} dept (Salary: Rs {emp[5]})")
    print("-" * 40)

    # --- OPERATION 4: Average Experience by Department ---
    # Map to (department, (experience, 1))
    dept_exp_rdd = parsed_rdd.map(lambda x: (x[2], (int(x[6]), 1)))
    # Reduce by adding experiences and counts
    total_exp_and_count = dept_exp_rdd.reduceByKey(lambda a, b: (a[0] + b[0], a[1] + b[1]))
    # Map to get the average
    avg_exp_per_dept = total_exp_and_count.mapValues(lambda v: round(v[0] / v[1], 1))

    print("4. Average Experience (Years) per Department:")
    for dept, avg_exp in avg_exp_per_dept.collect():
        print(f"   {dept}: {avg_exp} years")
    print("-" * 40)

    spark.stop()

if __name__ == "__main__":
    main()
