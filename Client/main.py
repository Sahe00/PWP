import sys
import os
import threading
from datetime import datetime
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QPushButton, QLabel, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QDialog
from PySide6.QtWidgets import *
from PySide6.QtCore import QObject, Signal, Slot, Qt
import socket
import logging
import json
import requests



#class OrderDialog(QDialog):
#    def __init__(self, customer_uuid, order_id, parent=None):
#        super().__init__(parent)
#        self.setWindowTitle("Create Order")
#
#        self.customer_uuid = customer_uuid
#        self.order_id = order_id
#
#        # Initialize UI components
#        dialog_layout = QVBoxLayout(self)
#
#        # Create dropdown menu
#        self.product_combobox = QComboBox(self)
#        dialog_layout.addWidget(QLabel("Select Product(s):"))
#        dialog_layout.addWidget(self.product_combobox)
#
#        # List product names in the dropdown menu
#        self.get_products()  # Fetch products (assuming this method exists)
#        products = self.products_dict["products"]
#        for prod in products:
#            self.product_combobox.addItem(prod["name"])
#
#        self.submit_button = QPushButton("Submit", self)
#        dialog_layout.addWidget(self.submit_button)
#        self.submit_button.clicked.connect(self.submit_order)
#
#    def submit_order(self):
#        selected_product = self.product_combobox.currentText()
#        print(f"Selected Product: {selected_product}")
#        # Perform further actions with the selected product and order details


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
        # Create customer
        self.create_customer_button = QPushButton("Add Customer")
        self.customer_buttons_layout.addWidget(self.create_customer_button)
        self.create_customer_button.clicked.connect(self.create_customer)
        # Delete customer
        self.delete_button = QPushButton("Delete")
        self.customer_buttons_layout.addWidget(self.delete_button)
        self.delete_button.clicked.connect(self.delete_customer)
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
        # Delete order
        self.delete_order_button = QPushButton("Delete")
        self.order_buttons_layout.addWidget(self.delete_order_button)
        self.delete_order_button.clicked.connect(self.delete_order)
        # Orders table
        self.orders_dict = {}
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
        # Create product
        self.create_product_button = QPushButton("Add Product")
        self.products_buttons_layout.addWidget(self.create_product_button)
        self.create_product_button.clicked.connect(self.create_product)
        # Delete product
        self.delete_product_button = QPushButton("Delete")
        self.products_buttons_layout.addWidget(self.delete_product_button)
        self.delete_product_button.clicked.connect(self.delete_product)
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

        self.auto_refresh()


