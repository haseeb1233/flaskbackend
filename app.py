from datetime import datetime
from flask import Flask, jsonify,render_template, request,redirect
from flask_sqlalchemy import SQLAlchemy

app=Flask(__name__)

# connecting with mysql
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:ktbeesahludba%40123@localhost/zomato_chronicle'



db = SQLAlchemy(app)


# Assuming you have an association table named 'order_items'

order_items = db.Table('order_items',
    db.Column('order_id', db.Integer, db.ForeignKey('orders.id'), primary_key=True),
    db.Column('menu_item_id', db.Integer, db.ForeignKey('menu_items.id'), primary_key=True)
)

# schema for menuitems
class MenuItem(db.Model):
    __tablename__ = 'menu_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    availability = db.Column(db.Boolean, default=True)

    def __init__(self, name, description, price, availability=True):
        self.name = name
        self.description = description
        self.price = price
        self.availability = availability

    def __json__(self):
        # Define a custom dictionary representation for the MenuItem
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'availability': self.availability
        }




# schema order
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    order_time = db.Column(db.DateTime, default=datetime.utcnow)

    # Define the many-to-many relationship with MenuItem
    items = db.relationship('MenuItem', secondary=order_items, backref=db.backref('orders', lazy='select'))

    def __init__(self, customer_name, status='received'):
        self.customer_name = customer_name
        self.status = status

    def __json__(self):
        # Define a custom dictionary representation for the Order
        self.items = self.items 
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'status': self.status,
            'order_time': self.order_time.isoformat(),
            'items': [{'id': item.id, 'name': item.name, 'price': item.price} for item in self.items]
        }







# view menu
@app.route('/menu')
def get_menu():
    menu_items = MenuItem.query.all()
    return jsonify([item.__json__() for item in menu_items])

# add to menu
@app.route('/addmenu', methods=['POST'])
def create_menu_item():
    data = request.get_json()
    new_menu_item = MenuItem(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        availability=data['availability']
    )
    db.session.add(new_menu_item)
    db.session.commit()
    return jsonify({'message': 'Menu item created successfully'}), 201   
   

# update menu
@app.route('/updatemenu/<int:menu_item_id>', methods=['PUT'])
def update_menu_item(menu_item_id):
    data = request.get_json()
    menu_item = MenuItem.query.get(menu_item_id)
    if not menu_item:
        return jsonify({'message': 'Menu item not found'}), 404

    menu_item.name = data['name']
    menu_item.description = data['description']
    menu_item.price = data['price']
    menu_item.availability = data['availability']

    db.session.commit()
    return jsonify({'message': 'Menu item updated successfully'})



# delete menu
@app.route('/demenu/<int:menu_item_id>', methods=['DELETE'])
def delete_menu_item(menu_item_id):
    menu_item = MenuItem.query.get(menu_item_id)
    if not menu_item:
        return jsonify({'message': 'Menu item not found'}), 404

    db.session.delete(menu_item)
    db.session.commit()
    return jsonify({'message': 'Menu item deleted successfully'})

# orders

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    customer_name = data['customer_name']
    item_ids = data['items']  # Assuming 'items' is a list of menu item IDs

    # Create a new order
    new_order = Order(customer_name=customer_name)

    # Query the database for the MenuItems with the given IDs
    menu_items = MenuItem.query.filter(MenuItem.id.in_(item_ids)).all()

    # Add the menu items to the order
    new_order.items.extend(menu_items)

    # Add the order to the database
    db.session.add(new_order)
    db.session.commit()

    return jsonify({'message': 'Order recorded successfully'}), 201



@app.route('/orders', methods=['GET'])
def get_orders():
    # Query the database to retrieve all orders
  orders = Order.query.all()

    # Create a list to store the JSON representations of the orders
  orders_list = []

    # Loop through the orders and convert them to JSON
  for order in orders:
     orders_list.append(order.__json__())  # Using the __json__ method you defined

    # Return the list of orders as JSON
  return jsonify(orders_list), 200

# update
@app.route('/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    # Get the order by its ID
    order = Order.query.get(order_id)
    print(order)
    # Check if the order with the given ID exists
    if not order:
        return jsonify({'error': 'Order not found'}), 404

    # Parse the JSON data from the request
    data = request.get_json()

    # Update the order attributes based on the data in the request
    if 'customer_name' in data:
        order.customer_name = data['customer_name']
    if 'status' in data:
        order.status = data['status']

    # Commit the changes to the database
    db.session.commit()

    # Return a success response
    return jsonify({'message': 'Order updated successfully'}), 200


@app.route('/customerorders', methods=['GET'])
def get_orders_by_customer():
    # Get the customer_name from the query parameter
    customer_name = request.args.get('customer_name')

    if not customer_name:
        return jsonify({'error': 'Customer name parameter is required'}), 400

    # Query the database to retrieve orders by customer name
    orders = Order.query.filter_by(customer_name=customer_name).all()

    if not orders:
        return jsonify({'message': 'No orders found for the customer'}), 404

    # Convert the orders to JSON format
    orders_json = [order.__json__() for order in orders]

    # Return the list of orders
    return jsonify({'orders': orders_json}), 200







