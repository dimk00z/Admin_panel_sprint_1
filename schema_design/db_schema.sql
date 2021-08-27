-- Don't forget to add a database: 
-- CREATE DATABASE online_movie_theater_db;

-- Create schema for current content
CREATE SCHEMA IF NOT EXISTS content;

-- Create tables
CREATE TABLE IF NOT EXISTS content.film_work
(
    id            uuid,
    title         character varying(250) NOT NULL,
    description   text,
    creation_date date,
    certificate   text,
    file_path     character varying(300),
    rating        numeric,
    type          character varying(30)  NOT NULL,
    created_at    timestamp with time zone,
    updated_at    timestamp with time zone,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS content.genre
(
    id          uuid,
    name        character varying(100) NOT NULL,
    description text,
    created_at  timestamp with time zone,
    updated_at  timestamp with time zone,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS content.person
(
    id         uuid,
    full_name  character varying(200) NOT NULL,
    birth_date date,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS content.genre_film_work
(
    id uuid,
    film_work_id uuid NOT NULL,
    genre_id uuid NOT NULL,
    created_at timestamp without time zone,
    PRIMARY KEY (id),
    UNIQUE (film_work_id, genre_id),
    CONSTRAINT "Filmwork" FOREIGN KEY (film_work_id)
        REFERENCES content.film_work (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT "Genre" FOREIGN KEY (genre_id)
        REFERENCES content.genre (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS content.person_film_work
(
    id uuid,
    role character varying(50),
    film_work_id uuid NOT NULL,
	person_id uuid NOT NULL,
    created_at timestamp with time zone,
    PRIMARY KEY (id),
    CONSTRAINT "Filmwork" FOREIGN KEY (film_work_id)
        REFERENCES content.film_work (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Create indexes
CREATE UNIQUE INDEX film_work_genre ON content.genre_film_work (film_work_id, genre_id);
CREATE UNIQUE INDEX film_work_person_role ON content.person_film_work (film_work_id, person_id, role);