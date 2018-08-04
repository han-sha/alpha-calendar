from datetime import datetime
from agenda import Agenda

class Suggestion(object):
	def __init__(self, jdID, db):
		self.jdID = jdID
		self.db = db

	def query_all(self):
		