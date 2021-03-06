# -*- coding: utf-8 -*-

import os
import numpy as np
import cv2
import pafy
import youtube_dl
import torch, torchvision
import torch
import detectron2
import warnings
warnings.filterwarnings("ignore")

from detectron2.utils.logger import setup_logger
setup_logger()

from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2 import model_zoo

def center(box):
  ''' 
  box: detected bounding box as list.

  Returns: detected object center (x, y).
  '''
  x1, y1, x2, y2 = box
  return (x1 + x2) / 2, (y1 + y2) / 2

def inside_box(box, detection_box):
  ''' 
  box: detected bounding box as list.
  detection_box: detection box bounding box as list

  Returns: True if the detected object is inside of the detection box.
  '''
  x, y = center(box)
  x1, y1, x2, y2 = detection_box
  if (x1 < x < x2) and (y1 < y < y2):
    return True
  return False

if __name__ == '__main__':

  # Current Directory
  CUR_DIR = os.getcwd()

  # Font Configurations
  RED = (0,0,255)
  BLACK = (0,0,0)
  WHITE = (255,255,255)
  FONT = cv2.FONT_HERSHEY_SIMPLEX
  FONT_SIZE = 1
  THICKNESS = 2


  # load video from YouTube
  url = 'https://www.youtube.com/watch?v=PJ5xXXcfuTc&ab_channel=Supercircuits'
  vPafy = pafy.new(url)
  play = vPafy.getbest() # get best resolution

  cap = cv2.VideoCapture(play.url) # video capture

  # Get video resolution
  width = cap.get(3)
  height = cap.get(4)

  # Detection box location and shape
  detection_box = [int(width/2), 500, int(width/2)+200, 540]

  # Get frames' total
  total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) 

  # Set starting frame
  num_frame = 0

  line_old = 0
  objects_old = 'empty'

  # Dict of Vehicles to detect
  objects_dict = {2 : 'car', 3 : 'motorcycle'}

  # Variables to store the counts
  lane_count = 0
  objects_count = {'car' : 0, 'motorcycle' : 0}


  # Model Configuration
  cfg = get_cfg()
  cfg.merge_from_file(model_zoo.get_config_file('COCO-Detection/faster_rcnn_R_50_FPN_1x.yaml'))
  cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5 # set threshold for this model
  cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url('COCO-Detection/faster_rcnn_R_50_FPN_1x.yaml')
  predictor = DefaultPredictor(cfg)

  # Output Configuration
  try:
    os.mkdir(os.path.join(CUR_DIR, 'output'))
  except:
    pass

  OUTPUT_PATH = os.path.join(CUR_DIR, 'output/result.mp4')
  video = cv2.VideoWriter(OUTPUT_PATH, cv2.VideoWriter_fourcc(*'mp4v'), 25, (int(width),int(height)),True)
  
  num_start_frame = 360

  # Detection Start
  while(cap.isOpened()):

    ret, frame = cap.read()
    

    if ret:

      if num_frame >= num_start_frame:
        output = predictor(frame)
      else:
        num_frame += 1
        continue

    
      line_new = 0
      objects_new = 'empty'

    # List to store detected vehicles
      boxes = []


      for i, box in enumerate(output['instances'].pred_boxes):
        x1 = int(box[0].item())
        y1 = int(box[1].item())
        x2 = int(box[2].item())
        y2 = int(box[3].item())
        if x1 < width/2 + 200: # if x1 is before end of the right lane then store the box
          boxes.append([[x1, y1, x2, y2], output['instances'].pred_classes[i].item()])


    # Check whether the vehicle is inside of the detection box or not
      for box in boxes:
        if inside_box(box[0], detection_box):
          if box[1] == 2 or box[1] == 3:  
            line_new = 1
            objects_new = objects_dict[box[1]]
          
          
    # Detection box color change
      if line_new == 1:
        color = RED
      else:
        color = WHITE    
          
      
      if (line_old != line_new) and line_new == 1:
        lane_count += 1
        objects_count[objects_new] += 1 
      
      line_old = line_new
      objects_old = objects_new


    # Draw detection box 
      x1, y1, x2, y2 = detection_box
      blk = np.zeros(frame.shape, np.uint8)
      cv2.polylines(blk,np.array([[[640,500],[805,500],[841,547],[654,547]]],np.int32), True, color, thickness=3)
      cv2.fillPoly(blk,np.array([[[640,500],[805,500],[841,547],[654,547]]],np.int32), color)
      frame = cv2.addWeighted(frame, 1.0, blk, 0.25, 1)

    # Print  counts  
      frame = cv2.putText(frame,'Total = ' + str(lane_count), (500, 60), FONT, FONT_SIZE, BLACK, THICKNESS)
      frame = cv2.putText(frame,'Carros = ' + str(objects_count['car']), (10, 60), FONT, FONT_SIZE, BLACK, THICKNESS)
      frame = cv2.putText(frame,'Motos = ' + str(objects_count['motorcycle']), (250, 60), FONT, FONT_SIZE, BLACK, THICKNESS)

      cv2.imshow('Result', frame)
      if cv2.waitKey(1) == 27:
        cap.release()
        cv2.destroyAllWindows()
        video.release()
        break 

    # Record the output frame
      video.write(frame)

    # Go to the next frame
      num_frame += 1  

    else:  
      cap.release()
      cv2.destroyAllWindows()
      video.release()

