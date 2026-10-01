# Entity-Relationship (ER) Model

The ER model is a way to design a database at a conceptual level before
writing any SQL, using entities, attributes and relationships.

## Entities and attributes

An **entity** is a real-world object or concept (e.g. `Student`, `Course`).
An **attribute** describes an entity (e.g. `Student` has `StudentID`, `Name`,
`Email`). A **key attribute** (like `StudentID`) uniquely identifies each
entity instance.

## Relationships

A **relationship** connects two or more entities (e.g. a `Student` *enrolls
in* a `Course`). Relationships have **cardinality**:

- **One-to-one (1:1)** — one `Employee` has one `ParkingSpot`.
- **One-to-many (1:N)** — one `Department` has many `Employees`.
- **Many-to-many (M:N)** — many `Students` enroll in many `Courses`. This
  requires a junction/bridge table (e.g. `Enrollment`) with foreign keys to
  both sides, because relational tables can't directly store M:N links.

## Weak entities

A **weak entity** cannot be uniquely identified by its own attributes alone
and depends on a related "owner" entity. Example: `Dependent` (a family
member on an insurance policy) is identified only in combination with the
`Employee` it belongs to.

## From ER diagram to tables

1. Each strong entity becomes a table; its key attribute becomes the primary
   key.
2. A 1:N relationship becomes a foreign key on the "many" side.
3. An M:N relationship becomes its own junction table with two foreign keys.
4. A weak entity's table includes the owner's primary key as part of its own
   key.
