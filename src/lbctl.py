import argparse
import sys
import pandas as pd
import time
import urllib.request
import os
import random
import platform
import socket
from utils.utils import success, info, warning, error, log, debug, select_option
from database.mysql_connection import DAO, MySQLConnectionError
from redis_db.redis_connection import r
from minio_s3.minio_connection import client
from minio.error import InvalidResponseError, S3Error
from PIL import Image
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from tqdm import tqdm, trange
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException, InvalidSessionIdException, WebDriverException
from termcolor import colored
from decouple import config

color_out = "green"
color_key = "yellow"
color_value = "blue"
color_error = "red"
color_warning = "magenta"
__version__ = '1.0.0'


host = config('WEBDRIVER_HOST')
port = config('WEBDRIVER_PORT_CLI')
port = int(port)

def main():

    parser = argparse.ArgumentParser(
        prog="lbctl",
        usage='lbctl <command> [flags]',
        description='''
            lbctl is a commandline database manager and provides commands for.
            \n
            \t- searching and managing as well as querying information about books.
        ''',
        epilog='Use "lbctl -h / --help" for more information about a given command.'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s {version} {platform} ({machine})'.format(version=__version__, platform=platform.system(),machine=platform.machine())
    )

    subparsers = parser.add_subparsers(dest='command', title='Most used commands:', metavar='')

    search_parser = subparsers.add_parser(
        'search',
        usage='lbctl search [search pattern]',
        description='Most used pattern:\n  Titulo, Autor, ISBN', 
        help='Busca libros por Titulo, Autor o ISBN'
    )
    search_parser.add_argument(
        'query', 
        nargs='*', 
        help='Se debe especificar el Titulo del libro, Autor o ISBN'
    )

    status_parser = subparsers.add_parser(
        'status',
        usage='lbctl status CONTAINER',
        help='Ver el estado del contenedor'
    )
    status_parser.add_argument(
        'container', 
        nargs='*', 
        help='Se debe indicar el id o name del container'
    )

    update_parser = subparsers.add_parser(
        'update',
        usage='lbctl update CONTAINER',
        help='Actualizar el contenedor'
    )
        
    update_parser.add_argument(
        'container', 
        nargs='*', 
        help='Se debe indicar el id o name del container'
    )

    restart_parser = subparsers.add_parser(
        'restart',
        usage='lbctl restart CONTAINER',
        help='restartear el contenedor'
    )
        
    restart_parser.add_argument(
        'container', 
        nargs='*', 
        help='Se debe indicar el id o name del container'
    )

    stop_parser = subparsers.add_parser(
        'stop',
        usage='lbctl stop CONTAINER',
        help='Detener el contenedor'
    )
        
    stop_parser.add_argument(
        'container', 
        nargs='*', 
        help='Se debe indicar el id o name del container'
    )

    args = parser.parse_args()

    if args.command is None:
        version = parser.parse_args(['-v']).version
        log(version)
        return
    if not (hasattr(args, 'v') and args.v or hasattr(args, 'h') and args.h):
        ## Crea un objeto socket
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        ## Establece un tiempo de espera para la conexión
        client_socket.settimeout(5)

        ## Intenta conectarse al host
        try:
            client_socket.connect((host, port))
            print("\n")
            print(f"Conexión exitosa a SELENIUM http://{host}:{config('WEBDRIVER_PORT_WEB')}")
        except socket.error as err:
            print(f"No se pudo conectar a SELENIUM http://{host}:{config('WEBDRIVER_PORT_WEB')}. Error: {err}")
            return
        finally:
            ## Cierra la conexión
            client_socket.close()
        
        if args is None:
            parser.print_help()
        elif hasattr(args, 'query'):
            if args.query:
                try:
                    options = webdriver.FirefoxOptions()
                    options.add_argument('--start-maximized')
                    options.add_argument('--disable-extensions')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-gpu')
                    driver = webdriver.Remote(
                        command_executor='http://{}:4444/wd/hub'.format(config('WEBDRIVER_HOST')),
                        options=options,
                    )
                    findBook(args.query, driver, parser)
                except WebDriverException:
                    try:
                        driver.quit()
                    except InvalidSessionIdException:
                        pass
                    ## TODO ERROR
                    warning("No se ha encontrado ninguna sesión activa")
                    driver = webdriver.Firefox()
            else:
                error("E:","Debe dar al menos un patrón de búsqueda. Use -h para ver la ayuda.")
                sys.exit(1)
        elif args.command == "status":
            if not args.container:
                error("E:","Debe dar al menos un patrón de búsqueda. Use -h para ver la ayuda.")
                sys.exit(1)
            else:
                initContainer(args.command, args.container)
        elif args.command == "update":
            if not args.container:
                error("E:","Debe dar al menos un patrón de búsqueda. Use -h para ver la ayuda.")
                sys.exit(1)
            else:
                initContainer(args.command, args.container)
        elif args.command == "restart":
            if not args.container:
                error("E:","Debe dar al menos un patrón de búsqueda. Use -h para ver la ayuda.")
                sys.exit(1)
            else:
                initContainer(args.command, args.container)
        elif args.command == "stop":
            if not args.container:
                error("E:","Debe dar al menos un patrón de búsqueda. Use -h para ver la ayuda.")
                sys.exit(1)
            else:
                initContainer(args.command, args.container)
        else:
            version = parser.parse_args(['-v']).version
            log(version)
    else:
        version = parser.parse_args(['-v']).version
        log(version)
  
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
    url = data_cover
    name_cover = generate_cover_rand(15)
    pictures_dir = f'/app/{config("BUCKET_NAME")}/'
    try:
        urllib.request.urlretrieve(url, pictures_dir + name_cover + '.png')
    except FileNotFoundError as e:
        error("Error: ", f"el directorio {pictures_dir} de destino no existe.")
        sys.exit(1)
    with Image.open(pictures_dir + name_cover + '.png') as img:
        img = img.resize((200, 322), resample=Image.LANCZOS, box=None, reducing_gap=None)
        img = img.convert('RGB')
        img.save(pictures_dir + name_cover + '.png', format='PNG', optimize=True)
    return name_cover

