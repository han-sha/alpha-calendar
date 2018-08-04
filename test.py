import os, json, time, re
from datetime import datetime
from datetime import timedelta
from flask import (Flask, request, abort, jsonify)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract, and_

from findevent import FindEvent
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
	content = request['intent']['slots']


	# event = db.session.query(Agenda).filter(and_(
	# Agenda.jdID==jdID, 
	# extract('year', Agenda.startTime) == 2018,
	# extract('month', Agenda.startTime) == 8,
	# extract('day', Agenda.startTime) == 9,
	# extract('hour', Agenda.startTime) == 9)).first()

	# event.startTime = datetime(2018, 8, 9, 11, 0)
	# event.endTime = datetime(2018, 8, 11, 11, 0)
	# db.session.commit()

	if action == 'Add':
		res = add(sessID, jdID, content)
	elif action == 'Change':
		res = update(jdID, content)
	elif action == 'Delete':
		res = delete(jdID, content)
	elif action == 'Find':
		res = find(jdID, content)
	elif action == 'Suggestion':
		res = suggest(jdID)
	return res


def add(sessID, jdID, content):
	#curyear, curmonth, curday, curhour, curmin = get_curtime()
	curtime = datetime.now()

	getDate = content['AlphaDate']['value'].split('-')
	getTime = content['StartTime']['value'].split(':')
	duration = content['Duration']['value']
	startyear, startmonth, startday = int(getDate[0]), int(getDate[1]), int(getDate[2])
	starthour, startmin = int(getTime[0]), int(getTime[1])

	startime = datetime(startyear, startmonth, startday, starthour, startmin, 0)
	
	diff = startime - curtime
	if (diff.days < 0) or (diff.seconds < 0) or (diff.microseconds < 0):
		rst = "您的行程本现在只能协助您规划未来的计划，并不支持记录以往的事务"
		return rst

	# check duration
	dur_week = re.findall(r'(\d+)W', duration)
	dur_day = re.findall(r'(\d+)D', duration)
	dur_hour = re.findall(r'(\d+)H', duration)
	dur_min = re.findall(r'(\d+)M', duration)

	if (not dur_week) and (not dur_day) and (not dur_hour) and (not dur_min):
		endtime = startime
	else:
		dur_week = 0 if not dur_week else int(dur_week[0])
		dur_day = 0 if not dur_day else int(dur_day[0]) + (dur_week*7)
		dur_hour = 0 if not dur_hour else int(dur_hour[0])
		dur_min = 0 if not dur_min else int(dur_min[0])
		duration = timedelta(days=dur_day, hours=dur_hour, minutes=dur_min)
		endtime = startime + duration

	agendaType = content['Event']['value']
	agenda = Agenda(sessID=sessID, jdID=jdID, agendaType=agendaType, startTime=startime, 
		endTime=endtime, agendaDetail=agendaType)
	try:
		db.session.add(agenda)
		db.session.commit()
	except Exception as err:
		log_error(err)
		rst = "您的行程本出了点小问题，这条行程添加失败了..."
		return rst
	rst = "已帮您添加了这条计划，感谢您的使用"
	return rst
	

def delete(jdID, content):
	print(content)
	getDate = content['deleteDate']['value'].split('-')
	getTime = content['deleteStartTime']
	if 'value' in getTime:
		getTime = getTime['value'].split(':')
		hour, minute = getTime[0], getTime[1]
	else:
		getTime = None
		hour, minute = 0, 0
	year = int(getDate[0])
	month = int(getDate[1])
	day = int(getDate[2])
	agendaDetail = content['deleteEvent']['value']

	record = []

	if agendaDetail == '所有计划':
		events = query_all_events_of_the_day(jdID, year, month, day)

	elif getTime is None:
		events = query_event_based_on_detail(jdID, year, month, day, agendaDetail)

	else:
		events = db.session.query(Agenda).filter(and_(
			Agenda.jdID==jdID, 
			extract('year', Agenda.startTime) == year,
			extract('month', Agenda.startTime) == month,
			extract('day', Agenda.startTime) == day,
			extract('hour', Agenda.startTime) == hour, 
			extract('minute', Agenda.startTime) == minute)).all()

	print(not events)
	if not events:
		rst = '没有找到您需要删除的这条计划，请回复查找或添加来查询或添加这条计划'
		return rst
	for item in events:
		print(item)
		record.append(item)
		db.session.delete(item)
	db.session.commit()

	if getTime is None:
		rst = '已经帮您删除' + str(year) + '年' + str(month) + '月' + str(day) + '号的' + agendaDetail + '计划了，感谢您的使用'
	else:
		minute = '' if minute == 0 else str(minute) + '分'
		rst = '已经帮您删除' + str(year) + '年' + str(month) + '月' + str(day) + '号' + str(hour) + '点' + minute + '开始的' + agendaDetail + '计划了，感谢您的使用'
	return rst

def find(jdID, content):
	getDate = content['Date']['value'].split('-')
	curtime = datetime.now()

	year = int(getDate[0])
	month = int(getDate[1])
	day = int(getDate[2])
	searchtime = datetime(year, month, day)
	diff = curtime - searchtime

	if diff.days > 7:
		rst = "不好意思哈，您的行程本目前只保存过去一星期内的行程记录。超过一星期的记录已经被自动删除了哟"
		return rst 
	
	getTime = content['Time']
	if 'value' in getTime:
		getTime = content['Time']['value']
	#events = db.session.query(Agenda.jdID, Agenda.startTime).filter(and_(Agenda.jdID==jdID, Agenda.startTime.between(startime, endtime))).all()
	
	events = db.session.query(
		Agenda.startTime, Agenda.endTime, Agenda.agendaType, Agenda.agendaDetail).filter(and_(
			Agenda.jdID==jdID, 
			extract('year', Agenda.startTime) == year,
			extract('month', Agenda.startTime) == month,
			extract('day', Agenda.startTime) == day)).all()
	# no record
	if len(events) == 0:
		rst = "您的行程本还没有记录这天的任何行程哈"

	else:
		n = len(events)
		if (diff.days < 0) or (diff.seconds < 0):
			rst = "在未来的这天里，您规划了这" + str(n) + "条事项："
		else:
			rst = "在过往的这天里，您曾规划过这" + str(n) + "条事项："
		for e in events:
			print(e)
			event = FindEvent(e)
			rst += event.get_overall_des()
	return rst


def suggest(jdID):
	return




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

# def query_event_based_on_time_detail(jdID, year, month, day, hour, details):
# 	print(year, month, day, hour, details)
# 	event = db.session.query(Agenda).filter(and_(
# 		Agenda.jdID==jdID, 
# 		extract('year', Agenda.startTime) == year,
# 		extract('month', Agenda.startTime) == month,
# 		extract('day', Agenda.startTime) == day,
# 		extract('hour', Agenda.startTime) == hour,
#		Agenda.agendaDetail == getNewEvent)).first()
# 	return event

def query_event_based_on_detail(jdID, year, month, day, details):
	events = db.session.query(Agenda).filter(and_(
		Agenda.jdID==jdID, 
		extract('year', Agenda.startTime) == year,
		extract('month', Agenda.startTime) == month,
		extract('day', Agenda.startTime) == day,
		Agenda.agendaDetail == details)).all()
	return events

def query_all_events_of_the_day(jdID, year, month, day):
	events = db.session.query(Agenda).filter(and_(
			Agenda.jdID==jdID, 
			extract('year', Agenda.startTime) == year,
			extract('month', Agenda.startTime) == month,
			extract('day', Agenda.startTime) == day)).all()
	return events

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
