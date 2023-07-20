import argparse
import sys
import pandas as pd
import time
import urllib.request
import os
import random
import platform
import socket
import re
import json
import datetime
from pathlib import Path
from collections import defaultdict
from utils.utils import success, info, warning, error, log, debug
from database.mysql_connection import DAO, MySQLConnectionError
from redis_db.redis_connection import r
from minio_s3.minio_connection import client
from minio.error import (InvalidResponseError, S3Error)
from PIL import Image
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from tqdm import tqdm, trange
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException, InvalidSessionIdException, WebDriverException
from termcolor import colored
from decouple import config
from colored import fg, bg, attr, style

color_out = "green"
color_key = "yellow"
color_value = "blue"
color_error = "red"
color_warning = "magenta"
__version__ = '2.1.0'
_books_found = []
host = config('WEBDRIVER_HOST')
port = config('WEBDRIVER_PORT_CLI')
_bucket_name = config("BUCKET_NAME")
port = int(port)
myOs = sys.platform
home = Path.home()
if os.path.exists('/app'):
    pictures_dir = str(Path("/app", "Pictures", _bucket_name))
else:
    pictures_dir = str(Path(home, "Pictures", _bucket_name))

debug(host)
debug(port)


def convertir_a_minusculas(cadena):
    cadena_en_mayusculas = cadena.upper()
    nueva_cadena = ""
    for letra in cadena:
        if letra in cadena_en_mayusculas:
            nueva_cadena += letra.lower()
        else:
            nueva_cadena += letra
    return nueva_cadena


standalone = convertir_a_minusculas(config('WEBDRIVER_STANDALONE'))
options = ""


def clear_screem():
    if os.name == "posix":
        os.system("clear")
    elif os.name == "ce" or os.name == "nt" or os.name == "dos":
        os.system("cls")


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
        version='%(prog)s {version} {platform} ({machine})'.format(
            version=__version__, platform=platform.system(), machine=platform.machine())
    )

    subparsers = parser.add_subparsers(
        dest='command', title='Most used commands:', metavar='')

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
        help='Reinicar el contenedor'
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
        if hasattr(args, 'query'):
            if args.query:
                # clear_screem()
                if (standalone == 'firefox'):
                    options = webdriver.FirefoxOptions()
                    options.add_argument('--start-maximized')
                    options.add_argument('--disable-extensions')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-gpu')
                elif (standalone == 'chrome'):
                    options = webdriver.ChromeOptions()
                    options.add_argument('--start-maximized')
                    options.add_argument('--disable-extensions')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-gpu')
                elif (standalone == 'edge'):
                    options = webdriver.EdgeOptions()
                    options.use_chromium = True
                    options.add_argument('--start-maximized')
                    options.add_argument('--disable-extensions')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-gpu')
                else:
                    error('Por favor revisar el nombre la variable STANDALONE, elegir una entre: ',
                          '["firefox", "chrome", "edge"]')
                    sys.exit(1)

                # TODO Crea un objeto socket
                client_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)

                # TODO Establece un tiempo de espera para la conexión
                client_socket.settimeout(5)

                # TODO Intenta conectarse al host
                try:
                    client_socket.connect((host, port))
                    print(
                        f"Conexión exitosa a SELENIUM http://{host}:{config('WEBDRIVER_PORT_WEB')}/?autoconnect=1&resize=scale&password=secret")
                except socket.error as err:
                    print(
                        f"No se pudo conectar a SELENIUM http://{host}:{config('WEBDRIVER_PORT_WEB')}. Error: {err}")
                    return
                # finally:
                #     client_socket.close()
                # TODO Si existe conexion, empezamos con el scraping
                try:
                    driver = webdriver.Remote(
                        command_executor='http://{}:{}'.format(
                            host, port),
                        options=options,
                    )
                    warning(driver)
                    print("-------")
                    findBook(args.query, driver, parser)
                except WebDriverException:
                    warning("No se ha encontrado ninguna sesión activa")
                    close_session_selenium(driver)
            else:
                error(
                    "E:", "Debe dar al menos un patrón de búsqueda. Use -h para ver la ayuda.")
                sys.exit(1)
        elif args.command == "status":
            if not args.container:
                error(
                    "E:", "Debe dar al menos un patrón de búsqueda. Use -h para ver la ayuda.")
                sys.exit(1)
            else:
                initContainer(args.command, args.container)
        elif args.command == "update":
            if not args.container:
                error(
                    "E:", "Debe dar al menos un patrón de búsqueda. Use -h para ver la ayuda.")
                sys.exit(1)
            else:
                initContainer(args.command, args.container)
        elif args.command == "restart":
            if not args.container:
                error(
                    "E:", "Debe dar al menos un patrón de búsqueda. Use -h para ver la ayuda.")
                sys.exit(1)
            else:
                initContainer(args.command, args.container)
        elif args.command == "stop":
            if not args.container:
                error(
                    "E:", "Debe dar al menos un patrón de búsqueda. Use -h para ver la ayuda.")
                sys.exit(1)
            else:
                initContainer(args.command, args.container)
        else:
            version = parser.parse_args(['-v']).version
            log(version)
    else:
        version = parser.parse_args(['-v']).version
        log(version)


