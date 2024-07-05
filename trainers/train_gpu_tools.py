# Copyright (C) 2023 by the CAM-AI team, info@cam-ai.de
# All rights reserved

import tensorflow as tf

def cmetrics(y_true, y_pred):
  y_true = tf.round(y_true)
  y_pred = tf.round(y_pred)
  ones = tf.ones_like(y_true)
  return tf.reduce_mean(tf.abs(y_pred + y_true - ones), axis=-1)

def hit100(y_true, y_pred):
  y_true = tf.round(y_true)
  y_pred = tf.round(y_pred)
  maxline = tf.reduce_max(tf.abs(y_true - y_pred), axis=-1)
  ones = tf.ones_like(maxline)
  return tf.abs(maxline - ones)
