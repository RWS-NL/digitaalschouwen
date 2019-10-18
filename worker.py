
# Worker process for smartcam devices

#import tensorflow as tf
import base64
import json
import logging
import multiprocessing as mp
import os
import random
import shutil
import time

###

os.environ['KERAS_BACKEND'] = 'tensorflow'

import tensorflow as tf
from serial import Serial
import pynmea2
import keras
from keras.models import load_model
import numpy as np
import requests
import serial
import pynmea2
import utils_dgx_copy
import cv2
from frontend import YOLO
import backend
import h5py
import predict_eigen

try:
    from scipy.misc import imread # deprecated
except:
    from imageio import imread

###

#IMAGE_FILEPATH = './tmp/35865.jpg'
IMAGE_FILEPATH = './tmp/Frame002438.jpg'
weights_path = 'fullmodel_model_boeikribbaken_2.h5'
#weights_path = 'full_yolo_boeien_laura7.h5'
GPS_DEVICEPORT = '/dev/tty50'
config_path = 'config_boeikribbaken_2.json'
#config_path = 'config_laura2.json'

###

def get_gps_location(ser):
    if not ser: return('no gps device')

    for _ in range(100):
        data = ser.readline().decode('utf-8')
        if data.startswith('$GPRMC'):
            msg = pynmea2.parse(data)
            return ("%s %s %s %s %f" %
                    (msg.lat, msg.lat_dir, msg.lon, msg.lon_dir, msg.spd_over_grnd))
    return('no gps fix')

###

def run(cam_id=0):
    logger = logging.getLogger()
    logger.info("Starting Worker process %d" % mp.current_process().pid)

    try:
        logger.error("Running keras v%s" % (keras.__version__))
        logger.error('Loading keras model..')

        with open(config_path) as config_buffer:
            config = json.load(config_buffer)

        #model2 = model.load_weights('fullmodel_tiny_yolo_boeien4.h5')
        # custom_objects={'tf':tf}
    except Exception as exc:
        logger.error(exc,exc_info=True)

    try:
        ser = serial.Serial('/dev/ttyS0', 9600)
    except serial.serialutil.SerialException:
        ser = None
        logger.error('unable to initialise gps device')

    try:
        with open('/etc/esb_url') as fh:
            esb_url = fh.readline().rstrip()
    except Exception:
        logger.error('unable to read esb target url')
        esb_url = 'http://127.0.0.1'

    ###

    while True:
        logger.debug('worker : starting loop')

        # get time
        t = time.localtime()
        time_string = "%d-%d-%d-%d-%d" % (t.tm_year, t.tm_yday, t.tm_hour, t.tm_min, t.tm_sec)

        # get photo
        if not shutil.which('raspistill'):
            logger.error('worker : raspistill utility not found')
            #sys.exit(1)

        logger.debug('worker : taking photo')
        cmd = "raspistill -o %s -w 416 -h 416 --nopreview -t 2000" % IMAGE_FILEPATH
        os.system(cmd)
        logger.debug('worker : reading photo')
        photo = imread(IMAGE_FILEPATH)
        #photo = cv2.resize(photo, (416, 416), interpolation = cv2.INTER_AREA)
        #photo = np.expand_dims(photo, axis=0)

        # get location
        logger.debug('worker : get location')
        location_string = get_gps_location(ser)

        # NOTE: dummy array to match model layout:

        logger.error('worker : make prediction')


        boxes = predict_eigen.prediction_eigenyolo(config_path, weights_path, IMAGE_FILEPATH)
        print("Number of boxes above threshold: {}".format(len(boxes)))
        for box in boxes:
            print("Confidence: {}".format(box.get_score()))

        # apply a random condition, later on this conditon is based on model applied to photo
        for box in boxes:
            if box.get_score() > 0.7:
                print("Confidence: {}".format(box.get_score()))
                logger.debug('worker : selected')
                with open(IMAGE_FILEPATH, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read())

                # information to be sent
                to_sent = {'photo': encoded_string.decode('ascii'),
                           'time': time_string,
                           'location': location_string,
                           'filename': "%s_%s_%s" % (cam_id, time_string, location_string)
                          }

                # construct json
                logger.debug('worker : sending json msg')
                to_sent = json.dumps(to_sent)

                # sent json:
                try:
                    # a message is approximately 180kb, so even when connection
                    # falls back to gsm/2g speed at @ 14.4 kbps upload, a timeout
                    # of a minute should suffice
                    res = requests.post(esb_url, json=to_sent, timeout=60)
                    if res.status_code == 200:
                        logger.debug('succesfully sent data')
                except Exception as exc:
                    logger.error(exc)

#run()

if __name__ == "__main__":
    run()
