from mongokit import Connection, Document

MLU = 'mongodb://heroku_app2744761:7j7n2hpdftkrumvl1uhf7k41k8@ds029847.mongolab.com:29847/heroku_app2744761'

connection = Connection(MLU)
db = connection.heroku_app2744761

class Class(Document):
    structure = {
            'name' : unicode,
            'label' : unicode,
            'description' : unicode,
            'professor' : unicode,
    }
    use_dot_notation = True

connection.register([Class])
