# Normalization

Normalization is the process of organizing columns and tables in a relational
database to reduce data redundancy and improve data integrity.

## Why normalize?

If the same fact (e.g. a customer's address) is stored in many rows, an update
has to change every copy. Miss one and the database becomes inconsistent. This
is called an **update anomaly**. There are also **insertion anomalies** (you
can't add a fact until an unrelated fact exists) and **deletion anomalies**
(deleting one fact accidentally deletes another).

## First Normal Form (1NF)

A table is in 1NF if every column holds a single (atomic) value and there are
no repeating groups. Example: a `phone_numbers` column holding
"555-1111, 555-2222" violates 1NF; it should be a separate table with one row
per phone number.

## Second Normal Form (2NF)

A table is in 2NF if it is in 1NF and every non-key column depends on the
*whole* primary key, not just part of it. This only matters when the primary
key is composite (more than one column). If `OrderID` + `ProductID` is the
key, a column like `ProductName` that depends only on `ProductID` violates
2NF and should move to a `Products` table.

## Third Normal Form (3NF)

A table is in 3NF if it is in 2NF and no non-key column depends on another
non-key column (no transitive dependency). Example: in an `Employees` table,
if `DepartmentName` depends on `DepartmentID` (a non-key column) rather than
directly on `EmployeeID`, that's a transitive dependency — move department
data to its own table.

## Trade-off

Normalization reduces redundancy but can require more joins at query time.
Systems that read far more than they write (e.g. reporting/analytics) often
**denormalize** on purpose for speed.
