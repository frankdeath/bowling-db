#! /usr/bin/env python2.5

from __future__ import division
import sys
import os.path
import sqlite3
import hashlib
from math import sqrt
#from threading import Thread
try:
	okToGraph = True
	from pylab import plot,show,bar,hist,legend,figure,subplot,xlabel,ylabel
except ImportError:
	okToGraph = False
	print
	print "You will not see pretty graphs until you install matplotlib"
	print

def calc_game(game_array):
	b = [' '] * 21
	s = [None] * 10
	n = [' '] * 10
	first_ball_ave = 0
	opens = 0
	strikes = 0
	spares = 0
	splits = 0
	splits_converted = 0
	score = 0

	### The game array will shrink with each call to score_frame.  This approach seemed
	### to be preferrable to maintaining the index of the game_array since the game_array
	### is not a fixed size (the existence of splits makes the length variable
	def score_frame(frame, previous_score, game_array, first_ball_ave, opens, strikes, spares, splits, splits_converted, b, n):
		###global first_ball_ave, opens, strikes, spares, splits, splits_converted
		#print game_array
		# index the (n+1)th ball of the game (counting starts with zero)
		index = frame * 2
		if game_array[0] == 'S' or game_array[0] == 's':
			# make a note of the split
			n[frame] = 'S'
			splits += 1
			if game_array[2] == '/':
				splits_converted += 1
			# score the frame after removing the 'S'
			score, new_game_array, first_ball_ave, opens, strikes, spares, splits, splits_converted = score_frame(frame, previous_score, game_array[1:], first_ball_ave, opens, strikes, spares, splits, splits_converted, b, n)
		elif game_array[0] == 'X' or game_array[0] == 'x':
			score = score_bonus(2, previous_score+10, game_array[1:])
			new_game_array = game_array[1:]
			# record the strike in the ball array
			b[index] = game_array[0]
			first_ball_ave += 1.0
			strikes += 1
			if frame == 9:
				# if 10th frame don't forget to record both bonus balls
				b[index+1] = game_array[1]
				b[index+2] = game_array[2]
				# don't forget to count the strikes
				if (game_array[1] == 'X' or game_array[1] == 'x'):
					strikes += 1
				if (game_array[2] == 'X' or game_array[2] == 'x'):
					strikes += 1
				# or the potential spare
				if game_array[2] == '/':
					spares += 1
		elif game_array[1] == '/':
			# if the second ball is a spare, I don't care what the 1st ball was
			score = score_bonus(1, previous_score+10, game_array[2:])
			new_game_array = game_array[2:]
			# record the spare in the ball array
			b[index] = game_array[0]
			b[index+1] = game_array[1]
			if frame == 9:
				# if you get a spare in the 10th frame, record the bonus ball
				b[index+2] = game_array[2]
				# don't forget to count the last strike
				if game_array[2] == 'X' or game_array[2] == 'x':
					strikes += 1
			first_ball_ave += int(game_array[0]) / 10.0
			spares += 1
		else:
			# If I don't have a split, a strike or a spare, then I have either a number or a '-'
			try:
				b1 = int(game_array[0])
			except ValueError:
				b1 = 0
			try:
				b2 = int(game_array[1])
			except ValueError:
				b2 = 0
			score = previous_score + b1 + b2
			new_game_array = game_array[2:]
			# record the frame in the ball array
			b[index] = game_array[0]
			b[index+1] = game_array[1]
			first_ball_ave += int(game_array[0]) / 10.0
			opens += 1
			#print "frame:", frame+1, "opens:", opens, "---", game_array
		# don't need to return b and n because they're passed by reference.  shouldn't need to return 
		# new_game_array either but it can't hurt to be more explicit
		return (score, new_game_array, first_ball_ave, opens, strikes, spares, splits, splits_converted)
	
	def score_bonus(bonus, previous_score, game_array):
		if bonus == 2:
			is_strike = True
		else:
			is_strike = False
		# Note that when bonus == 2, 1st iteration is the 2nd bonus ball, 1nd iteration is the 1st bonus ball
		while bonus > 0:
			bonus -= 1
			x = 0
			
			# use a bonus offset to handle a split indicator in the middle of my bonus balls
			bonus_offset = 0
			if is_strike == True:
				if bonus == 1 and (game_array[bonus] == 'S' or game_array[bonus] == 's'):
					# This handles the situation where the following a strike you have:
					# ['X', 'S', '7', '2']
					# since the 'S' is in the place of the 2st bonus ball, you need to 
					# simply increase the index by one to get the 1st ball of the split frame
					bonus_offset = 1
				if bonus == 0 and (game_array[bonus] == 'S' or game_array[bonus] == 's'): 
					# This handles the situation where following a strike you have:
					# ['S', '7', '2'] 
					# since the 'S' is in the place of the 1st bonus ball (and you've already 
					# counted the '7', you need to make sure you add the '2', which means
					# increasing the offset by 2.
					bonus_offset = 2
					### set a flag if a slpit-conversion follows a strike, otherwise 1st ball is counted twice
					if game_array[bonus_offset] == '/':
						previous_score -= int(game_array[bonus_offset-1])

			else:
				if bonus == 0 and (game_array[bonus] == 'S' or game_array[bonus] == 's'):
					# the above does not handle a split after a spare properly.  
					# it will incorrectly add the 2nd ball rather than the 1st
					bonus_offset = 1
	
			# bonus_i should get us to the value we actually want to score
			bonus_i = bonus + bonus_offset
			## debugging "if" statement
			#if bonus_offset > 0:
			#	print "--->", game_array
			#	#print "index", (bonus + bonus_offset), " - value", game_array[bonus+bonus_offset]
			#	print "bonus", bonus, "bonus_offset", (bonus_offset), " - value", game_array[bonus+bonus_offset]
	
			try:
				x = int(game_array[bonus_i])
			except ValueError:
				if game_array[bonus_i] == '/':
					previous_score += 10
					# already took into account the 1st ball so correct it here
					break
				if game_array[bonus_i] == 'X' or game_array[bonus_i] == 'x':
					x = 10
	
			previous_score += x
			
		return previous_score



	# loop over all ten frames and score them
	for f in range(10):
		#print "***", f, "***"
		###global first_ball_ave, opens, strikes, spares, splits, splits_converted
		score, game_array, first_ball_ave, opens, strikes, spares, splits, splits_converted = score_frame(f, score, game_array, first_ball_ave, opens, strikes, spares, splits, splits_converted, b, n)
		s[f] = score
		#print score

	# it might be useful to allow a single calc of the values below w/o adding them to the database
	#print s
	#print "1st ball ave", first_ball_ave
	#print "strikes", strikes
	#print "spares", spares
	#print "opens", opens
	#print "splits", splits
	#print "splits converted", splits_converted
	#print b
	#print n

	### Assemble most of the array that will be inserted into the database
	db_entry = b + n + s + [strikes, spares, opens, splits, splits_converted, first_ball_ave]
	return db_entry

