import os, json, time, re, random
from datetime import datetime
from datetime import timedelta
from flask import (Flask, request, abort, jsonify)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract, and_

from suggestion import Suggestion
from getevent import GetEvent
from queriedevent import QueriedEvent
from update import Update
from agenda import Agenda, db

# print a nice greeting.
def say_hello(username = "World"):
    return '<p>Hello %s!</p>\n' % username

project_dir = os.path.dirname(os.path.abspath(__file__))
db_file = "sqlite:///{}".format(os.path.join(project_dir, "agenda.db"))

# EB looks for an 'application' callable by default.
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_file

db.init_app(app)
# add a rule for the index page.
app.add_url_rule('/', 'index', (lambda: say_hello()))

# actions = ['Add', 'Change', 'Find' ,'Delete', 'Suggestion']
@app.route('/', methods=['POST', 'GET', 'PUT'])
def main():
	f = open('log', 'a')
	if not request.json:
		abort(400)
	f.write(json.dumps(request.json))
	f.write('\n')
	f.write('\n')
	req = request.json
	rst = process_request(req)
	response = postResponse(rst)
	return jsonify(response)


def process_request(req):
	request = req['request']
	action = request['intent']['name']
	jdID = req['session']['user']['userId'].replace('.','')
	sessID = req['session']['sessionId']
	if 'Alpha' not in action:
		content = request['intent']['slots']

	if action == 'Add':
		res = add(sessID, jdID, content)
	elif action == 'Change':
		res = update(jdID, content)
	elif action == 'Delete':
		res = delete(jdID, content)
	elif action == 'Find':
		res = find(jdID, content)
	elif action == 'Suggestion':
		res = suggest(jdID, db)
	elif action == 'Alpha.CancelIntent':
		res = cancel()
	return res

def cancel():
	phrase = ['感谢您的使用，向您比心', '我会变得更好，欢迎您下次使用', '您已成功退出，感谢您的使用']
	n = random.randrange(0, len(phrase), 1)
	return phrase[n]

def add(sessID, jdID, content):
	date = content['AlphaDate']['value']
	time = content['StartTime']['value']
	duration = content['Duration']['value']
	event_detail = content['Event']['value']

	event = GetEvent(db=db, sessID=sessID, jdID=jdID, date=date, duration=duration,
		time=time, event_type=event_detail, event_detail=event_detail, isAdd=True)

	diff = event.get_diff_between_now_start()
	if (diff.days < 0) or (diff.seconds < 0) or (diff.microseconds < 0):
		rst = event.get_add_pastevent_error()
		return rst

	rst = event.add_event()
	return rst
	

def delete(jdID, content):
	date = content['deleteDate']['value']
	time = content['deleteStartTime']
	time = time['value'] if 'value' in time else None
	detail = content['deleteEvent']['value']
	event = GetEvent(db=db, jdID=jdID, date=date, time=time, event_detail=detail)
	rst = event.delete_events()

	return rst


def find(jdID, content):
	date = content['Date']['value']
	time = content['Time']['value'] if 'value' in content['Time'] else None
	reply_type = content['findAction']['value']
	#print(reply_type)

	search_event = GetEvent(db=db, jdID=jdID, date=date, time=time)
	diff = search_event.get_diff_between_now_start()

	if diff.days > 7:
		rst = "不好意思哈，您的规划本只保存过去一星期内的记录。超过一星期的已经被自动删除了哟"
		return rst 
	
	rst = search_event.find_events(anstype=reply_type)
	return rst


def suggest(jdID, db):
	_obj = Suggestion(jdID, db)
	_suggestion = _obj.get_suggestion()

	return _suggestion


def update(jdID, content):
	print(content)
	time1, time2 = content['originalStartTime']['value'], content['changeStartTime']['value']
	date1, date2 = content['originalDate']['value'], content['newDate']['value']
	event1, event2 = content['originalEvent']['value'], content['changeEvent']['value']
	event2 = event1 if event2 == '原始' else event2
	duration2 = content['changeDuration']['value']

	e1 = GetEvent(date=date1, time=time1, event_detail=event1)
	e2 = GetEvent(date=date2, time=time2, duration=duration2, event_detail=event2, isAdd=True)

	update = Update(db=db, jdID=jdID, old_event=e1, new_event=e2)
	rst = update.update()

	return rst


def postResponse(rst):
	res = {}
	res["version"] = "1.0"
	res["response"] = {}
	res["response"]["output"] = {}
	res["response"]["output"]["text"] = rst
	res["response"]["output"]["type"] = "PlainText"
	res["shouldEndSession"] = "false"
	return res	

def log_error(err):
	f = open('err', 'a')
	f.write(str(err))
	f.write('\n')
	f.write('\n')
	f.close()

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run()
