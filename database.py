from mongokit import Connection, Document

import datetime

MLU = 'mongodb://heroku_app2744761:7j7n2hpdftkrumvl1uhf7k41k8@ds029847.mongolab.com:29847/heroku_app2744761'

connection = Connection(MLU)
db = connection.heroku_app2744761

class Class(Document):
    structure = {
        'name' : unicode,
        'label' : unicode,
        'description' : unicode,
        'professor' : list,
        #'lecture' : list,
        #'recitation' : list,
        'users': dict, #fbid : action fbid
        'userlist': list,
        'sessions': list, # type, time, place
    }
    use_dot_notation = True

class User(Document):
    structure = {
        'fb_id': unicode,
        'token': unicode,
        'date_creation': datetime.datetime,
    }
    required_fields = ['token', 'date_creation']
    default_values = {'date_creation': datetime.datetime.utcnow}

connection.register([Class, User])

