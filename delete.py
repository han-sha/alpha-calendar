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

		self.hour = event.get_hour()
		self.minute = event.get_minute()
		self.detail = event.get_detail()


	def __which_delete(self):
		if self.year is not None and self.cmd == '所有计划':
			rst = self.__delete_day()
		elif self.year is None and self.cmd == '所有计划':
			rst = self.__delete_all()
		elif self.cmd == '最近一次':
			rst = self.__delete_next()
		elif self.year is not None and self.hour is not None:
			rst = self.__delete_one()
		return rst


	def __delete_one(self):
		events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == self.year, extract('month', Agenda.startTime) == self.month, 
				extract('day', Agenda.startTime) == self.day,
				extract('hour', Agenda.startTime) == self.hour,
				extract('minute', Agenda.startTime) == self.minute)).all()
		rst, des = '', ''
		for e in events:
			a = e.make_event()
			des += a.day_des_gen() + a.time_des_gen() + '的' + a.get_detail() + '。'
			if e.detail() == self.detail:
				try:
					self.db.session.delete(event)
					self.db.session.commit()
				except Exception as err:
					self.__log_error(err)
					rst = "抱歉...您的规划本出了点小问题，计划删除失败了..."
					return rst
				rst = '已成功帮您删除' + self.e.day_des_gen() + self.e.time_des_gen() + \
				'的' + self.detail + '计划 。'
				return rst
		rst = '我只找到了' + des + '。'
		return rst


	def __delete_next(self):
		record = None
		query = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID, 
				Agenda.agendaDetail == self.detail))
		event = query.order_by(Agenda.startTime).first()
		if not event:
			rst = '您还没有规划关于' + self.detail + '的计划呢。您可以回复我要添加计划，来进行添加噢！'
			return rst

		record = year, month, day, hour, minute, detail = \
			event.startyear(), event.startmonth(), event.startday(), \
			event.starthour(), event.startminute(), event.detail()
		try:
			self.db.session.delete(event)
			self.db.session.commit()

		except Exception as err:
			self.__log_error(err)
			rst = "抱歉...您的规划本出了点小问题，计划删除失败了..."
			return rst

		rst = '已成功帮您删除' + record.day_des_gen() + record.time_des_gen() + \
		'的' + self.detail + '计划啦。'
		return rst


	def __delete_all(self):
		record = []
		events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID)).all()
		if not events:
			rst = '您的规划本里什么计划都还没有噢。您可以回复添加计划来进行添加。'
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

		rst = '已经帮您删除' + str(len(record)) + '条计划了哟。您的规划本现已被清空。'
		return rst



	def __delete_day(self):
		record = []
		events = self.db.session.query(Agenda).filter(and_(Agenda.jdID==self.jdID, 
				extract('year', Agenda.startTime) == self.year, extract('month', Agenda.startTime) == self.month, 
				extract('day', Agenda.startTime) == self.day)).all()
		if not events:
			rst = '您还没有制定'+ self.e.day_des_gen() + '的' + self.e.get_detail() + '计划呢，您可以先进行添加哈。'
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
			a = e.make_event()
			rst += a.day_des_gen() + a.time_des_gen() + a.get_detail() + '计划。'

		rst += '感谢您的使用！'
		return rst


	def __log_error(self, err):
		f = open('err/delete.err', 'a')
		f.write(str(err))
		f.write('\n')
		f.write('\n')
		f.close()


	def delete(self):
		rst = self.__which_delete()
		return rst

