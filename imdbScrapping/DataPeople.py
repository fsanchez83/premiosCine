'''
Created on 11 jan. 2025

@author: fsanchez
'''
# -*- coding: utf-8 -*-

import tmdbsimple as tmdb
import pandas as pd
import yaml
from yaml.loader import SafeLoader
import numpy as np
import ast
pd.set_option("display.max_columns", None)


with open('secrets.cfg') as f:
    data = yaml.load(f, Loader=SafeLoader)

tmdb.API_KEY = data['TMDB']['API_KEY']


def limpiar_lista(df):
    df_people = df[['PersonId','AssociatedIds']]

    # 1. Asegurarse de que los valores NaN o vacíos sean consistentes
    df['PersonId'] = df['PersonId'].fillna('').astype(str)

    # 2. Convertir cadenas a listas reales en AssociatedIds
    def parse_associated_ids(value):
        try:
            # Si el valor parece una lista en forma de cadena, evalúalo
            return ast.literal_eval(value) if isinstance(value, str) else []
        except (ValueError, SyntaxError):
            return []

    df['AssociatedIds'] = df['AssociatedIds'].apply(parse_associated_ids)

    # 3. Combinar ambas columnas en una sola lista
    all_codes = df['PersonId'].tolist() + [item for sublist in df['AssociatedIds'] for
                                           item in sublist]

    # 4. Limpiar la lista: eliminar valores vacíos y duplicados
    unique_codes = pd.Series(all_codes).replace('',
                                                np.nan).dropna().drop_duplicates().tolist()

    # Crear el DataFrame final con una sola columna
    result_df = pd.DataFrame({'imdb_id': unique_codes})

    return result_df


def obtener_tmdb_id(df):
    """
    Obtiene ID y tipo de medio de TMDB a partir de un DataFrame con IDs de IMDb.
    """
    resultados = []
    contador = 0
    for imdb_id in df['imdb_id']:
        print(contador)
        contador = contador + 1
        try:
            find = tmdb.Find(imdb_id)
            response = find.info(external_source='imdb_id')

            # Verifica si hay resultados en cualquiera de las categorías posibles
            if response.get('movie_results'):
                result = response['movie_results'][0]
                resultados.append(
                    {'imdb_id': imdb_id, 'tmdb_id': result['id'], 'tmdb_type': 'movie'})
            elif response.get('tv_results'):
                result = response['tv_results'][0]
                resultados.append(
                    {'imdb_id': imdb_id, 'tmdb_id': result['id'], 'tmdb_type': 'tv'})
            elif response.get('person_results'):
                result = response['person_results'][0]
                resultados.append(
                    {'imdb_id': imdb_id, 'tmdb_id': result['id'], 'tmdb_type': 'person'})
            else:
                # Si no se encuentra ningún resultado
                resultados.append(
                    {'imdb_id': imdb_id, 'tmdb_id': None, 'tmdb_type': None})
        except Exception as e:
            print(f"Error procesando el ID de IMDb {imdb_id}: {e}")
            resultados.append({'imdb_id': imdb_id, 'tmdb_id': None, 'tmdb_type': None})

    # Convierte la lista de resultados en un DataFrame
    return pd.DataFrame(resultados).dropna()


def enriquece_datos(tmdbmovielist):

    atributos_persona = ['tmdb_id', 'tmdb_type', 'imdb_id', 'Name', 'Gender', 'Birthday',
                         'Deathday', 'AKA', 'Department',
                      'Place_birth', 'Popularity', 'Biography']
    df_people = pd.DataFrame(columns=atributos_persona)
    errores = []

    for index, row in tmdbmovielist.iterrows():
        print(index)
        tmdb_id = row['tmdb_id']
        tmdb_type = row['tmdb_type']
        imdb_id = row['imdb_id']
        try:
            if tmdb_type == 'person':

                person = tmdb.People(tmdb_id)
                person_info = person.info()
                name = person_info['name']
                gender = person_info['gender']
                birthday = person_info['birthday']
                deathday = person_info['deathday']
                aka = person_info['also_known_as']
                department = person_info['known_for_department']
                place_birth = person_info['place_of_birth']
                popularity = person_info['popularity']
                biography = person_info['biography'].replace('\n', ' ').replace('\r', ' ')

                lista_persona = [tmdb_id, tmdb_type, imdb_id, name, gender, birthday,
                                 deathday, aka, department, place_birth, popularity,
                                 biography]

            else:
                lista_persona = []

            tamanio_df = len(df_people)
            df_people.loc[tamanio_df] = lista_persona

        except Exception as e:
            print("Error en el procesado de: ", row['imdb_id'])
            errores.append(row['imdb_id'])
            print(e)

    return df_people


inputFile = 'Datasets/Pruebas/Goya_awards.csv'
nombreDataset = 'Goya_People'
file_name = "Datasets/Pruebas/" + nombreDataset + '.csv'
file_name_esp = "Datasets/Pruebas/" + nombreDataset + '_esp.csv'

df_complete_list = pd.read_csv(inputFile)
# Para hacer una prueba solo con las 20 primeras personas
# df_complete_list = df_complete_list.loc[:3,:]
peoplelist = limpiar_lista(df_complete_list)
print(peoplelist)
tmdbpeopleList = obtener_tmdb_id(peoplelist)
DataPeopleList = enriquece_datos(tmdbpeopleList)
DataPeopleList.to_csv(file_name_esp, index=False,  encoding='utf-8-sig', sep=';')
DataPeopleList.to_csv(file_name, encoding='utf-8-sig', index=False)
