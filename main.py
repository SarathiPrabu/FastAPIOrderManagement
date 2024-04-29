from fastapi import FastAPI, HTTPException
import sqlite3
from pydantic import BaseModel

class Customer(BaseModel):
    customer_id: int | None = None
    name: str
    phone: str

app = FastAPI()
@app.get("/customers/{customer_id}")
def read_customer(customer_id: int, q=None):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT customer_id, name, phone from customers where customer_id = ?", (customer_id,))
    customer = cursor.fetchone()
    conn.close()
    if customer != None:
        return Customer(customer_id=customer[0],name=customer[1],phone=customer[2])
    else:
        raise HTTPException(status_code=404, detail="Customer not found")

@app.post("/customers/", responses={409:{"detail":"Mobile Number already exists"}})
def create_customer(customer:Customer):
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO CUSTOMERS (name, phone) VALUES(?,?)",(customer.name,customer.phone))
        customer.customer_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=409, detail="Mobile Number already exists") 
    finally:
        conn.close()
    return customer

# Use a decorator to validate the customer id is passed
@app.put("/customers/{customer_id}", responses={400:{"detail":"BAD REQUEST Customer ID is required!"},404: {"detail": "Customer not found! Update failed!!"}})
def update_customer(customer_id: int,customer:Customer):
    if customer.customer_id != customer_id:
        raise HTTPException(status_code=400, detail="Invalid Customer ID!") 
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE CUSTOMERS 
            SET name = ?,
            phone=? 
            WHERE customer_id = ?""",
            (customer.name,customer.phone, customer.customer_id))
        modified = cursor.rowcount
        if modified > 0:
            conn.commit()
            updated_customer = read_customer(customer.customer_id)
            return updated_customer
        else:
            raise HTTPException(status_code=404, detail="Customer not found. Update failed!!") 
    finally:
        conn.close()
    return customer

@app.delete("/customers/{customer_id}",responses={404: {"detail": "Customer ID not found"}})
def delete_customer(customer_id:int):
    if customer_id == None:
        raise HTTPException(status_code=400, detail="Invalid Customer ID!") 
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute(
            """DELETE FROM CUSTOMERS 
            WHERE customer_id = ?""",
            (customer_id,))
        modified = cursor.rowcount
        if modified > 0:
            conn.commit()
        else:
            raise HTTPException(status_code=404, detail="Customer ID not found") 
    finally:
        conn.close()
    return {"Message":f"{modified} rows affected"}