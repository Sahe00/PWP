# PWP SPRING 2024
# ONLINESTORE API
# Group information
* Student 1. Aleksi Rehu arehu20@student.oulu.fi
* Student 2. Arimo Pukari apukari@student.oulu.fi
* Student 3. Santeri Heikkinen saheikki20@student.oulu.fi
* Student 4. Tomi Pantsar tpantsar20@student.oulu.fi

<!--__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__-->

<!--
Instructions how to setup the database framework and external libraries you might have used, or a link where it is clearly explained.
Instructions on how to setup and populate the database.
-->

# Information

## Libraries

Onlinstore uses Flask SQLAlchemy's version of SQLite for the database. 

Libraries:
- flask
- flask-restful
- flask-sqlalchemy
- flasgger
- jsonschema
- pytest
- pytest-coverage

# How to start
## Required libraries can be installed with pip:
    pip install -e .

## Setup database

__Only one of the following should be run.__

### To create an empty database, run this:
    python tests/createdatabase.py

### To create database with test data, run this:
    python tests/createdatabase.py fill

## Run API

### Set Flask variables
    set FLASK_APP=onlinestore

### Run
    flask run