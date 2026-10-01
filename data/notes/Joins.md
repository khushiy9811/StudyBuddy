# SQL Joins

A join combines rows from two or more tables based on a related column,
typically a foreign key matching a primary key.

## INNER JOIN

Returns only rows that have a match in **both** tables. If a customer has no
orders, that customer is left out of an `INNER JOIN` between `Customers` and
`Orders`.

```sql
SELECT c.name, o.total
FROM Customers c
INNER JOIN Orders o ON c.id = o.customer_id;
```

## LEFT JOIN (LEFT OUTER JOIN)

Returns **all rows from the left table**, plus matching rows from the right
table. If there's no match, the right-table columns are `NULL`. This is the
join to use when you want "every customer, and their orders if they have
any."

## RIGHT JOIN (RIGHT OUTER JOIN)

The mirror of `LEFT JOIN` — all rows from the right table, matched rows from
the left. In practice most people just swap table order and use `LEFT JOIN`
instead, so `RIGHT JOIN` is rarely seen in real code.

## FULL OUTER JOIN

Returns all rows from both tables, with `NULL`s wherever there's no match on
either side. Not all databases support it natively (MySQL doesn't; it's
emulated with a `UNION` of `LEFT JOIN` and `RIGHT JOIN`).

## CROSS JOIN

Returns the Cartesian product — every row of the left table paired with
every row of the right table. No `ON` condition. Rarely intentional in
application code; usually a sign of a missing join condition.

## SELF JOIN

A table joined to itself, useful for hierarchical data like
"employee -> manager" where both are rows in the same `Employees` table.

## Common mistake

Forgetting the `ON` condition turns an intended `INNER JOIN` into an
accidental `CROSS JOIN`, producing far more rows than expected.