def capitalize_first_letter(string):
    return string[:1].upper() + string[1:]


def capitalizar_palabras(string, excluded_words=["de", "la", "del", "y", "el", "las"]):
    if (string):
        words = string.lower().split()
        capitalized_words = []
        for i, word in enumerate(words):
            if word not in excluded_words or i == 0:
                capitalized_words.append(capitalize_first_letter(word))
            else:
                capitalized_words.append(word)
        return " ".join(capitalized_words).encode('utf-8').decode('utf-8')
    else:
        return ''


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
    os.makedirs(pictures_dir, exist_ok=True)
    try:
        image_path = os.path.join(pictures_dir, name_cover + '.png')
        urllib.request.urlretrieve(url, image_path)
        with Image.open(image_path) as img:
            img = img.resize((200, 322), resample=Image.LANCZOS)
            img = img.convert('RGB')
            img.save(image_path, format='PNG', optimize=True)
        return name_cover
    except Exception as e:
        error("Error:", str(e))
        return None


def add_cover_minio(name_cover, old_name_cover=None):
    old_filename = old_name_cover
    filename = name_cover + ".png"
    bucket = _bucket_name
    found = client.bucket_exists(bucket)
    try:
        if not found:
            client.make_bucket(bucket)
            time.sleep(0.5)
            client.fput_object(
                bucket, filename, os.path.join(pictures_dir, filename),
            )
            return True
        else:
            if old_filename is not None:
                try:
                    if client.stat_object(bucket, old_filename):
                        client.remove_object(bucket, old_filename)
                except InvalidResponseError as e:
                    error(f"Error al actualizar el archivo {filename}", {e})
                    return None
            client.fput_object(
                bucket, filename, os.path.join(pictures_dir, filename),
            )
            return True
    except S3Error as exc:
        if exc.code == 'NoSuchKey':
            client.fput_object(
                bucket, filename, os.path.join(pictures_dir, filename),
            )
            return True
        if isinstance(exc):
            print("Error: La diferencia entre el tiempo de solicitud y el tiempo del servidor de Minio es demasiado grande")
            return None
        else:
            print("Error: Ocurrió un error al acceder al servidor de Minio")
            return None


def delete_book_redis():
    try:
        exist_book = r.exists('books')
        if exist_book:
            r.delete('books')
    except:
        pass
    return True


def delete_bookInfo_redis(idBook):
    bookID = idBook
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


