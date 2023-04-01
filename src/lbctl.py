import argparse
import subprocess
import sys
import json
import pandas as pd
import time
import redis
import urllib.request
from pathlib import Path
import os
import random
import mysql_connection
from minio import Minio
from minio.error import S3Error
from PIL import Image
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.alert import Alert
from tqdm import tqdm, trange
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException
from termcolor import colored
from decouple import config

color_out = "green"
color_key = "yellow"
color_value = "blue"
color_analizando = "yellow"
color_error = "red"
color_warning = "yellow"
color_success = "green"
def main():
    options = webdriver.FirefoxOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')

    parser = argparse.ArgumentParser(
        prog="lbctl",
        usage='lbctl <command> [flags]',
        description="Liburutegia control ('lbctl') provisions and manages local Liburutegia containers optimized for production workflows.",
        epilog='Use "lbctl --help" for more information about a given command.'
    )
    parser.add_argument("command", help='An ("status", "update", "reset", "stop", "find") command is needed, for default is status', type=str, default='status', nargs='?')
    parser.add_argument("-t", '--title', help='Search by TITLE, example (lbctl find -t="title") or (lbctl find --title="title")', type=str)
    parser.add_argument("-a", '--author', help='Search by AUTHOR, example (lbctl find -a="author") or (lbctl find --author="author")', type=str)
    parser.add_argument("-i", '--isbn', help='Search by ISBN, example (lbctl find -i="isbn") or (lbctl find --isbn="isbn")')
    parser.add_argument("-c", '--container', help="The following arguments are required: Container name")
    args = parser.parse_args()

    if args.command == "find" or (args.command == "help" and args.container == "find"):
        parser_find = argparse.ArgumentParser(
            prog="lbctl find",
            usage='lbctl find [flags]',
            description="Search book data on the web"
        )
        parser_find.add_argument("-t", '--title', help='Search by TITLE, example (lbctl find -t="title") or (lbctl find --title="title")', type=str)
        parser_find.add_argument("-a", '--author', help='Search by AUTHOR, example (lbctl find -a="author") or (lbctl find --author="author")', type=str)
        parser_find.add_argument("-i", '--isbn', help='Search by ISBN, example (lbctl find -i="isbn") or (lbctl find --isbn="isbn")')
        args_find, _ = parser_find.parse_known_args()
        if not all(v is None for v in vars(args_find).values()):
            # Si alguno de los valores no es None, se proporcionaron argumentos válidos
            # Llamada find Book
            driver = webdriver.Remote(
                command_executor='http://{}:4444/wd/hub'.format(config('WEBDRIVER_HOST')),
                options=options
            )
            initContainer(args, parser_find, driver)
        else:
            # No se proporcionaron argumentos válidos, imprimir ayuda
            parser_find.print_help()
    else:
        driver = webdriver.Remote(
                command_executor='http://{}:4444/wd/hub'.format(config('WEBDRIVER_HOST')),
            options=options
        )

        # Llamada init Container
        initContainer(args, parser_find, driver)


def capitalizar_palabras(cadena, excepciones=["de"]):
    palabras = cadena.split()
    palabras_mayusculas = []
    for i, palabra in enumerate(palabras):
        if palabra.lower() not in excepciones:
            palabra = palabra.lower()
            palabra = palabra.capitalize()
        else:
            palabra = palabra.lower()
        if i == 0:
            palabra = palabra.capitalize()
        palabras_mayusculas.append(palabra)
    return ' '.join(palabras_mayusculas)

def generate_cover_rand(length, type='default'):
    if type == 'num':
        characters = "0123456789"
    elif type == 'alf':
        characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    elif type == 'rand':
        characters = None
    else:
        characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    rand_name_cover = ""
    for i in range(length):
        if type == 'rand':
            rand_name_cover += chr(random.randint(33, 126))
        else:
            rand_name_cover += random.choice(characters)
    return rand_name_cover

def process_image(data_cover):
    # Descargar la imagen
    url = data_cover
    name_cover = generate_cover_rand(15)
    pictures_dir = './covers/'
    urllib.request.urlretrieve(url, pictures_dir + name_cover + '.png')
    
    # Abrir la imagen con Pillow
    with Image.open(pictures_dir + name_cover + '.png') as img:
        # Redimensionar la imagen y ajustar los parámetros de ajuste
        img = img.resize((200, 322), resample=Image.LANCZOS, box=None, reducing_gap=None)
        img = img.convert('RGB') # Convertir la imagen a modo RGB
        
        # Guardar la imagen redimensionada
        img.save(pictures_dir + name_cover + '.png', format='PNG', optimize=True)
    
    return name_cover

