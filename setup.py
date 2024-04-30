'''
Setup file for the onlinestore package.
'''
from setuptools import find_packages, setup

setup(
    name='onlinestore',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'requests',
        'pyside6',
        'flasgger',
        'flask',
        "flask-restful",
        "flask-sqlalchemy",
        "pytest",
        "pytest-coverage",
        "jsonschema",
    ],
)