def handle_duplicate_isbn(book_data_actual, data_book):
    bookID = book_data_actual[0][0]
    title = book_data_actual[0][1]
    author = book_data_actual[0][2]
    editorial = book_data_actual[0][3]
    isbn = book_data_actual[0][4]
    type = book_data_actual[0][5]
    language = book_data_actual[0][6]
    collection = book_data_actual[0][7]
    purchase_date = book_data_actual[0][8]
    observation = book_data_actual[0][9]
    reserved = book_data_actual[0][10]
    numReference = book_data_actual[0][12]
    cover = book_data_actual[1]
    book_dict = {
        'bookID': bookID,
        'title': title,
        'author': author,
        'editorial': editorial,
        'isbn': isbn,
        'category': type,
        'language': language,
        'collection': collection,
        'purchase_date': purchase_date,
        'observation': observation,
        'reserved': reserved,
        'numReference': numReference,
    }
    if cover is not None:
        book_dict['cover'] = cover[0]
    else:
        book_dict['cover'] = None
    book_dict_copy = {}
    for key, value in book_dict.items():
        if key == 'numReference':
            book_dict_copy['Numero de referencia'] = value
        elif key == 'purchase_date':
            book_dict_copy['Fecha de compra'] = value
        elif key == 'category':
            book_dict_copy['Categoria'] = value
        elif key == 'reserved':
            book_dict_copy['Libro reservado'] = 'Si' if value == 1 else 'No' if value == 0 else value
        elif key == 'cover':
            book_dict_copy['Portada'] = 'Si' if value != None else 'No' if value == None else value
        else:
            book_dict_copy[key] = value
            new_data = {}

    for key, value in data_book[0].items():
        if value != "":
            new_data[key] = value

    text = "Este libro ya existe en la base de datos..."
    print_data_json(text, book_dict_copy)
    text = "Se va actualizar A..."
    print_data_json(text, new_data)
    while True:
        update_input = input(
            f"{fg(15)}{bg(166)}{style.BOLD} ¿ Deseas actualizar su información? ( S/s - N/n ) ? > {attr(0)} >  ")
        if update_input.lower() == "n":
            return None
        elif update_input.lower() == "s":
            _book_actual = book_dict
            bookID = _book_actual['bookID']
            numReference = _book_actual['numReference']
            purchase_date = _book_actual['purchase_date']
            collection = _book_actual['collection']
            observation = _book_actual['observation']
            if (numReference):
                pass
            else:
                print("\n")
                numReference = input("Ingresa NUMERO DE REFERENCIA > ")
            if (purchase_date):
                pass
            else:
                purchase_date = datetime_purchase_date()
            if (collection):
                pass
            else:
                print("\n")
                collection = input("Ingresa COLECCIÓN > ")
            if (observation):
                pass
            else:
                print("\n")
                observation = input("Ingresa OBSERVACIÓN > ")
            _book_actual['bookID'] = bookID
            _book_actual['numReference'] = numReference
            _book_actual['purchase_date'] = purchase_date
            _book_actual['collection'] = collection
            _book_actual['observation'] = observation
            # TODO =======================>
            data_update = new_dict_data_update(new_data, _book_actual)
            return data_update
        else:
            print("\n\t", colored(f"La opción", color_error), colored({update_input}, "blue"), colored(" no es válida. Por favor, ingrese una opcion validad ", color_error) + colored(
                "S/s", color_out) + colored(" o ", color_error) + colored("N/n ", color_warning) + colored("para cancelar.", color_error))
            print("\n")


def new_dict_data_update(nuevo_dic, actual_dict):
    data_update = {}
    # TODO ============================>>

    data_update['numReference'] = actual_dict['numReference']
    data_update['purchase_date'] = actual_dict['purchase_date']
    data_update['collection'] = actual_dict['collection']
    data_update['observation'] = actual_dict['observation']
    data_update['reserved'] = actual_dict['reserved']
    # TODO ============================>>
    try:
        if (nuevo_dic['isbn'] != ''):
            data_update['isbn'] = nuevo_dic['isbn']
    except KeyError:
        data_update = add_update_sino_exist('isbn', data_update, actual_dict)
    # TODO ============================>>
    try:
        if (nuevo_dic['language'] != ''):
            data_update['language'] = nuevo_dic['language']
    except KeyError:
        data_update = add_update_sino_exist(
            'language', data_update, actual_dict)
    # TODO ============================>>
    try:
        if (nuevo_dic['editorial'] != ''):
            data_update['editorial'] = nuevo_dic['editorial']
    except KeyError:
        data_update = add_update_sino_exist(
            'editorial', data_update, actual_dict)
    # TODO ============================>>
    try:
        if (nuevo_dic['title'] != ''):
            data_update['title'] = nuevo_dic['title']
    except KeyError:
        data_update = add_update_sino_exist('title', data_update, actual_dict)
    # TODO ============================>>
    try:
        if (nuevo_dic['author'] != ''):
            data_update['author'] = nuevo_dic['author']
    except KeyError:
        data_update = add_update_sino_exist('author', data_update, actual_dict)
    # TODO ============================>>
    try:
        if (nuevo_dic['category'] != ''):
            data_update['category'] = nuevo_dic['category']
    except KeyError:
        data_update = add_update_sino_exist(
            'category', data_update, actual_dict)

    data_update['bookID'] = actual_dict['bookID']
    if (actual_dict['cover']):
        pass
    else:
        data_update['cover'] = nuevo_dic['cover']
    return data_update


