import os, json, time, re, random
from datetime import datetime
from datetime import timedelta
from flask import (Flask, request, abort, jsonify)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract, and_

from suggestion import Suggestion
from getevent import GetEvent
from queriedevent import QueriedEvent
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

	search_event = GetEvent(db=db, jdID=jdID, date=date, time=time)
	diff = search_event.get_diff_between_now_start()

	if diff.days > 7:
		rst = "不好意思哈，您的规划本只保存过去一星期内的记录。超过一星期的已经被自动删除了哟"
		return rst 
	
	rst = search_event.find_events()
	return rst


def suggest(jdID, db):
	_obj = Suggestion(jdID, db)
	_suggestion = _obj.get_suggestion()

	return _suggestion


def update(jdID, content):
	print(content)
	curtime = datetime.now()

	getOriginalTime = content['originalStartTime']['value'].split(':')
	getNewTime = content['changeStartTime']['value'].split(':')
	getOriginalDate = content['originalDate']['value'].split('-')
	getNewDate = content['newDate']['value'].split('-')
	getOriginalEvent = content['originalEvent']['value']
	getNewEvent = content['changeEvent']['value']
	if getNewEvent == '原始':
		getNewEvent = getOriginalEvent

	duration = content['changeDuration']['value']

	startyear, startmonth, startday = int(getOriginalDate[0]), int(getOriginalDate[1]), int(getOriginalDate[2])
	starthour, startmin = int(getOriginalTime[0]), int(getOriginalTime[1])

	n_startyear, n_startmonth, n_startday = int(getOriginalDate[0]), int(getOriginalDate[1]), int(getOriginalDate[2])
	n_starthour, n_startmin = int(getOriginalTime[0]), int(getOriginalTime[1])
	
	n_startime = datetime(n_startyear, n_startmonth, n_startday, n_starthour, n_startmin, 0)
	diff = n_startime - curtime

	if (diff.days < 0) or (diff.seconds < 0) or (diff.microseconds < 0):
		rst = "更改失败了，您所给的计划开始时间已过。如需删除计划，请回复删除。"
		return rst

	dur_week = re.findall(r'(\d+)W', duration)
	dur_day = re.findall(r'(\d+)D', duration)
	dur_hour = re.findall(r'(\d+)H', duration)
	dur_min = re.findall(r'(\d+)M', duration)

	dur_week = 0 if not dur_week else int(dur_week[0])
	dur_day = 0 if not dur_day else int(dur_day[0]) + (dur_week*7)
	dur_hour = 0 if not dur_hour else int(dur_hour[0])
	dur_min = 0 if not dur_min else int(dur_min[0])

	duration = timedelta(days=dur_day, hours=dur_hour, minutes=dur_min)

	#events = query_event_based_on_time_detail(jdID=jdID, year=startyear, month=startmonth,
	#	day=startday, hour=starthour, details=getOriginalEvent)

	event = db.session.query(Agenda).filter(and_(
		Agenda.jdID==jdID, 
		extract('year', Agenda.startTime) == startyear,
		extract('month', Agenda.startTime) == startmonth,
		extract('day', Agenda.startTime) == startday,
		extract('hour', Agenda.startTime) == starthour,
		Agenda.agendaDetail == getNewEvent)).first()

	if not event:
		rst = "更改失败了，规划本没有找到原始计划。请回复查找确认记录，或回复删除记录"
	else:
		event.startTime = n_startime
		event.endTime = n_startime + duration
		event.agendaDetail = getNewEvent

		db.session.commit()
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
