from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
import logging  # helps track what's happening during deletion

# Create a Flask application instance
app = Flask(__name__)

# Configure the SQLite database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///items.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create a SQLAlchemy object
db = SQLAlchemy(app)

# Define a database model for items
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)

# Initialize the database
with app.app_context():
    db.create_all()

# Configure logging
logging.basicConfig(
    filename='app.log',  # Name of the log file
    level=logging.INFO,  # Minimum level of logs to record
    format='%(asctime)s - %(levelname)s - %(message)s'  # Log format
)

# GET request (retrieve information)
@app.route('/items', methods=['GET'])
def get_items():
    items = Item.query.all()
    return jsonify([{"id": item.id, "name": item.name} for item in items])

# POST request (create a new item)
@app.route('/items', methods=['POST'])
def create_item():
    try:
        new_item = request.json.get('item')
        if not new_item:
            return jsonify({"error": "Item name is required"}), 400  # Bad Request

        item = Item(name=new_item)
        db.session.add(item)
        db.session.commit()
        return jsonify({"id": item.id, "name": item.name}), 201  # Created

    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the transaction if there's an error
        return jsonify({"error": "Database error occurred"}), 500  # Internal Server Error

# PUT request (update an existing item)
@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    try:
        item = db.session.get(Item, item_id)
        if item:
            new_name = request.json.get('item')
            if not new_name or len(new_name) < 1:  # Validation: make sure new name is valid
                return jsonify({"error": "Item name must be at least 1 character long"}), 400  #Bad Request

            item.name = new_name
            db.session.commit()
            return jsonify({"id": item.id, "name": item.name}), 200
        else:
            return jsonify({"error":"Item not found"}), 404

    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the transaction if there's an error
        return jsonify({"error": "Database error occurred"}), 500  # Internal Server Error

# DELETE request (remove an item)
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    try:
        item = db.session.get(Item, item_id)
        if item:
            db.session.delete(item)
            db.session.commit()
            logging.info(f"Deleted item with ID {item_id}")
            return jsonify({"message": f"Deleted item {item.name}"}), 200
        else:
            logging.warning(f"Attempted to delete non-existent item with ID {item_id}")
            return jsonify({"error": "Item not found"}), 404

    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback the transaction if there's an error
        logging.error(f"Database error during deletion: {e}")
        return jsonify({"error": "Database error occurred"}), 500  # Internal Server Error

# Run the application
if __name__ == '__main__':
    app.run(debug=True, port=8080)  # Flask will now run on port 8080
