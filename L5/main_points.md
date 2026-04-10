Introduce the general concept of an API and provide a simple, fundamental example.

- REST API concepts: Endpoints, HTTP methods (GET), basic request/response flow.
- FastAPI basics: Initialization, Routing, automatic JSON serialization.

1. General API Concepts

- What is an API and why it is used.
- Introduction to HTTP requests and responding with JSON.

2. FastAPI Setup and Basic Routing

- Initialize a simple FastAPI application in `main.py`.
- Create a basic endpoint (`GET /hello_world`) returning a simple JSON dictionary.
- Create another static endpoint (`GET /my_profile`) returning a few specific fields (Name, Age, City).

3. Path and Query Parameters

- Introduce **Path Parameters**: Create an endpoint (`GET /user/{user_id}`) to demonstrate dynamic routing and basic conditional logic.
- Introduce **Query Parameters**: Create an endpoint (`GET /items/{item_id}?q=...`) to show how optional query parameters are passed and handled alongside path parameters.
