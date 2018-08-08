
from flask_sqlalchemy import SQLAlchemy
import test

db = SQLAlchemy()

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

	def duration(self):
		return self.endTime - self.startTime

	def detail(self):
		return self.agendaDetail