# ----- METHODS --------------------------------------------

    def auto_refresh(self):
        self.get_customers()
        self.get_orders()
        self.get_products()
        self.get_stock()

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
                item = QTableWidgetItem(c[key])
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.customers_table.setItem(row, i, item)
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
            # print(ctrl)

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

    def delete_customer(self):
        selected_indexes = self.customers_table.selectionModel().selectedIndexes()
        if not selected_indexes:
            print("Please select a row to delete")
            self.statusBar().showMessage("Please select a row to delete")
            return

        row = selected_indexes[0].row()
        customer_uuid = self.customers_table.item(row, 0).text()
        customer_name = self.customers_table.item(row, 1).text() + " " + self.customers_table.item(row, 2).text()

        dialog = QDialog(self)
        dialog.setWindowTitle("Are you sure?")
        dialog_layout = QHBoxLayout(dialog)
        yes_button = QPushButton("Yes")
        no_button = QPushButton("No")
        dialog_layout.addWidget(yes_button)
        dialog_layout.addWidget(no_button)

        def delete_customer_confirm(dialog, customer_uuid):
            dialog.accept()
            with requests.Session() as s:
                href = self.customers_dict["@controls"]["self"]["href"]
                r = s.delete(f"{self.API_URL}{href}{customer_uuid}/")
                if r.status_code == 204:
                    QMessageBox.information(dialog, "Success", f"Customer {customer_name} deleted successfully")
                    print(f"Customer {customer_name} deleted successfully")
                    self.statusBar().showMessage(f"Customer {customer_name} deleted successfully")
                    self.get_customers()
                else:
                    QMessageBox.warning(dialog, "Failed", f"Failed to delete Customer {customer_name}: {r.text}")
                    print(f"Failed to delete Customer {customer_name}: {r.text}")
                    message = r.json()["@error"]["@messages"][0]
                    self.statusBar().showMessage(f"Error: {message}")

        yes_button.clicked.connect(lambda: delete_customer_confirm(dialog, customer_uuid))
        no_button.clicked.connect(dialog.reject)

        dialog.exec()

    def get_orders(self):
        self.statusBar().showMessage("Getting orders...")
        s = requests.Session()
        ctrl = {
            "method": "get",
            "href": "/api/orders/"
        }
        try:
            r = self.send_request(s, ctrl, None)
            self.orders_dict = r.json()
            orders = r.json()["orders"]
            # print(orders)
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
                item = QTableWidgetItem(str(o[key]))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.orders_table.setItem(row, i, item)


    def open_order(self):
        selected_indexes = self.orders_table.selectionModel().selectedIndexes()
        if not selected_indexes:
            print("Please select a row to open")
            self.statusBar().showMessage("Please select a row to open")
            return

        row = selected_indexes[0].row()
        order_id = self.orders_table.item(row, 0).text()

        self.statusBar().showMessage(f"Opening order {order_id}...")

        # list of product orders comes with orderitem get
        # check which ones match order id
        with requests.Session() as s:
            href = self.orders_dict["@controls"]["self"]["href"]
            r = s.get(f"{self.API_URL}{href}{order_id}/")
            data = r.json()
            product_order_list = data["productorders"]

        dialog = QDialog(self)
        dialog.setWindowTitle("Order Details")
        dialog_layout = QVBoxLayout(dialog)

        products_table = QTableWidget(0, 3)
        products_table.setHorizontalHeaderLabels(["Product name", "Quantity", "Price"])
        products_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        dialog_layout.addWidget(products_table)

        sum_display = QHBoxLayout()
        sum_display.addWidget(QLabel("Total:"))

        total_sum = 0

        # list of products in matching product orders
        with requests.Session() as s:
            for po in product_order_list:
                row = products_table.rowCount()
                products_table.insertRow(row)
                href = "/api/products/" + str(po["productId"]) + "/"
                r = s.get(f"{self.API_URL}{href}")
                product_data = r.json()
                products_table.setItem(row, 0, QTableWidgetItem(product_data["name"]))
                products_table.setItem(row, 1, QTableWidgetItem(str(po["quantity"])))
                products_table.setItem(row, 2, QTableWidgetItem(str(product_data["price"] * po["quantity"])))
                total_sum += product_data["price"] * po["quantity"]

        sum_display.addWidget(QLabel(str(total_sum)))
        dialog_layout.addLayout(sum_display)

        #maybe get customer info too

        self.statusBar().showMessage(f"Order {order_id} opened")
        dialog.exec()

    def edit_order(self):
        pass

    def delete_order(self):
        selected_indexes = self.orders_table.selectionModel().selectedIndexes()
        if not selected_indexes:
            print("Please select a row to delete")
            self.statusBar().showMessage("Please select a row to delete")
            return

        row = selected_indexes[0].row()
        order_id = self.orders_table.item(row, 0).text()

        dialog = QDialog(self)
        dialog.setWindowTitle("Are you sure?")
        dialog_layout = QHBoxLayout(dialog)
        yes_button = QPushButton("Yes")
        no_button = QPushButton("No")
        dialog_layout.addWidget(yes_button)
        dialog_layout.addWidget(no_button)

        def delete_order_confirm(dialog, order_id):
            dialog.accept()
            with requests.Session() as s:
                href = self.orders_dict["@controls"]["self"]["href"]
                r = s.delete(f"{self.API_URL}{href}{order_id}/")
                if r.status_code == 204:
                    QMessageBox.information(dialog, "Success", f"Order {order_id} deleted successfully")
                    print(f"Order {order_id} deleted successfully")
                    self.statusBar().showMessage(f"Order {order_id} deleted successfully")
                    self.get_orders()
                else:
                    QMessageBox.warning(dialog, "Failed", f"Failed to delete order {order_id}: {r.text}")
                    print(f"Failed to delete order {order_id}: {r.text}")
                    message = r.json()["@error"]["@messages"][0]
                    self.statusBar().showMessage(f"Error: {message}")

        yes_button.clicked.connect(lambda: delete_order_confirm(dialog, order_id))
        no_button.clicked.connect(dialog.reject)

        dialog.exec()

    def create_order(self):
        # Get customer uuid
        # Create order
        #    customer_uuid
        #    createdAt
        #    Save orderId from response header
        # Select products
        #    Get products in stock to dropdown menu
        #    set quantity
        # Create product orders
        #    orderId
        #    productId
        #    quantity
        #  Update stock for products

        # Select customer for order
        selected_indexes = self.customers_table.selectionModel().selectedIndexes()
        if not selected_indexes:
            print("Please select a row to create an order")
            self.statusBar().showMessage("Please select a row to create an order")
            return

        # Get customer uuid
        row = selected_indexes[0].row()
        customer_uuid = self.customers_table.item(row, 0).text()

        ctrl = {
            "method": "post",
            "href": "/api/orders/"
        }
        data = {
            "customerId": customer_uuid,
            "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            # Create order
            s = requests.Session()
            r = self.send_request(s, ctrl, data)
            if r.status_code == 201:
                # Save orderId from response
                order_id = r.headers["Location"].rstrip('/').split('/')[-1]
                print(f"Order created successfully: {order_id}")
                self.statusBar().showMessage(f"Order created successfully: {order_id}")
                #self.create_product_order(order_id)
            else:
                print(f"Failed to create order: {r.text}")
                message = r.json()["@error"]["@messages"][0]
                self.statusBar().showMessage(f"Error: {message}")
        except Exception as e:
            print(f"Error occurred: {e}")
            self.statusBar().showMessage(f"Error occurred: {e}")

        dialog = QDialog(self)
        dialog.setWindowTitle("Create Order")
        dialog_layout = QVBoxLayout(dialog)

        # Select products
        self.get_products()
        products = self.products_dict["products"]

        # Initialize UI components
        layout = QVBoxLayout(self)
        #dialog = OrderDialog(customer_uuid, order_id)

        # Create dropdown menu
        self.product_combobox = QComboBox(self)
        layout.addWidget(QLabel("Select Product(s):"))
        layout.addWidget(self.product_combobox)

        self.submit_button = QPushButton("Submit", self)
        #self.submit_button.clicked.connect(self.submit_products)
        layout.addWidget(self.submit_button)

        # List product names in the dropdown menu
        for prod in products:
            label = QLabel(prod["name"])
            self.product_combobox.addItem(prod["name"])
            dialog_layout.addWidget(label)

        save_button = QPushButton("Save")
        dialog_layout.addWidget(save_button)
        save_button.clicked.connect(lambda: self.save_product_order(dialog, order_id, ctrl))

        dialog.exec()

    def create_customer(self):
        # Create the dialog window
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Customer")
        layout = QFormLayout(dialog)
        # Input fields
        first_name_input = QLineEdit()
        last_name_input = QLineEdit()
        email_input = QLineEdit()
        phone_input = QLineEdit()
        # Adding widgets to the form
        layout.addRow("First Name:", first_name_input)
        layout.addRow("Last Name:", last_name_input)
        layout.addRow("Email:", email_input)
        layout.addRow("Phone (optional):", phone_input)
        # Save Button
        save_button = QPushButton("Save")
        layout.addRow(save_button)

        # Function to create customer
        def submit_customer():
            first_name = first_name_input.text()
            last_name = last_name_input.text()
            email = email_input.text()
            phone = phone_input.text()

            # Validate input data
            if not all([first_name, last_name, email]) or '@' not in email:
                QMessageBox.warning(dialog, "Invalid Input", "Check all the fields and provide valid inputs.")
                return

            ctrl = {
                "method": "post",
                "href": "/api/customers/"
            }

            # Setup the API request
            data = {
                "firstName": first_name,
                "lastName": last_name,
                "email": email,
                "phone": phone if phone else ""
            }
            try:
                s = requests.Session()
                r = self.send_request(s, ctrl, data)
                if r.status_code == 201:
                    # print(f"Customer created successfully: {first_name} {last_name}")
                    QMessageBox.information(dialog, "Success", f"Customer {first_name} {last_name} created successfully.")
                    dialog.accept()
                    self.get_customers()
                else:
                    QMessageBox.warning(dialog, "Failed", f"Unable to create customer: {r.text}")
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"An error occurred: {e}")

        save_button.clicked.connect(submit_customer)
        dialog.exec()


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
                item = QTableWidgetItem(str(p[key]))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.products_table.setItem(row, i, item)



    def edit_product(self):
        selected_indexes = self.products_table.selectionModel().selectedIndexes()
        if not selected_indexes:
            print("Please select a row to edit")
            self.statusBar().showMessage("Please select a row to edit")
            return

        row = selected_indexes[0].row()
        product_name = self.products_table.item(row, 0).text()
        href = self.products_dict["products"][row]["@controls"]["self"]["href"]

        with requests.Session() as s:
            # href = self.products_dict["@controls"]["self"]["href"]
            r = s.get(f"{self.API_URL}{href}")
            data = r.json()
            ctrl = data["@controls"]["edit"]
            # print(ctrl)

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Product")
        dialog_layout = QVBoxLayout(dialog)

        edit_fields = {}
        for i, key in enumerate(["name", "desc", "price"]):
            label = QLabel(key)
            dialog_layout.addWidget(label)
            line_edit = QLineEdit(self.products_table.item(row, i).text())
            dialog_layout.addWidget(line_edit)
            edit_fields[key] = line_edit

        def save_product():
            data = {key: line_edit.text() for key, line_edit in edit_fields.items()}
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
                    # message = r.json()["@error"]["@messages"][0]
                    # self.statusBar().showMessage(f"Error: {message}")
            except Exception as e:
                print(f"Error occurred: {e}")

        save_button = QPushButton("Save")
        dialog_layout.addWidget(save_button)
        save_button.clicked.connect(lambda: save_product())

        dialog.exec()



    def create_product(self):
        # Create the dialog window
        dialog = QDialog(self)
        dialog.setWindowTitle("Create Product")
        layout = QFormLayout(dialog)
        # Input fields
        name_input = QLineEdit()
        desc_input = QLineEdit()
        price_input = QLineEdit()
        quantity_input = QLineEdit()
        # Adding widgets to the form
        layout.addRow("Name:", name_input)
        layout.addRow("Description:", desc_input)
        layout.addRow("Price:", price_input)
        layout.addRow("Stock quantity:", quantity_input)
        # Save Button
        save_button = QPushButton("Save")
        layout.addRow(save_button)

        # Function to create customer
        def submit_product():
            name = name_input.text()
            desc = desc_input.text()
            price = price_input.text()

            # Validate input data
            if not all([name, desc, price]):
                QMessageBox.warning(dialog, "Invalid Input", "Check all the fields and provide valid inputs.")
                return

            ctrl = {
                "method": "post",
                "href": "/api/products/"
            }

            # Setup the API request
            data = {
                "name": name,
                "desc": desc,
                "price": float(price)
            }
            try:
                s = requests.Session()
                r = self.send_request(s, ctrl, data)
                if r.status_code == 201:
                    # print(f"Customer created successfully: {first_name} {last_name}")
                    QMessageBox.information(dialog, "Success", f"Product {name} created successfully.")
                    product_id = r.headers["Location"].rstrip('/').split('/')[-1]
                    create_stock_entry(product_id)
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Failed", f"Unable to create product: {r.text}")
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"An error occurred: {e}")

        def create_stock_entry(product_id):
            quantity = quantity_input.text()
            if not quantity:
                QMessageBox.warning(dialog, "Invalid Input", "Please provide a stock quantity.")
                return
            ctrl = {
                "method": "post",
                "href": "/api/stock/"
            }
            data = {
                "productId": int(product_id),
                "quantity": float(quantity)
            }
            try:
                s = requests.Session()
                r = self.send_request(s, ctrl, data)
                if r.status_code == 201:
                    print(f"Stock entry created successfully")
                    self.get_products()
                    self.get_stock()
                else:
                    print(f"Failed to create stock entry: {r.text}")
                    QMessageBox.warning(dialog, "Failed", f"Failed to create stock entry: {r.text}")
                    message = r.json()["@error"]["@messages"][0]
                    self.statusBar().showMessage(f"Error: {message}")
            except Exception as e:
                print(f"Error occurred: {e}")
                QMessageBox.critical(dialog, "Error", f"An error occurred: {e}")

        save_button.clicked.connect(lambda: submit_product())
        dialog.exec()

    def delete_product(self):
        selected_indexes = self.products_table.selectionModel().selectedIndexes()
        if not selected_indexes:
            print("Please select a row to delete")
            self.statusBar().showMessage("Please select a row to delete")
            return

        row = selected_indexes[0].row()
        product_name = self.products_table.item(row, 0).text()
        href = self.products_dict["products"][row]["@controls"]["self"]["href"]

        dialog = QDialog(self)
        dialog.setWindowTitle("Are you sure?")
        dialog_layout = QHBoxLayout(dialog)
        yes_button = QPushButton("Yes")
        no_button = QPushButton("No")
        dialog_layout.addWidget(yes_button)
        dialog_layout.addWidget(no_button)

        def delete_product_confirm():
            with requests.Session() as s:
                r = s.delete(f"{self.API_URL}{href}")
                if r.status_code == 204:
                    QMessageBox.information(dialog, "Success", f"Product {product_name} deleted successfully")
                    print(f"Product {product_name} deleted successfully")
                    self.statusBar().showMessage(f"Product {product_name} deleted successfully")
                    self.get_products()
                    self.get_stock()
                    dialog.accept()
                else:
                    QMessageBox.warning(dialog, "Failed", f"Failed to delete Product {product_name}: {r.text}")
                    print(f"Failed to delete Product {product_name}: {r.text}")
                    dialog.reject()

        yes_button.clicked.connect(lambda: delete_product_confirm())
        no_button.clicked.connect(dialog.reject)

        dialog.exec()

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
                item = QTableWidgetItem(str(p[key]))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.stock_table.setItem(row, i, item)



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
            # print(ctrl)

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Stock")
        dialog_layout = QVBoxLayout(dialog)

        edit_fields = {}
        for i, key in enumerate(["productId", "quantity"]):
            label = QLabel(key)
            dialog_layout.addWidget(label)
            line_edit = QLineEdit(self.stock_table.item(row, i).text())
            dialog_layout.addWidget(line_edit)
            edit_fields[key] = line_edit

        def save_stock():
            data = {key: line_edit.text() for key, line_edit in edit_fields.items()}
            data["quantity"] = float(data["quantity"])
            data["productId"] = int(data["productId"])
            s = requests.Session()
            try:
                r = self.send_request(s, ctrl, data)
                if r.status_code == 204:
                    print("Stock entry updated successfully")
                    self.statusBar().showMessage("Stock entry updated successfully")
                    dialog.accept()
                    self.get_stock() # Update view
                else:
                    print(f"Failed to update stock: {r.text}")
                    message = r.json()["@error"]["@messages"][0]
                    self.statusBar().showMessage(f"Error: {message}")
            except Exception as e:
                print(f"Error occurred: {e}")

        save_button = QPushButton("Save")
        dialog_layout.addWidget(save_button)
        save_button.clicked.connect(lambda: save_stock())

        dialog.exec()



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