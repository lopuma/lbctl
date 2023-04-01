import mysql.connector
from mysql.connector import errorcode, errors
from decouple import config
from termcolor import colored

class MySQLConnectionError(Exception):
    pass

try:
    mydb = mysql.connector.connect(
        host=config('MYSQL_HOST'),
        user=config('MYSQL_USER'),
        password=config('MYSQL_PASSWORD'),
        port=config('MYSQL_PORT'),
        database=config('MYSQL_DATABASE')
    )
except mysql.connector.IntegrityError  as err:
    if err.errno == 2003:
        message = f"No se pudo conectar al servidor MySQL al host : {config('MYSQL_HOST')} y puerto {config('MYSQL_PORT')} especificados. Por favor, revise el hosts o la dirección IP y el puerto."
        print("\n", colored(message, "red"))
        raise MySQLConnectionError(message)
    elif err.errno == 1062:
        message = f"Error de integridad: el valor que estás tratando de insertar ya existe en la base de datos."
        print("\n", colored(message, "red"))
        raise MySQLConnectionError(message)
    elif err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        message = "Something is wrong with your user name or password"
        print("\n", colored(message, "red"))
        raise MySQLConnectionError(message)
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        message = "Database does not exist"
        print("\n", colored(message, "red"))
        raise MySQLConnectionError(message)
    else:
        message = str(err)
        print("\nError:", err)
        raise MySQLConnectionError(message)
except mysql.connector.Error as err:
    if err.errno == 2003:
        message = f"No se pudo conectar al servidor MySQL al host : {config('MYSQL_HOST')} y puerto {config('MYSQL_PORT')} especificados. Por favor, revise el hosts o la dirección IP y el puerto."
        print("\n", colored(message, "red"))
        raise MySQLConnectionError(message)
    elif err.errno == 1062:
        message = f"Error de integridad: el valor que estás tratando de insertar ya existe en la base de datos."
        print("\n", colored(message, "red"))
        raise MySQLConnectionError(message)
    elif err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        message = "Something is wrong with your user name or password"
        print("\n", colored(message, "red"))
        raise MySQLConnectionError(message)
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        message = "Database does not exist"
        print("\n", colored(message, "red"))
        raise MySQLConnectionError(message)
    else:
        message = str(err)
        print("\nError:", err)
        raise MySQLConnectionError(message)
except errors.IntegrityError as err:
    if err.errno == 1062:
        message = f"Error de integridad: el valor que estás tratando de insertar ya existe en la base de datos."
        print("\n", colored(message, "red"))
        raise MySQLConnectionError(message)
    else:
        message = f"Error de integridad de datos: {err}"
        print("\n", colored(message, "red"))
        raise MySQLConnectionError(message)

