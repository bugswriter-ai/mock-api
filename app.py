from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
import os

# Initialize the Flask app
app = Flask(__name__)

# --- Configuration ---
# Replace with your actual MongoDB connection string
# IMPORTANT: This must be set as an environment variable (e.g., in Vercel or your local shell)
MONGO_URI = "mongodb+srv://sapangajjar101105:sAPANGAJJAR01@cluster0.roa0j9q.mongodb.net/" #os.getenv('MONGO_URI')

if not MONGO_URI:
    # Raise a clear error if the URI is not found. This is often the cause of 500 errors.
    raise ValueError("No MONGO_URI environment variable set. Please configure it.")

# Specify the database and collection
DB_NAME = "test"
COLLECTION_NAME = "ner_results"

# --- Utility Functions ---

def get_mongo_collection():
    """Establishes MongoDB connection and returns the collection."""
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return client, db[COLLECTION_NAME]

# --- Routes ---

@app.route('/')
def home():
    """
    Renders the HTML form for the user interface (if you have an index.html).
    If not, it just returns a status message.
    """
    return jsonify({"status": "Areax Bridge operational. Use /fetch_data or /update_coordinates endpoints."}), 200

@app.route('/fetch_data', methods=['GET'])
def fetch_data():
    """
    Connects to MongoDB and fetches documents that DO NOT have coordinates.
    The query filters for documents where 'coordinates' is missing or empty.
    """
    client = None
    try:
        client, collection = get_mongo_collection()

        # Query to filter out documents that already have coordinates.
        # This checks for documents where the 'coordinates' field does NOT exist, OR
        # where the 'coordinates' field exists but is an empty array (length 0).
        query = {
            "$or": [
                {"coordinates": {"$exists": False}},
                {"coordinates": {"$size": 0}}
            ]
        }

        # Fetch filtered documents and convert ObjectId to a string for JSON serialization
        data = list(collection.find(query))
        for document in data:
            # Convert ObjectId to string for all documents fetched
            if '_id' in document:
                document['_id'] = str(document['_id'])

        return jsonify(data), 200

    except Exception as e:
        print(f"An error occurred during fetch_data: {e}")
        # Return a 500 error with the exception details for debugging
        return jsonify({"error": "A server error has occurred", "details": str(e)}), 500
    finally:
        if client:
            client.close()


@app.route('/update_coordinates', methods=['POST'])
def update_coordinates():
    """
    Receives a POST request and updates the coordinates for a given document ID.
    It attempts to match the ID as both an ObjectId (_id) and a string ID (id).
    """
    client = None
    try:
        # Get the JSON data from the request body
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        # Extract id and coordinates
        document_id = data.get('id')
        new_coordinates = data.get('coordinates')

        if not document_id or not new_coordinates:
            return jsonify({"error": "Missing 'id' or 'coordinates' in request"}), 400

        client, collection = get_mongo_collection()
        
        query = None
        
        # 1. Attempt to query using MongoDB ObjectId (for the '_id' field)
        try:
            object_id = ObjectId(document_id)
            query = {"_id": object_id}
        except InvalidId:
            # 2. If it's not a valid ObjectId, assume it's a string ID (for the 'id' field)
            print(f"ID '{document_id}' is not a valid ObjectId, querying by string 'id' field.")
            query = {"id": document_id}
        
        # Define the update operation
        update = {"$set": {"coordinates": new_coordinates}}

        # Perform the update operation
        result = collection.update_one(query, update)

        # Check if the document was modified
        if result.modified_count > 0:
            return jsonify({"message": f"Successfully updated document with ID: {document_id}"}), 200
        else:
            # Also check if it was matched but not modified (e.g., if coordinates were identical)
            if result.matched_count > 0:
                 return jsonify({"message": f"Document matched but coordinates were already set or identical for ID: {document_id}"}), 200
            else:
                 return jsonify({"message": f"No document found matching ID: {document_id}"}), 404

    except Exception as e:
        print(f"An error occurred during update_coordinates: {e}")
        return jsonify({"error": "A server error has occurred", "details": str(e)}), 500
    finally:
        if client:
            client.close()

# --- Main entry point to run the app ---
if __name__ == '__main__':
    # Run in debug mode locally, but ensure debug=False for production hosting (like Vercel)
    app.run(debug=True)
