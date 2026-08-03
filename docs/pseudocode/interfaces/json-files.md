# Interface — UTF-8 JSON Files

## Provided By

Python standard library JSON and filesystem facilities.

## Used For

This is a project-profile convention reserved for future saved profiles or
demo data.  The initial BAD-rendered demo does not call this interface.

## Project Rules

- Persist JSON as UTF-8.
- Treat file I/O as an explicit outside operation, not reducer or organism
  behavior.
- Define a dedicated interface and effect contract before persistence is added.

