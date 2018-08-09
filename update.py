from event import Event
from agenda import Agenda
from sqlalchemy import extract, and_

class Update(object):
	def __init__(self, db, jdID, old_event, new_event):
		self.jdID = jdID
		self.db = db
		self.old_event = old_event
		self.new_event = new_event


	def __which_update(self):
		if self.new_event.is_future() == False:
			rst = "更改失败了，您所给的计划开始时间已过。如需删除计划，请回复删除。"
			return rst

		if self.old_event.get_hour() is None:
			rst = self.__multiples()
		else:
			rst = self.__singles()

		return rst


	def __multiples(self):
		query = self.db.session.query(Agenda).filter(and_(
			Agenda.jdID==self.jdID, 
			extract('year', Agenda.startTime) == self.old_event.get_year(),
			extract('month', Agenda.startTime) == self.old_event.get_month(),
			extract('day', Agenda.startTime) == self.old_event.get_day(),
			Agenda.agendaDetail == self.old_event.get_detail()))
		events = query.all()
		if len(events) == 0:
			rst = '更改失败了噢，您' + self.old_event.day_des_gen() + self.old_event.time_des_gen() + \
			'并没有' + self.old_event.get_detail() + '这条计划。请您先添加噢。'
		elif len(events) > 1:
			rst = '您在' + self.old_event.day_des_gen() + '有' + str(len(events)) + '条相似计划。开始时间分别为：'
			for e in events:
				a = e.make_event()
				rst += a.day_des_gen() + a.time_des_gen() + "。"
			rst += '请问您要更改哪一条呢？'
		else:
			try:
				event = query.first()
				if self.new_event.get_startime() is None:
					event.endTime = self.new_event.get_duration() + event.startTime
				else:
					event.startTime = self.new_event.get_startime()
					event.endTime = self.new_event.get_duration() + self.new_event.get_startime()
				event.agendaDetail = self.new_event.get_detail()
				self.db.session.commit()
			except Exception as err:
				self.__log_error(err)
				rst = "抱歉，我找到了您要更改的计划，只是现在出了点问题，更改失败了..."
				return rst

			rst = '更改成功！新的' + self.new_event.get_detail() + '时间为' + self.new_event.day_des_gen() + \
			self.new_event.time_des_gen() + '，预计需要' + self.new_event.duration_des_gen() + '，' + \
			'结束时间为' + self.new_event.day_des_gen(start=False) + self.new_event.time_des_gen(start=False) + \
			'。'
		return rst


	def __singles(self):
		event = self.db.session.query(Agenda).filter(and_(
			Agenda.jdID==self.jdID, extract('year', Agenda.startTime) == self.old_event.get_year(),
			extract('month', Agenda.startTime) == self.old_event.get_month(),
			extract('day', Agenda.startTime) == self.old_event.get_day(),
			extract('hour', Agenda.startTime) == self.old_event.get_hour(),
			extract('minute', Agenda.startTime) == self.old_event.get_minute(),
			Agenda.agendaDetail == self.old_event.get_detail())).first()
		if not event:
			rst = '更改失败了呢，规划本没有找到' + self.old_event.day_des_gen() + self.old_event.time_des_gen() + \
			'的' + self.old_event.get_detail() + '计划。请您先进行添加哈。'
		else:
			try:
				event.startTime = self.new_event.get_startime()
				event.endTime = self.new_event.get_endtime()
				event.agendaDetail = self.new_event.get_detail()
			except Exception as err:
				self.__log_error(err)
				rst = "抱歉，我找到了您要更改的计划，只是现在出了点问题，更改失败了..."
				return rst

			rst = '更改成功！新的' + self.new_event.get_detail() + '时间为' + self.new_event.day_des_gen() + \
			self.new_event.time_des_gen() + '，预计需要' + self.new_event.duration_des_gen() + '，' + \
			'结束时间为' + self.new_event.day_des_gen(start=False) + self.new_event.time_des_gen(start=False) + \
			'。'
		return rst
		

	def __log_error(self, err):
		f = open('err/update.err', 'a')
		f.write(str(err))
		f.write('\n')
		f.write('\n')
		f.close()


	def update(self):
		rst = self.__which_update()
		return rst