def add_update_sino_exist(key, data_update_, actual_dict):
    value = ''
    data_update = {
        'isbn': '',
        'numReference': '',
        'purchase_date': '',
        'collection': '',
        'observation': '',
        'reserved': '',
        'language': '',
        'editorial': '',
        'title': '',
        'author': '',
        'category': ''
    }

    if data_update_:
        try:
            data_update['isbn'] = data_update_['isbn']
        except KeyError:
            pass
        try:
            data_update['numReference'] = data_update_['numReference']
        except KeyError:
            pass
        try:
            data_update['purchase_date'] = data_update_['purchase_date']
        except KeyError:
            pass
        try:
            data_update['collection'] = data_update_['collection']
        except KeyError:
            pass
        try:
            data_update['observation'] = data_update_['observation']
        except KeyError:
            pass
        try:
            data_update['reserved'] = data_update_['reserved']
        except KeyError:
            pass
        try:
            data_update['language'] = data_update_['language']
        except KeyError:
            pass
        try:
            data_update['editorial'] = data_update_['editorial']
        except KeyError:
            pass
        try:
            data_update['title'] = data_update_['title']
        except KeyError:
            pass
        try:
            data_update['author'] = data_update_['author']
        except KeyError:
            pass
        try:
            data_update['category'] = data_update_['category']
        except KeyError:
            pass

    if actual_dict[key] == '':
        print("\n")
        value = input(f"Ingresa {key.upper()} > ")

    if value == '':
        if actual_dict and actual_dict[key] != '':
            data_update[key] = actual_dict[key]
    else:
        data_update[key] = value

    return data_update