def add_minio(name_cover):
    filename = name_cover + ".png"
    try:
        client = Minio(
        endpoint=config("MINIO_HOST"),
        access_key=config("MINIO_USER"),
        secret_key=config("MINIO_PASSWORD"),
        secure= False,
        )
        bucket = config("BUCKET_NAME")
        found = client.bucket_exists(bucket)
        if not found:
            client.make_bucket(bucket)
        else:
            pass
        client.fput_object(
            bucket, filename, os.path.join(".", "covers", filename),
        )
        print("\n")
        print(colored("Cover data upload MINIO.", color_success), filename)
    except S3Error as exc:
        print("\nerror occurred.", exc)

def delete_redis():
    try:
        r = redis.Redis(host=config("REDIS_HOST"), port=6379, password=config("REDIS_PASSWORD"))
        exist_book = r.exists('books')
        if exist_book:
            r.delete('books')
        # print("\n")
        # print(colored(f"Eliminados datos en redis.", color_success))
        yield
    except:
        pass

def delete_bookinfo_redis(idBook):
    try:
        bookID = idBook
        r = redis.Redis(host=config("REDIS_HOST"), port=6379, password=config("REDIS_PASSWORD"))
        exist_book = r.exists(f'bookInfo{bookID}')
        if exist_book:
            r.delete(f'bookInfo{bookID}')
    except:
        pass

def extract_nameCover(url):
    try:
        url_cover = url
        name_cover = process_image(url_cover)
    except (IndexError, KeyError):
        name_cover = None
    return name_cover
                
def extract_data(data):
    datos = {}
    try:
        datos['title'] = data[0]['title']
    except (IndexError, KeyError):
        print(colored("Error al acceder al title en los datos recibidos.", color_error))
    try:
        datos['author'] = data[0]['author']
    except (IndexError, KeyError):
        print(colored("Error al acceder al author en los datos recibidos.", color_error))
    try:
        datos['editorial'] = data[0]['editorial']
    except (IndexError, KeyError):
        print(colored("Error al acceder al editorial en los datos recibidos.", color_error))
    try:
        datos['isbn'] = data[0]['isbn']
    except (IndexError, KeyError):
        print(colored("Error al acceder al ISBN en los datos recibidos.", color_error))
    try:
        datos['type'] = data[0]['category']
    except (IndexError, KeyError):
        print(colored("Error al acceder al type en los datos recibidos.", color_error))
    try:
        datos['language'] = data[0]['language']
    except (IndexError, KeyError):
        print(colored("Error al acceder al language en los datos recibidos.", color_error))  
    try:
        datos['cover'] = data[0]['cover']
    except (IndexError, KeyError):
        print(colored("Error al acceder al cover en los datos recibidos.", color_error))   
    
    return datos

def connect_database():
    try:
        cnx = mysql_connection.mydb
        if cnx.is_connected():
            cursor = cnx.cursor()
    except:
        pass
    return (cursor, cnx)

def loop(tareas, callback=None):
    while tareas:
        actual = tareas.pop(0)
        try:
            next(actual)
            tareas.append(actual)
        except StopIteration:
            pass
        if callback is not None:
            callback()

def callback():
    print("\n")
    print(colored("La función delete_redis se ha ejecutado", color_success))
           
def select_idBook(book_data, name_cover, cursor):
    try:
        select_book = "SELECT bookID FROM books WHERE isbn = %s"
        data_isbn = (book_data["isbn"],)
        cursor.execute(select_book, data_isbn)
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    except mysql_connection.MySQLConnectionError as e:
        print("\n", colored("Error de integridad:", "red"), e.msg)
    except mysql_connection.errors.IntegrityError as e:
        print("\n", colored("Error de integridad en la base de datos --:", "red"), e.msg)

def insert_nameCover(name_cover, idBook, cursor):
    try:
        cover_name = name_cover+'.png'
        bookID = idBook
        insert_nameCover = ("INSERT INTO coverBooks "
                                "(bookID, nameCover) "
                                "VALUES (%s, %s)")
        data_nameCover = (bookID, cover_name)
        cursor.execute(insert_nameCover, data_nameCover)
    except mysql_connection.MySQLConnectionError as e:
        print("\n", colored("Error de integridad:", "red"), e.msg)
    except mysql_connection.errors.IntegrityError as e:
        print("\n", colored("Error de integridad en la base de datos --:", "red"), e.msg)
    finally:
        cursor.close()
    return True

