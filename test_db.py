import pymysql.cursors

# Connect to the database.
connection = pymysql.connect(host='104.131.139.15',
                             user='trinca',
                             password='Mrctrinca@23',                             
                             db='boobot',
                             charset='utf8',
                             cursorclass=pymysql.cursors.DictCursor)

print ("connect successful!!")

try:
 

    with connection.cursor() as cursor:
      
        # SQL 
        sql = "SELECT * FROM bookmarks"
        
        # Execute query.
        cursor.execute(sql)
        
        print ("cursor.description: ", cursor.description)

        print()

        for row in cursor:
            print(row)
            
finally:
    # Close connection.
    connection.close()

