#! /usr/bin/env python

import argparse
import os
import cv2
import numpy as np
#from tqdm import tqdm
from preprocessing import parse_annotation
from utils import draw_boxes
from frontend import YOLO
import json

def prediction_eigenyolo(config_path, weights_path, image_path):

    with open(config_path) as config_buffer:
        config = json.load(config_buffer)

    ###############################
    #   Make the model
    ###############################

    yolo = YOLO(backend             = config['model']['backend'],
                input_size          = config['model']['input_size'],
                labels              = config['model']['labels'],
                max_box_per_image   = config['model']['max_box_per_image'],
                anchors             = config['model']['anchors'])

    ###############################
    #   Load trained weights
    ###############################

    yolo.load_weights(weights_path)

    ###############################
    #   Predict bounding boxes
    ###############################

    image = cv2.imread(image_path)
    boxes = yolo.predict(image)
    image = draw_boxes(image, boxes, config['model']['labels'])

    print(len(boxes), 'boxes are found')

    cv2.imwrite(image_path[:-4] + '_detected' + image_path[-4:], image)

    return boxes

if __name__ == 'prediction_eigenyolo':
    args = argparser.parse_args()
    _main_(args)
