from fastapi import FastAPI, HTTPException
import sqlite3
from pydantic import BaseModel
import datetime

class Customer(BaseModel):
    customer_id: int | None = None
    name: str
    phone: str

class Item(BaseModel):
    item_id: int | None = None
    name: str
    price: float

class Order(BaseModel):
    order_id : int | None =None
    notes: str
    customer_id: int
    items: list[int]

app = FastAPI()
@app.get("/customers/{customer_id}", response_model=Customer)
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
        row_count = cursor.rowcount
        if row_count > 0:
            conn.commit()
        else:
            raise HTTPException(status_code=404, detail="Customer ID not found") 
    finally:
        conn.close()
    return {"Message":f"{row_count} row(s) affected"}

@app.get("/items/{item_id}")
def get_item(item_id:int):
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, name, price from ITEMS where item_id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()
    if item != None:
        return Item(item_id=item[0],name=item[1],price=item[2])
    else:
        raise HTTPException(status_code=404, detail="Item not found")

@app.post("/items/")
def create_item(item:Item):
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ITEMS (name, price) VALUES(?,?)",(item.name, item.price))
        item.item_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError as ie:
        raise HTTPException(status_code=409, detail="Item already exists") 
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Unable to insert the item!") 
    finally:
        conn.close()
    return {"detail":"Item Added", "Item":item}

@app.delete("/items/{item_id}")
def delete_item(item_id:int):
    if item_id == None:
        raise HTTPException(status_code=400, detail="Invalid Item ID!") 
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute(
            """DELETE FROM ITEMS 
            WHERE item_id = ?""",
            (item_id,))
        row_count = cursor.rowcount
        if row_count == 1:
            conn.commit()
        else:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Item ID not found") 
    finally:
        conn.close()
    return {"detail":f"{row_count} row(s) affected"}

@app.put("/items/{item_id}")
def update_item(item_id:int, item:Item):
    if item_id != item.item_id:
        raise HTTPException(status_code = 400, detail = "Invalid Item ID")
    try:
        conn = sqlite3.connect("db.sqlite")
        cursor = conn.cursor()
        cursor.execute("UPDATE ITEMS SET name=?,price=? WHERE item_id = ?",(item.name,item.price,item.item_id))
        modified_rows = cursor.rowcount
        # Checks if the update is affected exactly one row
        # If the item id is not found or it affects more than 1 row then update is considered as failed
        if cursor.rowcount != 1:
            conn.rollback()
            raise HTTPException(status_code= 404, detail = "Item not found")
        conn.commit()
    finally:
        conn.close()
    return {"detail":"Item updated", "item":item}

@app.post("/orders/")
def create_order(order:Order):
    try:
        conn = sqlite3.connect('db.sqlite')
        conn.execute("BEGIN")
        cursor = conn.cursor()
        cursor.execute("SELECT customer_id from CUSTOMERS WHERE customer_id = ?",(order.customer_id,))
        customer_id = cursor.fetchone()
        if customer_id == None:
            raise HTTPException(status_code=404, detail="Customer ID not found")
        timestamp = int(datetime.datetime.now().timestamp())
        cursor.execute("INSERT INTO ORDERS (notes, timestamp, customer_id) VALUES(?,?,?)",(order.notes, timestamp, customer_id[0]))
        order.order_id = cursor.lastrowid
        for item_id in order.items:
            cursor.execute("""
            INSERT INTO ORDER_LIST (order_id, item_id)
            SELECT ?, ? WHERE EXISTS (SELECT 1 from ITEMS WHERE item_id = ?)
            """,(order.order_id, item_id, item_id))
            if cursor.rowcount != 1:
                conn.rollback()
                raise HTTPException(status_code=404, detail=f"Item ID {item_id} not found")
        conn.commit()

        # Read the order items if required
        # cursor.execute("""
        # SELECT item_id, name, price from ITEMS WHERE item_id IN 
        # (SELECT item_id from ORDER_LIST WHERE order_id = ?)
        # """,(order.order_id,))
        # order_items = cursor.fetchall()
    finally:
        conn.close()
    return {"detail":"Order placed", "Order ID":order.order_id}

@app.get("/orders/{order_id}")
def get_order(order_id:int):
    if order_id == None:
        raise HTTPException(status_code=400, detail="Invalid Order ID!")
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("SELECT order_id, notes, timestamp, customer_id from ORDERS where order_id = ?", (order_id,))
        order = cursor.fetchone()
        cursor.execute("""
            SELECT item_id, name, price from ITEMS WHERE item_id IN 
            (SELECT item_id from ORDER_LIST WHERE order_id = ?)
            """,(order_id,))
        order_items = cursor.fetchall()
        items_dicts = [{"name": item[1], "price": item[2]} for item in order_items]
        if order != None and len(order) > 0:
            return {"order_id":order[0],"notes":order[1],"timestamp":order[2],"customer_id":order[3],"items":items_dicts}
        else:
            raise HTTPException(status_code=404, detail="Order not found")
    finally:
        conn.close()

@app.delete("/orders/{order_id}")
def delete_order(order_id:int):
    if order_id == None:
        raise HTTPException(status_code=400, detail="Invalid Order ID!")
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("DELETE FROM ORDERS WHERE order_id = ?",(order_id,))
        if cursor.rowcount == 1:
            conn.commit()
        else:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Order ID not found")
    finally:
        conn.close()
    return {"detail":f"{cursor.rowcount} row(s) affected"}

@app.put("/orders/{order_id}")
def update_order(order_id:int, order:Order):
    if order_id != order.order_id:
        raise HTTPException(status_code=400, detail="Invalid Order ID!")
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        timestamp = int(datetime.datetime.now().timestamp())
        cursor.execute("UPDATE ORDERS SET notes = ?,timestamp = ? WHERE order_id = ?",(order.notes,timestamp, order_id))
        print(f"Updated {cursor.rowcount} row(s)")
        if cursor.rowcount == 1:
            conn.commit()
        else:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Order ID not found")
        cursor.execute("DELETE FROM ORDER_LIST WHERE order_id = ?",(order.order_id,))
        print(f"Deleted {cursor.rowcount} row(s)")
        inserted = 0
        for item_id in order.items:
            
            cursor.execute("""
            INSERT INTO ORDER_LIST (order_id, item_id)
            SELECT ?, ? WHERE EXISTS (SELECT 1 from ITEMS WHERE item_id = ?)
            """,(order.order_id, item_id, item_id))
            inserted += cursor.rowcount
            if cursor.rowcount != 1:
                print("Unable to insert")
                conn.rollback()
                raise HTTPException(status_code=404, detail=f"Item ID {item_id} not found")
        conn.commit()
    finally:
        print(f"Inserted {inserted} row(s)")
        print(f"Total {conn.total_changes} row(s) affected")
        conn.close()
    return {"detail":"Order updated", "Order ID":order.order_id}
