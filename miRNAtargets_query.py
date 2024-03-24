#!/usr/bin/env python3

import cgi
import cgitb
import pymysql.cursors
from string import Template

#for debugging
cgitb.enable()

# Function to connect to the database
def connect_to_database():
    connection = pymysql.connect(
        host='********',
        user='****,
        password='****',
        db='****',
        port=****
    )
    cursor = connection.cursor()
    return (connection, cursor)

# Function to execute SQL query with parameters(params used to protect against sql injection attack)
def execute_query(connection, query, params=None):
    try:
        with connection.cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchall()
    except Exception as e:
        print("Error executing query:", str(e))
        result = None
    return result

# Function to generate stylized result table 
def generate_result_table(data):
    if not data:
        return ""

    result_table = "<div style='max-width: 600px; margin: 20px auto;'>"
    result_table += "<table style='width: 100%; border-collapse: collapse; border-radius: 8px; overflow: hidden; box-shadow: 0 0 20px rgba(0, 0, 0, 0.1); text-align: center;'>"
    result_table += "<thead style='background-color: #1E88E5; color: white; font-family: Arial, sans-serif;'>"
    result_table += "<tr><th style='padding: 10px;'>mid</th><th style='padding: 10px;'>miRNA Name</th><th style='padding: 10px;'>Targeting Score</th></tr>"
    result_table += "</thead>"
    result_table += "<tbody>"
    for row in data:
        result_table += "<tr>"
        result_table += "<td style='padding: 10px;'>{}</td>".format(row[0])
        result_table += "<td style='padding: 10px;'>{}</td>".format(row[1])
        result_table += "<td style='padding: 10px;'>{}</td>".format(row[2])
        result_table += "</tr>"
    result_table += "</tbody>"
    result_table += "</table>"
    result_table += "</div>"
    return result_table

#create the html template
#leave space for the style, title, intro, form, summary, table, error message
html_template = Template("""
<html>
<head>
    <title>${title}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: row;
        }
        .left-content {
            flex: 1;
            padding-right: 10px; /* Adjust spacing between left and right content */
        }
        .right-content {
            flex: 1;
        }
    </style>
</head>
<body>
    <div class="left-content">
        <h1>miRNA Gene Targets Database Search</h1>
        <p style='color: #666;'>Enter a gene name and select a maximum targeting score <br> to find the miRNAs which target the gene of interest.</p>
        <form method='get' action='nalluris_Search.py' style='margin-bottom: 20px;'>
            <label for='gene_name' style='display: block; margin-bottom: 10px; color: #1E88E5;'>Gene Name:</label>
            <input type='text' name='gene_name' id='gene_name' placeholder='Ex: A1CF' required style='padding: 8px; width: 200px; margin-bottom: 10px; border-radius: 4px; border: 1px solid #ccc;'>
            <br>
            <label for='max_score' style='display: block; margin-bottom: 10px; color: #1E88E5;'>Maximum Targeting Score:</label>
            <select name='max_score' id='max_score' style='padding: 8px; width: 150px; margin-bottom: 10px; border-radius: 4px; border: 1px solid #ccc;'>
            ${score_options}
            </select>
            <br>
            <input type='submit' value='Submit' style='padding: 10px 40px; font-size: 16px; background-color: #1E88E5; color: white; border: none; border-radius: 4px; cursor: pointer;'>
        </form>
    </div>
    <div class="right-content">
        ${responses}
    </div>
</body>
</html>
""")

#define the tab title
title="miRNA Gene Targets"

#initialize empty responses
responses = ""

#retrieve form data from the web server
form = cgi.FieldStorage()

# Get form data
gene_name = form.getvalue('gene_name')
max_score = form.getvalue('max_score')

# If form submitted, process input and display results
if gene_name and max_score:
    connection, cursor = connect_to_database()
    query = """
        SELECT miRNA.mid, miRNA.name, targets.score 
        FROM miRNA
        JOIN targets ON miRNA.mid = targets.mid
        JOIN gene ON targets.gid = gene.gid
        WHERE gene.name = %s 
        AND targets.score IS NOT NULL
        AND targets.score <= %s
        ORDER BY targets.score ASC
    """
    params = (gene_name, max_score)
    try:
        result = execute_query(connection, query, params)
        if len(result) > 0:
            responses += "<h3>Results:</h3>"
            responses += "<p>Gene {} is targeted by {} miRNAs with scores ≤ {}.</p>".format(gene_name, len(result), max_score)
            responses += generate_result_table(result)
        elif len(result) == 0:
            # Check if the gene exists in the database
            check_gene_query = "SELECT * FROM gene WHERE name = %s"
            gene_exists = execute_query(connection, check_gene_query, (gene_name,))
            if gene_exists:
                responses += "<h3>Results:</h3>"
                responses += "<p>Gene {} is targeted by 0 miRNAs with scores ≤ {}.</p>".format(gene_name, max_score)
            else:
                responses += "<h3>Results:</h3>"
                responses += "<p style='color: red;'>Gene {} does not exist in the miRNA database.</p>".format(gene_name)
    except Exception as e:
        responses += "<p style='color: red;'>Error: {}</p>".format(str(e))
    finally:
        # Close cursor and connection
        cursor.close()
        connection.close()

# Add options for maximum targeting score
score_options = ""
for score in range(-1, -8, -1):
    score_options += "<option value='{}'>score ≤ {}</option>".format(score / 10, score / 10)

#next line is always required as first part of html output
print("Content-type: text/html\n")

#print the html
print(html_template.safe_substitute(title=title, gene_name=gene_name, max_score=max_score, responses=responses, score_options=score_options))

