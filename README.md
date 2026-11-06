
# Movie Data Pipeline


## 1.Project Overview

This project builds a simple ETL (Extract, Transform, Load) pipeline using Python, Pandas, MySQL, and the OMDb API.

The pipeline extracts movie and rating data from the MovieLens dataset, transforms and cleans the data, enriches movie information using the OMDb API, and loads the processed data into a MySQL database.

## 2.Technologies Used

* Python 
* Pandas
* SqlAlchemy
* MySQL
*OMDb API


## 3.Dataset

Source: https://files.grouplens.org/datasets/movielens/ml-latest-small.zip


The dataset contains:

* 9,742 movies
* 100,835 ratings

## 4. ETL Pipeline

### Extract
 
* Read movies.csv and ratings.csv using Pandas.


### Transform

* Extract release years from movie title.
* Separate movie genres.
* Convert Unix timestamps into datetime values.
* Clean movie titles.


### Enrich

* Fetch additional movie information using the OMDb API.
* Retrieve director , plot and box office information.
* Cache API responseds to avoid unnecessary requests.
* Track daily API usage. 

### Load
* Load processed data into MySQL.
* Store movies , genres , movie-genre relationships , and ratings in separate tables.


## 5.Database Design

The database contains fout tables:

| Tables | Purpose |
|:-------:|:-------:|
|movies|Stores movie details|
|genres|Stores unique genres|
|movie_genres|Maps movies to genres|
|ratings|Stores user ratings|


The movie_gernes table handles the many-to-many relationship between movies and genres.

## 6. SQL Analysis

The project includes SQL queries to answer:

1. Which movie has the highest average rating?
2. What are the top five genres by average rating?
3. Which director has director has directed most movies?
4. What is the average rating of movies released each year?

See **queries.sql** for the SQL queries.

## 7 . Design Choices and assumptions

* Relational database: MySQL was used to store structured movie and rating data.
* Normalization: Genres are stored separately to avoid repeating genre names for every movie.
* API caching: API responses are stored locally in JSON so that previously fetched movie details do not need to be requested again.
* API usage limit: A daily application-level limit of 900 new requests is used as a safety buffer for the free API plan.


## 8. Project Results

Successfully loaded the following record into MySQL:

|Table|Records|
|:----|:----|
|Movies|9,742|
|Ratings|100,836|
|Genres|20|
|Movie Genres|22,084|

## 9. Project Structure

```text
movie-data-pipeline/
├── data/
│   ├── raw/          
│   ├── movies.csv      
│   ├── ratings.csv          
│   ├── omdb_cache.json
|   └── omdb_usage.json         
├── etl.py           
├── schema.sql
├── queries.sql
├── requirements.txt
├── README.md 
└── .gitigonre
```


## 10. How to Run the project

### Step 1 : Clone the project

```bash
  git clone https://github.com/Pradyumna40/movie-data-pipeline
```

### Step 2 : Go the the project directory

```bash
  cd my-project
```

### Step 3 : Install dependencies

```bash
  pip install -r requirements.txt
```

### Step 4 : Configure environment variables
Create a .env file in the project root:
```bash
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=movie_analytics
OMDB_API_KEY=your_omdb_api_key
```

### Step 5 : Create the database
Run schemas.sql in MySQL to create the database and tables.


### Step 6 : Run the ETL Pipeline

```bash
python etl.py
```

### Step 6 : Execute the SQL queries
```bash
mysql -u root -p --table movie_analytics < queries.sql
```
## 11. Challenges faced and solutions

# 1. OMDb API request limits

Fetching movie details for thousands of movies can consume the available daily API requests.

Solution: Implemented JSON-based caching and daily API usage tracking to avoid repeated requests 


# 2. Repeated API requests

Running the ETL pipeline multiple times could result in unnecessary API calls for movies whose details had already been fetched.

Solution: Checked the cache before making an API request. Previously fetched results are reused.


## 12. Future Imporvements

* Add automated ETL scheduling.
* Implement better logging and error handling.
* Add data validation checks.




## 13. Authors

- Pradyumna P Arakeri [@Pradyumna40](https://github.com/Pradyumna40)

