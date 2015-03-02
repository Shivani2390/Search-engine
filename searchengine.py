'''
CS 6913 Web search engines 
Assignment #3: Inverted index and Query processing.
Authors: Shivani Gupta and Anusha Gupta.  
'''

#importing all the necessary libraries.
import math
import Tkinter
import webbrowser
import math
import subprocess
import shlex
import signal,os
import heapq
import datetime

wordList = {}
urls = []	#contains the URL to Doc id mapping.
termList = {}	#contains the terms of the query.
rem = []
docavg = 0	#average size of the documents.

search_query = ""
search_result = ""

# class for the GUI component used to fetch input and display the output of the program.
class searchingApp(Tkinter.Tk):
    def __init__(self,parent, docavg, data):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()
        self.docavg = docavg
        self.data = data

    def initialize(self):
        self.grid()
        self.entryVariable = Tkinter.StringVar()
        self.entry = Tkinter.Entry(self,textvariable=self.entryVariable)
        self.entry.grid(column=0,columnspan=2,row=0,sticky='EW')
        self.entryVariable.set(u"Enter your query here.")
        button = Tkinter.Button(self,text=u"Search Now",command=self.OnButtonClick)
        button.grid(column=2,row=0)
        self.text = Tkinter.Text(self,state="normal",fg="black",bg="pink", wrap="word")
        self.text.grid(column=0,row=2,columnspan=3,sticky='EW')
        self.grid_columnconfigure(0,weight=3)
        self.entry.selection_range(0, Tkinter.END)

    def OnButtonClick(self):
		search_query = self.entry.get()
		results = executeQuery(search_query, self.docavg, self.data)
		##print results
		i = len(results) - 1
		hyperlinks = []
		while i >= 0:
			##print 'Result '+ str(results[i])
			self.text.insert(1.0, str(results[i][0]) + ' ')
			hyperlink = HyperlinkManager(self.text)
			self.text.insert(1.0, results[i][1], ("hyper", results[i][1]))
			self.text.insert(1.0, '\n')
			i -= 1
		self.grid_columnconfigure(0,weight=1)
		self.resizable(True,False)
		self.update()
		self.entry.focus_set()
		self.entry.selection_range(0, Tkinter.END)
	#self.abc = self.text.get(1.0, "end")

    def getQuery(self):
		return self.entry.get()
	
    def getText(self):
		return self.text


# class for making the links in the output web-accessible and click-able
class HyperlinkManager:
    def __init__(self, text):
		self.text = text
		self.text.tag_config("hyper", foreground="blue", underline=1)
		self.text.tag_bind("hyper", "<Enter>", self._enter)
		self.text.tag_bind("hyper", "<Leave>", self._leave)
		self.text.tag_bind("hyper", "<Button-1>", self._click)  
		#self.text.pack()
		self.reset()

    def reset(self):
		self.links = {}


    def _enter(self, event):
		self.text.config(cursor="hand2")

    def _leave(self, event):
		self.text.config(cursor="")

    def _click(self, event):
		w=event.widget
		x,y = event.x, event.y
		tags = w.tag_names("@%d,%d" % (x, y))
		for t in tags:
			if t.startswith("www"):
				print "clicked on link : "
				webbrowser.open_new('http://' + str(t))
				break
			else:
				print "link is broken"
			

#
def calculateBM25(terms, N, ft, docsize, docavg, freq):
	K = 1.2 * (0.25 + 0.25 * (docsize/docavg))
	score = 0
	for i in range(len(terms)):
		##print 'Term frequency '
		##print ft[i] 
		##print 'Total freq'
		##print freq[i]
		val1 = math.log((N - ft[i] + 0.5)/(ft[i] + 0.5))
		val2 = (2.2 * freq[i])/(K + freq[i])
		score += val1 * val2
	##print 'Score ' + str(score) 
	return score
	
def loadLexi():
	fileRead = open('Lexicon.txt', 'r')
	for line in fileRead:
		data = line.split()
		wordList[data[0]] = [data[1], data[2]]
	fileRead.close()
	
def loadUrls():
	fileRead = open('Urls.txt', 'r')
	docavg = 0
	for line in fileRead:
		items = line.split()
		urls.append(items)
	###print urls
	for ind in range(len(urls)):
		docavg += int(urls[ind][1])
	docavg /= len(urls)
	##print str(docavg) + '\n'
	fileRead.close()
	return docavg
	
	
