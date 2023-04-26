import mysql.connector
from decouple import config
from termcolor import colored
from utils.utils import success, info, error, warning
from mysql.connector.errors import ProgrammingError, DatabaseError

class MySQLConnectionError(Exception):
    pass

class DAO():
    def __init__(self):
        try:
            self.conexion = mysql.connector.connect(
                host=config('MYSQL_HOST'),
                user=config('MYSQL_USER'),
                password=config('MYSQL_PASSWORD'),
                port=config('MYSQL_PORT'),
                database=config('MYSQL_DATABASE')
            )
        except ProgrammingError as ex:
            raise MySQLConnectionError(ex)
        except DatabaseError as ex:
            raise MySQLConnectionError(ex)
        
    def check_data(self, book_data):
        if self.conexion.is_connected():
            try:
                cursor = self.conexion.cursor()
                #select_book = "SELECT * FROM books WHERE isbn = %s"
                select_book = "SELECT bookID, title, author, editorial, isbn, type, language, collection, DATE_FORMAT(purchase_date, '%Y-%m-%d') as purchase_date, observation, reserved, DATE_FORMAT(lastUpdate, '%Y-%m-%d') as lastUpdate, numReference FROM books WHERE isbn = %s"
                data_isbn = (book_data["isbn"],)
                cursor.execute(select_book, data_isbn)
                result = cursor.fetchall()
                if result:
                    return result[0]
                else:
                    return None
            except MySQLConnectionError as e:
                error("Error de integridad:", e)
            finally:
                cursor.close()

    def connect_database(self):
        if self.conexion.is_connected():
                success(f"[ 1 ] The DataBase is connected on host {config('MYSQL_HOST')} the PORT: {config('MYSQL_PORT')}")
        else:
            raise MySQLConnectionError(f"[ 1 ] No se pudo conectar al servidor MySQL al host : {config('MYSQL_HOST')} y puerto {config('MYSQL_PORT')} especificados. Por favor, revise el hosts o la dirección IP y el puerto.")
            
    def insert_nameCover(self, name_cover, idBook):
        if self.conexion.is_connected():
            try:
                cursor = self.conexion.cursor()
                cover_name = name_cover+'.png'
                bookID = idBook
                query = ("INSERT INTO coverBooks "
                                        "(bookID, nameCover) "
                                        "VALUES (%s, %s)")
                value = (bookID, cover_name)
                cursor.execute(query, value)
                self.conexion.commit()
            except MySQLConnectionError as e:
                error("Error de integridad:", e)
            finally:
                cursor.close()
            return True

    def exist_databook(self, book_data):
        print("<== BOOK DATA ==>", book_data)
        print("<== BOOK DATA ==>", book_data["isbn"])
        if self.conexion.is_connected():
            try:
                cursor = self.conexion.cursor()
                select_book = "SELECT bookID FROM books WHERE isbn = %s"
                data_isbn = (book_data["isbn"],)
                cursor.execute(select_book, data_isbn)
                result = cursor.fetchone()
                if result:
                    return result[0]
                else:
                    return None
            except MySQLConnectionError as e:
                error("Error de integridad:", e)
            finally:
                cursor.close()
                
    def get_name_cover(self, bookID):
        if self.conexion.is_connected():
            try:
                cursor = self.conexion.cursor()
                select_name_cover = "SELECT nameCover FROM coverBooks WHERE bookID = %s"
                data_bookID = (bookID,)
                cursor.execute(select_name_cover, data_bookID)
                result = cursor.fetchone()
                if result:
                    return result[0]
                else:
                    return None
            except MySQLConnectionError as e:
                error("Error de integridad:", e)
            finally:
                cursor.close()
    
    def insert_databook(self, book_data):
        if self.conexion.is_connected():
            try:
                cursor = self.conexion.cursor()
                query = ("INSERT INTO books "
                                    "(title, author, editorial, isbn, type, language) "
                                    "VALUES (%s, %s, %s, %s, %s, %s)")
                value = (book_data["title"], book_data["author"], book_data["editorial"], book_data["isbn"], book_data["category"], book_data["language"])
                cursor.execute(query, value)
                self.conexion.commit()
                book_id = cursor.lastrowid
            except MySQLConnectionError as e:
                error("Error de integridad:", e)
            finally:
                cursor.close()
            return book_id
    
    def update_databook(self, idBook, book_data):
        bookID = idBook
        dataBook = book_data
        if self.conexion.is_connected():
            try:
                cursor = self.conexion.cursor()
                query = ("UPDATE books SET title=%s, author=%s, editorial=%s, isbn=%s, type=%s, language=%s WHERE bookID=%s")
                value = (dataBook["title"], dataBook["author"], dataBook["editorial"], dataBook["isbn"], dataBook["category"], dataBook["language"], bookID)
                cursor.execute(query, value)
                self.conexion.commit()
            except MySQLConnectionError as e:
                error("Error de integridad:", e)
            finally:
                cursor.close()
            return True
    
    def update_nameCover(self, name_cover, idBook):
        cursor = self.conexion.cursor()
        nameCover = name_cover+".png"
        bookID = idBook
        try:
            cursor = self.conexion.cursor()
            query = ("SELECT * FROM coverBooks WHERE bookID=%s")
            value = (bookID,)
            cursor.execute(query, value)
            result = cursor.fetchone()
            if result:
                query = ("UPDATE coverBooks SET nameCover=%s WHERE bookID=%s")
                value = (nameCover, bookID)
                cursor.execute(query, value)
            else:
                query = ("INSERT INTO coverBooks (bookID, nameCover) VALUES (%s, %s)")
                value = (bookID, nameCover)
                cursor.execute(query, value)
            cursor.fetchall() # <-- leer todos los resultados pendientes
            self.conexion.commit()
        except MySQLConnectionError as e:
            error("Error de integridad:", e)
        finally:
                cursor.close()
        
        
        