def add_cover_minio(old_name_cover, name_cover):
    old_filename = old_name_cover
    filename = name_cover + ".png"
    bucket = config("BUCKET_NAME")
    found = client.bucket_exists(bucket)
    try:
        if not found:
            client.make_bucket(bucket)
            time.sleep(0.5)
            client.fput_object(
                bucket, filename, os.path.join(f'/app/{config("BUCKET_NAME")}', filename),
            )
            return True
        else:
            if old_filename is not None:
                try:
                    if client.stat_object(bucket, old_filename):
                        client.remove_object(bucket, old_filename)
                except InvalidResponseError as e:
                    error(f"Error al actualizar el archivo {filename}",{e})
                    return None
            client.fput_object(
                bucket, filename, os.path.join(f'/app/{config("BUCKET_NAME")}', filename),
            )
            return True
    except S3Error as exc:
        if exc.code == 'NoSuchKey':
            client.fput_object(
                bucket, filename, os.path.join(f'/app/{config("BUCKET_NAME")}', filename)
            )
            return True
        else:
            return None

def delete_book_redis(idBook):
    bookID = idBook
    try:
        exist_book = r.exists('books')
        if exist_book:
            r.delete('books')
    except:
        pass
    try:
        exist_book = r.exists(f'bookInfo{bookID}')
        if exist_book:
            r.delete(f'bookInfo{bookID}')
    except:
        pass
    
    return True

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
        warning("Error al acceder al title en los datos recibidos.")
    try:
        datos['author'] = data[0]['author']
    except (IndexError, KeyError):
        warning("Error al acceder al author en los datos recibidos.")
    try:
        datos['editorial'] = data[0]['editorial']
    except (IndexError, KeyError):
        warning("Error al acceder al editorial en los datos recibidos.")
    try:
        datos['isbn'] = data[0]['isbn']
    except (IndexError, KeyError):
        warning("Error al acceder al ISBN en los datos recibidos.")
    try:
        datos['type'] = data[0]['category']
    except (IndexError, KeyError):
        warning("Error al acceder al type en los datos recibidos.")
    try:
        datos['language'] = data[0]['language']
    except (IndexError, KeyError):
        warning("Error al acceder al language en los datos recibidos.")  
    try:
        datos['cover'] = data[0]['cover']
    except (IndexError, KeyError):
        warning("Error al acceder al cover en los datos recibidos.")   
    
    return datos