def add_mode():
	def verify_date(date_string):
		date_is_good = True
		date_array = date_string.split("-")
		try:
			year = int(date_array[0])
			month = int(date_array[1])
			day = int(date_array[2])
			if year < 1980 or year > 2080 or month < 1 or month > 12 or day < 1 or day > 31:
				print "Error: Date is not valid"
				date_is_good = False
		except ValueError:
			print "Error: Date is not valid"
			date_is_good = False
		
		return date_is_good

	def verify_game(game_string):
		game_is_good = True
		splits = game_string.count('S') + game_string.count('s')
		strikes = game_string.count('X') + game_string.count('x')
		characters = len(game_string)
		# number of balls in a game is the number of characters minus the number of splits
		# (a split indicator is not a ball) plus the number of strikes (a strike in one of the 
		# 1st nine frames skips a ball.  Since we don't know at this point in the calc how many 
		# of the strikes occurred in the 10th frame, we only know that the number of balls that 
		# were skipped is AT LEAST three less than the number of strikes and at most the number
		# of strikes.
		num_balls = len(game_string) - splits + max((strikes - 3), 0)
		if num_balls > 21 or num_balls < 17:
			print "Error: Game is not valid"
			game_is_good = False
		print splits, strikes, characters, num_balls
		return game_is_good

	# could add a hash function here or maybe a global function 
	# if one of the other modes uses it

	add_mode_exit = False
	while add_mode_exit == False:
		date = raw_input('Enter a date: ')
		# instead of printer, eventually allow reentry
		#print verify_date(date)
		num = raw_input('Enter the game number: ')
		arg = raw_input('Enter the game: ')
		# instead of printing, eventually allow reentry
		#print verify_game(arg)
		a = [x for x in arg]
		rest_of_values = calc_game(a[:])

		# determine the md5 hash
		string_to_hash = "%s %s %s" % (date, num, arg)
		m = hashlib.md5()
		m.update(string_to_hash)
		hash = m.hexdigest()
		del m

		# hash isn't particularly useful if it isn't compared to existing ones
		# check here to see if it is unique
		
		db_values = [None, date, num, arg] + rest_of_values + [hash]

		## add the values to the database here
		print len(db_values)
		conn = sqlite3.connect('bowling.db')
		c = conn.cursor()
		c.execute('insert into game_data values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', db_values)
		conn.commit()

		to_exit = raw_input('Type q to quit or enter to enter another game ')
		if to_exit == 'q':
			add_mode_exit = True

