from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

# Initialize the Flask app
app = Flask(__name__)

# Replace with your actual MongoDB connection string
MONGO_URI = os.getenv('MONGO_URI')

if not MONGO_URI:
    # This will prevent the app from running if the variable is not set
    raise ValueError("No MONGO_URI environment variable set.")


# Specify the database and collection you want to access
DB_NAME = "test"
COLLECTION_NAME = "ner_results"

# --- New Route for the Home Page ---
@app.route('/')
def home():
    """
    Renders the HTML form for the user interface.
    """
    return render_template('index.html')

# --- MODIFIED Route to fetch and display data (GET request) ---
@app.route('/fetch_data', methods=['GET'])
def fetch_data():
    """
    Connects to MongoDB, fetches documents that DO NOT have coordinates,
    and returns them as JSON.
    """
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        # MODIFICATION: Filter documents where 'coordinates' is null, not present, or an empty array.
        # $or: Match documents where
        # 1. 'coordinates' field does not exist ($exists: false)
        # 2. 'coordinates' field exists but is null ({"coordinates": None})
        # 3. 'coordinates' field exists but is an empty array ({"coordinates": []})
        query = {
            "$or": [
                {"coordinates": {"$exists": False}},
                {"coordinates": None},
                {"coordinates": {"$size": 0}}
            ]
        }

        # Fetch filtered documents and convert ObjectId to a string for JSON serialization
        data = list(collection.find(query))
        for document in data:
            document['_id'] = str(document['_id'])

        client.close()
        return jsonify(data), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": f"An error occurred: {e}"}), 500

# --- Existing Route to update coordinates (POST request) ---
@app.route('/update_coordinates', methods=['POST'])
def update_coordinates():
    """
    Receives a POST request and updates the coordinates for a given document ID.
    """
    try:
        # Get the JSON data from the request body
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        # Extract id and coordinates from the JSON data
        document_id = data.get('id')
        new_coordinates = data.get('coordinates')

        if not document_id or not new_coordinates:
            return jsonify({"error": "Missing 'id' or 'coordinates' in request"}), 400

        # Convert the string id to a MongoDB ObjectId
        try:
            object_id = ObjectId(document_id)
        except Exception:
            # Assumes the 'id' field passed from Flutter is the MongoDB document's '_id'
            # If the original database design uses a string ID that is NOT ObjectId, this try/except might need adjustment.
            # Assuming it's the string representation of an ObjectId for now.
            try:
                object_id = ObjectId(document_id)
            except:
                 # Fallback to querying by the string 'id' field if ObjectId conversion fails
                 client = MongoClient(MONGO_URI)
                 db = client[DB_NAME]
                 collection = db[COLLECTION_NAME]
                 query = {"id": document_id} # Assuming there is a field named 'id' that holds the value
                 
                 # Define the update operation
                 update = {"$set": {"coordinates": new_coordinates}}

                 # Perform the update operation
                 result = collection.update_one(query, update)

                 client.close()
                 if result.modified_count > 0:
                     return jsonify({"message": f"Successfully updated document with id (string): {document_id}"}), 200
                 else:
                    return jsonify({"message": f"No document found or no changes made for id (string): {document_id}"}), 404
        

        # Connect to MongoDB
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]

        # Define the query and the update operation
        query = {"_id": object_id}
        update = {"$set": {"coordinates": new_coordinates}}

        # Perform the update operation
        result = collection.update_one(query, update)

        # Close the connection
        client.close()

        # Check if the document was modified
        if result.modified_count > 0:
            return jsonify({"message": f"Successfully updated document with id: {document_id}"}), 200
        else:
            return jsonify({"message": f"No document found or no changes made for id: {document_id}"}), 404

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": f"An error occurred: {e}"}), 500

# --- Main entry point to run the app ---
if __name__ == '__main__':
    app.run(debug=True)