def loop(tareas):
    while tareas:
        actual = tareas.pop(0)
        try:
            next(actual)
            tareas.append(actual)
        except StopIteration:
            pass
             
def handle_duplicate_isbn(idBook, book_data, name_cover, driver):
    dao = DAO()
    bookID = idBook
    nameCover = name_cover
    print("Este libro ya existe en la base de datos, book ID: " + str(bookID))
    print("\n")
    while True:
        update_input = input("\n¿Deseas actualizar su información? ( S/s - N/n ) > ")
        if update_input.lower() == "n":
            print("\n")
            print("\n\t", colored('Cerrando session....', color_error))
            print("\n")
            driver.quit()
            sys.exit(1)
        elif update_input.lower() == "s":
            succes_data = dao.update_databook(bookID, book_data)
            if succes_data:
                dao.update_nameCover(nameCover, bookID)
            else:
                error(f"[ ERROR ], The BOOK with ID : {bookID} does not exist")
            break
        else:
            print("\n\t" , colored(f"La opción", color_error), colored({update_input}, "blue"),colored(" no es válida. Por favor, ingrese una opcion validad ", color_error) + colored("S/s", color_out) + colored(" o ",color_error) + colored("N/n ", color_warning) + colored("para cancelar.", color_error))
              
def data_operation(resultados, driver):
    data_book = resultados
    info("Realizando operaciones en la Base de datos....")
    
    with tqdm(total=6) as rbar:
        try:
            book_data = extract_data(data_book)
            if book_data:
                success("[ 1 ] Datos extraidos con éxito.")
                time.sleep(0.5)
                rbar.update(1)
        except:
            rbar.close()
            error("[ 1 ] Error al extraer datos.")
            driver.quit()
            sys.exit(1)
        yield
        
        try:
            dao = DAO()
            dao.connect_database()
            time.sleep(0.5)
            rbar.update(1)
        except MySQLConnectionError as ex:
            rbar.close()
            error("[ 2 ] Error de integridad:", ex)
            driver.quit()
            sys.exit(1)
        yield
        
        try:
            name_cover = extract_nameCover(book_data['cover'])
            if name_cover:
                success(f"[ 3 ] Cover {name_cover} descargado con éxito.")
                time.sleep(0.5)
                rbar.update(1)
        except:
            rbar.close()
            error(f"[ 3 ] Error al descargar Cover.")
            driver.quit()
            sys.exit(1)
        yield
        
        try:
            bookID = dao.exist_databook(book_data)
            old_name_cover = dao.get_name_cover(bookID)
            if bookID:
                handle_duplicate_isbn(bookID, book_data, name_cover, driver)
                success(f"[ 4 ] The book data has been update correctly, with ID : {bookID}")
                time.sleep(0.5)
                rbar.update(1)
            else:
                book_id = dao.insert_databook(book_data)
                if book_id:
                    dao.insert_nameCover(name_cover, book_id)
                else:
                    rbar.close()
                    error("[ ERROR ], The BOOK with ID : {} does not exist".format(book_id))
                success(f"[ 4 ] The book data has been added correctly, with ID : {book_id}")
                time.sleep(0.5)
                rbar.update(1)
        except:
            rbar.close()
            driver.quit()
            sys.exit(1)
        yield
        
        try:
            response_redis = delete_book_redis(bookID)
            if response_redis:
                success(f"[ 5 ] Eliminados datos en redis.")
                time.sleep(0.5)
                rbar.update(1)
        except:
            rbar.close()
            driver.quit()
            sys.exit(1)
        yield
        
        try:
            if name_cover is not None:
                response_cover = add_cover_minio(old_name_cover, name_cover)
                if response_cover:
                    success(f"[ 6 ] Cover data upload MINIO BUCKET {config('BUCKET_NAME')}, name cover is : {name_cover}.")
                    time.sleep(0.5)
                    rbar.update(1)
                else:
                    error(f"[ 6 ] Error al subir cover a BUCKET {config('BUCKET_NAME')}.")
                    rbar.close()
            rbar.close()
        except:
            rbar.close()
            driver.quit()
            sys.exit(1)
    yield

