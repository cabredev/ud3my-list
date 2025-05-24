import browser_cookie3
from pyfiglet import Figlet
from colorama import Fore, Back, Style, init
import requests
import logging, coloredlogs
import pandas as pd

LOG_FORMAT = '[%(asctime)s] [%(name)s] [%(funcName)s:%(lineno)d] %(levelname)s: %(message)s'
LOG_DATE_FORMAT = '%d-%m-%Y %H:%M:%S'
LOG_LEVEL = logging.INFO
LOG_STYLES = {
    'debug': {'color': 'blue'},
    'info': {'color': 'white'},
    'warning': {'color': 'yellow'},
    'error': {'color': 'red'},
    'critical': {'bold': True, 'color': 'red'},
    'success': {'bold': True, 'color': 'green'},
    'verbose': {'color': 'blue'},
    'notice': {'color': 'magenta'}
}
logger = logging.getLogger('list-courses')
coloredlogs.install(level=LOG_LEVEL, logger=logger, fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT, level_styles=LOG_STYLES)

init(autoreset=True) #Para restablecer colores después de cada impresión 
font = Figlet(font='slant')
script_title = 'My Courses'
print(Fore.MAGENTA + Style.BRIGHT + font.renderText(script_title))
print()

# Navegador recomendado Mozilla Firefox
cj = browser_cookie3.firefox()

def getCookies(domain, cookieName=''):
    Cookies = {}
    firefoxCookies = list(cj)

    for cookie in firefoxCookies:

        if (domain in cookie.domain):
            #print (cookie.name, cookie.domain, cookie.value)
            Cookies[cookie.name] = cookie.value

    if(cookieName!=''):
        try:
            return Cookies[cookieName] #return specified cookie
        except:
            return {} #if exception raised return an empty dictionary
    else:
        return Cookies #return all cookies or nothing

access_token = getCookies("udemy", "access_token")

# Preparar las cookies para la solicitud
session_cookies = {
    'access_token': access_token,
}

# API UDEMY
MY_COURSES_API = "https://udemy.com/api-2.0/users/me/subscribed-courses?fields[course]=id,title,url,visible_instructors,is_paid,published_title&ordering=last_enrolled&page=1"

response = requests.get(MY_COURSES_API, cookies=session_cookies)

all_courses_processed = []

# Verificar respuesta inicial
if response.status_code == 200:
    #logger.info("Successful request.")
    data = response.json()
    count = data.get('count', 0) # Usar .get() para evitar errores si la clave no existe
    logger.info(f"Total de Cursos: {count}")
    next_url = data.get('next') # URL para obtener las siguientes páginas
    results = data.get('results', []) # Inicializa la lista de resultados con los de la primera página

    c = 0

    for course in results:
        processed_course = {}
        for key, value in course.items():
            if key == 'visible_instructors':
                instructor_names = [instructor.get('title') for instructor in value if instructor.get('title')]
                processed_course['instructor(s)'] = ", ".join(instructor_names)
            elif key == 'url':
                processed_course[key] = f"www.udemy.com{value}"
            else:
                processed_course[key] = value
        all_courses_processed.append(processed_course)

    # Paginar a través de los resultados si hay una URL 'next'
    #for i in range(0,5):       
    while next_url:
        resp = requests.get(next_url, cookies=session_cookies)
        if resp.status_code == 200:
            c += 1
            logger.info(f"Página: {c}/{int(count/12)}")
            data = resp.json()
            results = data.get('results', [])
            for course in results:
                processed_course = {}
                for key, value in course.items():
                    if key == 'visible_instructors':
                        instructor_names = [instructor.get('title') for instructor in value if instructor.get('title')]
                        processed_course['instructor(s)'] = ", ".join(instructor_names)
                    elif key == 'url':
                        processed_course[key] = f"www.udemy.com{value}"
                    else:
                        processed_course[key] = value
                all_courses_processed.append(processed_course)
            next_url = data.get('next')
        else:
            print(f"Error al obtener la página: {next_url}, código de estado: {resp.status_code}")
            break # Detener la paginación en caso de error
    
    #print(json.dumps(all_courses_processed, indent=4, ensure_ascii= False))
    
else:
    print(f"Error al obtener la lista de cursos inicial: {response.status_code}")
    print(response.text)


#Guardar la lista de diccionarios en un DataFrame de pandas
if all_courses_processed:
    df = pd.DataFrame(all_courses_processed)

    # Guardar el DataFrame en un archivo Excel
    excel_filename = "cursos_udemy.xlsx"
    df.to_excel(excel_filename, index=False, sheet_name="Cursos")
    logger.info(f"Los cursos se han guardado en el archivo: {excel_filename}")
else:
    logger.info("No se encontraron cursos para guardar.")
