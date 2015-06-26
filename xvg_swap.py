#generic python modules
import argparse
import operator
from operator import itemgetter
import sys, os, shutil
import os.path

##########################################################################################
# RETRIEVE USER INPUTS
##########################################################################################

#=========================================================================================
# create parser
#=========================================================================================
version_nb = "0.0.1"
parser = argparse.ArgumentParser(prog = 'xvg_concatenate', usage='', add_help = False, formatter_class = argparse.RawDescriptionHelpFormatter, description =\
'''
**********************************************
v''' + version_nb + '''
author: Jean Helie (jean.helie@bioch.ox.ac.uk)
git: https://github.com/jhelie/xvg_swap
**********************************************

DESCRIPTION
	Swaps two columns in an xvg file.


REQUIREMENTS
	Numpy
 
USAGE

Option	      Default  	Description                    
-----------------------------------------------------
-f			: xvg file(s)
--captions		: captions of columns to swap (format: "cation 1","caption 2")
--indices		: indices of columns to swap (format: i,j)
--comments	@,#	: lines starting with these characters will be considered as comment

Other options
-----------------------------------------------------
--version		: show version number and exit
-h, --help		: show this menu and exit
 
''')

#options
parser.add_argument('-f', nargs='+', dest='xvgfilenames', help=argparse.SUPPRESS, required=True)
parser.add_argument('--index', nargs=1, dest='indices', default=['none'], help=argparse.SUPPRESS)
parser.add_argument('--caption', nargs=1, dest='captions', default=['none'], help=argparse.SUPPRESS)
parser.add_argument('--log', dest='log', action='store_true', help=argparse.SUPPRESS)
parser.add_argument('--comments', nargs=1, dest='comments', default=['@,#'], help=argparse.SUPPRESS)

#other options
parser.add_argument('--version', action='version', version='%(prog)s v' + version_nb, help=argparse.SUPPRESS)
parser.add_argument('-h','--help', action='help', help=argparse.SUPPRESS)

#=========================================================================================
# store inputs
#=========================================================================================

args = parser.parse_args()
args.indices = args.indices[0]
args.captions = args.caption[0]
args.comments = args.comments[0].split(',')

#=========================================================================================
# import modules (doing it now otherwise might crash before we can display the help menu!)
#=========================================================================================

#generic science modules
try:
	import numpy as np
except:
	print "Error: you need to install the np module."
	sys.exit(1)

#=======================================================================
# sanity check
#=======================================================================

index_used = False
for f in args.xvgfilenames:
	if not os.path.isfile(f):
		print "Error: file " + str(f) + " not found."
		sys.exit(1)

if args.indices == "none" and args.captions == "none":
	print "Error: either --indices or --captions must be specified, see --help."
	sys.exit(1)

if args.indices != "none" and args.captions != "none":
	print "Error: either --indices or --captions must be specified, see --help."
	sys.exit(1)

if args.indices != "none":
	try:
		index_used = True
		global index_1, index_2
		index_1 = int(args.indices.split(',')[0])
		index_2 = int(args.indices.split(',')[1])
	except:
		print "Error: wrong format for --indices, see --help."
		sys.exit(1)
else:
	try:
		global caption_1, caption_2
		caption_1 = int(args.captions.split(',')[0])
		caption_2 = int(args.captions.split(',')[1])
	except:
		print "Error: wrong format for --captions, see --help."
		sys.exit(1)
	
	
##########################################################################################
# FUNCTIONS DEFINITIONS
##########################################################################################

#=========================================================================================
# data loading
#=========================================================================================

