from datetime import datetime
from agenda import Agenda
from event import Event
from jdcommodity import JDCommodity
import random

class Suggestion(object):
	def __init__(self, jdID, db):
		self.jdID = jdID
		self.db = db
		self.events = db.session.query(Agenda).filter(Agenda.jdID==jdID).all()
		self.today = datetime.now()
		self.pastEvents = []
		self.futureEvents = []
		self.keyword = ""

		self.intro = ["向您推荐: ","打个软广告: ","我帮您在京东上找到的: ",
						"您可能会喜欢的: ", "和"+self.keyword+"有关的: ",]

		self.__classify_events()

	def __classify_events(self):
		for e in self.events:
			event = Event(e)
			if event.is_future() is False:
				self.pastEvents.append(event)
			else:
				self.futureEvents.append(event)

	def __get_pastEvents(self):
		return self.pastEvents

	def __get_futureEvents(self):
		return self.futureEvents

	def __suggestion_gen(self):
		# 0 - past event num
		# 1 - future event num
		# >1 %2 == 0 ads
		# 3, 5 - other random suggestion
		type_no = random.randrange(0, 6, 1)

	def my_suggestion(self):





		
