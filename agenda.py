
from event import Event
from flask_sqlalchemy import SQLAlchemy
import test

db = SQLAlchemy()

class Agenda(db.Model):
	__tablename__='JDSMARTAGENDA'

	timestamps = db.Column(db.String(30), nullable=False, primary_key=True)
	sessID = db.Column(db.String(63), nullable=False)
	jdID = db.Column(db.String(63), nullable=False)
	startTime = db.Column(db.DateTime, nullable=False)
	endTime = db.Column(db.DateTime)
	agendaType = db.Column(db.String(26), nullable=False)
	agendaDetail = db.Column(db.String(126))

	def __init__(self, timestamps=None, sessID=None, jdID=None, startTime=None, 
		endTime=None, agendaType=None, agendaDetail=None):
		self.timestamps = timestamps
		self.sessID = sessID
		self.jdID = jdID
		self.startTime = startTime
		self.endTime = endTime
		self.agendaType = agendaType
		self.agendaDetail = agendaDetail

	def startyear(self):
		return self.startTime.year

	def startmonth(self):
		return self.startTime.month

	def startday(self):
		return self.startTime.day

	def starthour(self):
		return self.startTime.hour

	def startminute(self):
		return self.startTime.minute

	def endyear(self):
		return self.endTime.year

	def endmonth(self):
		return self.endTime.month

	def endday(self):
		return self.endTime.day

	def endhour(self):
		return self.endTime.hour

	def endminute(self):
		return self.endTime.minute

	def duration(self):
		return self.endTime - self.startTime

	def detail(self):
		return self.agendaDetail

	def timestamp(self):
		return self.timestamp

	def make_event(self):
		year, month, day, hour, minute, detail = \
				self.startTime.year, self.startTime.month, self.startTime.day, \
				self.startTime.hour, self.startTime.minute, self.agendaDetail

		duration = self.endTime - self.startTime
		event = Event(jdID=self.jdID, year=year, month=month, day=day,
			hour=hour, minute=minute, duration=duration, event_detail=detail)
		return event