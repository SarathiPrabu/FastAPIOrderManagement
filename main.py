'''
This is a FastAPI application that demonstrates the basic CRUD operations on a SQLite database.
The application manages the customers, items and orders. The application uses the sqlite3 module to 
interact with the SQLite database.Pydantic is used for data validation and serialization.
'''
import sqlite3
import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class Customer(BaseModel):
    '''
    Pydanctic model for the Customer
    Customer ID is optional as it is auto-generated
    '''
    customer_id: int | None = None
    name: str
    phone: str

class Item(BaseModel):
    '''
    Pydanctic model for the Item
    Item ID is optional as it is auto-generated
    '''
    item_id: int | None = None
    name: str
    price: float

class Order(BaseModel):
    '''
    Pydanctic model for the Order
    Order ID is optional as it is auto-generated
    Items is a list of item ids
    '''
    order_id : int | None =None
    notes: str
    customer_id: int
    items: list[int]

app = FastAPI()
@app.get("/customers/{customer_id}", response_model=Customer)
def read_customer(customer_id: int):
    '''
    customer_id: int - Passed as path parameter to get the customer details

    Returns:
    Customer: The customer details for the given customer id. The return type is Customer model.

    Raises:
    HTTPException: 404 - If the customer id is not found in the database.
    '''
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT customer_id, name, phone from customers where customer_id = ?",(customer_id,))
    customer = cursor.fetchone()
    conn.close()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return Customer(customer_id=customer[0],name=customer[1],phone=customer[2])

@app.post("/customers/", responses={409:{"detail":"Mobile Number already exists"}})
def create_customer(customer:Customer):
    '''
    customer: Customer - The customer details to be added

    Returns:
    Customer: If the customer is added successfully

    Raises:
    HTTPException: 400 - If the customer detail is not passed
    HTTPException: 409 - If the mobile number already exists
    '''

    if customer.customer_id is not None:
        raise HTTPException(status_code=400, detail="Customer ID should not be passed!")
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO CUSTOMERS (name, phone) VALUES(?,?)",(customer.name,customer.phone))
        customer.customer_id = cursor.lastrowid
        conn.commit()
    # The mobile number is a unique column in the database
    # If the mobile number already exists, then IntegrityError is raised
    except sqlite3.IntegrityError as ie:
        raise HTTPException(status_code=409, detail="Mobile Number already exists") from ie
    finally:
        conn.close()
    return customer

#Defining the response here will add the responses in the OpenAPI documentation
@app.put("/customers/{customer_id}",
            responses= {400:{"detail":"BAD REQUEST Customer ID is required!"},
                        404:{"detail": "Customer not found! Update failed!!"}})
def update_customer(customer_id: int,customer:Customer):
    '''
    customer_id: int - The customer id to be updated 
    customer: Customer - The customer details to be updated for the given customer id

    Returns:
    Customer: The updated customer details if the update is successful

    Raises:
    HTTPException: 400 - If the customer id is not passed/ Not valid
    HTTPException: 404 - If the customer id is not found in the database

    '''
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
        else:
            raise HTTPException(status_code=404, detail="Customer not found. Update failed!!")
    finally:
        conn.close()
    return {"detail":"Updated","item":customer}

