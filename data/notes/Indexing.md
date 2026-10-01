# Indexing

An index is a data structure (usually a B-tree) that lets the database find
rows quickly without scanning the whole table, at the cost of extra storage
and slower writes.

## Why indexes speed up reads

Without an index, `WHERE email = 'x@y.com'` requires a full table scan —
checking every row. A B-tree index on `email` lets the database jump almost
directly to the matching row, turning an O(n) scan into roughly O(log n)
lookups.

## Primary vs. secondary indexes

The **primary index** is usually built automatically on the primary key. A
**secondary index** is any additional index you create on other columns that
are frequently filtered or joined on, e.g. `CREATE INDEX idx_email ON
Users(email);`.

## Composite indexes

An index on `(last_name, first_name)` speeds up queries that filter on
`last_name` alone, or on `last_name` AND `first_name` together — but it does
**not** help a query that filters on `first_name` alone, because the index
is ordered by `last_name` first. Column order in a composite index matters.

## The write cost

Every `INSERT`, `UPDATE`, or `DELETE` has to update every index on that
table, not just the table itself. Tables with many indexes are slower to
write to. This is why indexes are added deliberately based on actual query
patterns, not on every column "just in case."

## When an index won't help

- Functions applied to the indexed column in the query (e.g.
  `WHERE LOWER(email) = ...`) usually prevent the index from being used,
  unless a functional index was created for that expression.
- Low-cardinality columns (e.g. a boolean `is_active`) rarely benefit from an
  index because a large fraction of rows match any given value.
