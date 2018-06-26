from pymongo import MongoClient

conn = MongoClient('127.0.0.1', 27017)
db = conn.Products
products = db.product
products_part = db.products_part
request_fail = db.request_fail

