#! /usr/bin/env python

import sys
import os.path
import sqlite3
import hashlib
from math import sqrt

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
			c.execute('''CREATE TABLE summary (id INTEGER PRIMARY KEY, date TEXT, num_games INTEGER, average REAL, std_dev REAL, high_series INTEGER, ave_strikes REAL, ave_spares REAL, ave_opens REAL, ave_splits REAL, ave_splitConv REAL, firstBallAve REAL)''')
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

def list_mode(min_score):
	conn = sqlite3.connect('bowling.db')
	c = conn.cursor()
	c.execute('select * from game_data where score10 >= ?', (min_score,))
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

			## double check the counts (X,/,S)

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
	
	print data_date_list
	print summary_date_list

	no_update_counter = 0
	update_counter = 0

	for date in data_date_list:
		if date in summary_date_list:
			print "doing nothing, %s already in summary" % date
			no_update_counter += 1
		else:
			print "Adding %s to summary" % date
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
				print row
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
			splitconv_ave = 1.0 * splitconv_sum / num_games
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
			
			db_values = (None, date, num_games, ave, std_dev, high_series, strike_ave, spare_ave, open_ave, split_ave, splitconv_ave, fba)
			c.execute('insert into summary values (?,?,?,?,?,?,?,?,?,?,?,?)', db_values)
	# commit all the changes
	conn.commit()


def disp_selected(c):
	print "  1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Score X  /  O  S  S/  FBA"
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

		print "%s  %s" % (disp_str1, disp_str2)

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
		if comm[0] == '190':
			conn = sqlite3.connect('bowling.db')
			c = conn.cursor()
			c.execute('select * from game_data where score10 > 190')
			disp_selected(c)

def main():
	exit = False
	while exit == False:
		command = raw_input('> ')
		if command == "":
			comm = 'dummy'
		else:
			comm = command.split()
		if comm[0] == 'quit' or comm[0] == 'exit':
			exit = True
		if comm[0] == 'list':
			if len(comm) != 2:
				#print 'selecting all games'
				list_mode(0)
			else:
				list_mode(int(comm[1]))
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
		if comm[0] == 'help':
			print
			print '=======\t\t==========='
			print 'Command\t\tDescription'
			print '=======\t\t==========='
			print 'create\t\tenter create mode'
			print 'import\t\timport games from txt file'
			print 'add\t\tenter add mode'
			print 'list\t\tdisplay all games'
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
