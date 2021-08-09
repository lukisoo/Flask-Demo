import pymysql

#Creates connection to the SQL database
def create_connection():
  return pymysql.connect(
       host = '127.0.0.1',
       user = 'root',
       password = 'pasword1089',
       db = 'resourcesdatabase',
       charset = 'utf8mb4',
       cursorclass = pymysql.cursors.DictCursor
       )