def create_mode():
	def verify_path(desired_path):
		directory, filename = os.path.split(desired_path)
		if directory == '':
			directory = '.'
		if not os.path.isdir(directory):
			print "Directory does not exist"
			path_is_ok = False
		elif os.path.isfile(desired_path):
			print "File already exists"
			path_is_ok = False
		elif desired_path == '':
			print "Filename cannot be blank"
			path_is_ok = False
		else:
			path_is_ok = True

		return path_is_ok

	def create_db():
		conn = sqlite3.connect('bowling.db')
		c = conn.cursor()
		try:
			c.execute('''CREATE TABLE game_data (id INTEGER PRIMARY KEY, date TEXT, game_num INTEGER, game_str TEXT, frame1a TEXT, frame1b TEXT, frame2a TEXT, frame2b TEXT, frame3a TEXT, frame3b TEXT, frame4a TEXT, frame4b TEXT, frame5a TEXT, frame5b TEXT, frame6a TEXT, frame6b TEXT, frame7a TEXT, frame7b TEXT, frame8a TEXT, frame8b TEXT, frame9a TEXT, frame9b TEXT, frame10a TEXT, frame10b TEXT, frame10c TEXT, note1 TEXT, note2 TEXT, note3 TEXT, note4 TEXT, note5 TEXT, note6 TEXT, note7 TEXT, note8 TEXT, note9 TEXT, note10 TEXT, score1 INTEGER, score2 INTEGER, score3 INTEGER, score4 INTEGER, score5 INTEGER, score6 INTEGER, score7 INTEGER, score8 INTEGER, score9 INTEGER, score10 INTEGER, strikes INTEGER, spares INTEGER, opens INTEGER, splits INTEGER, splitConv INTEGER, firstBallAve REAL, hash TEXT)''')
			c.execute('''CREATE TABLE summary (id INTEGER PRIMARY KEY, date TEXT, num_games INTEGER, average REAL, std_dev REAL, high_game INTEGER, high_series INTEGER, ave_strikes REAL, ave_spares REAL, ave_opens REAL, ave_splits REAL, splitConv_percent REAL, firstBallAve REAL)''')
			print "Creating the database"
			conn.commit()
		except sqlite3.OperationalError:
			print "game_data table already exists"

	#create_mode_exit = False
	## for now don't allow the user to change the name of the database
	#create_mode_exit = True
	#while create_mode_exit == False:
	#	db_name = raw_input('Enter the database name (or \'q\' to quit): ')
	#	if db_name == 'q':
	#		create_mode_exit = True
	#	else:
	#		ok_to_create = verify_path(db_name)
	#		if ok_to_create == True:
	#			print "creating %s" % db_name
	#			# call to actually create the database will go here.
	#			create_mode_exit = True

	create_db()

def list_mode(min_score, max_score):
	conn = sqlite3.connect('bowling.db')
	c = conn.cursor()
	c.execute('SELECT * FROM game_data WHERE score10 BETWEEN ? AND ?', (min_score,max_score))
	disp_selected(c)

def listseries_mode(min_ser, max_ser):
	conn = sqlite3.connect('bowling.db')
	c = conn.cursor()
	c.execute('SELECT * FROM summary WHERE high_series BETWEEN ? AND ?', (min_ser,max_ser))
	disp_summary(c)

def last_mode(num):
	conn = sqlite3.connect('bowling.db')
	c = conn.cursor()
	c.execute('SELECT * FROM (SELECT * FROM game_data ORDER BY id DESC LIMIT ?) ORDER BY id ASC', (num,))
	disp_selected(c)

def disp_summary(c):
	num_games = 0
	total_score = 0

	print "   i      date      #    Ave     dev   game  ser    X    /    O    S    S/%   FBA"
	#		db_values = (None, date, num_games, ave, std_dev, high_game, high_series, strike_ave, spare_ave, open_ave, split_ave, splitconv_ave, fba)

	for row in c:
		print "%4i   %s  %2i   %.1f   %4.1f    %3i  %3i   %.1f  %.1f  %.1f  %.1f  %4.1f   %.1f" % row
		num_games += row[2]
		total_score += ( row[2] * row[3] )

	print "  Average: %4.1f" % (1.0 * total_score / num_games)

def summary_mode(days, offset):
	conn = sqlite3.connect('bowling.db')
	c = conn.cursor()
	if days == 0:
		##  select all in ascending order
		c.execute('select * from summary')
	else:
		##  select last 10 in descending order
		#c.execute('SELECT * FROM (SELECT * FROM summary ORDER BY id DESC) LIMIT 10')
		##  select last 10 in ascending order
		#c.execute('SELECT * FROM (SELECT * FROM (SELECT * FROM summary ORDER BY id DESC) LIMIT ?) ORDER BY id ASC', (days,))
		#SELECT * FROM (SELECT * FROM (SELECT * FROM summary ORDER BY id DESC) LIMIT 14) ORDER BY id ASC LIMIT 10
		#SELECT * FROM (SELECT * FROM summary ORDER BY id DESC LIMIT 14) ORDER BY id ASC LIMIT 10
		c.execute('SELECT * FROM (SELECT * FROM summary ORDER BY id DESC LIMIT ?) ORDER BY id ASC LIMIT ?', (days+offset,days))
	print "   i      date      #    Ave     dev   game  ser    X    /    O    S    S/%   FBA"
	#		db_values = (None, date, num_games, ave, std_dev, high_game, high_series, strike_ave, spare_ave, open_ave, split_ave, splitconv_ave, fba)

	num_games = 0
	total_score = 0

	for row in c:
		print "%4i   %s  %2i   %.1f   %4.1f    %3i  %3i   %.1f  %.1f  %.1f  %.1f  %4.1f   %.1f" % row
		num_games += row[2]
		total_score += ( row[2] * row[3] )

	print "  Average: %4.1f" % (1.0 * total_score / num_games)

