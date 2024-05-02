# IS601_Final_Project
### Dosa Restaurant API - Sarathi Prabu Mohan (sm3393)
## Project Overview
This project is a REST API backend for a dosa restaurant, developed using FastAPI and SQLite. The API manages three main entities: customers, items, and orders, providing CRUD functionality for these objects.

## System Design
### Components
- **example_orders.json:** Contains sample data for customers, items, and orders, which are used to populate our database.
- **init_db.py:** A script that creates the tables with proper constraints and populates the sample data from `example_orders.json`.
- **db.sqlite:** The SQLite database file where all data pertaining to the customers, items, and orders is stored. This file will be generated after running the `init_db.py` script. You can remove this file and run the script again to reset the database.
- **main.py:** The FastAPI server that defines all endpoint logic for interacting with the database and handles CRUD operations for customers, items, and orders.

### Database Design
The database schema includes four tables: `CUSTOMERS`, `ITEMS`, `ORDERS`, and `ORDER_LISTS`, utilizing SQLite's built-in `ROWID` as the primary key for each table. The schema is designed to enforce relational integrity with primary and foreign keys, and unique constraints where necessary:

- **CUSTOMERS**: This table stores customer details. `customer_id` (leveraging `ROWID`) serves as the primary key. The mobile number is required to be unique, enforced by a UNIQUE constraint.
- **ITEMS**: Manages details about the items available. `item_id` (leveraging `ROWID`) is the primary key.
- **ORDERS**: Contains details of the orders. `order_id` (leveraging `ROWID`) is the primary key. This table stores the customer_id which is a foreign key reference to the CUSTOMERS table, linking each order to the respective customer. 
- **ORDER_LISTS**: Manages the relationship between `ORDERS` and `ITEMS`. It stores `order_id` and `item_id` to track which items are included in which orders. This table helps in normalizing the data where an order can contain multiple items.Foreign key references to the `ORDERS` and  `ITEMS` table.

## Usage
Clone this repository and navigate to the project folder.

To initalize the database run the `init_db.py` script using the following command. If you want to reset the databse remove `db.sqlite` file and run this script.
```bash
python3 init_db.py
```
To start the FastAPI 
```bash
uvicorn main:app --reload
```
This command will start the FastAPI server. By default, you can access  at `http://localhost:8000/` followed by endpoints. 
To learn more about the endpoints, access the FastAPI documentation at `http://localhost:8000/docs`. You can also interactively test this API using FastAPI `docs` page.

