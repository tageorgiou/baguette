import base64
import hashlib
import hmac
import httplib2
import json
import os
import urlparse
from urllib import urlencode
import re
from werkzeug.contrib.cache import SimpleCache
cache = SimpleCache()

from flask import Flask, request, redirect, render_template, session
from database import db

FB_APP_ID = 196886180398409
FB_APP_SECRET = '3c8ac9932be4a87c132751ee8f9ee804'
FB_DOMAIN = 'https://baguette.herokuapp.com/'
UNSECURE_DOMAIN = 'http://baguette.herokuapp.com/'
OAUTH_URL = 'https://www.facebook.com/dialog/oauth?client_id=%s&redirect_uri=%s&scope=publish_actions'
TOKEN_ENDPOINT = 'https://graph.facebook.com/oauth/access_token?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s'
ME_URL = "https://graph.facebook.com/me?access_token=%s"
NOACTION_CLASS_TAKE = '-1'
BYPASS = False

app = Flask(__name__)
app.debug = True
app.secret_key = '\x98_M\xcaAV\x19\xfe\x01""\xf6|\xf4\xe4\x18\xc6\xbb^\x93\x8e\x13\x0f\xe5'

def takeClass(cl, fbid):
    """ Given a class and fbid for user, take the class"""
    url = 'https://graph.facebook.com/me/mitcourses:take?'
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
        cl['userlist'].append(fbid)
        db.classes.save(cl)
    else: 
        cl['users'][fbid] = NOACTION_CLASS_TAKE
        cl['userlist'].append(fbid)
        db.classes.save(cl)
#        return redirect(FB_DOMAIN + '/class/%s' % cl.name)
#    return str(resp) + '\\' + content['id']
    return ""

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
    if BYPASS:
        friendList = []
    else:
        friendList = get_friends()
    classTakers = cl['userlist']
    print classTakers
    friendClassTakers = []
    #print friendList[0]['uid']
    for f in friendList:
        if unicode(f['uid']) in classTakers:
            friendClassTakers.append(f)
    schedule = makeClassSchedule(cl)
    return render_template('class.html', cl=cl, fbid=fbid, dbg=dbg,
            cl_is_taking=cl_is_taking, friends=friendClassTakers,
            schedule=schedule)

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
#    return 'yay. you are now taking %s %s' % (classname, dbg)
    return redirect('/class/%s' % classname)

def untakeClass(cl, fbid):
    url = 'https://graph.facebook.com/%s?'
    if 'token' not in session:
        raise Exception
    accesstoken = session['token']
    classurl = urlencode({'access_token' : accesstoken})
    if fbid not in cl['users']:
        return "Um, you aren't taking this class"
    actionid = cl['users'][fbid]
    if actionid == NOACTION_CLASS_TAKE:
        if fbid in cl['users']:
            del cl['users'][fbid]
            cl['userlist'].remove(fbid)
            db.classes.save(cl)
        return "Not taking"
    else:
        url = (url % actionid ) + classurl
        h = httplib2.Http()
        resp, content = h.request(url, "DELETE", '')
        was_successful = (resp['status'] == '200')
        if was_successful:
            if fbid in cl['users']:
                del cl['users'][fbid]
                cl['userlist'].remove(fbid)
                db.classes.save(cl)
    #return str(resp) + "---" + str(content)
    return ""



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
    #return 'yay. you are now not taking %s %s' % (classname, dbg)
    return redirect('/class/%s' % classname)

def find_registered_classes(fbid):
    classes = []
    clcc = db.classes.find({ 'userlist': unicode(fbid) })
    for i in range(0,clcc.count()):
        classes.append(clcc.next())
    return classes

