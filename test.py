import os, json, time, re, random
from datetime import datetime
from datetime import timedelta
from flask import (Flask, request, abort, jsonify)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract, and_

from event import Event
from find import Find
from delete import Delete
from add import Add
from suggestion import Suggestion

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
	phrase = ['感谢您的使用，向您比心。', '我会变得更好，欢迎您再次使用。', '您已成功退出，感谢您的使用。']
	n = random.randrange(0, len(phrase), 1)
	return phrase[n]


def add(sessID, jdID, content):
	date, time, duration, detail = \
	content['AlphaDate'], content['StartTime'], content['Duration'], content['Event']

	year, month, day, hour, minute, duration, detail = \
	get_properties(date=date, time=time, duration=duration, detail=detail)

	event = Event(sessID=sessID, jdID=jdID, year=year, month=month, 
		day=day,hour=hour, minute=minute, duration=duration, event_detail=detail, isAdd=True)

	add = Add(db=db, jdID=jdID, event=event)
	rst = add.add()
	return rst


def delete(jdID, content):
	date, time, detail = content['deleteDate'], content['deleteStartTime'], content['deleteEvent']
	year, month, day, hour, minute, detail = get_properties(date=date, time=time, detail=detail)

	event = Event(db=db, jdID=jdID, year=year, month=month, 
		day=day, hour=hour, minute=minute, detail=detail, event_detail=detail)
	delete = Delete(db=db, jdID=jdID, event=event)
	rst = delete.delete()

	return rst


def find(jdID, content):
	date, time, detail = content['Date'], content['alphaTime'], content['eventDetail']
	year, month, day, hour, minute, detail = get_properties(date=date, time=time, detail=detail)

	nearest = True if 'value' in content['nearest'] else False
	reply_type = content['findAction']['value']
	#print(reply_type)
	event = Event(db=db, jdID=jdID, year=year, month=month, 
		day=day, hour=hour, minute=minute, detail=detail, event_detail=detail)
	find = Find(db=db, jdID=jdID, event=event, nearest=nearest)
	rst = find.find()
	return rst


def suggest(jdID, db):
	_obj = Suggestion(jdID, db)
	_suggestion = _obj.get_suggestion()

	return _suggestion


def update(jdID, content):
	time1, time2 = content['originalStartTime']['value'], content['changeStartTime']['value']
	date1, date2 = content['originalDate']['value'], content['newDate']['value']
	event1, event2 = content['originalEvent']['value'], content['changeEvent']['value']
	event2 = event1 if event2 == '原始' else event2
	duration2 = content['changeDuration']['value']

	e1 = Event(date=date1, time=time1, event_detail=event1)
	e2 = Event(date=date2, time=time2, duration=duration2, event_detail=event2, isAdd=True)

	update = Update(db=db, jdID=jdID, old_event=e1, new_event=e2)
	rst = update.update()

	return rst


def get_properties(date=None, time=None, duration=None, detail=None):
	date = date['value'].split('-') if 'value' in date else None
	time = time['value'].split(':') if 'value' in time else None
	detail = detail['value'] if 'value' in detail else None
	duration = duration['value'] if 'value' in duration else None
	if date is not None:
		year, month, day = date[0], date[1], date[2]
	else:
		year, month, day = None, None, None

	if time is not None:
		hour, minute = time[0], time[1]
	else:
		hour, minute = None, None

	return int(year), int(month), int(day), int(hour), int(minute), duration, detail


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
