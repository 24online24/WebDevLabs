from fastapi import FastAPI

app = FastAPI()


@app.get("/hello_world")
def hello():
    return {
        "Hello": "World"
    }


@app.get("/my_profile")
def get_student():
    return {
        "Nume": "John Doe",
        "Varsta": 30,
        "Oras": "Bucuresti"
    }


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


@app.get("/user/{user_id}")
def get_profile(user_id: str):
    if user_id == 'me':
        return {
        "user_id": "124dsadsa2",
        "name": "You",
        "age": 25,
        "city": "Your City"
    }
    return {
        "user_id": user_id,
        "name": "Some Person",
        "age": 25,
        "city": "Some City"
    }
