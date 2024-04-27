import sys
import os
import threading
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QDialog
from PySide6.QtWidgets import *
from PySide6.QtCore import QObject, Signal, Slot, Qt
import socket
import logging
import json
import requests

class TableWidget(QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        super().mouseDoubleClickEvent(event)
        index = self.indexAt(event.pos())
        if index.isValid():
            print(f"Double clicked on row {index.row()}")
        else:
            pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.API_URL = "http://localhost:5000"

        self.setWindowTitle("Onlinestore")
        self.resize(800,600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

# CUSTOMERS TAB
        self.customer_tab = QWidget()
        self.customer_layout = QVBoxLayout(self.customer_tab)
        # CUSTOMER BUTTONS
        self.customer_buttons = QWidget()
        self.customer_buttons_layout = QHBoxLayout(self.customer_buttons)
        # Get customers
        self.get_customers_button = QPushButton("Refresh")
        self.customer_buttons_layout.addWidget(self.get_customers_button)
        self.get_customers_button.clicked.connect(self.get_customers)
        # Edit customer
        self.edit_button = QPushButton("Edit")
        self.customer_buttons_layout.addWidget(self.edit_button)
        self.edit_button.clicked.connect(self.edit_customer)
        # Create order
        self.create_order_button = QPushButton("Create Order")
        self.customer_buttons_layout.addWidget(self.create_order_button)
        self.create_order_button.clicked.connect(self.create_order)
        # self.layout.addLayout(self.customer_buttons)
        # Customers table
        self.customers_dict = {}
        self.customers_table = QTableWidget(0, 5)
        self.customers_table.setHorizontalHeaderLabels(["UUID", "First name", "Last name", "Email", "Phone number"])
        self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.layout.addWidget(self.customers_table)
        self.customer_layout.addWidget(self.customer_buttons)
        self.customer_layout.addWidget(self.customers_table)
        # self.customer_tab.setLayout(self.customer_layout)
        self.tab_widget.addTab(self.customer_tab, "Customers")

# ORDERS TAB
        self.orders_tab = QWidget()
        self.order_layout = QVBoxLayout(self.orders_tab)
        # ORDER BUTTONS
        self.order_buttons = QWidget()
        self.order_buttons_layout = QHBoxLayout(self.order_buttons)
        # Get orders
        self.get_orders_button = QPushButton("Refresh")
        self.order_buttons_layout.addWidget(self.get_orders_button)
        self.get_orders_button.clicked.connect(self.get_orders)
        # Open order
        self.open_order_button = QPushButton("Open")
        self.order_buttons_layout.addWidget(self.open_order_button)
        self.open_order_button.clicked.connect(self.open_order)
        # Edit order
        self.edit_order_button = QPushButton("Edit")
        self.order_buttons_layout.addWidget(self.edit_order_button)
        self.edit_order_button.clicked.connect(self.edit_order)
        # Orders table
        self.orders_table = QTableWidget(0, 3)
        self.orders_table.setHorizontalHeaderLabels(["Order number", "Customer ID", "Created at"])
        self.orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.order_layout.addWidget(self.order_buttons)
        self.order_layout.addWidget(self.orders_table)

        self.tab_widget.addTab(self.orders_tab, "Orders")

# PRODUCTS TAB
        self.products_tab = QWidget()
        self.products_layout = QVBoxLayout(self.products_tab)
        # PRODUCTS BUTTONS
        self.products_buttons = QWidget()
        self.products_buttons_layout = QHBoxLayout(self.products_buttons)
        # Get products
        self.get_products_button = QPushButton("Refresh")
        self.products_buttons_layout.addWidget(self.get_products_button)
        self.get_products_button.clicked.connect(self.get_products)
        # Edit product
        self.edit_product_button = QPushButton("Edit")
        self.products_buttons_layout.addWidget(self.edit_product_button)
        self.edit_product_button.clicked.connect(self.edit_product)
        # Products table
        self.products_dict = {}
        self.products_table = QTableWidget(0, 3)
        self.products_table.setHorizontalHeaderLabels(["Name", "Description", "Price"])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.products_layout.addWidget(self.products_buttons)
        self.products_layout.addWidget(self.products_table)

        self.tab_widget.addTab(self.products_tab, "Products")

# STOCK TAB

        self.stock_tab = QWidget()
        self.stock_layout = QVBoxLayout(self.stock_tab)
        # STOCK BUTTONS
        self.stock_buttons = QWidget()
        self.stock_buttons_layout = QHBoxLayout(self.stock_buttons)
        # Get stock
        self.get_stock_button = QPushButton("Refresh")
        self.stock_buttons_layout.addWidget(self.get_stock_button)
        self.get_stock_button.clicked.connect(self.get_stock)
        # Edit stock
        self.edit_stock_button = QPushButton("Edit")
        self.stock_buttons_layout.addWidget(self.edit_stock_button)
        self.edit_stock_button.clicked.connect(self.edit_stock)
        # Stock table
        self.stock_dict = {}
        self.stock_table = QTableWidget(0, 2)
        self.stock_table.setHorizontalHeaderLabels(["Product ID", "Quantity"])
        self.stock_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.stock_layout.addWidget(self.stock_buttons)
        self.stock_layout.addWidget(self.stock_table)

        self.tab_widget.addTab(self.stock_tab, "Stock")

        self.setStatusBar(QStatusBar(self))

    def get_customers(self):
        self.statusBar().showMessage("Getting customers...")
        s = requests.Session()
        ctrl = {
            "method": "get",
            "href": "/api/customers/"
        }
        try:
            r = self.send_request(s, ctrl, None)
            self.customers_dict = r.json()
            customers = r.json()["customers"]
            self.show_customers(customers)
            self.statusBar().showMessage("Customers retrieved successfully")
        except Exception as e:
            print(f"An error occurred: {e}")
            self.statusBar().showMessage(f"An error occurred: {e}")

    def show_customers(self, customers):
        self.customers_table.setRowCount(0)
        for c in customers:
            row = self.customers_table.rowCount()
            self.customers_table.insertRow(row)
            for i, key in enumerate(["uuid", "firstName", "lastName", "email", "phone"]):
                self.customers_table.setItem(row, i, QTableWidgetItem(c[key]))
            # s = c["firstName"] + " " + c["lastName"]
            # self.customers_table.setItem(row, 0, QTableWidgetItem(s.strip()))


    def edit_customer(self):
        selected_indexes = self.customers_table.selectionModel().selectedIndexes()
        if not selected_indexes:
            print("Please select a row to edit")
            self.statusBar().showMessage("Please select a row to edit")
            return

        row = selected_indexes[0].row()
        customer_id = self.customers_table.item(row, 0).text()

        with requests.Session() as s:
            href = self.customers_dict["@controls"]["self"]["href"]
            r = s.get(f"{self.API_URL}{href}{customer_id}/")
            data = r.json()
            ctrl = data["@controls"]["edit"]
            print(ctrl)

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Customer")
        dialog_layout = QVBoxLayout(dialog)

        self.edit_fields = {}
        for i, key in enumerate(["firstName", "lastName", "email", "phone"]):
            label = QLabel(key)
            dialog_layout.addWidget(label)
            line_edit = QLineEdit(self.customers_table.item(row, i+1).text())
            dialog_layout.addWidget(line_edit)
            self.edit_fields[key] = line_edit

        save_button = QPushButton("Save")
        dialog_layout.addWidget(save_button)
        save_button.clicked.connect(lambda: self.save_customer(dialog, customer_id, ctrl))

        dialog.exec()

    def save_customer(self, dialog, customer_id, ctrl):
        data = {key: line_edit.text() for key, line_edit in self.edit_fields.items()}
        s = requests.Session()
        try:
            r = self.send_request(s, ctrl, data)
            if r.status_code == 204:
                print("Customer updated successfully")
                self.statusBar().showMessage("Customer updated successfully")
                dialog.accept()
                self.get_customers()
            else:
                print(f"Failed to update customer: {r.text}")
                message = r.json()["@error"]["@messages"][0]
                self.statusBar().showMessage(f"Error: {message}")
        except Exception as e:
            print(f"Error occurred: {e}")

    def get_orders(self):
        self.statusBar().showMessage("Getting orders...")
        s = requests.Session()
        ctrl = {
            "method": "get",
            "href": "/api/orders/"
        }
        try:
            r = self.send_request(s, ctrl, None)
            orders = r.json()["orders"]
            print(orders)
            self.show_orders(orders)
            self.statusBar().showMessage("orders retrieved successfully")
        except Exception as e:
            print(f"An error occurred: {e}")
            self.statusBar().showMessage(f"An error occurred: {e}")

    def show_orders(self, orders):
        self.orders_table.setRowCount(0)
        for o in orders:
            row = self.orders_table.rowCount()
            self.orders_table.insertRow(row)
            for i, key in enumerate(["id", "customerId", "createdAt"]):
                self.orders_table.setItem(row, i, QTableWidgetItem(str(o[key])))

    def open_order(self):
        selected_indexes = self.customers_table.selectionModel().selectedIndexes()
        if not selected_indexes:
            print("Please select a row to open")
            self.statusBar().showMessage("Please select a row to open")
            return

        row = selected_indexes[0].row()
        order_id = self.orders_table.item(row, 0).text()

        pass

    def edit_order(self):
        pass

    def create_order(self):
        # Get customer uuid
        # Create order
        #    createdAt
        #    customerId
        #    Save orderId from response
        # Select products
        #    Get products in stock to dropdown menu
        #    set quantity
        # Create product orders
        #    orderId
        #    productId
        #    quantity
        #  Update stock for products

        pass

    def get_products(self):
        self.statusBar().showMessage("Getting products...")
        s = requests.Session()
        ctrl = {
            "method": "get",
            "href": "/api/products/"
        }
        try:
            r = self.send_request(s, ctrl, None)
            self.products_dict = r.json()
            products = r.json()["products"]
            self.show_products(products)
            self.statusBar().showMessage("Products retrieved successfully")
        except Exception as e:
            print(f"An error occurred: {e}")
            self.statusBar().showMessage(f"An error occurred: {e}")

    def show_products(self, products):
        self.products_table.setRowCount(0)
        for p in products:
            row = self.products_table.rowCount()
            self.products_table.insertRow(row)
            for i, key in enumerate(["name", "desc", "price"]):
                self.products_table.setItem(row, i, QTableWidgetItem(str(p[key])))


    def edit_product(self):
        selected_indexes = self.products_table.selectionModel().selectedIndexes()
        if not selected_indexes:
            print("Please select a row to edit")
            self.statusBar().showMessage("Please select a row to edit")
            return

        row = selected_indexes[0].row()
        product_name = self.products_table.item(row, 0).text()

        with requests.Session() as s:
            href = self.products_dict["@controls"]["self"]["href"]
            r = s.get(f"{self.API_URL}{href}{product_name}/")
            data = r.json()
            ctrl = data["@controls"]["edit"]
            print(ctrl)

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Product")
        dialog_layout = QVBoxLayout(dialog)

        self.edit_fields = {}
        for i, key in enumerate(["name", "desc", "price"]):
            label = QLabel(key)
            dialog_layout.addWidget(label)
            line_edit = QLineEdit(self.products_table.item(row, i).text())
            dialog_layout.addWidget(line_edit)
            self.edit_fields[key] = line_edit

        save_button = QPushButton("Save")
        dialog_layout.addWidget(save_button)
        save_button.clicked.connect(lambda: self.save_product(dialog, product_name, ctrl))

        dialog.exec()


    def save_product(self, dialog, ctrl):
        data = {key: line_edit.text() for key, line_edit in self.edit_fields.items()}
        data["price"] = float(data["price"])
        s = requests.Session()
        try:
            r = self.send_request(s, ctrl, data)
            if r.status_code == 204:
                print("Product updated successfully")
                self.statusBar().showMessage("Product updated successfully")
                dialog.accept()
                self.get_products()
            else:
                print(f"Failed to update product: {r.text}")
                message = r.json()["@error"]["@messages"][0]
                self.statusBar().showMessage(f"Error: {message}")
        except Exception as e:
            print(f"Error occurred: {e}")

    def get_stock(self):
        self.statusBar().showMessage("Getting stock...")
        s = requests.Session()
        ctrl = {
            "method": "get",
            "href": "/api/stock/"
        }
        try:
            r = self.send_request(s, ctrl, None)
            self.stock_dict = r.json()
            stock = r.json()["items"]
            self.show_stock(stock)
            self.statusBar().showMessage("Stock retrieved successfully")
        except Exception as e:
            print(f"An error occurred: {e}")
            self.statusBar().showMessage(f"An error occurred: {e}")

    def show_stock(self, stock):
        self.stock_table.setRowCount(0)
        for p in stock:
            row = self.stock_table.rowCount()
            self.stock_table.insertRow(row)
            for i, key in enumerate(["productId", "quantity"]):
                self.stock_table.setItem(row, i, QTableWidgetItem(str(p[key])))


    def edit_stock(self):
        selected_indexes = self.stock_table.selectionModel().selectedIndexes()
        if not selected_indexes:
            print("Please select a row to edit")
            self.statusBar().showMessage("Please select a row to edit")
            return

        row = selected_indexes[0].row()
        product_name = self.stock_table.item(row, 0).text()

        with requests.Session() as s:
            href = self.stock_dict["@controls"]["self"]["href"]
            r = s.get(f"{self.API_URL}{href}{product_name}/")
            data = r.json()
            ctrl = data["@controls"]["edit"]
            print(ctrl)

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Stock")
        dialog_layout = QVBoxLayout(dialog)

        self.edit_fields = {}
        for i, key in enumerate(["productId", "quantity"]):
            label = QLabel(key)
            dialog_layout.addWidget(label)
            line_edit = QLineEdit(self.stock_table.item(row, i).text())
            dialog_layout.addWidget(line_edit)
            self.edit_fields[key] = line_edit

        save_button = QPushButton("Save")
        dialog_layout.addWidget(save_button)
        save_button.clicked.connect(lambda: self.save_stock(dialog, ctrl))

        dialog.exec()


    def save_stock(self, dialog, ctrl):
        data = {key: line_edit.text() for key, line_edit in self.edit_fields.items()}
        data["quantity"] = float(data["quantity"])
        data["productId"] = int(data["productId"])
        s = requests.Session()
        try:
            r = self.send_request(s, ctrl, data)
            if r.status_code == 204:
                print("Product updated successfully")
                self.statusBar().showMessage("Product updated successfully")
                dialog.accept()
                self.get_stock() # Update view
            else:
                print(f"Failed to update product: {r.text}")
                message = r.json()["@error"]["@messages"][0]
                self.statusBar().showMessage(f"Error: {message}")
        except Exception as e:
            print(f"Error occurred: {e}")

    # Utils:

    def send_request(self, s, ctrl, data):
        ''' Send a request to the API '''
        r = s.request(
            ctrl["method"],
            self.API_URL + ctrl["href"],
            data=json.dumps(data),
            headers={"Content-type": "application/json"}
        )
        return r

if __name__ == "__main__":
    app = QApplication([])

    window = MainWindow()
    window.show()

    sys.exit(app.exec())