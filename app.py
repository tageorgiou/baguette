import base64
import hashlib
import hmac
import httplib2
import json
import os
import urlparse
from urllib import urlencode

from flask import Flask, request, redirect, render_template, session
from database import db

FB_APP_ID = 196886180398409
FB_APP_SECRET = '3c8ac9932be4a87c132751ee8f9ee804'
FB_DOMAIN = 'https://baguette.herokuapp.com/'
UNSECURE_DOMAIN = 'http://baguette.herokuapp.com/'
OAUTH_URL = 'https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s&scope=publish_actions'
TOKEN_ENDPOINT = 'https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s'
ME_URL = "https://graph.facebook.com/me?access_token=%s"

app = Flask(__name__)
app.debug = True
app.secret_key = '\x98_M\xcaAV\x19\xfe\x01""\xf6|\xf4\xe4\x18\xc6\xbb^\x93\x8e\x13\x0f\xe5'

def takeClass(cl, fbid):
    url = 'https://graph.facebook.com/me/mitcourses:take?'
    #session['token'] = \
    #'AAACzESLYBUkBAEknGENPIb36viFtt0Fnpn9o8PZBII8dSoxhQnuFBSy3BJFhdAuRYZBZCxTdqbJ6rPPEF3zAcWyXryBz3JkANJSZCM9mZAQZDZD'
    if 'token' not in session:
        raise Exception
    accesstoken = session['token']
    classurl = urlencode({'class': UNSECURE_DOMAIN + 'class/' + cl['name'],
        'access_token': accesstoken,
        'professor' : cl['professor']})
    url = url + classurl
    h = httplib2.Http()
    resp, content = h.request(url, "POST", '')
    content = json.loads(content)
    was_successful = (resp['status'] == '200')
    if was_successful:
        cl['users'][fbid] = unicode(content['id'])
        db.classes.save(cl)
#        return redirect(FB_DOMAIN + '/class/%s' % cl.name)
    return str(resp) + '\\' + content['id']

@app.route('/class/<classname>')
def show_class(classname):
    fbid = "nope"
    dbg = 'eee'
    cl = db.classes.find_one({'name': classname})
    if 'fb_id' in session:
        fbid = session['fb_id']
        #dbg = str(takeClass(cl))
    if cl == None:
        return "404", 404
    cl_is_taking = fbid in cl['users']
    return render_template('class.html', cl=cl, fbid=fbid, dbg=dbg,
            cl_is_taking=cl_is_taking)

@app.route('/class/<classname>/take')
def take_class(classname):
    cl = db.classes.find_one({'name': classname})
    if cl == None:
        return "404", 404
    if 'fb_id' not in session:
        return "not authorized"
    if 'token' not in session:
        return "not logged in"
    fbid = session['fb_id']
    dbg = takeClass(cl, fbid)
    return 'yay. you are now taking %s %s' % (classname, dbg)
#    redirect('FB_DOMAIN/class/%s' % classname)

def untakeClass(cl, fbid):
    url = 'https://graph.facebook.com/{%s}?'
    if 'token' not in session:
        raise Exception
    accesstoken = session['token']
    classurl = urlencode({'access_token' : accesstoken})
    if fbid not in cl['users']:
        return "Um, you aren't taking this class"
    actionid = cl['users'][fbid]
    url = (url % actionid ) + classurl
    h = httplib2.Http()
    resp, content = h.request(url, "DELETE", '')
    return str(resp) + "---" + str(content)


@app.route('/class/<classname>/untake')
def untake_class(classname):
    cl = db.classes.find_one({'name': classname})
    if cl == None:
        return "404", 404
    if 'fb_id' not in session:
        return "not authorized"
    if 'token' not in session:
        return "not logged in"
    fbid = session['fb_id']
    dbg = untakeClass(cl, fbid)
    return 'yay. you are now not taking %s %s' % (classname, dbg)
#    redirect('FB_DOMAIN/class/%s' % classname)


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

    resp, content = h.request(ME_URL % access_token)
    fb_id = json.loads(content)['id']

    user = db.users.find_one({'fb_id': fb_id})
    created = 'Updated existing'
    if user is None:
        created = 'Created new'
        user = db.users.User()
        user['token'] = unicode(access_token)
        user['fb_id'] = fb_id
        user.save()
    else:
        user['token'] = unicode(access_token)
        user['fb_id'] = fb_id
        db.users.save(user)
    session['fb_id'] = fb_id
    session['token'] = access_token
    return '%s user (fb_id: %s) with access_token %s' % (created, fb_id, access_token)
    return content

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
