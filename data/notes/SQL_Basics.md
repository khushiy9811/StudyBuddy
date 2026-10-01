# SQL Basics

SQL (Structured Query Language) is used to define, query and modify data in a
relational database.

## Core statements

- `SELECT columns FROM table WHERE condition` — retrieve rows.
- `INSERT INTO table (cols) VALUES (...)` — add a row.
- `UPDATE table SET col = value WHERE condition` — modify rows.
- `DELETE FROM table WHERE condition` — remove rows.

## Filtering and sorting

`WHERE` filters rows before grouping; `HAVING` filters groups after
`GROUP BY`. `ORDER BY col ASC|DESC` sorts the result set. `LIMIT n`
restricts the number of rows returned.

## Aggregate functions

`COUNT()`, `SUM()`, `AVG()`, `MIN()`, `MAX()` compute a single value across a
group of rows. They are almost always used with `GROUP BY` when you want a
value per category rather than one value for the whole table.

## Keys

A **primary key** uniquely identifies each row in a table and cannot be
NULL. A **foreign key** is a column that references the primary key of
another table, enforcing referential integrity — you can't insert a foreign
key value that doesn't exist in the referenced table.

## Transactions

A transaction groups statements so they succeed or fail together
(`BEGIN` ... `COMMIT` / `ROLLBACK`). The ACID properties — Atomicity,
Consistency, Isolation, Durability — describe what a reliable transaction
guarantees.