def add_book_bd(data, driver):
    info("Analizando datos....")
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
            data_title = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, './/*[@id="app"]/div[1]/main/div/div/div/div[3]//div[contains(@class, "product-info")]//h1')))
            title = capitalizar_palabras(data_title.text)
        except TimeoutException:
                title = ''
        try:
            data_category = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, './/*[@id="breadcrumbs"]/div/div[2]/div[5]/a/span')))
            category = capitalizar_palabras(data_category.text)
        except TimeoutException:
                category = ''
        try:
            data_cover = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//*[@id="app"]/div[1]/main/div/div/div/div[3]//div[contains(@class, "swiper-img-container")]//img')))
        except TimeoutException:
            data_cover = ''

        if data_cover:
            url_cover = data_cover.get_attribute("srcset").split(",")[-1].split(" ")[0]
        abar.update(1)
        
        book = []
        resultados = []
        isbn = None
        idioma = None
        editorial = None
        
        try:
            elementos = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/div[1]/main/div/div/div/div[7]//div[contains(@class,"border-left")]//div[@class="hidden-sm-and-down"]//span')))
        except TimeoutException:
            try:
                elementos = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/div[1]/main/div/div/div/div[6]//div[contains(@class,"border-left")]//div[@class="hidden-sm-and-down"]//span')))
            except TimeoutException:
                try:
                    elementos = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="app"]/div[1]/main/div/div/div/div[4]//div[contains(@class,"border-left")]//div[@class="hidden-sm-and-down"]//span')))
                except TimeoutException:
                    elementos = ''
        time.sleep(0.5)
        if elementos:
            for elemento in elementos:
                valor = elemento.text.strip() # elimina espacios en blanco al inicio y final
                if valor: # verifica si el valor no está vacío
                    book.append(valor)      
            for i in range(len(book)):
                if book[i] == "ISBN:":
                    isbn = book[i+1]
                if book[i] == "Idioma:":
                    idioma = book[i+1]
                if book[i] == "Editorial:":
                    editorial = book[i+1]
            resultados.append({'isbn': isbn, 'language': capitalizar_palabras(idioma), 'editorial': capitalizar_palabras(editorial), 'title': title, 'author': author, 'category': category, 'cover': url_cover})
            if not resultados:
                warning('No se encontraron resultados.')
                abar.close()
            else:
                abar.close()
                tareas = [data_operation(resultados, driver)]
                loop(tareas)
        else:
            warning('No se pudo encontrar la hoja técnica.')
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
            print("\n")
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
                warning('El elemento no está disponible para interactuar.')
                pass
            except ElementClickInterceptedException:
                warning('El elemento está oculto y no se puede hacer clic en él.')
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
                warning('El elemento no está disponible para interactuar.')
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
                title = ''
            try:
                author = article.find_element(By.CSS_SELECTOR, ".ebx-result-authors").text.strip()
            except NoSuchElementException:
                author = ''
            try:
                link = article.find_element(By.CSS_SELECTOR, ".ebx-result-title a").get_attribute('href')
            except NoSuchElementException:
                link = ''
            try:
                other = article.find_element(By.CSS_SELECTOR, ".ebx-result-binding-type").text.strip()
            except NoSuchElementException:
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
        info("Cargando datos....")
        for i in trange(5, unit="s", unit_scale=0.1, unit_divisor=1):
            time.sleep(0.2)
        select_book(list_articles_data, df, driver)
    else :
        warning('No se pudo encontrar el elemento deseado.')

    try:
        driver.quit()
    except InvalidSessionIdException:
        pass

def findBook(data, driver, parser_find):
    data_find = data
    data_element = ' '.join(data_find)
    if (data_find == ''):
        parser_find.print_help()
        driver.quit()
    else:
        print("\n" + f"{colored('The search pattern is', color_key, attrs=['bold'])} --> {colored({data_element}, color_value)}")
        info("Buscando datos....")
        scraping(data_element, driver)            

def initContainer(command, container):
    match command:
        case "update":
            log(f"El comando que ejecutas es : {command} y el contenedor : {container}")
        case "stop":
            log(f"El comando que ejecutas es : {command} y el contenedor : {container}")
        case "restart":
            log(f"El comando que ejecutas es : {command} y el contenedor : {container}")
        case "status":
            log(f"El comando que ejecutas es : {command} y el contenedor : {container}")
        case _:
            error("E:","Debe dar al menos un patrón de búsqueda. Use -h para ver la ayuda.")
            sys.exit(1)

if __name__=='__main__':
    main()