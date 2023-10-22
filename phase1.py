import numpy as np
import cv2
import os
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile
import pathlib
import argparse
from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image
from IPython.display import display
from object_detection.utils import ops as utils_ops
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

parser = argparse.ArgumentParser(description='Object Tracking Rover')
parser.add_argument("--model", help = "Name of the model to be used", default = 'ssd_inception_v2_coco_2017_11_17')
args = parser.parse_args()

while "models" in pathlib.Path.cwd().parts:
    os.chdir('..')
 
"""
----------------------------------------------------------------------
Loading and setting up model 
----------------------------------------------------------------------
"""
def load_model(model_name):
  base_url = 'http://download.tensorflow.org/models/object_detection/'
  model_file = model_name + '.tar.gz'
  model_dir = tf.keras.utils.get_file(
    fname=model_name,
    origin=base_url + model_file,
    untar=True)
 
  model_dir = pathlib.Path(model_dir)/"saved_model"
  model = tf.saved_model.load(str(model_dir), None)
  return model
 
PATH_TO_LABELS = 'models/research/object_detection/data/mscoco_label_map.pbtxt'
category_index = label_map_util.create_category_index_from_labelmap(PATH_TO_LABELS, use_display_name=True)
 
model_name = args.model
detection_model = load_model(model_name)
 
"""
----------------------------------------------------------------------
General functions
----------------------------------------------------------------------
"""
def run_inference_for_single_image(model, image):
  image = np.asarray(image)
  # The input needs to be a tensor, convert it using `tf.convert_to_tensor`.
  input_tensor = tf.convert_to_tensor(image)
  # The model expects a batch of images, so add an axis with `tf.newaxis`.
  input_tensor = input_tensor[tf.newaxis,...]
 
  # Run inference
  model_fn = model.signatures['serving_default']
  output_dict = model_fn(input_tensor)
 
  # All outputs are batches tensors.
  # Convert to numpy arrays, and take index [0] to remove the batch dimension.
  # We're only interested in the first num_detections.
  num_detections = int(output_dict.pop('num_detections'))
  output_dict = {key:value[0, :num_detections].numpy() 
                 for key,value in output_dict.items()}
  output_dict['num_detections'] = num_detections
 
  # detection_classes should be ints.
  output_dict['detection_classes'] = output_dict['detection_classes'].astype(np.int64)
    
  # Handle models with masks:
  if 'detection_masks' in output_dict:
    # Reframe the the bbox mask to the image size.
    detection_masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
              output_dict['detection_masks'], output_dict['detection_boxes'],
               image.shape[0], image.shape[1])      
    detection_masks_reframed = tf.cast(detection_masks_reframed > 0.5,
                                       tf.uint8)
    output_dict['detection_masks_reframed'] = detection_masks_reframed.numpy()
     
  return output_dict

def show_inference(model, frame):
  # Take the frame from webcam feed and convert that to an array
  image_np = np.array(frame)
  # Actual detection.
  output_dict = run_inference_for_single_image(model, image_np)
  # Visualization of the results of a detection.
  vis_util.visualize_boxes_and_labels_on_image_array(
      image_np,
      output_dict['detection_boxes'],
      output_dict['detection_classes'],
      output_dict['detection_scores'],
      category_index,
      instance_masks=output_dict.get('detection_masks_reframed', None),
      use_normalized_coordinates=True,
      line_thickness=5)

  return(image_np, output_dict)

# Returns the normalized coordinates of the center point for the given bounding box in form (x_center, y_center)
def get_centerpoint(detection_box):
    x_center = (detection_box[1] + detection_box[3]) / 2
    y_center = (detection_box[0] + detection_box[2]) / 2
    center = [x_center, y_center]
    return center

# Returns the size of the bounding box expressed as a percentage of the frame
def get_box_size(detection_box):
    x_length = detection_box[3] - detection_box[1]
    y_length = detection_box[2] - detection_box[0]
    area = x_length * y_length
    return area

# Returns True if a cat is found in the frame
def contains_cat(output_dict):
  classes = output_dict['detection_classes']
  cat_detected = 17 in classes
  return cat_detected

# Returns the location of the specified detection class in the output_dict['detection_classes'] array
# Function may be pointless since finding the index is such a simple operation
def find_index(detection_class, output_dict):
  idx = output_dict['detection_classes'].index(detection_class)
  return idx

"""
----------------------------------------------------------------------
Real-time object detection
----------------------------------------------------------------------
"""
video_capture = cv2.VideoCapture(0)
print("Initializing real-time object detection")
while True:
    # Capture frame-by-frame
    read, frame = video_capture.read()
    image, output_dict = show_inference(detection_model, frame)
    cv2.imshow('object detection', image)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
video_capture.release()
cv2.destroyAllWindows()
