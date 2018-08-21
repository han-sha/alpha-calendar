import os, json, time, re, random, fileinput
from datetime import datetime
from datetime import timedelta
from flask import (Flask, request, abort, jsonify)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract, and_

from event import Event
from find import Find
from delete import Delete
from add import Add
from update import Update
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
	rst, action = process_request(req)
	response = postResponse(rst, action)
	return jsonify(response)


def process_request(req):
	request = req['request']
	if 'intent' not in request:
		rst = '欢迎使用您的智能规划本，请问您需要添加、修改、查找、删除计划，还是听取建议呢？'
		return rst, None
	action = request['intent']['name']
	timestamps = request['timestamp']
	jdID = req['session']['user']['userId'].replace('.','')
	sessID = req['session']['sessionId']
	if 'Alpha' not in action:
		content = request['intent']['slots']

	if action == 'Add':
		res = add(sessID, jdID, content, timestamps)
		res += '请问您还需要添加什么计划？'
	elif action == 'Change':
		res = update(jdID, content)
		res += '请问你还需要修改什么计划？'
	elif action == 'Delete':
		res = delete(jdID, content)
		res += '请问您还需要删除什么计划？'
	elif action == 'Find':
		res = find(jdID, content)
		res += '请问您还需要查找什么计划？'
	elif action == 'Suggestion':
		res = suggest(jdID, db)
		res += '如果您对这个建议不满意，您可以再继续说听听建议来获取不同的回复噢。'
	elif action == 'Alpha.CancelIntent':
		res = cancel()
	elif action == 'Alpha.HelpIntent':
		res = help(jdID)
		res += '请问您希望添加，查找，修改，删除计划，还是听建议呢？'
	else:
		res = repeat(jdID)
		res += '请问您希望添加，查找，修改，删除计划，还是听建议呢？'
	if action != 'Alpha.RepeatIntent':
		record(jdID, res)
	return res, action


def record(jdID, info):
	f = open('repeat', 'r')
	lines = f.readlines()
	for n,l in enumerate(lines):
		line = l.rstrip().split(' ')
		if line[0] == jdID:
			lines.remove(lines[n])
		break
	f.close()
	lines.append(jdID + ' ' + info.replace('\n', '').replace('\t', '') + '\n')
	print(lines)
	f2 = open('repeat', 'w')
	f2.writelines(lines)


def repeat(jdID):
	f = open('repeat', 'r')
	for l in f.readlines():
		l = l.rstrip().split(' ')
		print(l)
		if l[0] == jdID:
			rst = l[1]
			return rst

	return '您之前还没有和规划本有过任何互动噢。您可以回复帮助来获取使用信息。'


def help(jdID):
	e = Find(jdID=jdID, db=db)
	rst = e.help()
	return rst

def cancel():
	phrase = ['感谢您的使用，向您比心。', '我会变得更好，欢迎您再次使用。', '您已成功退出，感谢您的使用。']
	n = random.randrange(0, len(phrase), 1)
	return phrase[n]


def add(sessID, jdID, content, timestamps):
	date, time, duration, detail, endate, endtime = \
	content['AlphaDate'], content['StartTime'], content['Duration'], content['Event'], content['EndDate'], content['EndTime']

	year, month, day, hour, minute, duration, detail = \
	get_properties(date=date, time=time, duration=duration, detail=detail)

	endyear, endmonth, enday, endhour, endminute, __, __ = get_properties(date=endate, time=endtime)
	if endyear is None and endhour is not None:
		endyear, endmonth, enday = year, month, day
		duration = datetime(endyear, endmonth, enday, endhour, endminute) - datetime(year, month, day, hour, minute)

	event = Event(sessID=sessID, jdID=jdID, year=year, month=month, 
		day=day,hour=hour, minute=minute, duration=duration, event_detail=detail)

	add = Add(db=db, timestamps=timestamps, jdID=jdID, event=event)
	rst = add.add()
	return rst


def delete(jdID, content):
	date, time, detail = content['deleteDate'], content['deleteStartTime'], content['deleteEvent']
	year, month, day, hour, minute, __, detail = get_properties(date=date, time=time, detail=detail)
	nearest = True if 'value' in content['nearest'] else False
	print(nearest)
	cmd = detail if nearest is False else '最近一次'
	event = Event(jdID=jdID, year=year, month=month, 
		day=day, hour=hour, minute=minute, event_detail=detail, isDelete=True)

	delete = Delete(db=db, jdID=jdID, event=event, cmd=cmd) if (hour is not None or nearest is True) else \
	Delete(db=db, jdID=jdID, event=event)

	rst = delete.delete()

	return rst


def find(jdID, content):
	date, time, detail = content['Date'], content['alphaTime'], content['eventDetail']
	year, month, day, hour, minute, __, detail = get_properties(date=date, time=time, detail=detail)

	nearest = True if 'value' in content['nearest'] else False
	reply_type = content['findAction']['value']

	event = Event(jdID=jdID, year=year, month=month, 
		day=day, hour=hour, minute=minute, event_detail=detail)
	find = Find(db=db, jdID=jdID, event=event, nearest=nearest)
	rst = find.find()
	return rst


def suggest(jdID, db):
	_obj = Suggestion(jdID, db)
	_suggestion = _obj.get_suggestion()

	return _suggestion


def update(jdID, content):
	time1, date1, detail1 = content['originalStartTime'], content['originalDate'], content['originalEvent']
	time2, date2, detail2 = content['changeStartTime'], content['newDate'], content['changeEvent']
	year1, month1, day1, hour1, minute1, __, detail1 = get_properties(date=date1, time=time1, detail=detail1)
	year2, month2, day2, hour2, minute2, __, detail2 = get_properties(date=date2, time=time2, detail=detail2)

	detail2 = detail1 if detail2 is None else detail2
	hour2 = hour1 if hour2 is None else hour2
	minute2 = minute1 if minute2 is None else minute2
	duration2 = content['changeDuration']['value'] if 'value' in content['changeDuration'] else None

	e1 = Event(jdID=jdID, year=year1, month=month1, 
		day=day1, hour=hour1, minute=minute1, isUpdate=True,
		event_detail=detail1)

	
	e2 = Event(jdID=jdID, year=year2, month=month2, 
		day=day2, hour=hour2, minute=minute2, isUpdate=True, 
		duration=duration2, event_detail=detail2)


	update = Update(db=db, jdID=jdID, old_event=e1, new_event=e2)
	rst = update.update()

	return rst


def get_properties(date=None, time=None, duration=None, detail=None):
	if date is not None:
		date = date['value'].split('-') if 'value' in date else None
	if time is not None:
		time = time['value'].split(':') if 'value' in time else None
	if detail is not None:
		detail = detail['value'] if 'value' in detail else None
		print(detail)
	if duration is not None:
		duration = duration['value'] if 'value' in duration else None
	if date is not None:
		year, month, day = int(date[0]), int(date[1]), int(date[2])
	else:
		year, month, day = None, None, None

	if time is not None:
		hour, minute = int(time[0]), int(time[1])
	else:
		hour, minute = None, None

	return year, month, day, hour, minute, duration, detail


def postResponse(rst, action):
	res = {}
	res["version"] = "1.0"
	res["response"] = {}
	res["response"]["output"] = {}
	res["response"]["output"]["text"] = rst
	res["response"]["output"]["type"] = "PlainText"
	res["shouldEndSession"] = 'true' if action == 'Alpha.CancelIntent' else 'false'
	return res	


# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run()