def handle_duplicate_isbn(response):
    print(colored("Este libro ya existe en la base de datos", "yellow"), response)
    print(colored("¿Deseas actualizar su información? (S/N)", "yellow"))
    answer = input("> ")
    if answer == "S" or answer == "s":
        print(colored("¡Genial! Vamos a actualizar su información.", "green"))
    elif answer == "N" or answer == "n":
        print(colored("¡Entendido! Saliendo del programa...", "green"))
        sys.exit()
    else:
        print(colored("No seleccionaste una opción válida. Saliendo del programa...", "red"))
        sys.exit()
                   
def data_operation(resultados):
    data_book =  resultados
    print("\n")
    print("\033[33mRealizando operaciones en la Base de datos....\033[0m")
    with tqdm(total=6) as rbar:
        # extraer los datos del libro
        book_data = extract_data(data_book)
        if book_data:
            print("\n")
            print(colored("Datos extraidos con existos.", color_success))
        time.sleep(0.5)
        rbar.update(1)
        yield
        # extraer el nombre del cover guardado en local
        name_cover = extract_nameCover(book_data['cover'])
        if name_cover:
            print("\n")
            print(colored(f"Cover {name_cover} descargado con existos.", color_success))        
        time.sleep(0.5)
        rbar.update(1)
        yield
        
        # conect mysql
        cursor, cnx = connect_database()
        if cursor:
            print("\n")
            print(colored(f"The DataBase is connected on the PORT: {config('MYSQL_PORT')}", color_success))
        time.sleep(0.5)
        rbar.update(1)
        yield
        bookID = ""
        response = exist_databook(book_data, cursor)
        if response:
            rbar.close()
            handle_duplicate_isbn(response)
            time.sleep(0.5)
            rbar.update(1)
            yield
        else:
            succes_data = insert_databook(book_data, cursor)
            if succes_data:
                cnx.commit()
                bookID = select_idBook(book_data, name_cover, cursor)
                if bookID:
                    response_namecover = insert_nameCover(name_cover, bookID, cursor)
                    if response_namecover:
                        cnx.commit()
                        print("\n")
                        print(colored(f"The book data has been added correctly, with ID : {bookID}", color_success))
                        time.sleep(0.5)
                        rbar.update(1)
                else:
                    rbar.close()
                    print("\n")
                    print(colored(f"[ ERROR ], The BOOK with ID : {bookID} does not exist", color_error))
            yield
        
        # delete book Info
        succes_delete_bookinfo = delete_bookinfo_redis(bookID)
        print("\n")
        print(colored(f"Eliminados datos en redis.", color_success))
        time.sleep(0.5)
        rbar.update(1)
        yield
        
        if name_cover is not None:
            add_minio(name_cover)
            time.sleep(0.5)
            rbar.update(1)
        else:
            print(colored("\nError al descargar cover.", color_error))
            rbar.close()
        rbar.close()

def exist_databook(book_data, cursor):
    try:
        select_book = "SELECT * FROM books WHERE isbn = %s"
        data_isbn = (book_data["isbn"],)
        cursor.execute(select_book, data_isbn)
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    except mysql_connection.MySQLConnectionError as e:
        print("\n", colored("Error de integridad:", "red"), e.msg)

def insert_databook(book_data, cursor):
    try:
        add_book = ("INSERT INTO books "
                            "(title, author, editorial, isbn, type, language) "
                            "VALUES (%s, %s, %s, %s, %s, %s)")
        data_book = (book_data["title"], book_data["author"], book_data["editorial"], book_data["isbn"], book_data["type"], book_data["language"])
        cursor.execute(add_book, data_book)
    except mysql_connection.MySQLConnectionError as e:
        print("\n", colored("Error de integridad:", "red"), e.msg)
    return True

