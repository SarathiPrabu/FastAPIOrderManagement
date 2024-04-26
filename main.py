from http.client import HTTPException
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

app = FastAPI()

@app.get("/")
def read_root():
    return {"message":"Hello World"}

@app.get("/customers/{customer_id}")
def read_customer(customer_id: int, q=None):
    pass