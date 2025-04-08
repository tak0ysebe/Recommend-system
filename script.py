import streamlit as st
import pandas as pd
import pickle
import requests
import ast

# Загрузка данных
with open("movies_metadata.pkl", "rb") as f:
    merged_df = pickle.load(f)

with open("cosine_sim.pkl", "rb") as f:
    cosine_sim = pickle.load(f)

# Создание индексов
indices = pd.Series(merged_df.index, index=merged_df['title']).drop_duplicates()


# Функция для получения постера фильма через OMDB API
def get_movie_poster(title):
    api_key = "2bc61912"  # Твой API-ключ
    url = f"http://www.omdbapi.com/?t={title}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    return data.get('Poster', 'https://via.placeholder.com/300x450?text=No+Image')


# Функция для получения актёров фильма
def get_actors(title):
    api_key = "2bc61912"  # Твой API-ключ
    url = f"http://www.omdbapi.com/?t={title}&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    return data.get('Actors', 'Информация не доступна')


# Функция для преобразования строки в список (если это строковое представление списка)
def parse_list_from_string(data_str):
    try:
        return ast.literal_eval(data_str)
    except:
        return []


# Функция для обработки вложенных данных
def parse_genres(genres_data):
    if isinstance(genres_data, str):
        genres_data = parse_list_from_string(genres_data)
    return ', '.join([genre['name'] for genre in genres_data]) if genres_data else "Неизвестно"


def parse_production_countries(countries_data):
    if isinstance(countries_data, str):
        countries_data = parse_list_from_string(countries_data)
    return ', '.join([country['name'] for country in countries_data]) if countries_data else "Неизвестно"


# Функция для получения информации о фильме
def get_similar_movies(title, num_movies=5):
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:num_movies + 1]
    movie_indices = [i[0] for i in sim_scores]
    return merged_df.iloc[movie_indices][
        ['title', 'mean_rating', 'num_votes', 'metadata', 'budget', 'genres', 'production_countries', 'release_date',
         'runtime', 'genre_names']]


# Сохранение истории выбора
if 'history' not in st.session_state:
    st.session_state.history = []

# Интерфейс
st.title("🎬 Рекомендательная система фильмов")

# Ввод строки поиска с динамическим фильтром
search_input = st.text_input("Введите часть названия фильма:")

# Если что-то введено, фильтруем список фильмов
if search_input:
    matched_titles = merged_df[merged_df['title'].str.contains(search_input, case=False, na=False)]['title'].tolist()
else:
    matched_titles = []

# Динамический выбор из списка
if matched_titles:
    selected_movie = st.selectbox("Выберите фильм из списка:", matched_titles)

    # Отображаем постер выбранного фильма
    poster_url = get_movie_poster(selected_movie)
    st.image(poster_url, width=200)

    # Добавляем опцию для выбора количества рекомендаций
    num_recommendations = st.slider("Выберите количество рекомендаций:", min_value=1, max_value=20, value=5)

    # Показываем рекомендации после выбора
    if st.button("Показать рекомендации"):
        recommendations = get_similar_movies(selected_movie, num_movies=num_recommendations)
        st.subheader("📌 Рекомендованные фильмы:")

        # Выводим рекомендации по одному фильму
        for index, movie in recommendations.iterrows():
            st.markdown(f"### {movie['title']}")
            st.image(get_movie_poster(movie['title']), width=200)

            # Выводим нужную информацию с корректной обработкой
            st.write(f"**Бюджет**: ${movie['budget']:,}")
            st.write(f"**Жанры**: {parse_genres(movie['genres'])}")
            st.write(f"**Страны производства**: {parse_production_countries(movie['production_countries'])}")
            st.write(f"**Дата выпуска**: {movie['release_date']}")
            st.write(f"**Длительность**: {movie['runtime']} минут")

            # Получаем актёров фильма
            actors = get_actors(movie['title'])
            st.write(f"**Актёры**: {actors}")

            st.write("---")

        # Сохраняем фильм в истории
        st.session_state.history.append(selected_movie)

    # История выбора
    st.subheader("📝 История ваших выборов:")
    if st.session_state.history:
        for movie in st.session_state.history:
            st.write(f"- {movie}")
else:
    st.info("Введите название фильма для поиска.")