def add_book_bd(data, driver):
    print("\n\033[33mAnalizando datos....\033[0m")
    with tqdm(total=5) as abar:
        link_book = data['view']
        author = capitalizar_palabras(data['author'])
        abar.update(1)
        driver.get(link_book)
        abar.update(1)
        category = ''
        data_cover = ''
        url_cover = ''
        try:
            data_title = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, './/*[@id="app"]/div[1]/main/div/div/div/div[3]/div/div[2]/div/h1')))
            title = capitalizar_palabras(data_title.text)
        except TimeoutException:
                title = ''
        try:
            data_category = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, './/*[@id="breadcrumbs"]/div/div[2]/div[5]/a/span')))
            category = capitalizar_palabras(data_category.text)
        except TimeoutException:
                category = ''
        try:
            data_cover = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, './/*[@id="app"]/div[1]/main/div/div/div/div[3]/div/div[1]/div[1]/div/div/div/img')))
        except TimeoutException:
            try:
                data_cover = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, './/*[@id="app"]/div[1]/main/div/div/div/div[3]/div/div[1]/div[2]/div/div/div/img')))
            except TimeoutException:
                data_cover = ''
        if data_cover:
            url_cover = data_cover.get_attribute("srcset").split(",")[-1].split(" ")[0]
        abar.update(1)
        xpath_list = ['//*[@id="app"]/div[1]/main/div/div/div/div[7]/div/div[3]', 
                    '//*[@id="app"]/div[1]/main/div/div/div/div[6]/div/div[3]', 
                    '//*[@id="app"]/div[1]/main/div/div/div/div[4]/div/div[3]']
        data_sheet = None
        for xpath in xpath_list:
            try:
                data_sheet = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
                abar.update(1)
                break
            except TimeoutException:
                pass
            
        resultados = []
        if data_sheet is not None:
            rows = data_sheet.find_elements(By.XPATH, './/div[@class="row text-body-2 no-gutters"]')
            tech_specs = {}
            for row in rows:
                name = row.find_element(By.XPATH, './/span/strong').text
                value = row.find_element(By.XPATH, './/div[@class="col col-6"][2]/span')
                tech_specs[name] = value.text
            isbn = tech_specs.get('ISBN:', '')
            idioma = tech_specs.get('Idioma:', '')
            editorial = tech_specs.get('Editorial:', '')
            resultados.append({'isbn': isbn, 'language': capitalizar_palabras(idioma), 'editorial': capitalizar_palabras(editorial), 'title': title, 'author': author, 'category': category, 'cover': url_cover})
            abar.update(1)
            if not resultados:
                print(colored('No se encontraron resultados.', color_error))
                abar.close()
            else:
                abar.close()
                tareas = [data_operation(resultados), delete_redis()]
                loop(tareas)
        else:
            print(colored('No se pudo encontrar la hoja técnica.', color_error))
            abar.close()
            
def select_book(data, df, driver):
    total_elements = len(df)
    print("\n------------------------------------------------------------------------------------------------------------------------")
    print("------------------------------------------------- LIBROS DISPONIBLES ---------------------------------------------------")
    print("------------------------------------------------------------------------------------------------------------------------")
    print('\n',df,'\n')
    print("\n\t\t", colored("[X]   Salir", color_error), "\n")
    print(f"{colored('El total de libros encontrados es :',  color_out, attrs=['bold'])} {colored(total_elements, color_key)}")
    while True:
        user_input = input("\nIngrese el ID de la opción que desea o X para salir: ")
        if user_input.lower() == "x":
            print("\n\t", colored('Cerrando session....', color_error))
            return None
        try:
            choice = int(user_input)
            for book in data:
                if book["ID"] == choice:
                    book_data  = {'view': book['view'], 'title': book['title'], 'author': book['author']}
                    add_book_bd(book_data , driver)
                    return choice
        except ValueError:
            print("\n\t" , colored(f"La opción {user_input} no es válida. Por favor, ingrese un número entre ", color_error) + colored("0", color_out) + colored(f" y {len(data) - 1}", color_out) + colored(" o ",color_error) + colored("X ", color_warning) + colored("para salir.", color_error))

