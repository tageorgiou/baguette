import base64
import hashlib
import hmac
import httplib2
import json
import os
import urlparse

from flask import Flask, request, redirect, render_template
from database import db, User

FB_APP_ID = 196886180398409
FB_APP_SECRET = '3c8ac9932be4a87c132751ee8f9ee804'
FB_DOMAIN = 'https://baguette.herokuapp.com/'
OAUTH_URL = 'https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s'
TOKEN_ENDPOINT = 'https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s'
ME_URL = "https://graph.facebook.com/me?access_token=%s"

app = Flask(__name__)
app.debug = True

@app.route('/class/<classname>')
def show_class(classname):
    cl = db.classes.find_one({'name': classname})
    if cl == None:
        return "404", 404
    else:
        return render_template('class.html', cl=cl)

@app.route('/', methods=['GET', 'POST'])
def main():
    if 'code' not in request.args:
        return redirect(OAUTH_URL % (FB_APP_ID, FB_DOMAIN))
    code = request.args.get('code', None)
    h = httplib2.Http()
    url = TOKEN_ENDPOINT % (FB_APP_ID, FB_DOMAIN, FB_APP_SECRET, code)

    resp, content = h.request(url)
    if resp['status'] != '200':
        return "Error requesting token.", 500
    param = urlparse.parse_qs(content)
    access_token, expires = [x[0] for x in param.values()]

    resp, content = h.request(OBJ_URL % access_token)
    fb_id = json.loads(content)['id']

    user = db.users.find_one({'fb_id': fb_id})
    created = 'Updated existing'
    if user is None:
        created = 'Created new'
        user = db.users.User()
    user['token'] = unicode(access_token)
    user.save()
    return '%s user (fb_id: %s) with access_token %s' % (created, fb_id, access_token)
    return content

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
