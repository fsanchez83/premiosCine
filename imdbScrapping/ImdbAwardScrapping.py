'''
Created on 10 jan. 2025

@author: fsanchez
'''
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import sys


def scrape_imdb_awards(base_url, years):
    data = []  # Lista para guardar la información

    for year in years:
        print(f"Scraping year: {year}")
        url = f"{base_url}/{year}"  # URL para cada año
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 "
                          "Safari/537.36"
        }
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to fetch {url}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')

        # Encontrar todas las secciones de categorías
        categories = soup.find_all('section', {'data-testid': lambda x: x and 'Best' in
                                                                        x})
        for category in categories:
            # Extraer el nombre de la categoría
            category_name = category['data-testid']
            # Nominados
            nominees_set = category.find_all('li', class_='ipc-metadata-list__item')
            ganador = True
            for nominees_set in nominees_set:
                if ganador is True:
                    status = 'Winner'
                    ganador = False
                else:
                    status = 'Nominee'

                nominees = nominees_set.find_all('div', class_='ipc-title')
                if len(nominees) > 0:  # Premios a películas
                    AssociatedPeople = []
                    AssociatedIds = []

                    # Extraer personas asociadas a la pelicula
                    associatedPerson = nominees_set.find_all('a', class_='ipc-link')
                    for asocPerson in associatedPerson:
                        AsPerson_name = asocPerson.text.strip()
                        person_link_id = asocPerson['href']
                        person_link = re.search(r"(nm[0-9]+)", person_link_id)
                        if person_link:
                            AsPerson_id = person_link.group(1)
                        else:
                            AsPerson_id = ""
                        AssociatedPeople.append(AsPerson_name)
                        AssociatedIds.append(AsPerson_id)

                    # Extraer peliculas nominadas
                    for nominee in nominees:
                        nominee_title = nominee.h3.text.strip()
                        nominee_link = nominee.a['href']
                        movie_link = re.search(r"(tt[0-9]+)", nominee_link)
                        if movie_link:
                            movie_id = movie_link.group(1)
                        else:
                            movie_id = ""

                        data.append({
                            'Year': year,
                            'Category': category_name,
                            'Status': status,
                            'Movie': nominee_title,
                            'MovieId': movie_id,
                            'AssociatedPeople': AssociatedPeople,
                            'AssociatedIds': AssociatedIds
                        })
                else:  # Premios a personas
                    # Buscar candidatos nominados si no hay películas
                    candidate_sections = nominees_set.find_all('div',
                                                               class_='ipc-metadata-list-item__content-container')
                    for candidate_section in candidate_sections:

                        # Extraer persona nominada
                        person = candidate_section.find('a', class_='ipc-link')
                        if person:
                            person_name = person.text.strip()
                            person_link_id = person['href']
                            person_link = re.search(r"(nm[0-9]+)", person_link_id)
                            if person_link:
                                person_id = person_link.group(1)
                            else:
                                person_id = ""

                            # Extraer película asociada
                            movie = person.find_next('a', class_='ipc-link')
                            if movie:
                                movie_title = movie.text.strip()
                                movie_link_id = movie['href']
                                movie_link = re.search(r"(tt[0-9]+)", movie_link_id)
                                if movie_link:
                                    movie_id = movie_link.group(1)
                                else:
                                    movie_id = ""

                                data.append({
                                    'Year': year,
                                    'Category': category_name,
                                    'Status': status,
                                    'Person': person_name,
                                    'PersonId': person_id,
                                    'Movie': movie_title,
                                    'MovieId': movie_id
                                })

        honorificos = soup.find_all('section', {'class': 'ipc-page-section '
                                                         'ipc-page-section--base',
                                                'data-testid': lambda x: x is None})

        try:
            for secciones in honorificos:
                ganadores = secciones.get_text().count('Winner')
                people = secciones.find_all('a', class_='ipc-link')[0:ganadores]
                peliculas = secciones.find_all('li', class_='ipc-metadata-list__item')[
                            0:ganadores]
                if len(people) > 0:
                    for person in people:
                        person_name = person.text.strip()
                        person_link_id = person['href']
                        person_link = re.search(r"(nm[0-9]+)", person_link_id)
                        if person_link:
                            person_id = person_link.group(1)
                        else:
                            person_id = ""
                        data.append({
                            'Year': year,
                            'Category': 'Honorary(Honorifico)',
                            'Status': 'Winner',
                            'Person': person_name,
                            'PersonId': person_id
                        })
                else:
                    for ganadoras in peliculas:
                        ganadoras_name = ganadoras.h3.text.strip()
                        label_ganadoras = ganadoras.find('a')
                        ganadoras_link = re.search(r"(tt[0-9]+)", label_ganadoras.get('href'))
                        if ganadoras_link:
                            ganadora_id = ganadoras_link.group(1)
                        else:
                            ganadora_id = ""
                        data.append({
                            'Year': year,
                            'Category': 'Especiales',
                            'Status': 'Winner',
                            'Movie': ganadoras_name,
                            'MovieId': ganadora_id
                        })
        except Exception as e:
            print('Error en honorificos o especiales')

    # Crear el DataFrame con los resultados
    df = pd.DataFrame(data)
    return df


# Configuración de parámetros
# Ejemplo: Oscar: ev0000003
# Goya: ev0000299
name_awards = 'Goya'
imdb_awards_code = 'ev0000299'
base_url = "https://www.imdb.com/event/" + imdb_awards_code
years = range(2022, 2023)  # Rango de años que deseas scrapear (último no inclusive)

df_awards = scrape_imdb_awards(base_url, years)
file_name = "Datasets/Pruebas/" + name_awards + '_awards.csv'
file_name_esp = "Datasets/Pruebas/" + name_awards + '_awards_esp.csv'

# Guardar en un CSV
df_awards.to_csv(file_name_esp, index=False, encoding='utf-8-sig', sep=';')
df_awards.to_csv(file_name, encoding='utf-8-sig', index=False)
print("Datos guardados en ", file_name)
