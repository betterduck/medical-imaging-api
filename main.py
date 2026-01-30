from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World! My first API is working!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/patients")
def get_patients():
    patients = [
        {"id": 1, "name": "John Doe", "mrn": "MRN001"},
        {"id": 2, "name": "Jane Smith", "mrn": "MRN002"}
    ]
    return {"patients": patients}