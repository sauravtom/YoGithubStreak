#!/usr/bin/env python
from credentials import api_token
import webapp2,urllib,urllib2,json,jinja2,os,datetime
from google.appengine.ext import db
from dateutil import parser as string2date
import pytz

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

class UsernameDB2(db.Expando):
    github_username = db.StringProperty()
    yo_username = db.StringProperty()

def need_to_notify(github_username):
    api_url = "https://api.github.com/users/%s/events/public"%github_username
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

def send_yo(yo_username):
    data = {'api_token':api_token, "username":yo_username}
    data = urllib.urlencode(data)

    request_object = urllib2.Request('http://api.justyo.co/yo/', data)
    response = urllib2.urlopen(request_object)

    print response.read()

class Index(webapp2.RequestHandler):
    def get(self):
        send_yo('sauravtom')
        template = jinja_environment.get_template('templates/index.html')
        self.response.out.write(template.render())

class AddtoDB(webapp2.RequestHandler):
    def get(self):
        github_username = self.request.get('github_username')
        yo_username = self.request.get('yo_username')
        all_github_usernames = [i.github_username for i in UsernameDB2.all().fetch(1000000)]
        if github_username in all_github_usernames:
            template = jinja_environment.get_template('templates/onsubmit.html')
            self.response.out.write(template.render())
            return
        user = UsernameDB2()
        user.github_username = github_username
        user.yo_username = yo_username
        user.put()
        template = jinja_environment.get_template('templates/onsubmit.html')
        self.response.out.write(template.render())

class Cron(webapp2.RequestHandler):
    def get(self):
        all_users = [{'github_username':i.github_username,'yo_username':i.yo_username} for i in UsernameDB2.all().fetch(1000000)]
        for user in all_users:
            if need_to_notify(user['github_username']):
                send_yo(user['yo_username'])

application = webapp2.WSGIApplication([
    ('/', Index),
    ('/cron', Cron),
    ('/add_user', AddtoDB)
    ],debug=True)