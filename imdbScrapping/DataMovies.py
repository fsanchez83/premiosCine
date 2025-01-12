'''
Created on 11 jan. 2025

@author: fsanchez
'''
# -*- coding: utf-8 -*-

import tmdbsimple as tmdb
import pandas as pd
import yaml
from yaml.loader import SafeLoader
pd.set_option("display.max_columns", None)


with open('secrets.cfg') as f:
    data = yaml.load(f, Loader=SafeLoader)

tmdb.API_KEY = data['TMDB']['API_KEY']


def limpiar_lista(df):
    df_films = df['MovieId']
    movielist = df_films.drop_duplicates().reset_index(drop=True)
    return movielist


def obtener_tmdb_id(df):
    """
    Obtiene ID y tipo de medio de TMDB a partir de un DataFrame con IDs de IMDb.
    """
    resultados = []
    contador = 0
    for imdb_id in df:
        contador = contador + 1
        print(contador)
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

    atributos_peli = ["Id_peli", "Tipo", "imdb_id", "Titulo", "Titulo original",
                      "Popularidad", 'Rating',
                      'Fecha', 'Duracion', 'Paises', 'Idioma', 'productoras_id',
                      'productoras_nombre', 'productoras_pais',
                      'Presupuesto', 'Ganancia', 'Generos', 'Director', 'Genero_dir',
                      'Casting', 'Genero_cast', 'Guion', 'Genero_guion', 'Montaje',
                      'Genero_montaje', 'DOP', 'Genero_dop', 'Resumen']
    df_films = pd.DataFrame(columns=atributos_peli)
    errores = []

    for index, row in tmdbmovielist.iterrows():
        print(index)
        tmdb_type = row['tmdb_type']
        tmdb_id = row['tmdb_id']
        imdb_id = row['imdb_id']
        try:
            if tmdb_type == 'movie':
                movie = tmdb.Movies(tmdb_id)
                movieInfo = movie.info()
                id_peli = tmdb_id
                titulo = movieInfo['title']
                popularidad = movieInfo['popularity']
                rating = movieInfo['vote_average']
                fecha = movieInfo['release_date']
                duracion = movieInfo['runtime']
                idioma = movieInfo['original_language']
                titulo_original = movieInfo['original_title']
                paises = movieInfo['origin_country']
                productoras = movieInfo['production_companies']
                productoras_id = []
                productoras_nombre = []
                productoras_pais = []
                for empresas in productoras:
                    productoras_id.append(empresas['id'])
                    productoras_nombre.append(empresas['name'])
                    productoras_pais.append(empresas['origin_country'])

                presupuesto = movieInfo['budget']
                ganancia = movieInfo['revenue']

                resumen = movieInfo['overview'].replace('\n', ' ').replace('\r', ' ')
                generos = []
                for dic in movieInfo['genres']:
                    generos.append(dic['name'])

                director = []
                director_genre = []
                guion = []
                guion_genre = []
                montaje = []
                montaje_genre = []
                dop = []
                dop_genre = []
                casting = []
                casting_genre = []

                creditos = movie.credits()
                for dic in creditos['crew']:
                    if dic['job'] == 'Director':
                        director.append(dic['name'])
                        director_genre.append(dic['gender'])
                    if dic['job'] == 'Screenplay':
                        guion.append(dic['name'])
                        guion_genre.append(dic['gender'])
                    if dic['job'] == 'Editor':
                        montaje.append(dic['name'])
                        montaje_genre.append(dic['gender'])
                    if dic['job'] == 'Director of Photography':
                        dop.append(dic['name'])
                        dop_genre.append(dic['gender'])

                for dic in creditos['cast']:
                    casting.append(dic['name'])
                    casting_genre.append(dic['gender'])

                lista_peli = [id_peli, row['tmdb_type'], imdb_id, titulo, titulo_original,
                              popularidad, rating,
                              fecha, duracion, paises, idioma, productoras_id,
                              productoras_nombre, productoras_pais,
                              presupuesto, ganancia, generos, director, director_genre,
                              casting, casting_genre, guion, guion_genre, montaje,
                              montaje_genre, dop, dop_genre, resumen]

            if tmdb_type == 'tv':
                movie = tmdb.TV(tmdb_id)
                movieInfo = movie.info()
                id_peli = tmdb_id
                titulo = movieInfo['name']
                titulo_original = movieInfo['original_name']
                popularidad = movieInfo['popularity']
                rating = movieInfo['vote_average']
                fecha = movieInfo['first_air_date']
                try:
                    duracion = movieInfo['number_of_episodes'] * \
                               movieInfo['episode_run_time'][0]
                except IndexError:
                    duracion = ''
                paises = movieInfo['origin_country']
                idioma = movieInfo['original_language']
                presupuesto = ''
                ganancia = ''
                resumen = movieInfo['overview'].replace('\n', ' ').replace('\r', ' ')
                generos = []
                for dic in movieInfo['genres']:
                    generos.append(dic['name'])

                productoras = movieInfo['production_companies']
                productoras_id = []
                productoras_nombre = []
                productoras_pais = []
                for empresas in productoras:
                    productoras_id.append(empresas['id'])
                    productoras_nombre.append(empresas['name'])
                    productoras_pais.append(empresas['origin_country'])

                director = []
                director_genre = []
                guion = []
                guion_genre = []
                montaje = []
                montaje_genre = []
                dop = []
                dop_genre = []
                casting = []
                casting_genre = []

                creditos = movie.credits()
                for dic in creditos['crew']:
                    if dic['job'] == 'Director':
                        director.append(dic['name'])
                        director_genre.append(dic['gender'])
                    if dic['job'] == 'Screenplay':
                        guion.append(dic['name'])
                        guion_genre.append(dic['gender'])
                    if dic['job'] == 'Editor':
                        montaje.append(dic['name'])
                        montaje_genre.append(dic['gender'])
                    if dic['job'] == 'Director of Photography':
                        dop.append(dic['name'])
                        dop_genre.append(dic['gender'])

                for creadores in movieInfo['created_by']:
                    try:
                        director.append(creadores['name'])
                        director_genre.append(creadores['gender'])
                    except IndexError:
                        director = []

                for dic in creditos['cast']:
                    casting.append(dic['name'])
                    casting_genre.append(dic['gender'])

                lista_peli = [id_peli, row['tmdb_type'], imdb_id, titulo, titulo_original,
                              popularidad, rating,
                              fecha, duracion, paises, idioma, productoras_id,
                              productoras_nombre, productoras_pais,
                              presupuesto, ganancia, generos, director, director_genre,
                              casting, casting_genre, guion, guion_genre, montaje,
                              montaje_genre, dop, dop_genre, resumen]

            tamanio_df = len(df_films)
            df_films.loc[tamanio_df] = lista_peli

        except Exception as e:
            print("Error en el procesado de: ", row['imdb_id'])
            errores.append(row['imdb_id'])
            print(e)

    return df_films


inputFile = 'Datasets/Pruebas/Goya_awards.csv'
nombreDataset = 'Goya_movies'
file_name = "Datasets/Pruebas/" + nombreDataset + '.csv'
file_name_esp = "Datasets/Pruebas/" + nombreDataset + '_esp.csv'

df_complete_list = pd.read_csv(inputFile)
# Para hacer una prueba solo con las 3 primeras peliculas
# df_complete_list = df_complete_list.loc[:2,:]
movieList = limpiar_lista(df_complete_list)
print(movieList)
TMDBMovieList = obtener_tmdb_id(movieList)
DataMovieList = enriquece_datos(TMDBMovieList)
print(DataMovieList)
DataMovieList.to_csv(file_name_esp, index=False,  encoding='utf-8-sig', sep=';')
DataMovieList.to_csv(file_name, encoding='utf-8-sig', index=False)
