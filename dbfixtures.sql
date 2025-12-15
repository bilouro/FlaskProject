-- ############################################################
-- Full setup script for PostgreSQL
-- - (Optional) create database
-- - Create "books" table
-- - Create trigger function
-- - Insert sample data
-- ############################################################

-- =============[ 1. (Optional) Create database ]==============
-- Run this part only if you want to create a dedicated database
-- and you are connected as a superuser (e.g., postgres).
-- If the database already exists, you can skip this section.

-- CREATE DATABASE flask_example
--     WITH OWNER = postgres
--     ENCODING = 'UTF8'
--     LC_COLLATE = 'en_US.utf8'
--     LC_CTYPE = 'en_US.utf8'
--     TEMPLATE = template0;

-- After creating, connect to the database:
-- \c flask_example;

-- =============[ 2. Drop and create tables ]==================

-- Drop table if it already exists (dev-friendly)
DROP TABLE IF EXISTS books;

-- Main "books" table
CREATE TABLE books (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(255) NOT NULL,
    author      VARCHAR(255) NOT NULL,
    year        INTEGER NOT NULL,
    isbn        VARCHAR(32) NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =============[ 3. Trigger function for updated_at ]=========

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_books_set_updated_at
BEFORE UPDATE ON books
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

-- =============[ 4. Insert sample data ]======================

INSERT INTO books (title, author, year, isbn)
VALUES
    ('Clean Code',
     'Robert C. Martin',
     2008,
     '9780132350884'),

    ('The Pragmatic Programmer',
     'Andrew Hunt; David Thomas',
     1999,
     '9780201616224'),

    ('Design Patterns: Elements of Reusable Object-Oriented Software',
     'Erich Gamma; Richard Helm; Ralph Johnson; John Vlissides',
     1994,
     '9780201633610'),

    ('Refactoring: Improving the Design of Existing Code',
     'Martin Fowler',
     1999,
     '9780201485677'),

    ('Test-Driven Development: By Example',
     'Kent Beck',
     2002,
     '9780321146533');