def load_xvg():															#DONE
	
	global label_xaxis
	global label_yaxis
	global data
	global meta

	data = {}
	meta = {}
	label_xaxis = "x axis"
	label_yaxis = "y axis"
	
	for f_index in range(0,len(args.xvgfilenames)):
		progress = '\r -reading file ' + str(f_index+1) + '/' + str(len(args.xvgfilenames)) + '                      '  
		sys.stdout.flush()
		sys.stdout.write(progress)
		filename = args.xvgfilenames[f_index]
		tmp_nb_rows_to_skip = 0
		#get file content
		with open(filename) as f:
			lines = f.readlines()
		
		if index_used:
			f_col_to_use_1 = index_1
			f_col_to_use_2 = index_2
			f_col_legend_1 = ""
			f_col_legend_2 = ""
		else:
			f_col_legend_1 = caption_1
			f_col_legend_2 = caption_2
			f_col_legend_1_found = False
			f_col_legend_2_found = False
		
		#determine legends and nb of lines to skip
		for l_index in range(0,len(lines)):
			line = lines[l_index]
			if line[-1] == '\n':
				line = line[:-1]
			if line[0] in args.comments:
				tmp_nb_rows_to_skip += 1
				if "legend \"" in line:
					try:
						tmp_col = int(int(line.split("@ s")[1].split(" ")[0]))
						tmp_name = line.split("legend \"")[1][:-1]
						if index_used == False and tmp_name == caption_1:
							f_col_to_use_1 = tmp_col 
							f_col_legend_found_1 = True
							l_index_1 = l_index
						elif index_used == False and tmp_name == caption_2:
							f_col_to_use_2 = tmp_col 
							f_col_legend_found_2 = True
							l_index_2 = l_index
						elif index_used and index_1 == tmp_col:
							f_col_legend_1 = tmp_name			
							l_index_1 = l_index
						elif index_used and index_2 == tmp_col:
							f_col_legend_2 = tmp_name			
							l_index_2 = l_index
					except:
						print "\nError: unexpected data format in line " + str(l_index) + " in file " + str(filename) + "."
						print " -> " + str(line)
						sys.exit(1)
				if f_index == 0 and "xaxis" in line and  "label " in line:
					label_xaxis = line.split("label ")[1]
				if f_index == 0 and "yaxis" in line and  "label " in line:
					label_yaxis = line.split("label ")[1]

		#get all meta data
		data[f_index] = lines[:tmp_nb_rows_to_skip]
		
		#switch caption
		data[f_index][l_index_1] = "@ s" + str(f_col_to_use_1)) + " legend \"" + str(f_col_legend_2)) + "\"\n"
		data[f_index][l_index_2] = "@ s" + str(f_col_to_use_2)) + " legend \"" + str(f_col_legend_1)) + "\"\n"
				
		#get all data in the file
		data[f_index] = np.loadtxt(filename, skiprows = tmp_nb_rows_to_skip)
									
		#check the column was/can be found
		if index_used:
			if not f_col_to_use_1 < (np.shape(data[f_index])[1] - 1) or not f_col_to_use_2 < (np.shape(data[f_index])[1] - 1):
				print "\nError: --indices set to " + str(f_col_to_use_1) + " and " + str(f_col_to_use_1) + " but file " + str(filename) + " only contains " + str(np.shape(data[f_index])[1] - 1) + " data columns (index should be 0 based)."
				sys.exit(1)
		elif not f_col_legend_found:
			print "\nError: no column with caption \"" + str(f_col_legend_1) + "\" or \"" + str(f_col_legend_2) + "\" could be found in " + str(filename) + "."
			sys.exit(1)

		#switch columns
		data[f_index][:,[f_col_to_use_1 + 1, f_col_to_use_2 + 1]] = data[f_index][:,[f_col_to_use_2 + 1, f_col_to_use_1 + 1]]
			
	return

#=========================================================================================
# outputs
#=========================================================================================

def write_xvg():

	#open files
	for f_index in range(0,len(args.xvgfilenames)):
		filename = args.xvgfilenames[f_index]
		filename_xvg = os.getcwd() + '/' + str(filename[:-4]) + '_swap.xvg'
		output_xvg = open(filename_xvg, 'w')
		
		#general header
		output_xvg.write("# [written by xvg_swap v" + str(version_nb) + "]\n")
		
		#meta
		for l_index in range(0,len(meta[f_index])):
			output_xvg.write(meta[f_index][l_index])
		
		#data
		for r_index in range(0, np.shape(data[f_index])[0]):
			results = str(data[f_index][r_index, 0])
			for c_index in range(1, np.shape(data[f_index])[1]):
				results += "	" + str(data[f_index][r_index, c_index])
			output_xvg.write(results + "\n")		
		output_xvg.close()	
	
	return

##########################################################################################
# MAIN
##########################################################################################

print "\nReading files..."
load_xvg()

print "\n\nWriting concatenated file..."
write_xvg()

#=========================================================================================
# exit
#=========================================================================================
print "\nFinished successfully! Check result in file '" + args.output_file + ".xvg'."
print ""
sys.exit(0)
