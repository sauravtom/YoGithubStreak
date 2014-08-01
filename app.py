#!/usr/bin/env python
from credentials import api_token
import webapp2,urllib,urllib2,json,jinja2,os,datetime
from google.appengine.ext import db
from dateutil import parser as string2date
import pytz

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

class UsernameDB(db.Expando):
    username = db.StringProperty()

def need_to_notify(username):
    api_url = "https://api.github.com/users/%s/events/public"%username
    result = json.loads(urllib2.urlopen(api_url).read())
    
    last_commit_time = [i['created_at'] for i in result if i['type'] == "PushEvent"][0]
    last_commit_time_obj = string2date.parse(last_commit_time)
    
    #dealing with timezon stuff
    last_commit_time_obj = last_commit_time_obj.replace(tzinfo=None)
    
    diff = datetime.datetime.now() - last_commit_time_obj
    minutes_diff = divmod(diff.days * 86400 + diff.seconds, 60)[0]
    
    if minutes_diff > (24*60-3*60):
        return True
    
    return False

def send_yo(username):
    data = {'api_token':api_token, "username":username}
    data = urllib.urlencode(data)

    request_object = urllib2.Request('http://api.justyo.co/yo/', data)
    response = urllib2.urlopen(request_object)

    print response.read()

class Index(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template('templates/index.html')
        self.response.out.write(template.render())

class AddtoDB(webapp2.RequestHandler):
    def get(self):
        username = self.request.get('username')
        all_users = [i.username for i in UsernameDB.all().fetch(1000000)]
        if username in all_users:
            template = jinja_environment.get_template('templates/onsubmit.html')
            self.response.out.write(template.render())
            return
        user = UsernameDB()
        user.username =  username
        user.put()
        template = jinja_environment.get_template('templates/onsubmit.html')
        self.response.out.write(template.render())

class Cron(webapp2.RequestHandler):
    def get(self):
        all_users = [i.username for i in UsernameDB.all().fetch(1000000)]
        for user in all_users:
            if need_to_notify(user):
                send_yo(user)

application = webapp2.WSGIApplication([
    ('/', Index),
    ('/cron', Cron),
    ('/add_user', AddtoDB)
    ],debug=True)