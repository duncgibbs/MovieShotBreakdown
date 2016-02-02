import subprocess as sp
import numpy as np
import cv2
import pylab as plt #debug
import os
from scipy.spatial import distance as dist
import sys
import re

fileName = sys.argv[1]

FFMPEG_BIN = "ffmpeg"

command = [FFMPEG_BIN,'-i',fileName]
proc = sp.Popen(command,stdout=sp.PIPE, stderr=sp.PIPE)
proc.stdout.readline()
proc.terminate()
infos = proc.stderr.read()
(x,y) = re.search('\s\d+x\d+\s',infos).group(0).split('x')
resolution = [int(x), int(y)]

command = [FFMPEG_BIN, '-i', fileName,'-f','image2pipe','-pix_fmt','rgb24','-vcodec','rawvideo','-']
pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=10**8)

frame = 1
shot = 1
differences = []
differenceMean = 0
dirname = 'Shot_1'
os.mkdir(dirname)

raw_image = pipe.stdout.read(resolution[0]*resolution[1]*3)
imageOne = np.fromstring(raw_image, dtype='uint8')
imageOne = imageOne.reshape((resolution[1],resolution[0],3))
pipe.stdout.flush()

while True:

	frame += 1

	raw_image = pipe.stdout.read(resolution[0]*resolution[1]*3)

	if not raw_image:
		break;

	imageTwo = np.fromstring(raw_image, dtype='uint8')
	imageTwo = imageTwo.reshape((resolution[1],resolution[0],3))
	pipe.stdout.flush()

	greyOne = cv2.cvtColor(imageOne, cv2.COLOR_BGR2RGB)
	histOne = cv2.calcHist([greyOne],[0,1,2],None,[16,16,16],[0,256,0,256,0,256])
	histOne = cv2.normalize(histOne).flatten()

	greyTwo = cv2.cvtColor(imageTwo, cv2.COLOR_BGR2RGB)
	histTwo = cv2.calcHist([greyTwo],[0,1,2],None,[16,16,16],[0,256,0,256,0,256])
	histTwo = cv2.normalize(histTwo).flatten()

	#differenceRating = dist.chebyshev(histOne,histTwo)
	differenceRating = dist.euclidean(histOne,histTwo)**2

	if differenceRating > differenceMean*30 and differenceMean > 0:
		differences = []
		differenceMean = 0
		shot += 1
		dirname = 'Shot_' + str(shot);
		os.mkdir(dirname)
	else:
		differences += [differenceRating]
		differenceMean = sum(differences)/len(differences)

	# if len(differences) > 1 and (differenceRating > (sum(differences)/len(differences))*7 and (sum(differences)/len(differences)) > 0):
	# 	differences = []
	# 	shot += 1
	# 	dirname = 'Shot_' + str(shot);
	# 	os.mkdir(dirname)
	# else:
	# 	differences += [differenceRating]

	print 'FR: ' + str(frame) + ' --- ' + 'DR: ' + str(differenceRating*100) + ' --- ' + 'MEAN: ' + str(differenceMean*100)

	cv2.imwrite(os.path.join(dirname,'Frame_' + str(frame) + ' - ' + str(differenceRating*100) + '.png'),greyTwo)
	#cv2.imwrite('Frame_' + str(frame) + ' - ' + str(differenceRating*100) + '.png',greyTwo)

	imageOne = imageTwo

pipe.terminate()