def add_book_bd(data, driver):
    info("Analizando datos....")
    with tqdm(total=7) as abar:
        category = ''
        data_cover = ''
        url_cover = ''
        link_book = data['view']
        # TODO ====================>
        try:
            driver.get(link_book)
        except:
            pass
        # TODO ====================>
        try:
            author = capitalizar_palabras(data['author'])
            abar.update(1)
        except:
            pass
        # TODO ====================>
        try:
            data_title = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, './/*[@id="app"]/div[1]/main/div/div/div/div[3]//div[contains(@class, "product-info")]//h1')))
            title = capitalizar_palabras(data_title.text)
            try:
                small_element = data_title.find_element(By.XPATH, ".//small")
                if (small_element):
                    small_text = capitalizar_palabras(small_element.text)
                    title = title.replace(small_text, "").strip()
            except NoSuchElementException:
                pass
            abar.update(1)
        except TimeoutException:
            title = ''
        # TODO ====================>
        try:
            data_category = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, './/*[@id="breadcrumbs"]/div/div[2]/div[9]/a/span')))
            category = capitalizar_palabras(data_category.text)
            abar.update(1)
        except TimeoutException:
            try:
                data_category = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                    (By.XPATH, './/*[@id="breadcrumbs"]/div/div[2]/div[7]/a/span')))
                category = capitalizar_palabras(data_category.text)
                abar.update(1)
            except TimeoutException:
                try:
                    data_category = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                        (By.XPATH, './/*[@id="breadcrumbs"]/div/div[2]/div[5]/a/span')))
                    category = capitalizar_palabras(data_category.text)
                    abar.update(1)
                except TimeoutException:
                    category = ''
        # TODO ====================>
        try:
            data_cover = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="app"]/div[1]/main/div/div/div/div[3]//div[contains(@class, "swiper-img-container")]//img')))
        except TimeoutException:
            data_cover = ''
        # TODO ====================>
        if data_cover:
            url_cover = data_cover.get_attribute(
                "srcset").split(",")[-1].split(" ")[0]
            abar.update(1)
        else:
            url_cover = None
        # TODO ====================>
        resultados = []
        isbn = None
        idioma = None
        editorial = None
        # TODO ====================>
        try:
            elementos = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located(
                (By.XPATH, '//*[@id="app"]/div[1]/main/div/div/div/div[8]//div[contains(@class,"dataSheet")]')))
        except TimeoutException:
            try:
                elementos = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located(
                    (By.XPATH, '//*[@id="app"]/div[1]/main/div/div/div/div[7]//div[contains(@class,"dataSheet")]')))
            except TimeoutException:
                try:
                    elementos = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located(
                        (By.XPATH, '//*[@id="app"]/div[1]/main/div/div/div/div[6]//div[contains(@class,"dataSheet")]')))
                except TimeoutException:
                    try:
                        elementos = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located(
                            (By.XPATH, '//*[@id="app"]/div[1]/main/div/div/div/div[4]//div[contains(@class,"dataSheet")]')))
                    except TimeoutException:
                        elementos = ''
        # TODO ====================>
        datos = {}
        if elementos:
            for elemento in elementos:
                textos = elemento.find_elements(By.XPATH, ".//span")
                for i in range(0, len(textos), 2):
                    clave = textos[i].text.strip(":")
                    valor = textos[i+1].text
                    datos[clave] = valor
                    if textos[i].text == "ISBN:":
                        isbn = textos[i+1].text
                        abar.update(1)
                    if textos[i].text == "Idioma:":
                        idioma = textos[i+1].text
                        abar.update(1)
                    if textos[i].text == "Editorial:":
                        editorial = textos[i+1].text
                        abar.update(1)
            resultados.append({'isbn': isbn, 'language': capitalizar_palabras(idioma), 'editorial': capitalizar_palabras(
                editorial), 'title': title, 'author': author, 'category': category, 'cover': url_cover})
            if not resultados:
                warning('No se encontraron resultados.')
                abar.close()
            else:
                abar.close()
                tareas = [data_operation(resultados, driver)]
                loop(tareas)
        # TODO ====================>
        else:
            warning('No se pudo encontrar la hoja técnica.')
            abar.close()
            sys.exit(1)


def select_element(driver):
    info("Cargando datos....")
    for i in trange(5, unit="s", unit_scale=0.1, unit_divisor=1):
        time.sleep(0.2)
    # clear_screem()
    imprimir_menu()
    while True:
        user_input = input(
            "\nIngrese el ID de la opción que desea o X para salir: ")
        if user_input.lower() == "x":
            print("\n\t", colored('Cerrando session....', color_error))
            print("\n")
            close_session_selenium(driver)
            return None
        try:
            choice = int(user_input)
            for book in _books_found:
                if book["ID"] == choice:
                    book_data = {
                        'view': book['view'], 'title': book['title'], 'author': book['author']}
                    add_book_bd(book_data, driver)
                    return choice
        except ValueError:
            print("\n\t", colored(f"La opción {user_input} no es válida. Por favor, ingrese un número entre ", color_error) + colored("0", color_out) + colored(
                f" y {len(_books_found) - 1}", color_out) + colored(" o ", color_error) + colored("X ", color_warning) + colored("para salir.", color_error))


