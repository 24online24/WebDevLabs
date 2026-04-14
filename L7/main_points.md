Showcase how a backend uses a database for reliable, persistent data storage and querying. For example:

- Relational Database basics: Tables, rows, and SQLite
- ORM (Object-Relational Mapping): SQLModel (Pydantic + SQLAlchemy)
- Database Sessions and FastAPI Dependency Injection (`Depends`)
- CRUD operations: Creating and reading data from a real database

1. Database Setup & Engine

- Explain why we are moving from JSON files to SQLite (handling concurrent requests, efficient querying, data integrity).
- Set up `database.py` and create an SQLite engine connecting to a local `coffee_shop.db` file.
- Explain the concept of the "Engine" as the core connection point to the database.
- Use FastAPI's `lifespan` (or startup events) to trigger `SQLModel.metadata.create_all(engine)` to automatically create tables when the server starts.

2. Defining Models: Pydantic to SQLModel

- Upgrade the previous Pydantic models to SQLModel classes by adding `table=True`.
- Define the `MenuItem` and `Reservation` tables.
- Introduce database-specific fields, specifically the Primary Key (`id: int | None = Field(default=None, primary_key=True)`).
- Explain how SQLModel does double duty: it validates incoming data (like Pydantic) _and_ defines the database schema (like SQLAlchemy).

3. Sessions & Dependency Injection

- Explain what a Database Session is (a temporary "workspace" or "conversation" with the database).
- Create a `get_session` generator function that yields a `Session(engine)`.
- Introduce FastAPI's `Depends` system to inject the database session directly into the route functions.
- Show how this automatically handles opening and safely closing the database connection for each request.

4. Refactoring GET Endpoints (Reading from the DB)

- **Seed Data:** Write a quick script or startup function to populate the `MenuItem` table from the old `menu.json` if the table is empty.
- **Get All / Filter:** Refactor `GET /api/menu` to use the database: `session.exec(select(MenuItem)).all()`. Update the category query parameter to filter at the SQL level using `.where(MenuItem.category == category)`.
- **Get One:** Refactor `GET /api/menu/{item_id}` to use `session.get(MenuItem, item_id)`. Introduce raising an `HTTPException(status_code=404)` if the database returns `None`.

5. Refactoring POST Endpoints (Writing to the DB)

- Refactor the `POST /api/reservations` endpoint to accept a `Reservation` object.
- Replace the JSON file append logic with SQLModel operations:
  - `session.add(reservation)` to stage the data.
  - `session.commit()` to save it to the SQLite database.
  - `session.refresh(reservation)` to get the newly generated `id` back from the database.
- Verify the integration by submitting a form on the frontend and using a tool like DB Browser for SQLite (or an IDE extension) to show students the new row physically sitting in the database table.
