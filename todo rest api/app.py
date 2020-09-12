from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import uuid
# from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import jwt # create a jason web token
from functools import wraps


app = Flask(__name__)  
db = SQLAlchemy(app)  #creating the istance of database
# bcrypt = Bcrypt(app)


# configuring the flask app
app.config['SECRET_KEY'] = '2b0d8b00f94a994b9c08a152beb82e1a'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tmp/tmp.db' # giving the location for the app to create the database

# Creating the data base model
# Creating the user model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(60), unique=True)
    name = db.Column(db.String(25), unique=True)
    password = db.Column(db.String(80))
    admin = db.Column(db.Boolean)

# Creating the todo model
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(200))
    complete = db.Column(db.Boolean)
    user_id = db.Column(db.Integer)

# db.create_all()  # creating the database ; this command to be used only once or it will be overwritten

# creating a wrapping function to check whether the user is autherized
def token_required(f) :
    @wraps(f)
    def decorated(*args, **kwargs) :
        token = None
        if 'x-access-token' in request.headers:          # Checking whether the header x-access-token is present in header
            token = request.headers['x-access-token']    # Getting the token from header
        if not token :
            return jsonify({'message' : 'Token invalid!!!!!!'}), 401  # If token doesnot exist
        try :
            data = jwt.decode(token, app.config['SECRET_KEY'])  # Decoding the token into jason having public_id , name, etc etc
            current_user = User.query.filter_by(public_id=data['public_id']).first() # querying the database whether it has the public_id from the token
        except:
            return jsonify({'message' : 'Token invalid!!!!!!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated


# Creating the routes for user
# This route displays the all users in database
@app.route('/user', methods=['GET'])    # by default it does GET method
@token_required
def get_all_user(current_user):  # 
    if not current_user.admin :
        return jsonify({'Message' : 'Cannot perform the action'})
    users = User.query.all()
    output=[]
    for user in users:
        user_data = {}
        user_data['public_id'] = user.public_id  # particular record . is used (from database)
        print(type(user.password))
        user_data['name'] = user.name
        user_data['password'] = user.password
        user_data['admin'] = user.admin
        output.append(user_data)
    
    return jsonify({'users': output})

# This route is used to create Users
@app.route('/user', methods=['POST'])
@token_required
def create_user(current_user):  #
    if not current_user.admin :
        return jsonify({'Message' : 'Cannot perform the action'})
    data = request.get_json()

    hashed_password = generate_password_hash(data['password'], method='sha256')
    user = User(public_id=str(uuid.uuid4()), 
                name=data['name'],
                password=hashed_password, 
                admin=False)

    db.session.add(user)
    db.session.commit()
    return jsonify({'message':"The user is created!!!"})

# This route is used to get one user from database
@app.route('/user/<public_id>')
@token_required
def get_one_user(current_user, public_id):
    if not current_user.admin :
        return jsonify({'Message' : 'Cannot perform the action'})
    user = User.query.filter_by(public_id=public_id).first()
    if not user :
        return jsonify({"message" : "No user found!!"})
    user_data = {}
    user_data['public_id'] = user.public_id  # particular record . is used (from database)
    user_data['name'] = user.name
    user_data['password'] = user.password
    user_data['admin'] = user.admin
    return jsonify({'user': user_data})    

# This route is used to promote user to become an admin
@app.route('/user/<public_id>', methods=['PUT'])
@token_required
def promote_user(current_user, public_id):
    if not current_user.admin :
        return jsonify({'Message' : 'Cannot perform the action'})
    user = User.query.filter_by(public_id=public_id).first()
    if not user :
        return jsonify({"message" : "No user found!!"})
    user.admin = True
    # db.session.add(user)  no need to add what is already added
    db.session.commit()
    return jsonify({'message':'The user has been promoted!!! he is now admin'})

# This route is to delete the User
@app.route('/user/<public_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, public_id):
    if not current_user.admin :
        return jsonify({'Message' : 'Cannot perform the action'})
    user = User.query.filter_by(public_id=public_id).first()
    if not user :
        return jsonify({"message" : "No user found!!"})
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message':'That user has been "deleted"!!!!'})

# Route for logging in by token (jason web token)
@app.route('/login')
def login():
    auth = request.authorization
    if not auth or not auth.username or not auth.password:
        return make_response('could not verify', 
            401, 
            {'WWW-Authenticate':'basic realm="Login Required!"'}) 
    user = User.query.filter_by(name=auth.username).first()
    if not user :
        return make_response('could not verify', 
            401, 
            {'WWW-Authenticate':'basic realm="Login Required!"'}) 
    if check_password_hash(user.password, auth.password):
        token = jwt.encode({'public_id' : user.public_id, 
            'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)},
            app.config['SECRET_KEY'])
        return jsonify({'token' : token.decode('UTF-8')})
    
    return make_response('could not verify', 
            401, 
            {'WWW-Authenticate':'basic realm="Login Required!"'}) 


@app.route('/todo')
@token_required
def get_all_todo(current_user):
    todos = Todo.query.filter_by(user_id=current_user.id).all()
    output = []
    for todo in todos:
        data_todo = {}
        data_todo['id'] = todo.id
        data_todo['text'] = todo.text
        data_todo['complete'] = todo.complete
        output.append(data_todo)
    return jsonify({'todos' : output})

@app.route('/todo', methods=['POST'])
@token_required
def create_todo(current_user):
    data = request.get_json()
    new_todo = Todo(text=data['text'], complete=False, user_id=current_user.id)
    db.session.add(new_todo)
    db.session.commit()
    return jsonify({'message' : 'Todo Created!!!'})

@app.route('/todo/<todo_id>')
@token_required
def get_one_todo(current_user, todo_id) :
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first() # Current_user_id because we dont wnat others to see other peoples id
    if not todo :
        return jsonify({'Message' : 'No todos found!!!'})
    data_todo = {}
    data_todo['id'] = todo.id
    data_todo['text'] = todo.text
    data_todo['complete'] = todo.complete

    return jsonify({data_todo})

@app.route('/todo/<todo_id>', methods=['PUT'])
@token_required
def complete_todo(current_user, todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first() # Current_user_id because we dont wnat others to see other peoples id
    if not todo :
        return jsonify({'Message' : 'No todos found!!!'}) 
    todo.completed = True
    db.session.commit()

    return jsonify({'Message' : 'Todo item is complete!!'})

@app.route('/todo/<todo_id>', methods=['DELETE'])
@token_required
def delete_todo(current_user, todo_id):
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first() # Current_user_id because we dont wnat others to see other peoples id
    if not todo :
        return jsonify({'Message' : 'No todos found!!!'}) 
    db.session.delete(todo)
    db.session.commit()    
    return jsonify({"Message" : "Todo item deleted!!!!"})



if __name__ == '__main__' :
    app.run(debug=True)