def scraping(text_find, driver):
    print(
        "\n" + f"{colored('The search pattern is ', color_key, attrs=['bold'])} --> {fg(7)}{bg(17)}  {text_find}  {attr(0)}")
    info("Buscando datos....")
    element = None
    articles = []
    with tqdm(total=3) as sbar:
        driver.get('https://www.casadellibro.com/')
        time.sleep(1)
        try:
            cookies_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler')))
            cookies_button.click()
            sbar.update(1)
        except TimeoutException:
            sbar.close()
            pass
        except NoSuchElementException:
            sbar.close()
            pass
        time.sleep(0.5)
        try:
            input_element = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="app"]/div[1]/div[1]/div[3]/div[1]/div[1]/input')))
            input_element.click()
            # try:
            #     boton_element = driver.find_element(
            #         By.XPATH, '//*[@id="app"]/div[1]/div[1]/div[3]/div[1]/div[1]/button/span')
            #     boton_element.click()
            # except TimeoutException:
            #     warning(
            #         '[ ERROR ] No se puede interactuar en el ELEMENTO BUTTON. ')
            #     sbar.close()
            # except ElementClickInterceptedException:
            #     warning(
            #         '[ ERROR ] El ELEMENTO BUTTON está oculto y no se puede hacer clic en él.')
            #     sbar.close()
            sbar.update(1)
        except TimeoutException:
            warning('[ ERROR ] No se puede interactuar en el ELEMENTO INPUT.')
            sbar.close()
        except ElementClickInterceptedException:
            warning(
                '[ ERROR ] El ELEMENTO INPUT está oculto y no se puede hacer clic en él.')
            sbar.close()
        time.sleep(0.5)
        try:
            input2_element = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                (By.XPATH, '/html/body/div[3]/div/div[1]/div/div[1]/header/div/div/div[1]/input')))
            input2_element.send_keys(text_find)
            try:
                element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'section.ebx-grid.ebx-empathy-x__grid')))
            except TimeoutException:
                try:
                    element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, 'div.ebx-sliding-panel__scroll')))
                except TimeoutException:
                    try:
                        element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                            (By.CSS_SELECTOR, 'x-staggering-transition-group x-staggered-fade-and-slide x-base-grid x-base-grid--cols-6')))
                    except TimeoutException:
                        try:
                            element = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                                (By.XPATH, '//*[@id="main-scroll"]/div[3]/div/ul')))
                        except TimeoutException:
                            element = None
            sbar.update(1)
        except TimeoutException:
            warning('El ELEMENTO SEARCH no está disponible para interactuar.')
    if element:
        articles = element.find_elements(By.TAG_NAME, "article")
    else:
        articles = []
    extract_list_book(driver, articles)


def close_session_selenium(driver):
    try:
        driver.quit()
        time.sleep(1)
        sys.exit(1)
    except InvalidSessionIdException:
        pass


def extract_list_book(driver, articles):
    id = 0
    if articles:
        for article in articles:
            try:
                title = driver.find_element(
                    By.XPATH, ".//a[1]/div/h2[1]").text.strip()
            except NoSuchElementException:
                title = ''
            try:
                author = article.find_element(
                    By.XPATH, ".//a[1]/div/h2[2]").text.strip()
            except NoSuchElementException:
                author = ''
            try:
                link = article.find_element(
                    By.XPATH, ".//div[1]/a").get_attribute('href')
            except NoSuchElementException:
                link = ''
            try:
                other = article.find_element(
                    By.XPATH, ".//a[1]/div/span").text.strip()
            except NoSuchElementException:
                other = ''
            dict_article_data = {}
            if any([len(title) > 0, len(author) > 0, len(link) > 0, len(other) > 0]):
                dict_article_data["ID"] = id
                dict_article_data["title"] = title
                dict_article_data["author"] = author
                dict_article_data["view"] = link
                dict_article_data["other"] = other
                _books_found.append(dict_article_data)
            id += 1
        if _books_found:
            select_element(driver)
        else:
            warning('No hay datos para ese elemento a buscar.')
            close_session_selenium(driver)
    else:
        warning('No se pudo encontrar el elemento deseado.')
        close_session_selenium(driver)