def getTerms(query):
	terms = query.split()
	termList = []
	for i in range(len(terms)):
		if terms[i] in wordList.keys():
			termList.append(terms[i])
	return termList

def openListTermcached(term, f_list, data):
	line = data[wordList[term][0], wordList[term][0] + wordList[term][1]]
	line = line.replace('[','')
		###print line
	line = line.replace(']', ',')
		###print line
	data = line.split(',')
	d_list = []
	i = 0
	while i < len(data):
		data[i] = data[i].strip()
		if data[i] != '':
			if i  % 3 == 0:
			###print data[i]
				temp = int(data[i])
				##print temp
				if len(d_list) % 4 != 3:
					d_list.append(vbEncode(int(data[i])))
				else:
					d_list.append(int(data[i]))
			elif i % 3 == 1:
				if f_list.has_key(temp):
					f_list[temp].append(int(data[i]))
				else:
					f_list[temp] = [int(data[i])]
		i += 1
	##print f_list	
	return d_list, f_list
	 
def openList(term, ind, f_list):
	line = readBinary('output' + term, ind)
	##print 'data ' + line
	line = line.replace('[','')
		###print line
	line = line.replace(']', ',')
		###print line
	data = line.split(',')
	##print data
	d_list = []
	i = 0
	while i < len(data):
		data[i] = data[i].strip()
		##print data[i]
		if data[i] != '':
			if i  % 3 == 0:
			###print data[i]
				temp = int(data[i])
				##print temp
				if len(d_list) % 4 != 3:
					d_list.append(vbEncode(int(data[i])))
				else:
					d_list.append(int(data[i]))
			elif i % 3 == 1:
				if f_list.has_key(temp):
					f_list[temp].append(int(data[i]))
				else:
					f_list[temp] = [int(data[i])]
		i += 1
	##print f_list	
	return d_list, f_list
 
def closeList(list):
	list = []
	
def vbEncode(docID):
	###print docID
	bytes = ''
	cnt = 0
	while True:
		temp = bin(docID % 128)
		###print temp
		while len(temp) < 8:
			temp = '0' + temp
		temp = temp.replace('b', '')
		if cnt == 0:
			tmp_list = list(temp)
			tmp_list[0] = '0'
			temp = "".join(tmp_list)
		cnt += 1
		bytes =  temp + ' ' + bytes
		if docID < 128:
			break
		docID = docID / 128
	###print bytes
	return bytes

def vbDecode(bytes):
	bitstream = bytes.split()
	###print bitstream
	n = 0
	for i in range(len(bitstream)):
		val = int(bitstream[i],2)
		if val < 128:
			n = 128 * n + val
		else:
			n = 128 * n + (val - 128)
			break
	###print n
	return n


def uncompress(terms, data):
	termsCached = []
	for term in terms:
		filename = 'output' + term
		locn = int(wordList[term][0])
		size = int(wordList[term][1])
		end = locn + size
		##print str(end) + ' ' + str(len(data))
		if end > len(data):
			skip = int(math.floor(locn/size))
			##print end%size
			rem.append(end%size)
			if not os.path.exists(filename):	
				data = './unzip_part.sh'+ ' ' + str(size) + ' ' + str(skip) + ' ' + filename
			###print str(size) + ' ' + str(skip) + '\n'
				args = shlex.split(data)
				subprocess.Popen.stderr = '/dev/null'
				p = subprocess.Popen(args, stdout= subprocess.PIPE, stderr = subprocess.PIPE, preexec_fn = lambda:signal.signal(signal.SIGPIPE, signal.SIG_DFL ))
				p.wait()
			else:
				pass
		else:
			rem.append(0)
			termsCached.append(term)
	return termsCached
	###print 'File created'
		
	
def readBinary(fileName, ind):
	file = open(fileName, 'rb')
	line = ''
	char = ''
	read = ''
	##print rem[ind]
	##print os.stat(fileName)
	file.seek(rem[ind])
	##print rem
	while True:
		char = ''
		read = ''
		while read != ' ':
			###print 'In loop ' + read
			read = file.read(1)
			if not read:
				file.close()
				###print 'In read Binary ' + line
				return line
			char += read
		char = char.strip()
		char = chr(int(char,2))
		line += char
	##print line
	
	
def getFreq(list, docId):
	for i in range(len(list[0])):
		if docId == list[0][i]:
			##print docId
			break 
	return list[1][i]
	