@app.delete("/customers/{customer_id}",responses={404: {"detail": "Customer ID not found"}})
def delete_customer(customer_id:int):
    '''
    customer_id: int - The customer id to be deleted 

    Returns:
    dict: The number of rows affected by the delete operation

    Raises:
    HTTPException: 400 - If the customer id is not passed/ None
    HTTPException: 404 - If the customer id is not found in the database
    '''
    if customer_id is None:
        raise HTTPException(status_code=400, detail="Invalid Customer ID!")
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute(
            """DELETE FROM CUSTOMERS WHERE customer_id = ? """,(customer_id,))
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
    '''
    item_id: int - The item id to be fetched

    Returns:
    Item: The item details for the given item id

    Raises:
    HTTPException: 400 - If the item id is not passed/ None
    HTTPException: 404 - If the item id is not found in the database
    '''
    if item_id is None:
        raise HTTPException(status_code=400, detail="Invalid Item ID!")
    conn = sqlite3.connect('db.sqlite')
    cursor = conn.cursor()
    cursor.execute("SELECT item_id, name, price from ITEMS where item_id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(item_id=item[0],name=item[1],price=item[2])

@app.post("/items/")
def create_item(item:Item):
    '''
    item: Item - The item details to be added

    Returns:
    Item: If the item is added successfully

    Raises:
    HTTPException: 400 - If the item detail is not passed
    HTTPException: 409 - If the item already exists
    '''
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ITEMS (name, price) VALUES(?,?)",(item.name, item.price))
        item.item_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError as ie:
        raise HTTPException(status_code=409, detail="Item already exists") from ie
    finally:
        conn.close()
    return {"detail":"Item Added", "Item":item}

@app.delete("/items/{item_id}")
def delete_item(item_id:int):
    '''
    item_id: int - The item id to be deleted

    Returns:
    dict: The number of rows affected by the delete operation

    Raises:
    HTTPException: 400 - If the item id is not passed/ None
    HTTPException: 404 - If the item id is not found in the database
    '''
    if item_id is None:
        raise HTTPException(status_code=400, detail="Invalid Item ID!")
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM ITEMS WHERE item_id = ?",(item_id,))
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
    '''
    item_id: int - The item id to be updated
    item: Item - The item details to be updated for the given item id

    Returns:
    Item: The updated item details if the update is successful

    Raises:
    HTTPException: 400 - If the item id is not passed/ None
    HTTPException: 404 - If the item id is not found in the database
    '''
    if item_id != item.item_id:
        raise HTTPException(status_code = 400, detail = "Invalid Item ID")
    try:
        conn = sqlite3.connect("db.sqlite")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE ITEMS SET name=?,price=? WHERE item_id = ?",(item.name,item.price,item.item_id))
        # Checks if the update is affected exactly one row
        # If the item id is not found in the database, then the rowcount will be 0
        if cursor.rowcount != 1:
            conn.rollback()
            raise HTTPException(status_code= 404, detail = "Item not found")
        conn.commit()
    finally:
        conn.close()
    return {"detail":"Item updated", "item":item}

@app.post("/orders/")
def create_order(order:Order):
    '''
    order: Order - The order details to be added

    Returns:
    dict: If the order is added successfully

    Raises:
    HTTPException: 404 - If the customer id is not found 
    HTTPException: 404 - If the item id is not found
    '''

    try:
        conn = sqlite3.connect('db.sqlite')
        conn.execute("BEGIN")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT customer_id from CUSTOMERS WHERE customer_id = ?",(order.customer_id,))
        customer_id = cursor.fetchone()
        if customer_id is None:
            raise HTTPException(status_code=404, detail="Customer ID not found")
        timestamp = int(datetime.datetime.now().timestamp())
        cursor.execute(
            "INSERT INTO ORDERS (notes, timestamp, customer_id) VALUES(?,?,?)",
            (order.notes, timestamp, customer_id[0]))
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
    finally:
        conn.close()
    return {"detail":"Order placed", "Order ID":order.order_id}

@app.get("/orders/{order_id}")
def get_order(order_id:int):
    '''
    order_id: int - The order id to be fetched

    Returns:
    dict: The order details for the given order id

    Raises:
    HTTPException: 400 - If the order id is not passed/ None
    HTTPException: 404 - If the order id is not found in the database
    '''
    if order_id is None:
        raise HTTPException(status_code=400, detail="Invalid Order ID!")
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT order_id, notes, timestamp, customer_id from ORDERS where order_id = ?", 
            (order_id,))
        order = cursor.fetchone()
        cursor.execute("""
            SELECT item_id, name, price from ITEMS WHERE item_id IN 
            (SELECT item_id from ORDER_LIST WHERE order_id = ?)
            """,(order_id,))
        order_items = cursor.fetchall()
        items_dicts = [{"name": item[1], "price": item[2]} for item in order_items]
        if order is not None and len(order) > 0:
            return {
                "order_id"      :order[0],
                "notes"         :order[1],
                "timestamp"     :order[2],
                "customer_id"   :order[3],
                "items"         :items_dicts
            }
        raise HTTPException(status_code=404, detail="Order not found")
    finally:
        conn.close()

@app.delete("/orders/{order_id}")
def delete_order(order_id:int):
    '''
    order_id: int - The order id to be deleted

    Returns:
    dict: The number of rows affected by the delete operation

    Raises:
    HTTPException: 400 - If the order id is not passed/ None
    HTTPException: 404 - If the order id is not found in the database
    '''
    if order_id is None:
        raise HTTPException(status_code=400, detail="Invalid Order ID!")
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        # By default, foreign key constraints are disabled in SQLite
        # Enabling the foreign key constraints
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
    '''
    order_id: int - The order id to be updated
    order: Order - The order details to be updated for the given order id

    Returns:
    dict: The updated order details if the update is successful

    Raises:
    HTTPException: 400 - If the order id is not passed/ None
    HTTPException: 404 - If the order id is not found in the database
    '''
    if order_id is not order.order_id:
        raise HTTPException(status_code=400, detail="Invalid Order ID!")
    try:
        conn = sqlite3.connect('db.sqlite')
        cursor = conn.cursor()
        timestamp = int(datetime.datetime.now().timestamp())
        cursor.execute(
            "UPDATE ORDERS SET notes = ?,timestamp = ? WHERE order_id = ?",
            (order.notes,timestamp, order_id))
        if cursor.rowcount == 1:
            conn.commit()
        else:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Order ID not found")
        cursor.execute("DELETE FROM ORDER_LIST WHERE order_id = ?",(order.order_id,))
        inserted = 0
        for item_id in order.items:
            cursor.execute("""
            INSERT INTO ORDER_LIST (order_id, item_id)
            SELECT ?, ? WHERE EXISTS (SELECT 1 from ITEMS WHERE item_id = ?)
            """,(order.order_id, item_id, item_id))
            inserted += cursor.rowcount
            if cursor.rowcount != 1:
                conn.rollback()
                raise HTTPException(status_code=404, detail=f"Item ID {item_id} not found")
        conn.commit()
    finally:
        conn.close()
    return {"detail":"Order updated", "Order ID":order.order_id}
