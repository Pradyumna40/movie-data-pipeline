create database if not exists movie_analytics;


use movie_analytics;


-- 1. Movies table

CREATE TABLE IF NOT EXISTS movies (
    movie_id INT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    release_year SMALLINT,
    director VARCHAR(255),
    plot TEXT,
    box_office VARCHAR(50)
)ENGINE=InnoDB;


-- 2.Genres Table
CREATE TABLE IF NOT EXISTS genres (
    genre_id INT AUTO_INCREMENT PRIMARY KEY,
    genre_name = VARCHAR(100) NOT NULL UNION

)ENGINE=InnoDB;


-- 3. Movie genres table

CREATE TABLE IF NOT EXISTS movie_genres (
    movie_id INT NOT NULL,
    genre_id INT NOT NULL,


    PRIMARY KEY(movie_id , genre_id),
    FOREIGN KEY(movie_id)
        REFERENCES movies(movie_id),
    FOREIGN KEY(genre_id)
        REFERENCES genres(genre_id)
)ENGINE=InnoDB;


-- 4.Ratings table
CREATE TABLE IF not EXISTS ratings (
    user_id INT NOT NULL,
    movie_id INT NOT NULL,
    rating DECIMAL(2,1) NOT NULL,
    rated_at DATETIME NOT NULL,

    PRIMARY KEY(user_id , movie_id),

    FOREIGN KEY(movie_id)
        REFERENCES movies(movie_id)

    CHECK (rating >= 0.5 AND rating <= 5.0)
)ENGINE=InnoDB;