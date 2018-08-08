from datetime import datetime
from event import Event
from agenda import Agenda
from sqlalchemy import extract, and_
import random


class Delete(object):
	def __init__(self, db, jdID, event, cmd='所有计划'):
		self.db = db
		self.jdID = jdID
		self.e = event
		self.cmd = cmd

		self.year = event.get_year()
		self.month = event.get_month()
		self.day = event.get_day()


	def __which_delete(self):
		if self.cmd == '所有计划':
			rst = self.__delete_all()
		elif self.cmd == '下一次':
			rst = self.__delete_next()
		else:
			rst = self.__delete_one()
		return rst


	def __delete_all(self):
		record = []
		events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == self.year, extract('month', Agenda.startTime) == self.month, 
				extract('day', Agenda.startTime) == self.day)).all()
		if not events:
			rst = '您还没有制定任何计划呢，可以回复添加'+ self.e.day_des_gen() + \
			self.e.time_des_gen() + '来进行添加哈。'
			return rst

		try:
			for item in events:
				self.db.session.delete(item)
				record.append(item)
			self.db.session.commit()

		except Exception as err:
			self.__log_error(err)
			rst = "抱歉...您的规划本出了点小问题，计划删除失败了..."
			return rst

		rst = '已经帮您删除' + str(len(record)) + '条计划了哟。这些计划是：'
		for e in record:
			year, month, day, hour, minute, detail = \
			e.startyear(), e.startmonth(), e.startday(), e.starthour(), e.startminute(), e.detail()
			event = Event(jdID=self.jdID, year=year, month=month, day=day,
				hour=hour, minute=minute, detail=detail)
			rst += event.day_des_gen() + event.time_des_gen() + detail + '计划。'

		rst += '感谢您的使用！'
		return rst


	#def __delete_next(self):


	def __log_error(self, err):
		f = open('err/delete.err', 'a')
		f.write(str(err))
		f.write('\n')
		f.write('\n')
		f.close()


	def delete(self):
		rst = self.__which_delete()
		return rst

