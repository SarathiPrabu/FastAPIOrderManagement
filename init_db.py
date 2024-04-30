import sqlite3
import json

connection = sqlite3.connect("db.sqlite")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS CUSTOMERS(
customer_id INTEGER PRIMARY KEY,
name CHAR(64) NOT NULL,
phone CHAR(10) UNIQUE NOT NULL);
""")

cursor.execute(
"""
CREATE TABLE IF NOT EXISTS ORDERS(
order_id INTEGER PRIMARY KEY,
notes TEXT,
customer_id INTEGER NOT NULL,
timestamp INTEGER NOT NULL,
FOREIGN KEY(customer_id) REFERENCES CUSTOMERS(customer_id)
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ITEMS(
item_id INTEGER PRIMARY KEY,
name CHAR(64) NOT NULL UNIQUE,
price REAL NOT NULL);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ORDER_LIST(
order_list_id INTEGER PRIMARY KEY,
order_id INTEGER NOT NULL REFERENCES ORDERS(order_id) ON DELETE CASCADE,
item_id INTEGER NOT NULL,
FOREIGN KEY(item_id) REFERENCES ITEMS(item_id));
""")

def list_customers():
    rows = cursor.execute("SELECT customer_id, name, phone FROM CUSTOMERS;").fetchall()
    return rows
def list_orders():
    rows = cursor.execute("SELECT order_id, notes, customer_id FROM ORDERS;").fetchall()
    return rows
def list_items():
    rows = cursor.execute("SELECT item_id, name, price FROM ITEMS;").fetchall()
    return rows
def list_order_list():
    rows = cursor.execute("SELECT order_list_id, order_id, item_id FROM ORDER_LIST;").fetchall()
    return rows

def read_json(filename: str) -> dict:
    with open(filename, 'r', encoding='utf-8') as file_object:
        order_list = json.load(file_object)
    return order_list

if __name__ == "__main__":
    order_list = read_json("example_orders.json")


    customers = {}
    items = {}
    for order in order_list:
        customers[order['phone']] = order['name']
    for order in order_list:
        for item in order['items']:
            items[item['name']]= item['price']
    
    # Insert Customers
    for phone, name in customers.items():
        cursor.execute("INSERT INTO CUSTOMERS (name, phone) values(?,?)",(name,phone))

    # Insert items
    for name,price in items.items():
        cursor.execute("INSERT INTO ITEMS (name, price) values (?,?)", (name, price))


    for order in order_list:
        cursor.execute("SELECT customer_id from CUSTOMERS WHERE phone = ? ", (order['phone'],))
        cust_id  = cursor.fetchone()[0]

        cursor.execute("INSERT INTO ORDERS (notes, customer_id, timestamp) VALUES (?,?,?)", (order['notes'],cust_id,order['timestamp']))
        order_id = cursor.lastrowid

        for items in order['items']:
            item_id = cursor.execute("SELECT item_id FROM ITEMS WHERE name = ? ",(items['name'],)).fetchone()[0]
            cursor.execute("INSERT INTO ORDER_LIST (order_id, item_id) VALUES (?,?)",(order_id, item_id))
    connection.commit()
    connection.close()
