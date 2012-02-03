import os
import json
import base64

from flask import Flask, request, redirect
from mongokit import Connection, Document

OAUTH_URL = 'https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s'
FB_APP_ID = 196886180398409
FB_DOMAIN = 'https://baguette.herokuapp.com/'

app = Flask(__name__)
app.debug = True

MLU = 'mongodb://heroku_app2744761:7j7n2hpdftkrumvl1uhf7k41k8@ds029847.mongolab.com:29847/heroku_app2744761'
connection = Connection(MLU)
db = connection.heroku_app2744761


# Page unauthenticated users land at.
@app.route('/start', methods=['GET', 'POST'])
def start():
    return redirect(OAUTH_URL % (FB_APP_ID, FB_DOMAIN))

@app.route('/', methods=['POST'])
def main():
    signed_req_raw = base64.b64decode(request.form.get('signed_request', ''))
    if not signed_req_raw:
        return '', 400
    signed_req = json.parse(signed_req_raw)
    raise
    return 'welcome'

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
