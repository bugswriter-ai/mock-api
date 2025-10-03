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
# NOTE: Using the hardcoded URI for demonstration purposes as requested, but recommend using os.getenv()
MONGO_URI = "mongodb+srv://sapangajjar101105:sAPANGAJJAR01@cluster0.roa0j9q.mongodb.net/" #os.getenv('MONGO_URI')

if not MONGO_URI:
    # Raise a clear error if the URI is not found. This is often the cause of 500 errors.
    raise ValueError("No MONGO_URI environment variable set. Please configure it.")

# Specify the databases and collections
DB_NAME = "test"
USERS_COLLECTION_NAME = "users"        # For user authentication
NER_RESULTS_COLLECTION_NAME = "ner_results" # For your main data

# --- Utility Functions ---

def get_mongo_client_db():
    """Establishes MongoDB connection and returns the client and database object."""
    client = MongoClient(MONGO_URI)
    # The client must be closed in a finally block in the route handlers
    db = client[DB_NAME]
    return client, db

def get_users_collection():
    """Returns the client and the dedicated users collection for authentication."""
    client, db = get_mongo_client_db()
    return client, db[USERS_COLLECTION_NAME]

def get_ner_collection():
    """Returns the client and the main ner_results collection."""
    client, db = get_mongo_client_db()
    return client, db[NER_RESULTS_COLLECTION_NAME]

# --- Routes ---

@app.route('/')
def home():
    """
    Returns a status message and instructions.
    """
    return jsonify({"status": "Areax Bridge operational. Use /authenticate to log in."}), 200

# -----------------------------------------------------------------
# NEW AUTHENTICATION ROUTE
# -----------------------------------------------------------------
@app.route('/authenticate', methods=['POST'])
def authenticate():
    """
    Authenticates a user by checking the provided 'user' and 'key' against
    documents in the 'test.users' collection.
    """
    client = None
    try:
        data = request.get_json()
        user_name = data.get('user')
        access_key = data.get('key')

        # Basic input validation
        if not user_name or not access_key:
            return jsonify({"authenticated": False, "message": "Missing 'user' or 'key' in request"}), 400

        # Get the users collection
        client, users_collection = get_users_collection()

        # IMPORTANT SECURITY NOTE:
        # Checking passwords/keys directly is highly insecure. In a production app,
        # you MUST store a hashed version of the key (using bcrypt/Argon2) and compare
        # the hash of the provided key against the stored hash.

        # Query the database for the matching user and key
        user_document = users_collection.find_one({
            "user": user_name,  # Matches the 'user' field in your document
            "key": access_key   # Matches the 'key' field in your document
        })

        if user_document:
            # Authentication successful
            return jsonify({
                "authenticated": True, 
                "user": user_name, 
                "message": "Authentication successful"
            }), 200
        else:
            # Authentication failed
            return jsonify({
                "authenticated": False, 
                "message": "Invalid credentials"
            }), 401

    except Exception as e:
        print(f"Authentication error: {e}")
        return jsonify({
            "authenticated": False, 
            "message": "Server error during authentication", 
            "details": str(e)
        }), 500
    finally:
        if client:
            client.close()
# -----------------------------------------------------------------


@app.route('/fetch_data', methods=['GET'])
def fetch_data():
    """
    Connects to MongoDB and fetches documents that DO NOT have coordinates.
    """
    client = None
    try:
        client, collection = get_ner_collection() # Using the new collection getter

        # Query to filter out documents that already have coordinates.
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

        client, collection = get_ner_collection() # Using the new collection getter
        
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
            # Check if it was matched but not modified (e.g., if coordinates were identical)
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
