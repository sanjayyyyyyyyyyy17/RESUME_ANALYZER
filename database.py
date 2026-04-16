import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)

# Database
db = client.resume_analyzer

# Collections
submissions_collection = db.submissions

def get_submissions_collection():
    return submissions_collection