def get_friends():
    if 'fb_id' not in session:
        raise Exception()
    if 'token' not in session:
        raise Exception()
    authtoken = session['token']
    fbid = session['fb_id']

    friendsList = cache.get('friends_' + str(fbid))
    if friendsList is not None:
        return friendsList

    url = 'https://graph.facebook.com/fql?'
    endurl = urlencode({'access_token' : authtoken,
        'q': 'SELECT uid, name, pic_square FROM user WHERE uid = me() OR uid IN (SELECT uid2 FROM friend WHERE uid1 = me())'})
    url = url + endurl
    h = httplib2.Http()
    resp, content = h.request(url, "GET", '')
    was_successful = (resp['status'] == '200')
    if was_successful:
        friendsList = json.loads(content)['data']
        cache.set('friends_' + str(fbid), friendsList, 15*60) #15min
        return friendsList
    else:
        raise Exception("Need to login")

@app.route('/search')
def search():
    if 'q' not in request.args:
        return "No query specified"
    query = request.args['q']
    return redirect('/class/%s' % query)

@app.route('/autocomplete')
def autocomplete():
    if 'term' not in request.args:
        return "No query specified"
    query = re.escape(request.args['term'])
    print query
    results = []
    mongoquery = {'$or' : [
        {'professor': {'$regex': query, '$options': 'i'}}, #case insensitive
        {'name': {'$regex': '^' + query}},
        ]}

    for c in db.classes.Class.find(mongoquery).limit(8):
        val = {'label': c['name'] + ' ' + c['label'],
                'value': c['name'],
                'title': 'tttt',
                }
        results.append(val)
    print results
    return json.dumps(results)


def get_user_profile(access_token):
    h = httplib2.Http()
    resp, content = h.request(ME_URL % access_token)
    user_profile = json.loads(content)
    return user_profile

@app.route('/', methods=['GET', 'POST'])
def main():
    fb_id = 1111
    friends = []
    first_name='Thomas'
    classes = []
    if not BYPASS:
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

        user_profile = get_user_profile(access_token)
        fb_id = user_profile['id']
        first_name = user_profile['first_name']

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
        session['first_name'] = first_name
        friends = get_friends()
    else:
        pass

    return render_template('home.html', fbid=fb_id,
            classes=find_registered_classes(fb_id), friends=friends,
            first_name=first_name)
#    return '%s user (fb_id: %s) with access_token %s' % (created, fb_id, access_token)
#    return content

@app.route('/about')
def about():
    fbid = "nope"
    dbg = 'eee'
    if 'fb_id' in session:
        fbid = session['fb_id']
    return render_template('about.html', fbid=fbid)

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

def getClassesForFBID(fbid):
    return db.classes.Class.find({'userlist': unicode(fbid)})

def makeClassSchedule(cl, color=0):
    schedule = []
    time = getTimeForClass(cl)
    if '-' in time:
        return []
    else:
        days = re.match('([MTWRF]+)', time).group(1)
        ttime = re.match('[MTWRF]*([0-9]+)', time).group(1)
        ittime = int(ttime)
        if ittime < 8:
            ittime += 12
        for c in days:
            s = {
                    'name': cl['name'],
                    'day': c,
                    'time': ittime,
                    'length': 1.0,
                    'color': color,
                }
            schedule.append(s)
    return schedule

@app.route('/user/<userid>')
def show_user(userid):
    fbid = ''
    if 'fb_id' in session:
        fbid = session['fb_id']
    else:
        if not BYPASS:
            raise AuthError
    if BYPASS:
        friendList = []
    else:
        friendList = get_friends()
    #for f in friendList:
    #    if unicode(f['uid']) in classTakers:
    #        friendClassTakers.append(f)
    classes = getClassesForFBID('552102999')
    schedule = []
    colorcounter = 0
    for cl in classes:
        print getTimeForClass(cl)
        schedule += makeClassSchedule(cl, color=colorcounter)
        colorcounter += 1
    print schedule
    return render_template('user.html', classes=classes, fbid=fbid,
            schedule=schedule)

def getTimeForClass(cl):
    for s in cl['sessions']:
        if s['type'] == u'lecture':
            return s['time']

if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get('PORT', 5005))
    app.run(host='0.0.0.0', port=port)
