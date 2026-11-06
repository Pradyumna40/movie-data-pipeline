-- 1. HIGHEST MOVIE AVERAGE RATING

select m.title , avg(r.rating) as avg_rating
from movies m 
join ratings r
on m.movie_id = r.movie_id
group by m.movie_id , m.title
order by avg_rating desc
limit 1; 


-- 2. TOP 5 MOVIE GENRES WITH HIGHEST AVERAGE RATING

select g.genre_name , avg(r.rating) as avg_rating
from genres g
join movie_genres mg
on g.genre_id = mg.genre_id
join ratings r
on mg.movie_id = r.movie_id
group by g.genre_name
order by avg_rating desc
limit 5;


-- 3. Who is the director with most movies in the dataset?

select director , count(*) as total_movies
from movies
where director is not null
group by director
order by total_movies desc
limit 1;


--4. what is the average ratings of the movies released each year


select m.release_year , avg(r.rating) as avg_rating
from movies m
join ratings r 
on m.movie_id = r.movie_id
where release_year is not null
group by m.release_year
order by m.release_year;




