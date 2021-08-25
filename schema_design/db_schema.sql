-- Don't forget to add a database: 
-- CREATE DATABASE online_movie_theater_db;

-- Create schema for current content
CREATE SCHEMA IF NOT EXISTS content;

-- Create films table
CREATE TABLE IF NOT EXISTS content.film_work
(
    id uuid,
    title character varying(250) NOT NULL,
    description text,
    creation_date date,
    certificate text,
    file_path character varying(300),
    rating numeric,
    type character varying(30) NOT NULL,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    PRIMARY KEY (id)
);

-- Create genres table
CREATE TABLE IF NOT EXISTS content.genre
(
    id uuid,
    name character varying(100) NOT NULL,
    description text,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    PRIMARY KEY (id)
);
-- Create table for actors
CREATE TABLE IF NOT EXISTS content.person
(
    id uuid,
    full_name character varying(200) NOT NULL,
    birth_date date,
    created_at timestamp with time zone,
    updated_at timestamp with time zone,
    PRIMARY KEY (id)
);
-- Create table for many-to-many relatiomship for films and genres
CREATE TABLE IF NOT EXISTS content.genre_film_work
(
    id uuid,
    film_work_id uuid NOT NULL,
    genre_id uuid NOT NULL,
    created_at timestamp with time zone,
    PRIMARY KEY (id),
    UNIQUE (film_work_id, genre_id),
    CONSTRAINT film_work_id FOREIGN KEY (film_work_id)
        REFERENCES content.film_work (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT genre_id FOREIGN KEY (genre_id)
        REFERENCES content.genre (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
);

-- Create table for many-to-many relatiomship for films and actors
CREATE TABLE IF NOT EXISTS content.person_film_work
(
    id uuid,
    film_work_id uuid NOT NULL,
    person_id uuid NOT NULL,
    role character varying(150),
    created_at timestamp with time zone,
    PRIMARY KEY (id),
    UNIQUE (film_work_id, person_id),
    CONSTRAINT "FK_film_work_id" FOREIGN KEY (film_work_id)
        REFERENCES content.film_work (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT "FK_person_id" FOREIGN KEY (person_id)
        REFERENCES content.person (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- Create indexes
CREATE UNIQUE INDEX film_work_genre ON content.genre_film_work (film_work_id, genre_id);
CREATE UNIQUE INDEX film_work_person_role ON content.person_film_work (film_work_id, person_id, role);