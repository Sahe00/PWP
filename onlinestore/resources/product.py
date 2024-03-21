import json
from sqlalchemy.exc import IntegrityError
from flask import Response, request, url_for
from flask_restful import Resource
from jsonschema import ValidationError, draft7_format_checker, validate
from werkzeug.exceptions import BadRequest
from onlinestore import db
from onlinestore.models import Product
from onlinestore.api import *


MASON = "application/vnd.mason+json"
LINK_RELATIONS_URL = "/storage/link-relations/"
ERROR_PROFILE = "/profiles/error/"
PRODUCT_PROFILE = "/profiles/product/"


class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

    def add_control_post(self, ctrl_name, title, href, schema):
        """
        Utility method for adding POST type controls. The control is
        constructed from the method's parameters. Method and encoding are
        fixed to "POST" and "json" respectively.

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        self.add_control(
            ctrl_name,
            href,
            method="POST",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_put(self, title, href, schema):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control name, method and
        encoding are fixed to "edit", "PUT" and "json" respectively.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        self.add_control(
            "edit",
            href,
            method="PUT",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_delete(self, title, href):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control method is fixed to
        "DELETE", and control's name is read from the class attribute
        *DELETE_RELATION* which needs to be overridden by the child class.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        """

        self.add_control(
            "mumeta:delete",
            href,
            method="DELETE",
            title=title,
        )


class InventoryBuilder(MasonBuilder):
    def add_control_all_products(self):
        self.add_control(
            "storage:products-all",
            url_for(ProductCollection),
            method="GET"
        )

    def add_control_delete_product(self, product):
        self.add_control(
            "storage:delete",
            url_for(ProductItem, name=product.name),
            method="DELETE"
        )

    def add_control_add_product(self):
        self.add_control(
            "storage:add-product",
            url_for(ProductCollection),
            method="POST",
            encoding="json",
            schema=Product.json_schema()
        )

    def add_control_edit_product(self, product):
        self.add_control(
            "edit",
            url_for(ProductItem, name=product.name),
            method="PUT",
            encoding="json",
            schema=Product.json_schema()
        )
        

class ProductCollection(Resource):

    # Get list of all products (returns a Mason document)
    def get(self):
        body = InventoryBuilder()
        body["items"] = []

        body.add_namespace("storage", LINK_RELATIONS_URL)
        body.add_control("self", href=url_for(ProductCollection))
        body.add_control_all_products()  # GET
        body.add_control_add_product()  # POST

        try:
            for product in db.session.query(Product).all():
                item = MasonBuilder(product.serialize())
                item.add_control("self", href=url_for(ProductItem, name=product.name))
                item.add_control("profile", PRODUCT_PROFILE)
                body["items"].append(item)

            return Response(json.dumps(body), 200, mimetype=MASON)
        except Exception as e:
            return f"Error: {e}", 500

        # try:
        #    result = []
        #    for product in db.session.query(Product).all():
        #        p_info = {"name": "", "desc": "", "price": 0.0}
        #        p_info["name"] = product.name
        #        p_info["desc"] = product.desc
        #        p_info["price"] = product.price
        #        result.append(p_info)
        #    return result, 200
        # except Exception as e:
        #    return f"Error: {e}", 500

    # Creates a new product to the database
    def post(self):
        try:
            name = request.json["name"]
            if name is None:
                return "Request content type must be JSON", 415

            # Validate the JSON document against the schema
            try:
                validate(request.json, Product.json_schema(), format_checker=draft7_format_checker)
            except ValidationError as e:
                raise BadRequest(description=str(e))  # 400 Bad request

            if db.session.query(Product).filter(Product.name == name).first():
                return "Product already exists", 409
            try:
                product = Product()
                product.deserialize(request.json)
            except ValueError:
                return "Invalid request body", 400
            try:
                # product = Product(name=name, desc=desc, price=price)
                db.session.add(product)
                db.session.commit()

                product_uri = url_for("api.productcollection", name=product.name)

                return Response(status=201, headers={"Location": product_uri})  # Created
            except Exception as e:  # IntegrityError:
                db.session.rollback()
                return f"Incomplete request - missing fields - {e}", 500
        except (KeyError, ValueError):
            return "Invalid request body", 400


class ProductItem(Resource):

    # Retrieves information from a specific product
    def get(self, name):
        return name.serialize()

    # Deletes a product from the database
    def delete(self, name):
        try:
            db.session.delete(name)
            db.session.commit()

            return Response(status=204)
        except IntegrityError:
            return "Product not found", 404

    # Updates product information to the database
    def put(self, name):
        if not request.json:
            return "Unsupported media type", 415

        try:
            validate(request.json, Product.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        try:
            name.deserialize(request.json)
            db.session.add(name)
            try:
                db.session.commit()
            except IntegrityError:
                return "Database error", 500

            return Response(status=200)
        except IntegrityError:
            return "Product not found", 404