def day_mode(index):
	conn = sqlite3.connect('bowling.db')
	c = conn.cursor()
	c.execute('select date from summary where id == ?', (index,))
	for row in c:
		date = row[0]
	c.execute('select * from game_data where date == ?', (date,))
	disp_selected(c)
		
def import_mode(file_to_import):
	if os.path.isfile(file_to_import):
		f = open(file_to_import, "r")
		if not os.path.isfile('bowling.db'):
			print "Database does not exist"
			create_mode()
		conn = sqlite3.connect('bowling.db')
		c = conn.cursor()

		# initialize counters
		num_dupes = 0
		num_new = 0

		# get the list of hashes from the database
		hash_itera = c.execute('select hash from game_data')
		hash_list = []
		for h in hash_itera:
			hash_list.append(h[0])

		for line in f:
			#print line.split()
			## quit when a blank line is reached
			if line.split() == []:
				break

			## only accept games that are defined (not just scores)
			if len(line.split()) != 5:
				continue

			photo, date, num, game, score = line.split()

			## handle games that only have scores eventually
			if photo == '---':
				continue
			
			## add the line to the database
			a = [x for x in game]
			rest_of_values = calc_game(a[:])

			## double-check the calculation of the score
			if int(score) != rest_of_values[-7]:
				print "check %s %s %s %s %s - %i" % (photo, date, num, game, score, rest_of_values[-7])

			## db_entry = b + n + s + [strikes, spares, opens, splits, splits_converted, first_ball_ave]
			## double check the counts (X,/,S)
			c_str = game.count('X') + game.count('x')
			c_spr = game.count('/')
			#print rest_of_values[:21]
			t_game = rest_of_values[:21]
			c_opn = 0
			for i in range(10):
				if i != 9:
					temp = t_game[2*i:2*i+2]
				else:
					temp = t_game[2*i:2*i+3]
				if temp.count('X') == 0 and temp.count('x') == 0 and temp.count('/') == 0:
					c_opn += 1
			if c_str != rest_of_values[-6]:
				print c_str, rest_of_values[-6]
			if c_spr != rest_of_values[-5]:
				print c_spr, rest_of_values[-5]
			if c_opn != rest_of_values[-4]:
				print c_opn, rest_of_values[-4]

			# determine the md5 hash
			string_to_hash = "%s %s %s" % (date, num, game)
			m = hashlib.md5()
			m.update(string_to_hash)
			hash = m.hexdigest()
			del m

			# check here to see if it is game is unique
			if hash in hash_list:
				#print "Dupe!"
				num_dupes += 1
			else:
				db_values = [None, date, num, game] + rest_of_values + [hash]
				c.execute('insert into game_data values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', db_values)
				num_new += 1
		# commit the changes after all the games have been imported to prevent lots of little writes
		conn.commit()
		print "Imported %s - %i new, %i dupes" % (file_to_import, num_new, num_dupes)
	else:
		print "File does not exist"

