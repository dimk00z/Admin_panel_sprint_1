-- Don't forget to add a database: 
-- CREATE DATABASE online_movie_theater_db;

-- Create schema for current content
CREATE SCHEMA IF NOT EXISTS content;
CREATE TABLE IF NOT EXISTS content.movies
(
    id uuid,
    genre character varying(50),
    director character varying(100) NOT NULL,
    writer character varying(100) NOT NULL,
    title character varying(250)  NOT NULL,
    plot text,
    imdb_rating numeric,
    writers text,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS content.writers
(
    id uuid,
    name character varying(100) NOT NULL,
    PRIMARY KEY (id)
);


CREATE TABLE IF NOT EXISTS content.rating_agency
(
    id uuid,
    name character varying(150) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS content.actors
(
    id uuid,
    name character varying(150) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS content.movie_actors
(
    movie_id uuid NOT NULL,
    actor_id uuid NOT NULL,
    CONSTRAINT "PK" PRIMARY KEY (movie_id, actor_id),
    CONSTRAINT movie_id FOREIGN KEY (movie_id)
        REFERENCES content.movies (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT actor_id FOREIGN KEY (actor_id)
        REFERENCES content.actors (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
);


-- TODO Remove sqlite code

-- from sql lite
-- CREATE TABLE movies (
--     -- id text primary key,
--     -- genre text,
--     -- director text,
--     -- writer text,
--     -- title text,
--     -- plot text,
--     -- ratings text,
--     -- imdb_rating text, 
--     writers text
-- );

-- CREATE TABLE writers(
--     id uuid PRIMARY KEY,
--     name text
-- );

-- CREATE TABLE rating_agency(
--     id uuid PRIMARY KEY,
--     name text
-- );

-- CREATE TABLE actors(
--     id uuid PRIMARY KEY,
--     name text
-- );
