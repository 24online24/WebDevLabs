Showcase how a backend serves data and handles business logic for a web application. For example:

- REST API concepts: Endpoints, HTTP methods (GET, POST), Status Codes
- FastAPI basics: Routing, automatic JSON serialization, CORS
- Data Validation: Pydantic models

1. API Setup, Routing, and In-Memory Data

- Initialize the FastAPI application in `main.py`.
- Load coffee shop menu data from `menu.json` into a Python dictionary/list when the server starts (in-memory storage).
- Create a simple health-check endpoint (`GET /api/status`) to verify the server is running.
- Explain how FastAPI automatically converts Python dictionaries and lists into JSON responses.

2. Serving Data: GET Requests & Parameters

- Create a `GET /api/menu` endpoint to serve the entire coffee shop menu.
- Introduce **Query Parameters**: Update the endpoint to accept an optional category (`GET /api/menu?category=espresso`) so the backend can handle data filtering.
- Introduce **Path Parameters**: Create a `GET /api/menu/{item_id}` endpoint to retrieve the details of a specific coffee or pastry, demonstrating dynamic routing.

3. Receiving Data: POST Requests & Pydantic

- Create an empty list in memory for reservations, backed by a `reservations.json` file.
- Introduce **Pydantic**: Create a `ReservationRequest` model to define the exact structure the backend expects (e.g., `guest_count`, `date`, `time`, `contact_name`).
- Create a `POST /api/reservations` endpoint.
- Explain how FastAPI uses Pydantic to automatically validate incoming JSON bodies (e.g., rejecting a string if an integer is expected for `guest_count`).
- On successful validation, append the new reservation to the in-memory list, save it to `reservations.json`, and return a `201 Created` status code.

4. CORS (Cross-Origin Resource Sharing)

- Explain why the browser blocks requests from the frontend (running on, say, port 5500) to the backend (running on port 8000).
- Import and configure `CORSMiddleware` in `main.py`.
- Set allowed origins to enable the coffee shop frontend to successfully communicate with the FastAPI backend.

5. Frontend Integration

- Modify `script.js` to replace the local `fetch("menu.json")` with `fetch("http://localhost:8000/api/menu")`.
- Update the frontend filtering logic to optionally use the new backend query parameter (`?category=...`) instead of filtering in the browser.
- Modify the reservation form's `submit` event listener:
  - Keep the local JavaScript validation they already built.
  - Construct a JSON payload from the form inputs.
  - Send a `fetch("http://localhost:8000/api/reservations", { method: "POST", ... })` request.
  - Handle the API response to display the final success or error feedback message in the DOM.