def update_summary():
	print "updating summary"
	data_date_list = []
	summary_date_list = []
	conn = sqlite3.connect('bowling.db')
	c = conn.cursor()
	c.execute('select distinct date from game_data')
	for row in c:
		data_date_list.append(row[0])
	
	c.execute('select distinct date from summary')
	for row in c:
		summary_date_list.append(row[0])
	
	#print data_date_list
	#print summary_date_list

	no_update_counter = 0
	update_counter = 0

	for date in data_date_list:
		if date in summary_date_list:
			#print "doing nothing, %s already in summary" % date
			no_update_counter += 1
		else:
			#print "Adding %s to summary" % date
			update_counter += 1

			# initialize sums
			score_sum = 0
			strike_sum = 0
			spare_sum = 0
			open_sum = 0
			split_sum = 0
			splitconv_sum = 0
			fba_sum = 0

			num_games = 0
			game_array = []
			high_series = -1
			std_dev = 0

			# Select all games with date to do summary calculations
			c.execute('select score10,strikes,spares,opens,splits,splitConv,firstBallAve from game_data where date=?', (date,))
			for row in c:
				#print row
				num_games += 1
				game_array.append(row[0])
				score_sum += row[0]
				strike_sum += row[1]
				spare_sum += row[2]
				open_sum += row[3]
				split_sum += row[4]
				splitconv_sum += row[5]
				fba_sum += row[6]
			# calc averages
			ave = 1.0 * score_sum / num_games
			strike_ave = 1.0 * strike_sum / num_games
			spare_ave = 1.0 * spare_sum / num_games
			open_ave = 1.0 * open_sum / num_games
			split_ave = 1.0 * split_sum / num_games
			# calculate split conversion percentage
			if split_sum > 0:
				splitconv_percent = 100.0 * splitconv_sum / split_sum
			else:
				splitconv_percent = 0.0
			#print "split_sum = %i; splitconv_sum = %i; splitconv_percent = %f" % (split_sum, splitconv_sum, splitconv_percent)
			fba = fba_sum / num_games
			# calc high series
			if num_games > 2:
				for i in range(len(game_array)-2):
					temp = game_array[i:i+3]
					hs = temp[0] + temp[1] + temp[2]
					if hs > high_series:
						high_series = hs
			# calc std_dev
			sum = 0
			for game in game_array:
				sum += (game - ave) * (game - ave) * 1.0
			std_dev = sqrt(1.0 * sum / num_games)
			# calc high game
			high_game = max(game_array)
			
			db_values = (None, date, num_games, ave, std_dev, high_game, high_series, strike_ave, spare_ave, open_ave, split_ave, splitconv_percent, fba)
			c.execute('insert into summary values (?,?,?,?,?,?,?,?,?,?,?,?,?)', db_values)
	# commit all the changes
	conn.commit()


def disp_selected(c):
	print "   i     Date     #  | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Score X  /  O  S  S/  FBA"
	for row in c:
		#print row
		index = row[0]
		#print index
		date = row[1]
		#print date
		game_num = row[2]
		#print game_num
		game_str = row[3]
		#print game_str
		ball_array = row[4:25]
		#print ball_array
		note_array = row[25:35]
		#print note_array
		score_array = row[35:45]
		#print score_array
		strikes = row[45]
		#print strikes
		spares = row[46]
		#print spares
		opens = row[47]
		#print opens
		splits = row[48]
		#print splits
		splits_converted = row[49]
		#print splits_converted
		first_ball_ave = row[50]
		#print first_ball_ave

		# convert game array to a list
		g_a = list(ball_array)
		#print "".join(g_a)

		# index and date
		disp_str0 = "%4i  %s %2i" % (index, date, game_num)

		# Add the notes to the game_array list
		a = range(10)
		a.reverse()
		for x in a:
			g_a.insert(2*x,note_array[x])
			g_a.insert(2*x,' ')
		disp_str1 = "".join(g_a)
		#print disp_str1

		# Append the total score and calulated stats
		#print [str(x) for x in row[44:]] 
		##calcs = [str(x) for x in row[44:]] 
		##disp_str2 = " ".join(calcs)
		#disp_str2 = "%4i %2i %2i %2i %2i %2i %5.1f  %s" % row[44:]
		disp_str2 = "%4i %2i %2i %2i %2i %2i %5.1f" % row[44:-1]

		print "%s  %s  %s" % (disp_str0, disp_str1, disp_str2)

def ave_mode():
		# connect to database
		conn = sqlite3.connect('bowling.db')
		c = conn.cursor()

		# average last 10 games
		c.execute('SELECT * FROM (SELECT id,score10 FROM game_data ORDER BY id DESC LIMIT 10) ORDER BY id ASC')
		ave10 = 0
		for row in c:
			ave10 += row[1] / 10.0
		#print ave10

		# average last 50 games
		c.execute('SELECT * FROM (SELECT id,score10 FROM game_data ORDER BY id DESC LIMIT 50) ORDER BY id ASC')
		ave50 = 0
		for row in c:
			ave50 += row[1] / 50.0
		#print ave50

		# average last 100 games
		c.execute('SELECT * FROM (SELECT id,score10 FROM game_data ORDER BY id DESC LIMIT 100) ORDER BY id ASC')
		ave100 = 0
		for row in c:
			ave100 += row[1] / 100.0
		#print ave100

		# average all games
		c.execute('SELECT id,score10 FROM game_data')
		sumAll = 0
		counter = 0
		for row in c:
			sumAll += row[1]
			counter += 1
		aveAll = 1.0 * sumAll / counter
		#print aveAll
		num_games = counter

		# average last 3 sessions
		c.execute('SELECT * FROM (SELECT id,num_games,average FROM summary ORDER BY id DESC LIMIT 3) ORDER BY id ASC')
		sum3 = 0
		counter = 0
		for row in c:
			sum3 += row[2] * row[1]
			counter += row[1]
		ave3 = 1.0 * sum3 / counter
		#print ave3

		# average last 15 sessions
		c.execute('SELECT * FROM (SELECT id,num_games,average FROM summary ORDER BY id DESC LIMIT 15) ORDER BY id ASC')
		sum15 = 0
		counter = 0
		for row in c:
			sum15 += row[2] * row[1]
			counter += row[1]
		ave15 = 1.0 * sum15 / counter
		#print ave15

		# average last 30 sessions
		c.execute('SELECT * FROM (SELECT id,num_games,average FROM summary ORDER BY id DESC LIMIT 30) ORDER BY id ASC')
		sum30 = 0
		counter = 0
		for row in c:
			sum30 += row[2] * row[1]
			counter += row[1]
		ave30 = 1.0 * sum30 / counter
		#print ave30

		# average over all sessions to doublecheck 1st all average calc
		c.execute('SELECT id,num_games,average FROM summary')
		allSum = 0
		counter = 0
		num_days = 0
		for row in c:
			allSum += row[2] * row[1]
			counter += row[1]
			num_days += 1
		allAve = 1.0 * allSum / counter
		#print allAve

		if aveAll != allAve:
			print "Error with average calc"

		# print averages in a table
		print "Last 10 games:  %4.1f\tLast 3 days:  %4.1f" % (ave10, ave3)
		print "Last 50 games:  %4.1f\tLast 15 days: %4.1f" % (ave50, ave15)
		print "Last 100 games: %4.1f\tLast 30 days: %4.1f" % (ave100, ave30)
		print "All-time ave:   %4.1f\t(%i games, %i days)" % (allAve, num_games, num_days)

