# backend/database.py
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv() 

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "mydatabase")

client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB_NAME]

# Collections
user_collection = db["users"]
shipment_collection = db["shipments"]
device_collection = db["devices"]
