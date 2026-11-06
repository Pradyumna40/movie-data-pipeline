
from pathlib import Path
import pandas as pd
import os
import requests
from dotenv import load_dotenv
import time
import json
from sqlalchemy import create_engine, URL
from datetime import date


# ---------------- CONFIGURATION ----------------

load_dotenv()

# Project directory
BASE_DIR = Path(__file__).resolve().parent

# File paths
DATA_DIR = BASE_DIR / "data"

MOVIES_FILE = DATA_DIR / "raw" / "movies.csv"
RATINGS_FILE = DATA_DIR / "raw" / "ratings.csv"

CACHE_FILE = DATA_DIR / "omdb_cache.json"
USAGE_FILE = DATA_DIR / "omdb_usage.json"

API_KEY = os.getenv("OMDB_API_KEY")

# MySQL connection
db_url = URL.create(
    drivername="mysql+pymysql",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 3306)),
    database=os.getenv("DB_NAME")
)

engine = create_engine(db_url)

DAILY_LIMIT = 900


# ---------------- EXTRACT ----------------

def extract_data():

    # Read CSV files
    movies = pd.read_csv(MOVIES_FILE)
    ratings = pd.read_csv(RATINGS_FILE)

    print("Movies extracted:", movies.shape)
    print("Ratings extracted:", ratings.shape)

    return movies, ratings


# ---------------- TRANSFORM ----------------

def transform_movies(movies):

    # Extract release year from movie title
    movies["release_year"] = movies["title"].str[-5:-1]

    # Convert year into numeric format
    movies["release_year"] = pd.to_numeric(
        movies["release_year"],
        errors="coerce"
    ).astype("Int64")

    print("Release years extracted")

    return movies


def clean_movie_titles(movies):

    # Create a separate column for cleaned titles
    movies["clean_title"] = movies["title"]

    # Remove the last 7 characters containing the year
    movies.loc[
        movies["release_year"].notna(),
        "clean_title"
    ] = movies["title"].str[:-7]

    print("Movie titles cleaned")

    return movies


def transform_genres(movies):

    # Split genres into individual items
    movies["genres"] = movies["genres"].str.split("|")

    print("Genres transformed")

    return movies


def transform_ratings(ratings):

    # Convert Unix timestamp into datetime
    ratings["rated_at"] = pd.to_datetime(
        ratings["timestamp"],
        unit="s"
    )

    print("Ratings transformed")

    return ratings


# ---------------- JSON CACHE AND USAGE ----------------

def load_json(file_path):

    # Load existing JSON data if the file exists
    if file_path.exists():

        with open(file_path, "r") as file:
            return json.load(file)

    return {}


def save_json(file_path, data):

    # Save data into JSON file
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


def load_cache():

    return load_json(CACHE_FILE)


def save_cache(cache):

    save_json(CACHE_FILE, cache)


def load_usage():

    data = load_json(USAGE_FILE)

    # Check whether the saved usage belongs to today
    if data.get("date") == str(date.today()):
        return data.get("requests", 0)

    # Reset request count for a new day
    return 0


def save_usage(requests_used):

    data = {
        "date": str(date.today()),
        "requests": requests_used
    }

    save_json(USAGE_FILE, data)


# ---------------- OMDB API ----------------

def get_omdb_details(title, year, cache):

    key = str(title) + "-" + str(year)

    # Check whether movie details are already saved
    if key in cache:

        print("Using cached data:", title)
        return cache[key]

    url = "https://www.omdbapi.com/"

    params = {
        "apikey": API_KEY,
        "t": title
    }

    # Add release year if available
    if pd.notna(year):
        params["y"] = int(year)

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        # Check whether movie details were found
        if data.get("Response") == "True":

            result = {
                "director": data.get("Director"),
                "plot": data.get("Plot"),
                "box_office": data.get("BoxOffice")
            }

        else:

            result = {
                "director": None,
                "plot": None,
                "box_office": None
            }

        # Save API result in cache
        cache[key] = result
        save_cache(cache)

        return result

    except requests.exceptions.RequestException as error:

        print("API error:", error)

        return {
            "director": None,
            "plot": None,
            "box_office": None
        }


