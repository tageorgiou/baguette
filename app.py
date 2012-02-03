import os
from flask import Flask, request
from mongokit import Connection, Document

app = Flask(__name__)
app.debug = True

MLU = 'mongodb://heroku_app2744761:7j7n2hpdftkrumvl1uhf7k41k8@ds029847.mongolab.com:29847/heroku_app2744761'
connection = Connection(MLU)
db = connection.heroku_app2744761

@app.route('/', methods=['GET','POST'])
def hello():
    raise
    return 'Hello world!!'

class TUser(Document):
    structure = {
            'name' : unicode,
            'email' : unicode,
    }
    use_dot_notation = True

connection.register([TUser])
collection = db.tusers
user = collection.TUser()
user['name'] = u'aaaa'
user['email'] = u'assss'
user.save()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
