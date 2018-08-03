import os, json, time, re
from datetime import datetime
from datetime import timedelta
from flask import (Flask, request, abort, jsonify)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract, and_
from findevent import FindEvent

# print a nice greeting.
def say_hello(username = "World"):
    return '<p>Hello %s!</p>\n' % username

project_dir = os.path.dirname(os.path.abspath(__file__))
db_file = "sqlite:///{}".format(os.path.join(project_dir, "agenda.db"))

# EB looks for an 'application' callable by default.
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = db_file

db = SQLAlchemy(app)
# add a rule for the index page.
app.add_url_rule('/', 'index', (lambda: say_hello()))

# actions = ['Add', 'Change', 'Find' ,'Delete', 'Suggestion']

class Agenda(db.Model):
	__tablename__='JDSMARTAGENDA'
	sessID = db.Column(db.String(63), unique=True, nullable=False, primary_key=True)
	jdID = db.Column(db.String(63), nullable=False)
	startTime = db.Column(db.DateTime, nullable=False)
	endTime = db.Column(db.DateTime)
	agendaType = db.Column(db.String(26), nullable=False)
	agendaDetail = db.Column(db.String(126))

	def __init__(self, sessID=None, jdID=None, startTime=None, endTime=None, agendaType=None, agendaDetail=None):
		self.sessID = sessID
		self.jdID = jdID
		self.startTime = startTime
		self.endTime = endTime
		self.agendaType = agendaType
		self.agendaDetail = agendaDetail

	
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
		rst = "您的行程本现在只能协助您规划未来的行程，并不支持记录以前的行程哈"
		return rst

	# check duration
	dur_day = re.findall(r'(\d+)D', duration)
	dur_hour = re.findall(r'(\d+)H', duration)
	dur_min = re.findall(r'(\d+)M', duration)

	if (not dur_day) and (not dur_hour) and (not dur_min):
		endtime = startime
		print("could not find wtf?")
	else:
		dur_day = 0 if not dur_day else int(dur_day[0])
		dur_hour = 0 if not dur_hour else int(dur_hour[0])
		dur_min = 0 if not dur_min else int(dur_min[0])
		duration = timedelta(days=dur_day, hours=dur_hour, minutes=dur_min)
		endtime = startime + duration
		print(endtime)

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
	rst = "已帮您添加了这条行程哟，感谢您的使用"
	return rst
	

def update(jdID):
	return

def delete(jdID, content):
	
	return

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
		if (diff.days > 0) or (diff.seconds > 0):
			rst = "在过往的这天里，您曾有过这些安排："
		else:
			rst = "在未来的这天里，您将有这些安排："
		for e in events:
			print(e)
			event = FindEvent(e)
			rst += event.get_overall_des()
	return rst

def suggest(jdID):
	return

def postResponse(rst):
	res = {}
	res["version"] = "1.0"
	res["response"] = {}
	res["response"]["output"] = {}
	res["response"]["output"]["text"] = rst
	res["response"]["output"]["type"] = "PlainText"
	res["shouldEndSession"] = "true"
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
