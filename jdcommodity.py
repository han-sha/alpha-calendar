import requests
import urllib
import random
from bs4 import BeautifulSoup

class JDCommodity(object):
	def __init__(self, keyword):
		self.keyword = keyword

	def __get_soup(self):
		url_keyword = urllib.parse.quote(self.keyword)
		url = "https://search.jd.com/Search?keyword={}&enc=utf-8".format(url_keyword)
		header = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'}
		html = requests.get(url, headers=header)
		html.encoding = html.apparent_encoding
		soup = BeautifulSoup(html.text,"html5lib")

		return soup

	
	def __process_soup(self):
		soup = self.__get_soup()
		titles = soup.find_all(class_="p-name")
		prices = soup.find_all(class_="p-price")
		comments = soup.find_all(class_="p-commit")

		rnum = random.randrange(0, len(comments), 1)

		randtitle = titles[rnum].text.strip().replace(" ","").replace("\t", " ", 1).replace("\t", "").replace("\n", "")
		randprice = prices[rnum].text.strip().replace("￥", "")
		randcomment = comments[rnum].text.strip().replace("+", "多")

		return randtitle, randprice, randcomment


	def get_info(self):
		title, price, comment = self.__process_soup()

		sentence = title + "。" + "价格为" + price + "，" + "目前已经有" + comment + "了。"
		return sentence