def scraping(element, driver):
    articles = []
    with tqdm(total=3) as sbar:
        try:
            driver.get('https://www.casadellibro.com/')
            try:
                cookies_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler')))
                try:
                    cookies_button.click()
                    sbar.update(1)
                except NoSuchElementException:
                    pass
            except TimeoutException:
                pass
            driver.implicitly_wait(5)
            try:
                input_element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div[1]/div[1]/div[3]/div[1]/div[1]/input')))
                input_element.click()
                driver.implicitly_wait(5)
                boton_element = driver.find_element(By.XPATH, '//*[@id="app"]/div[1]/div[1]/div[3]/div[1]/div[1]/button')
                driver.implicitly_wait(5)
                boton_element.click()
                sbar.update(1)
            except TimeoutException:
                print(colored('El elemento no está disponible para interactuar.', color_error))
                pass
            except ElementClickInterceptedException:
                print(colored('El elemento está oculto y no se puede hacer clic en él.', color_error))
                pass
            driver.implicitly_wait(5)
            try:
                input2_element = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="empathy-x"]/header/div/div/input')))
                input2_element.send_keys(element)
                driver.implicitly_wait(5)
                try:
                    element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'section.ebx-grid.ebx-empathy-x__grid')))
                except TimeoutException:
                    try:
                        element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'div.ebx-sliding-panel__scroll')))
                    except TimeoutException:
                        element = None
                if element:
                    articles = element.find_elements(By.TAG_NAME, "article")
                    sbar.update(1)
                else:
                    articles = []
            except TimeoutException:
                print(colored('El elemento no está disponible para interactuar.', color_warning))
        except:
            sbar.close()
            raise
    list_articles_data = []
    id = 0
    if articles:
        for article in articles:
            try:
                title = article.find_element(By.CSS_SELECTOR, ".ebx-result-title a").text.strip()
            except NoSuchElementException:
                print(colored('No se pudo encontrar el elemento del título.', color_warning))
                title = ''
            try:
                author = article.find_element(By.CSS_SELECTOR, ".ebx-result-authors").text.strip()
            except NoSuchElementException:
                print(colored('No se pudo encontrar el elemento del autor.', color_warning))
                author = ''
            try:
                link = article.find_element(By.CSS_SELECTOR, ".ebx-result-title a").get_attribute('href')
            except NoSuchElementException:
                print(colored('No se pudo encontrar el elemento del enlace.', color_warning))
                link = ''
            try:
                other = article.find_element(By.CSS_SELECTOR, ".ebx-result-binding-type").text.strip()
            except NoSuchElementException:
                print(colored('No se pudo encontrar el elemento de otra informacion.', color_warning))
                other = ''
            
            dict_article_data = {}
            if any([len(title)>0, len(author)>0, len(link)>0, len(other)>0]):
                dict_article_data["ID"] = id
                dict_article_data["title"] = title
                dict_article_data["author"] = author
                dict_article_data["view"] = link
                dict_article_data["other"] = other
                
                list_articles_data.append(dict_article_data)
                dict_articles_data = {}
            id+=1
        for d in list_articles_data:
            for k, v in d.items():
                dict_articles_data.setdefault(k, []).append(v)
        df = pd.DataFrame.from_dict(dict_articles_data)
        print("\n\033[33mCargando datos....\033[0m")
        for i in trange(5, unit="s", unit_scale=0.1, unit_divisor=1):
            time.sleep(0.2)
        select_book(list_articles_data, df, driver)
    else :
        print(colored('No se pudo encontrar el elemento deseado.', color_error))

    #Cerramos session en selenium
    time.sleep(5)
    driver.quit()

def findBook(data, driver, parser_find):
    title   = data[0] if data[0] is not None else ''
    author  = data[1] if data[1] is not None else ''
    isbn    = data[2] if data[2] is not None else ''
    data_element = ' '.join([title, author, isbn])
    
    if (title == '' and author == '' and isbn == ''):
        parser_find.print_help()
        driver.quit()
    else:
        print("\n" + f"{colored('El libro a buscar es', color_key, attrs=['bold'])} --> {colored('Title: ', color_key)} --> {colored(title, color_value)}, {colored('Author:', color_key)} --> {colored(author, color_value)}, {colored('isbn:', color_key)} --> {colored(isbn, color_value)}")
        print("\033[33m\nBuscando datos....\033[0m")
        scraping(data_element, driver)            

def initContainer(args, parser_find, driver):
    match args.command:
        case "update":
            print(f"El comando que ejecutas es 1 : {args.command} y el contenedor : {args.container}")
        case "stop":
            print(f"El comando que ejecutas es 2 : {args.command} y el contenedor : {args.container}")
        case "restart":
            print(f"El comando que ejecutas es 3 : {args.command} y el contenedor : {args.container}")
        case "find":
            flags = []
            flags.append(args.title)
            flags.append(args.author)
            flags.append(args.isbn)
            findBook(flags, driver, parser_find)
        case _:
            print(f"El comando que ejecutas es 4 : {args.command} y el contenedor : {args.container}")
            #    result = subprocess.run(['docker', '-H', 'unix:///var/run/docker.sock', 'ps'], stdout=subprocess.PIPE)
            #    print(result.stdout.decode('utf-8'))

if __name__=='__main__':
    main()