def enrich_movies(movies):

    cache = load_cache()
    requests_used = load_usage()

    directors = []
    plots = []
    box_offices = []

    # Go through each movie
    for _, movie in movies.iterrows():

        title = movie["clean_title"]
        year = movie["release_year"]

        key = str(title) + "-" + str(year)

        # Use cached details if available
        if key in cache:

            details = cache[key]

        # Call API only if daily limit is not reached
        elif requests_used < DAILY_LIMIT:

            details = get_omdb_details(
                title,
                year,
                cache
            )

            requests_used += 1
            save_usage(requests_used)

            # Avoid sending requests too frequently
            time.sleep(1)

        else:

            details = {
                "director": None,
                "plot": None,
                "box_office": None
            }

        # Store API results in separate lists
        directors.append(details["director"])
        plots.append(details["plot"])
        box_offices.append(details["box_office"])

    # Add API details to movies dataframe
    movies["director"] = directors
    movies["plot"] = plots
    movies["box_office"] = box_offices

    return movies


# ---------------- LOAD INTO MYSQL ----------------

def load_movies(movies):

    # Select required columns
    movies_to_load = movies[[
        "movieId",
        "title",
        "release_year",
        "director",
        "plot",
        "box_office"
    ]].copy()

    # Rename column to match MySQL table
    movies_to_load = movies_to_load.rename(
        columns={"movieId": "movie_id"}
    )

    # Insert movies into MySQL
    movies_to_load.to_sql(
        name="movies",
        con=engine,
        if_exists="append",
        index=False
    )

    print("Movies inserted successfully")


def load_genres(movies):

    # Separate all genres into individual rows
    genre_data = movies["genres"].explode()

    # Remove duplicate genres
    genre_data = genre_data.dropna().drop_duplicates()

    # Convert into dataframe
    genre_df = pd.DataFrame({
        "genre_name": genre_data
    })

    # Insert genres into MySQL
    genre_df.to_sql(
        name="genres",
        con=engine,
        if_exists="append",
        index=False
    )

    print("Genres inserted successfully")


def load_movie_genres(movies):

    # Get genre IDs from MySQL
    genre_df = pd.read_sql(
        "SELECT genre_id, genre_name FROM genres",
        con=engine
    )

    # Create dictionary to find genre IDs
    genre_map = dict(zip(
        genre_df["genre_name"],
        genre_df["genre_id"]
    ))

    movie_genre_data = []

    # Go through each movie
    for _, movie in movies.iterrows():

        # Go through each genre of that movie
        for genre in movie["genres"]:

            movie_genre_data.append({
                "movie_id": movie["movieId"],
                "genre_id": genre_map[genre]
            })

    # Convert into dataframe
    movie_genre_df = pd.DataFrame(movie_genre_data)

    # Insert movie-genre relationships into MySQL
    movie_genre_df.to_sql(
        name="movie_genres",
        con=engine,
        if_exists="append",
        index=False
    )

    print("Movie genres inserted successfully")


def load_ratings(ratings, movies):

    # Keep ratings only for movies in our movies dataframe
    ratings = ratings[
        ratings["movieId"].isin(movies["movieId"])
    ].copy()

    # Select required columns
    ratings_to_load = ratings[[
        "userId",
        "movieId",
        "rating",
        "rated_at"
    ]].copy()

    # Rename columns to match MySQL table
    ratings_to_load = ratings_to_load.rename(columns={
        "userId": "user_id",
        "movieId": "movie_id"
    })

    # Insert ratings into MySQL
    ratings_to_load.to_sql(
        name="ratings",
        con=engine,
        if_exists="append",
        index=False
    )

    print("Ratings inserted successfully")
    print("Total ratings:", len(ratings_to_load))


# ---------------- MAIN PIPELINE ----------------

if __name__ == "__main__":

    print("\nStarting ETL...\n")

    # EXTRACT
    movies, ratings = extract_data()

    # TRANSFORM
    print("\nTransforming movies...")

    movies = transform_movies(movies)
    movies = clean_movie_titles(movies)
    movies = transform_genres(movies)

    print("\nTransforming ratings...")

    ratings = transform_ratings(ratings)

    # ENRICH
    print("\nStarting OMDb enrichment...")

    movies = enrich_movies(movies)

    # LOAD
    print("\nLoading movies...")

    load_movies(movies)

    print("\nLoading genres...")

    load_genres(movies)

    print("\nLoading movie genres...")

    load_movie_genres(movies)

    print("\nLoading ratings...")

    load_ratings(ratings, movies)

  
   

    print("\nETL completed successfully!")