def nextGEQ(list, docId):
	last = []
	i = 3
	temp = []
	##print list
	##print len(list)
	while i < len(list) and list[i] < docId :
		##print i 
		i += 4
		if i >= len(list):
			for j in range(i - 3, len(list)):
				temp.append(vbDecode(list[j])) 
			break
	if i < len(list):
		j = i - 3
		##print list[i]
		for i in range(j, j+3):
			##print list[i]
			temp.append(vbDecode(list[i]))
		temp.append(list[i + 1])
	i = 0
	while i < len(temp) and temp[i] < docId:
		i += 1
	###print 'In next GEQ ' + str(temp[i])
	if len(temp) > 1:
		##print 'Temp ' + str(temp)
		if i == len(temp):
			return temp[i - 1]
		return temp[i]
	else:
		return docId
def findMax(lp):
	max = lp[0][len(lp[0]) - 1]
	ind = len(lp[0]) - 1
	for i in range(1, len(lp)):
		size = len(lp[i])
		if lp[i][size - 1] < max:
			max = lp[i][size - 1]
			ind = len(lp[i]) - 1
	if ind %  4 == 3:
		return max
	else:
		maxdocId = vbDecode(max)
		##print 'Max is ' + str(maxdocId)
		###print 'Max is ' + str(maxdocId)
		return maxdocId

def findShortest(lp):
	shortest = len(lp[0])
	for i in range(1, len(lp)):
		if len[lp[i]] < shortest:
			ind = i
	temp = lp[0]
	lp[0] = lp[ind]
	lp[ind] = temp

def loadCache():
	cache = []
	filename = 'cache.txt'
	data = './unzip_cache.sh'
			###print str(size) + ' ' + str(skip) + '\n'
	args = shlex.split(data)
	subprocess.Popen.stderr = '/dev/null'
	p = subprocess.Popen(args, stdout= subprocess.PIPE, stderr = subprocess.PIPE, preexec_fn = lambda:signal.signal(signal.SIGPIPE, signal.SIG_DFL ))
	p.wait()
	fobj = open(filename, 'r') 
	data = fobj.read()
	fobj.close()
	return data 


def executeQuery(query, docavg, data):
	N = len(urls)
	##print N
	lp = []
	f_list = {}
	freq = []
	ft = []
	h = []
	print str(datetime.datetime.now())
	terms = getTerms(query)
	termsCached = uncompress(terms, data)
	##print 'Back in main'
	###print 'Remainder ' + str(rem)
	##print termsCached
	for term in termsCached:
		temp, f_list = openListTermCached(term, f_list, data)
		if temp != []:
			lp.append(temp)
			print 'Cached'	 
	for i in range(len(terms)):
		###print terms[i]
		###print wordList[terms[i]][1]
		if terms[i] not in termsCached:
			temp, f_list = openList(terms[i], i, f_list)
			##print temp
			if temp != []:
				lp.append(temp)
	docId = 0
	maxdocId = findMax(lp)
	try:
		while docId < maxdocId:
			docId = nextGEQ(lp[0], docId)
			##print docId
			i = 1
			d = docId
			while i < len(terms) and d == docId:
				d = nextGEQ(lp[i], docId)
				i += 1
			##print d
			if d > docId: 
				docId = d
			elif d == docId:
				freq = f_list[d]
				for i in range(len(terms)):
					ft.append(len(lp[i]))
			###print freq + ' ' + ft
				docsize = int(urls[docId][1])
				##print str(docsize) + ' ' + str(docavg)
				score = calculateBM25(terms, N, ft, docsize, docavg, freq)
				docId += 1
				##print docId
				##print urls[docId - 1][0]
				item = (score, urls[docId - 1][0])
				heapq.heappush(h, item)
				h = heapq.nlargest(10,h)
			else:
				docId += 1
		for i in range(len(terms)):
			closeList(lp[i])
	except KeyError, ValueError:
		pass
	best = heapq.nlargest(10,h)
	print str(datetime.datetime.now())
	return best

if __name__ == "__main__":
		 
	##print search_result
	loadLexi()
	data = loadCache()
	docavg = loadUrls()
	app = searchingApp(None, docavg, data)	
	app.title('Search Engine')
	
	#search_query = app.getQuery()
	##print search_query
	#text_content = app.getText()
	#hyperlink = HyperlinkManager(app.text)
	#app.text.insert(1.0,search_result, "hyper", hyperlink.add(search_result[0]))
	#text.insert(INSERT, "www.google.com", "hyper", hyperlink.add(text.get))
	app.mainloop()
	