def data_operation(resultados, driver):
    data_book = resultados
    tipo = None
    add_or_update = None
    info("Realizando operaciones en la Base de datos....")
    with tqdm(total=3) as rbar:
        # TODO ==============>
        try:
            dao = DAO()
            dao.connect_database()
            rbar.update(1)
        except MySQLConnectionError as ex:
            rbar.close()
            error("[ 1 ] Error de integridad:", ex)
            close_session_selenium(driver)
        yield
        time.sleep(0.5)
        # TODO ==============>
        try:
            book_data = extract_data(data_book)
            if book_data:
                success("[ 2 ] Datos extraidos con éxito.")
                rbar.update(1)
        except:
            rbar.close()
            error("[ 2 ] Error al extraer datos.")
            close_session_selenium(driver)
        yield
        time.sleep(0.5)
        # TODO ==============>
        try:
            dao = DAO()
            result = dao.check_data(book_data)
            success("[ 3 ] Comprobando datos.")
            rbar.update(1)
            print("\n")
        except:
            rbar.close()
            error("[ 3 ] Error al comprobar datos.")
            close_session_selenium(driver)
        yield
        time.sleep(0.5)
        # TODO ====================>
        try:
            if (result):
                add_or_update = handle_duplicate_isbn(result, data_book)
                tipo = 'update'
            else:
                add_or_update = scheck_data_after_add(data_book)
                tipo = 'add'
        except:
            rbar.close()
            sys.exit(0)
        yield
        # TODO ====================>
        try:
            if add_or_update is None:
                rbar.close()
                select_element(driver)
            else:
                añadir_book_bd(driver, add_or_update, tipo)
        except:
            rbar.close()
            sys.exit(0)
        yield
    yield


def añadir_book_bd(driver, add_or_update, tipo='add'):
    with tqdm(total=5) as uabar:
        step = 0
        if add_or_update:
            dao = DAO()
            name_cover = None
            succes_insert_cover = None
            try:
                url_cover = add_or_update['cover']
            except KeyError:
                url_cover = None
            # TODO ==============>
            if url_cover:
                try:
                    name_cover = extract_nameCover(url_cover)
                    if name_cover:
                        success(
                            f"[ 1 ] Cover {name_cover} descargado con éxito in {pictures_dir}.")
                        step += 1
                        uabar.update(step)
                except:
                    uabar.close()
                    error(f"[ 1 ] Error al descargar Cover.")
                    close_session_selenium(driver)
            # TODO ==============>
            time.sleep(0.5)
            if tipo == 'add':
                dao = DAO()
                book_id = dao.insert_databook(add_or_update)
                if book_id:
                    success(
                        f"[ 2 ] The book data has been added correctly, with ID : {book_id}")
                    step += 1
                    uabar.update(step)
                else:
                    error("[ 2 ] Error al añadir libro a la BD !")
                    uabar.close()
            elif tipo == 'update':
                book_id = add_or_update['bookID']
                dao.update_databook(book_id, add_or_update)
                if book_id:
                    success(
                        f"[ 2 ] The book data has been update correctly, with ID : {book_id}")
                    step += 1
                    uabar.update(step)
                else:
                    error("[ 2 ] Error al actualizar el libro en la BD !")
                    uabar.close()
            else:
                pass
            # TODO ==============>
            time.sleep(1)
            if name_cover and book_id:
                succes_insert_cover = dao.insert_nameCover(name_cover, book_id)
                if (succes_insert_cover):
                    success(
                        f"[ 3 ] The cover added correctly, with ID : {book_id}")
                    step += 1
                    uabar.update(step)
                else:
                    error(f"[ 3 ] Error al añadir cover a la BD !")
                    uabar.close()
            # TODO ==============>
            time.sleep(0.5)
            if succes_insert_cover:
                response_cover = add_cover_minio(name_cover)
                if response_cover:
                    success(
                        f"[ 4 ] Cover data upload MINIO BUCKET {config('BUCKET_NAME')}, name cover is : {name_cover}.")
                    step += 1
                    uabar.update(step)
                else:
                    error(
                        f"[ 4 ] Error al subir cover a BUCKET {config('BUCKET_NAME')}.")
                    uabar.close()
            # TODO ==============>
            time.sleep(0.5)
            try:
                succes_redis_books = delete_book_redis()
                time.sleep(0.5)
                succes_redis_bookInfo = delete_bookInfo_redis(book_id)
                if succes_redis_books and succes_redis_bookInfo:
                    success(f"[ 5 ] Eliminados datos en redis.")
                    step += 1
                    uabar.update(step)
                else:
                    error(f"[ 5 ] Error al eliminar datos en REDIS.")
                    uabar.close()
            except:
                uabar.close()
                driver.quit()
                sys.exit(1)
            uabar.close()
            close_session_selenium(driver)
        else:
            uabar.close()
            select_element(driver)


