
from database import get_submissions_collection
import os
from dotenv import load_dotenv

load_dotenv()

def check_db():
    coll = get_submissions_collection()
    count = coll.count_documents({})
    print(f"Total submissions in DB: {count}")
    
    # Check status distribution
    statuses = coll.aggregate([
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ])
    print("Status distribution:")
    for s in statuses:
        print(f"  {s['_id']}: {s['count']}")

if __name__ == "__main__":
    check_db()
