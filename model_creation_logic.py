# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 12:46:37 2019

@author: Admin
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.optimizers import Adam
from keras.layers import Convolution2D, MaxPooling2D, Dropout, Flatten, Dense
from keras.callbacks import ModelCheckpoint
import cv2
from imgaug import augmenters as iaa
import pandas as pd
import random
import ntpath
import matplotlib.image as mpimg
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split

import tensorflow as tf  
from keras.backend.tensorflow_backend import set_session  
config = tf.ConfigProto()  
config.gpu_options.allow_growth = True  # dynamically grow the memory used on the GPU  
config.log_device_placement = True 
                                   
sess = tf.Session(config=config)  
set_session(sess)  # set this TensorFlow session as the default session for Keras  



datadir = 'C:/Users/Admin/OneDrive/School_Aktual/bc/new_data_set_GOOD_ONE'
columns = ['center', 'left', 'right', 'steering', 'throttle', 'reverse', 'speed']
data = pd.read_csv(datadir + '/driving_log.csv', names = columns)
pd.set_option('display.max_colwidth', -1)

data.head()

def path_leaf(path):
  head, tail = ntpath.split(path)
  return tail

data['center'] = data['center'].apply(path_leaf)
data['left'] = data['left'].apply(path_leaf)
data['right'] = data['right'].apply(path_leaf)
data.head()
num_bins = 35
samples_per_bin = 200
hist, bins = np.histogram(data['steering'], num_bins)
center = (bins[:-1]+ bins[1:]) 

print('total data:', len(data))

remove_list = []
for j in range(num_bins):
  list_ = []
  for i in range(len(data['steering'])):
    if data['steering'][i] >= bins[j] and data['steering'][i] <= bins[j+1]:
      list_.append(i)
  list_ = shuffle(list_)
  list_ = list_[samples_per_bin:]
  remove_list.extend(list_)
 
print('removed:', len(remove_list))
data.drop(data.index[remove_list], inplace=True)
print('remaining:', len(data))
 
hist, _ = np.histogram(data['steering'], (num_bins))

print(data.iloc[1])
def load_img_steering(datadir, df):
  image_path = []
  steering = []
  for i in range(len(data)):
    indexed_data = data.iloc[i]
    center, left, right = indexed_data[0], indexed_data[1], indexed_data[2]
    image_path.append(os.path.join(datadir, center.strip()))
    steering.append(float(indexed_data[3]))
    # left image append
    image_path.append(os.path.join(datadir,left.strip()))
    steering.append(float(indexed_data[3])+0.15)
    # right image append
    image_path.append(os.path.join(datadir,right.strip()))
    steering.append(float(indexed_data[3])-0.15)
  image_paths = np.asarray(image_path)
  steerings = np.asarray(steering)
  return image_paths, steerings
 
image_paths, steerings = load_img_steering(datadir + '/IMG', data)
X_train, X_valid, y_train, y_valid = train_test_split(image_paths, steerings, test_size=0.3, random_state=0)
print('Training Samples: {}\nValid Samples: {}'.format(len(X_train), len(X_valid)))

def zoom(image):
  zoom = iaa.Affine(scale=(1, 1.3))
  image = zoom.augment_image(image)
  return image

def pan(image):
  pan = iaa.Affine(translate_percent= {"x" : (-0.1, 0.1), "y": (-0.1, 0.1)})
  image = pan.augment_image(image)
  return image

def img_random_brightness(image):
    brightness = iaa.Multiply((0.2, 1.2))
    image = brightness.augment_image(image)
    return image

def img_random_flip(image, steering_angle):
    image = cv2.flip(image,1)
    steering_angle = -steering_angle
    return image, steering_angle

def random_augment(image, steering_angle):
    image = mpimg.imread(image)
    if np.random.rand() < 0.42:
      image = pan(image)
    if np.random.rand() < 0.42:
      image = zoom(image)
    if np.random.rand() < 0.42:
      image = img_random_brightness(image)
    if np.random.rand() < 0.42:
      image, steering_angle = img_random_flip(image, steering_angle)
    
    return image, steering_angle
 
def img_preprocess(img):
    img = img[60:135,:,:]
    img = cv2.cvtColor(img, cv2.COLOR_RGB2YUV)
    img = cv2.GaussianBlur(img,  (3, 3), 0)
    img = cv2.resize(img, (200, 66))
    img = img/255
    return img

def batch_generator(image_paths, steering_ang, batch_size, istraining):
  
  while True:
    batch_img = []
    batch_steering = []
    
    for i in range(batch_size):
      random_index = random.randint(0, len(image_paths) - 1)
      
      if istraining:
        im, steering = random_augment(image_paths[random_index], steering_ang[random_index])
     
      else:
        im = mpimg.imread(image_paths[random_index])
        steering = steering_ang[random_index]
      
      im = img_preprocess(im)
      batch_img.append(im)
      batch_steering.append(steering)
    yield (np.asarray(batch_img), np.asarray(batch_steering))  
    

def bc_model():
  model = Sequential()
  model.add(Convolution2D(32, 5, 5, input_shape=(66, 200, 3), activation='relu'))
  model.add(MaxPooling2D(pool_size=(2,2)))
  model.add(Convolution2D(32, 5, 5, activation='relu'))
  Dropout(0.3)
  model.add(Convolution2D(64, 5, 5, activation='relu'))
  model.add(MaxPooling2D(pool_size=(2,2)))
  model.add(Convolution2D(64, 3, 3, activation='relu'))
  model.add(Convolution2D(128, 3, 3, activation='relu'))
  
  model.add(Flatten())
  
  model.add(Dense(128, activation = 'relu'))
  model.add(Dense(64, activation = 'relu'))
  model.add(Dense(32, activation = 'relu'))
  model.add(Dense(16, activation = 'relu'))
  model.add(Dense(8, activation = 'relu'))
  model.add(Dense(1))

  optimizer = Adam(lr=0.00001)

  model.compile(loss='mse', optimizer=optimizer)
  return model


model = bc_model()
print(model.summary())


checkpoint = ModelCheckpoint(filepath='C:/Users/Admin/Desktop/Models/LastAttempts/model_checkpoint_epoch_{epoch:02d}_loss_{loss:.4f}_val_loss_{val_loss:.4f}_FROM_EXTRA.hdf5')

history = model.fit_generator(batch_generator(X_train, y_train, 150, 1),
                                  steps_per_epoch=200, 
                                  epochs=25,
                                  validation_data=batch_generator(X_valid, y_valid, 100, 0),
                                  validation_steps=150,
                                  callbacks=[checkpoint], 
                                  verbose=1,
                                  shuffle = 1)

#from keras.models import save_model
model.save('C:/Users/Admin/Desktop/Models/LastAttempts/test_mode.h5')