def print_data_json(text, result_check_pint):
    if isinstance(result_check_pint, list):
        result_check_pint = defaultdict(
            lambda: None, {f"New DATA": item for i, item in enumerate(result_check_pint)})
    else:
        result_check_pint = defaultdict(lambda: None, result_check_pint)

    for key, value in result_check_pint.items():
        if isinstance(value, datetime.datetime):
            result_check_pint[key] = value.strftime('%Y-%m-%d')
        elif value is None:
            result_check_pint[key] = 'None'

    result_check_pint = dict(result_check_pint)

    json_str = json.dumps(result_check_pint, indent=4, ensure_ascii=False)
    encoded_str = json_str.encode('utf-8')
    print("\n")
    print(f"{fg(190)} {text} {attr(0)}")
    print(encoded_str.decode('utf-8'))
    print("\n")


def scheck_data_after_add(data_book):
    text = "Estos son los datos que se van añadir a la Bases de datos..."
    print_data_json(text, data_book)
    while True:
        add_input = input(
            f"{fg(15)}{bg(22)} ¿ Deseas añadir este libro a la Bases de datos ? ( S/s - N/n ){attr(0)} >  ")
        if add_input.lower() == 'n':
            return None
        elif add_input.lower() == "s":
            print("\n")
            numReference = input("Ingresa NUMERO DE REFERENCIA > ")
            purchase_date = datetime_purchase_date()
            print("\n")
            collection = input("Ingresa COLECCIÓN > ")
            print("\n")
            observation = input("Ingresa OBSERVACIÓN > ")
            _data_book = data_book[0]
            _data_book['numReference'] = numReference
            _data_book['purchase_date'] = purchase_date
            _data_book['collection'] = collection
            _data_book['observation'] = observation
            return _data_book
        else:
            print("\n\t", colored(f"La opción", color_error), colored({add_input}, "blue"), colored(" no es válida. Por favor, ingrese una opcion validad ", color_error) + colored(
                "S/s", color_out) + colored(" o ", color_error) + colored("N/n ", color_warning) + colored("para cancelar.", color_error))
            print("\n")


def datetime_purchase_date():
    while True:
        print("\n")
        purchase_date = input("Ingresa FECHA DE COMPRA ( aaaa-mm-dd ) > ")
        if not purchase_date:
            return None
        try:
            fecha = datetime.datetime.strptime(purchase_date, '%Y-%m-%d')
            return fecha
        except ValueError:
            error("El formato de fecha ingresado es incorrecto. Debe ser aaaa-mm-dd.")


def findBook(data, driver, parser_find):
    data_find = data
    data_element = ' '.join(data_find)
    if (data_find == ''):
        parser_find.print_help()
        close_session_selenium(driver)
    else:
        scraping(data_element, driver)


def imprimir_menu():
    dict_articles_data = {}
    for d in _books_found:
        for k, v in d.items():
            dict_articles_data.setdefault(k, []).append(v)
    df = pd.DataFrame.from_dict(dict_articles_data)
    total_elements = len(df)
    print("\n------------------------------------------------------------------------------------------------------------------------")
    print("------------------------------------------------- LIBROS DISPONIBLES ---------------------------------------------------")
    print("------------------------------------------------------------------------------------------------------------------------")
    print('\n', df, '\n')
    print("\n\t\t", colored("[X]   Salir", color_error), "\n")
    print(
        f"{colored('El total de libros encontrados es :',  color_out, attrs=['bold'])} {colored(total_elements, color_key)}")


def initContainer(command, container):
    match command:
        case "update":
            log(
                f"El comando que ejecutas es : {command} y el contenedor : {container}")
        case "stop":
            log(
                f"El comando que ejecutas es : {command} y el contenedor : {container}")
        case "restart":
            log(
                f"El comando que ejecutas es : {command} y el contenedor : {container}")
        case "status":
            log(
                f"El comando que ejecutas es : {command} y el contenedor : {container}")
        case _:
            error(
                "E:", "Debe dar al menos un patrón de búsqueda. Use -h para ver la ayuda.")
            sys.exit(1)


if __name__ == '__main__':
    main()
