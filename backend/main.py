from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message":"quest video dialogue finder"}




