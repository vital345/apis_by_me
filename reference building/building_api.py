from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource, reqparse, abort, fields, marshal_with


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db' # new
db = SQLAlchemy(app)
api = Api(app)

# arguments in the api url 
app_put_args = reqparse.RequestParser()
# app_put_args.add_argument('id', type=int, help='id invalid', required=True)
app_put_args.add_argument('title', type=str, help='title invalid', required=True)
app_put_args.add_argument('content', type=str, help='content invalid', required=True)

app_update_args = reqparse.RequestParser()
app_update_args.add_argument('id', type=int, help='id invalid')
app_update_args.add_argument('title', type=str, help='title invalid')
app_update_args.add_argument('content', type=str, help='content invalid')


# creating the database model
class databaseModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    content = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'id = {id} \n title = {title} \n content = {content}'

resource_fields = {
    'id' : fields.Integer,
    'title' : fields.String,
    'content' : fields.String
}

# db.create_all() # only once otherwise it overwrites the db

class createapi(Resource) :
    '''get function'''
    @marshal_with(resource_fields)
    def get(self, thing_id) :
        result = databaseModel.query.filter_by(id = thing_id).first()
        if not result :
            abort(404, message='thing not found')
        return result

    '''put function'''
    @marshal_with(resource_fields)
    def put(self, thing_id) :
        result = databaseModel.query.filter_by(id = thing_id).first()
        if result :
            abort(409, message='thing alredy exists.....')
        args = app_put_args.parse_args()
        data_to_put = databaseModel(id=thing_id, title=args['title'], content=args['content'])
        db.session.add(data_to_put) #adding the data to database 
        db.session.commit() #saving the changes to the database
        return data_to_put, 201
    
    @marshal_with(resource_fields)
    def patch(self, thing_id) :
        result = databaseModel.query.filter_by(id = thing_id).first()
        if not result :
            abort(404, message='thing not found...')
        args = app_update_args.parse_args()

        if args['title'] :
            result.title = args['title']

        if args['content'] :
            result.content = args['content']

        db.session.commit()
        return result
        

    '''delete function'''
    def delete(self, thing_id) :
        result = databaseModel.query.filter_by(id = thing_id).first()
        if not result :
            abort(404, message='thing not found....')
        db.session.delete(result)
        db.session.commit()
        return 'deleted'

api.add_resource(createapi, '/api/<int:thing_id>')

if __name__ == '__main__':
    app.run(debug=True)