def dist_mode():
		print "something"
		dist_array = []

		# connect to the database
		conn = sqlite3.connect('bowling.db')
		c = conn.cursor()
		
		last_s = 0
		resolution = 5
		for s in range(resolution,301,resolution):
			## the following line is bad because it double-counts values
			#c.execute('SELECT score10 FROM game_data WHERE score10 BETWEEN ? AND ?', (last_s, s))
			c.execute('SELECT score10 FROM game_data WHERE score10 BETWEEN ? AND ?', (last_s, s - 0.5))

			counter = 0
			for row in c:
				counter += 1

			dist_array.append(counter)

			last_s = s

		print dist_array

		for i in range(len(dist_array)):
			print i*resolution, dist_array[i]

		if okToGraph:
			#plot(range(0,300,resolution),dist_array)
			bar(range(0,300,resolution),dist_array,width=resolution)
			show()

def hist_mode():
	score_array = []


	# connect to the database
	conn = sqlite3.connect('bowling.db')
	c = conn.cursor()

	c.execute('SELECT score10 FROM game_data')

	for s in c:
		score_array.append(s[0])
	
	#print min(score_array)
	#print max(score_array)

	#a_bins = range(0,300,5)
	#a_bins = range(90,250,5)
	a_bins = range(100,240,5)

	hist(score_array,bins=a_bins)
	show()

def plotave_mode():
	ave_array = []

	# connect to the database
	conn = sqlite3.connect('bowling.db')
	c = conn.cursor()

	c.execute('SELECT average FROM summary')

	for ave in c:
		ave_array.append(ave[0])
	
	plot(ave_array)
	show()

def gamenumdist_mode(num):
	conn = sqlite3.connect('bowling.db')
	c = conn.cursor()

	# since I don't know the maximum number of games there will be in one day, I have to determine it
	max_games = 0
	c.execute('SELECT DISTINCT num_games FROM summary')
	for i in c:
		if i[0] > max_games:
			max_games = i[0]
	#print max_games

	# nums [ [] ]
	# nums[1] = [games, total_score, strikes, spares, opens, splits, splits_converted, fba_sum]
	gamenum_totals = []
	for i in range(max_games):
		gamenum_totals.append([0,0,0,0,0,0,0,0])

	if num == 0:
		#c.execute('SELECT * FROM game_data')
		c.execute('SELECT game_num,score10,strikes,spares,opens,splits,splitConv,firstBallAve FROM game_data')
	else:
		c.execute('SELECT * FROM (SELECT * FROM game_data ORDER BY id DESC LIMIT ?) ORDER BY id ASC', (num,))
	
	for g in c:
		gamenum = g[0] - 1
		# gamenum is -1 for games that I just practiced
		if gamenum < 0:
			continue
		# increment number of games with this game number
		gamenum_totals[gamenum][0] += 1
		# add score to total_score
		gamenum_totals[gamenum][1] += g[1]
		# add strikes
		gamenum_totals[gamenum][2] += g[2]
		# add spares
		gamenum_totals[gamenum][3] += g[3]
		# add opens
		gamenum_totals[gamenum][4] += g[4]
		# add splits
		gamenum_totals[gamenum][5] += g[5]
		# add conversions
		gamenum_totals[gamenum][6] += g[6]
		# add fba
		gamenum_totals[gamenum][7] += g[7]

	## display game stats as rows
	#for i in range(len(gamenum_totals)):
	#	print i+1, gamenum_totals[i]
	#print

	# display game stats as columns
	labels = {0:'Number  ',
			  1:'Score   ',
	          2:'Strikes ',
			  3:'Spares  ',
			  4:'Opens   ',
			  5:'Splits  ',
			  6:'Conv\'s  ',
			  7:'FBA     '}
	print 'Game    ' + "".join(["%4i   " % x for x in range(1,max_games+1)])
	for i in range(0,8):
		str = ""
		for j in range(max_games):
			if i == 0:
				temp_str = "%4i   " % gamenum_totals[j][i]
			elif i == 1:
				temp_str = " %5.1f " % (gamenum_totals[j][i] / gamenum_totals[j][0])
			else:
				temp_str = "%5.1f  " % (gamenum_totals[j][i] / gamenum_totals[j][0])
			if j == 0:
				temp_str = labels[i] + temp_str
			str += temp_str
		print str

