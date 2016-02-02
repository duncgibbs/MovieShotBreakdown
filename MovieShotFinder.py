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

videoFPS = float(re.search('\S+\sfps',infos).group(0).split(' ')[0])

command = [FFMPEG_BIN, '-i', fileName,'-f','image2pipe','-pix_fmt','rgb24','-vcodec','rawvideo','-']
pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=10**8)

frame = 1
shot = 1
differences = []
differenceMean = 0

shots = []

#DEBUG
#dirname = 'Shot_1'
#os.mkdir(dirname)

raw_image = pipe.stdout.read(resolution[0]*resolution[1]*3)
imageOne = np.fromstring(raw_image, dtype='uint8')
imageOne = imageOne.reshape((resolution[1],resolution[0],3))
pipe.stdout.flush()

while True:

	if len(differences) == 100:
		differences = differences[1:]

	frame += 1

	raw_image = pipe.stdout.read(resolution[0]*resolution[1]*3)

	if not raw_image:
		shots += [(frame-1)/videoFPS]
		break;

	imageTwo = np.fromstring(raw_image, dtype='uint8')
	imageTwo = imageTwo.reshape((resolution[1],resolution[0],3))
	pipe.stdout.flush()

	recoloredOne = cv2.cvtColor(imageOne, cv2.COLOR_BGR2RGB)
	greyOne 	 = cv2.cvtColor(imageOne, cv2.COLOR_BGR2GRAY)
	colorHistOne = cv2.calcHist([recoloredOne],[0,1,2],None,[16,16,16],[0,256,0,256,0,256])
	colorHistOne = cv2.normalize(colorHistOne).flatten()
	greyHistOne  = cv2.calcHist([greyOne],[0],None,[256],[0,256])
	greyHistOne  = cv2.normalize(greyHistOne)

	recoloredTwo = cv2.cvtColor(imageTwo, cv2.COLOR_BGR2RGB)
	greyTwo 	 = cv2.cvtColor(imageTwo, cv2.COLOR_BGR2GRAY)
	colorHistTwo = cv2.calcHist([recoloredTwo],[0,1,2],None,[16,16,16],[0,256,0,256,0,256])
	colorHistTwo = cv2.normalize(colorHistTwo).flatten()
	greyHistTwo  = cv2.calcHist([greyTwo],[0],None,[256],[0,256])
	greyHistTwo  = cv2.normalize(greyHistTwo)

	colorDifferenceRating = dist.euclidean(colorHistOne,colorHistTwo)
	greyDifferenceRating  = dist.euclidean(greyHistOne,greyHistTwo)**2
	differenceRating 	  = (colorDifferenceRating*greyDifferenceRating)


	if differenceRating > differenceMean*100 and differenceMean > 0 and differenceRating > (differences[len(differences)-1]*80) and differenceRating > .001:
		#DEBUG
		#print str((frame-1)/videoFPS) + ' seconds (' + str(frame-1) + ' frames at ' + str(videoFPS) + ' frames per second)'

		differences    = []
		differenceMean = 0
		shot 		   += 1
		shots 		   += [(frame-1)/videoFPS]
		frame 		   = 0

		#DEBUG
		#dirname = 'Shot_' + str(shot);
		#os.mkdir(dirname)
	else:
		differences += [differenceRating]
		differenceMean = sum(differences)/len(differences)

	#DEBUG
	#print 'FR: ' + str(frame) + ' --- ' + 'DR: ' + str(differenceRating*100) + ' --- ' + 'MEAN: ' + str(differenceMean*100)
	#cv2.imwrite(os.path.join(dirname,'Frame_' + str(frame) + ' - ' + str(differenceRating) + '.png'),recoloredTwo)

	imageOne = imageTwo

pipe.terminate()
print '# OF SHOTS: ' + str(len(shots)) + ' - AVG. TAKE LENGTH: ' + str("{0:.2f}".format(sum(shots)/len(shots))) + ' seconds'
