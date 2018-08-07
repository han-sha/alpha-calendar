from getevent import GetEvent
from agenda import Agenda
from sqlalchemy import extract, and_

class Update(object):
	def __init__(self, db, jdID, old_event, new_event):
		self.jdID = jdID
		self.db = db
		self.old_event = old_event
		self.new_event = new_event


	def __query_oldevent(self):
		print(self.old_event.get_month())
		event = self.db.session.query(Agenda).filter(and_(
			Agenda.jdID==self.jdID, extract('year', Agenda.startTime) == self.old_event.get_year(),
			extract('month', Agenda.startTime) == self.old_event.get_month(),
			extract('day', Agenda.startTime) == self.old_event.get_day(),
			extract('hour', Agenda.startTime) == self.old_event.get_hour(),
			Agenda.agendaDetail == self.old_event.get_detail())).first()
		return event


	def update(self):
		if self.new_event.is_future() == False:
			rst = "更改失败了，您所给的计划开始时间已过。如需删除计划，请回复删除。"
			return rst

		event = self.__query_oldevent()
		if not event:
			rst = '更改失败了，规划本没有找到原始计划。请回复查找确认记录'
			return rst
		else:
			event.startTime = self.new_event.get_startime()
			event.endTime = self.new_event.get_startime() + self.new_event.get_duration()
			event.agendaDetail = self.new_event.get_detail()

			self.db.session.commit()
			rst = '更改成功！'
		return rst