def framedist_mode(num):
	conn = sqlite3.connect('bowling.db')
	c = conn.cursor()
	if num == 0:
		c.execute('SELECT * FROM game_data')
	else:
		c.execute('SELECT * FROM (SELECT * FROM game_data ORDER BY id DESC LIMIT ?) ORDER BY id ASC', (num,))

	counter = 0
	str = [0] * 10
	spa = [0] * 10
	ope = [0] * 10
	spl = [0] * 10
	con = [0] * 10
	str_b_strike = 0
	str_b_spare = 0
	spa_b_strike = 0
		
	for row in c:
		ball_array = row[4:25]
		#print ball_array
		note_array = row[25:35]
		#print note_array

		# do 1st 9 frames
		for i in range(9):
			# check str
			if ball_array[2*i] == 'X' or ball_array[2*i] == 'x':
				str[i] += 1
			elif ball_array[2*i+1] == '/':
				spa[i] += 1
			else:
				ope[i] += 1
			if note_array[i] == 'S' or note_array[i] == 's':
				spl[i] += 1
				if ball_array[2*i+1] == '/':
					con[i] += 1

		# do 10th frame separately ball_array[18,19,20]
		if ball_array[18] == 'X' or ball_array[18] == 'x':
			str[9] += 1
			if ball_array[19] == 'X' or ball_array[19] == 'x':
				str_b_strike += 1
			elif ball_array[20] == '/':
				str_b_spare += 1
		elif ball_array[19] == '/':
			spa[9] += 1
			if ball_array[20] == 'X' or ball_array[20] == 'x':
				spa_b_strike += 1
		else:
			ope[9] += 1
		# note: there is some ambiguity due to the fact that the
		# automated scorer doesn't distinguish between splits on
		# the first ball or the last ball (assuming no strikes)
		if note_array[9] == 'S' or note_array[9] == 's':
			spl[9] += 1
			if ball_array[19] == '/' or ball_array[20] == '/':
				con[9] += 1
		
		counter += 1

	#print str
	strike_percent = [1.0 * x / counter for x in str]
	#print spa
	spare_percent = [1.0 * x / counter for x in spa]
	#print ope
	open_percent = [1.0 * x / counter for x in ope]
	#print spl
	split_percent = [1.0 * x / counter for x in spl]
	#print con
	splitconv_percent = [1.0 * x / counter for x in con]

	#print str, str_b_strike, str_b_spare
	#print spa, spa_b_strike

	# if there are no strikes, there can't be any bonus strikes, so to avoid divide-by-zero error, set denom to 1
	if str[9] == 0:
		str_denom = 1
	else:
		str_denom = str[9]
	# do the same with spares (these cases only an issue with framedist <low_number>)
	if spa[9] == 0:
		spa_denom = 1
	else:
		spa_denom = spa[9]

	print "10th frame strike %\tBonus strike %\tBonus spare %"
	print "%.2f\t\t\t%.2f\t\t%.2f" % ((1.0 * str[9] / counter), (1.0 * str_b_strike / str_denom), (1.0 * str_b_spare / str_denom))

	print "10th frame spare %\tBonus strike %"
	print "%.2f\t\t\t%.2f" % ((1.0 * spa[9] / counter), (1.0 * spa_b_strike / spa_denom))

	# Plot the percentages
	xlabel('Frame')
	ylabel('Percent')
	x_axis = range(1,11)
	#figure(1)
	#subplot(2,1,1)
	#plot(strike_percent,label="Strike %")
	#plot(spare_percent,label="Spare %")
	#plot(open_percent,label="Open %")
	plot(x_axis, strike_percent,'gs-',label="Strike %")
	plot(x_axis, spare_percent,'b^-',label="Spare %")
	plot(x_axis, open_percent,'ro-',label="Open %")
	#subplot(2,1,2)
	#plot(split_percent,label="Split %")
	#plot(splitconv_percent,label="Conversion %")
	plot(x_axis, split_percent,'co-',label="Split %")
	plot(x_axis, splitconv_percent,'m^-',label="Conversion %")
	#legend()
	show()
	
def plotrunave_mode(num):
	# connect to the database
	conn = sqlite3.connect('bowling.db')
	c = conn.cursor()

	c.execute('SELECT id,num_games,average FROM summary')

	the_list = []

	for row in c:
		the_list.append(row)
	
	#print the_list

	## for i in range(len(list)-num+1):
	##	print list[i:i+num]

	running_ave = []
	index = []
	# loop over groups of days of length num
	for i in range(len(the_list)-num+1):
		# each item in current_block is a tuple (id, #, ave)
		current_block = the_list[i:i+num]

		# append last id as the index
		index.append(current_block[-1][0])

		current_sum = 0
		counter = 0
		for id,numg,ave in current_block:
			counter += numg
			current_sum += 1.0 * numg * ave

		running_ave.append(1.0 * current_sum / counter)

	#print running_ave
	plot(index, running_ave)
	show()

def calc_mode():
	exit = False
	while exit == False:
		command = raw_input('c> ')
		if command == "":
			comm = 'dummy'
		else:
			comm = command.split()
		if comm[0] == 'quit' or comm[0] == 'exit':
			exit = True
		if comm[0] == 'ave':
			ave_mode()
		if comm[0] == 'dist':
			dist_mode()

def main():
	exit = False
	history = []
	while exit == False:
		prompt = '%i> ' % len(history) 
		command = raw_input(prompt)
		if command != "" and command[0] == '!':
			command = history[int(command[1:])]
			print command
		if command == "":
			comm = 'dummy'
		else:
			history.append(command)
			comm = command.split()
		if comm[0] == 'quit' or comm[0] == 'exit':
			exit = True
		if comm[0] == 'list':
			if len(comm) == 3:
				list_mode(int(comm[1]),int(comm[2]))
			elif len(comm) == 2:
				list_mode(int(comm[1]),300)
			else:
				#print 'selecting all games'
				list_mode(0,300)
		if comm[0] == 'listseries':
			if len(comm) == 3:
				listseries_mode(int(comm[1]),int(comm[2]))
			elif len(comm) == 2:
				listseries_mode(int(comm[1]),900)
			else:
				#print 'selecting all games'
				listseries_mode(0,900)
		if comm[0] == 'last':
			if len(comm) == 2:
				last_mode(int(comm[1]))
			else:
				last_mode(10)
		if comm[0] == 'ave':
			ave_mode()
		if comm[0] == 'summary':
			if len(comm) == 1:
				#print 'selecting all games'
				#summary_mode(0)
				summary_mode(10, 0)
			elif len(comm) == 2:
				summary_mode(int(comm[1]), 0)
			else:
				summary_mode(int(comm[1]),int(comm[2]))
		if comm[0] == 'day':
			if len(comm) == 2:
				day_mode(int(comm[1]))
			else:
				print "Usage: day <index>"
		if comm[0] == 'dist':
			dist_mode()
			#th = Thread(None, dist_mode)
			#th.run()
		if comm[0] == 'hist':
			hist_mode()
		if comm[0] == 'plotave':
			plotave_mode()
			#th = Thread(None, plotave_mode)
			#th.run()
		if comm[0] == 'framedist':
			if len(comm) == 1:
				# do all
				framedist_mode(0)
			else:
				# do some
				framedist_mode(int(comm[1]))
		if comm[0] == 'gamenumdist':
			# do all
			gamenumdist_mode(0)
		if comm[0] == 'plotrunave':
			if len(comm) == 1:
				# assume 10 days
				plotrunave_mode(10)
			else:
				plotrunave_mode(int(comm[1]))
		if comm[0] == 'import':
			try:
				import_mode(comm[1])
			except IndexError:
				print "Usage: import <file_to_import>"
			update_summary()
		if comm[0] == 'add':
			print 'entering adding mode'
			add_mode()
		if comm[0] == 'calc':
			print 'entering calc mode'
			calc_mode()
		if comm[0] == 'create':
			#print 'entering create mode'
			create_mode()
		if comm[0] == 'history':
			for i in range(len(history)):
				print "  %3i\t%s" % (i, history[i])
		if comm[0] == 'help':
			print
			print '=======\t\t==========='
			print 'Command\t\tDescription'
			print '=======\t\t==========='
			#print 'create\t\tenter create mode'
			print 'import\t\timport games from txt file'
			#print 'add\t\tenter add mode'
			print 'list\t\tdisplay all games'
			print 'summary\t\tdisplay all days'
			print 'calc\t\tenter calc mode'
			print 'help\t\tdisplay this message'
			print

num_args = len(sys.argv) - 1

if num_args > 0:
	print 'Usage: program.py'
	print
	print 'there are no arguments. running the command will get you'
	print 'a prompt.  the following commands might be useful'
else:
	main()
