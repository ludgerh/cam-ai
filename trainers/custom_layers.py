"""
Copyright (C) 2025-2026 by the CAM-AI team, info@cam-ai.de
More information and complete source: https://github.com/ludgerh/cam-ai
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.losses import BinaryFocalCrossentropy, Loss
from tensorflow.keras.utils import register_keras_serializable

@register_keras_serializable(package="CAMAI")
class AdaptiveFocalLoss(Loss):
  """
  Serialization-safe adaptive focal loss.
  Gamma can be changed dynamically during training.
  """

  def __init__(self, gamma=2.0, from_logits=False, name="adaptive_focal_loss"):
    super().__init__(name=name)
    # Variable instead of Python float: a float is baked into the traced graph
    self.gamma = tf.Variable(float(gamma), trainable=False, dtype=tf.float32)
    
  def set_gamma(self, value):
    self.gamma.assign(float(value))

  def call(self, y_true, y_pred):
    # gamma is a tf.Variable now, so changes take effect inside the traced graph
    return(tf.keras.losses.binary_focal_crossentropy(
      y_true, y_pred, gamma=self.gamma
    ))

  def get_config(self):
    return({'gamma': float(self.gamma.numpy()), 'name': self.name})

  @classmethod
  def from_config(cls, config):
    return(cls(**config))

# ================================================================
# Utility functions
# ================================================================

PI = 3.141592653589793

def _shape(x):
  s = tf.shape(x)
  return(s[0], s[1], s[2])

def _random_sign(b):
  return(tf.where(
    tf.random.uniform([b, 1, 1, 1]) < 0.5,
    -tf.ones([b, 1, 1, 1]),
    tf.ones([b, 1, 1, 1]),
  ))

def _bernoulli_mask(batch_size, p):
  # Bernoulli mask ∈ {0,1}
  r = tf.random.uniform([batch_size, 1, 1, 1], 0.0, 1.0)
  return(tf.cast(r < p, tf.float32))

# ================================================================
# Projective transforms
# (based on Google TF Model Garden transform_ops)
# ================================================================

def _rotate(x, degrees):
  b, h, w = _shape(x)
  rad = degrees * PI / 180.0               # [B]
  cos = tf.cos(rad)                        # [B]
  sin = tf.sin(rad)                        # [B]
  zeros = tf.zeros_like(cos)               # [B]
  transforms = tf.stack(
    [
      cos, -sin, zeros,
      sin,  cos, zeros,
      zeros, zeros
    ],
    axis=1                                 # → [B,8]
  )
  return(tf.raw_ops.ImageProjectiveTransformV3(
    images=x,
    transforms=transforms,
    output_shape=tf.stack([h, w]),
    interpolation="BILINEAR",
    fill_value=0.0,
  ))

def _translate_x(x, pixels):
  b, h, w = _shape(x)
  ones = tf.ones([b])
  zeros = tf.zeros([b])
  transforms = tf.stack(
    [
      ones, zeros, -pixels,
      zeros, ones,  zeros,
      zeros, zeros
    ],
    axis=1
  )
  return(tf.raw_ops.ImageProjectiveTransformV3(
    images=x,
    transforms=transforms,
    output_shape=tf.stack([h, w]),
    interpolation="BILINEAR",
    fill_value=0.0,
  ))

def _translate_y(x, pixels):
  b, h, w = _shape(x)
  ones = tf.ones([b])
  zeros = tf.zeros([b])
  transforms = tf.stack(
    [
      ones, zeros,  zeros,
      zeros, ones, -pixels,
      zeros, zeros
    ],
    axis=1
  )
  return(tf.raw_ops.ImageProjectiveTransformV3(
    images=x,
    transforms=transforms,
    output_shape=tf.stack([h, w]),
    interpolation="BILINEAR",
    fill_value=0.0,
  ))

# ================================================================
# Color / contrast / brightness ops (Google style)
# ================================================================

def _brightness(x, magnitude):
  b = tf.shape(x)[0]
  max_delta = magnitude / 30.0 * 0.5
  delta = tf.random.uniform([b, 1, 1, 1], -max_delta, max_delta)
  return(tf.clip_by_value(x + delta, 0.0, 1.0))

def _contrast(x, magnitude):
  b = tf.shape(x)[0]
  max_change = magnitude / 30.0 * 0.75
  lower = tf.maximum(0.0, 1.0 - max_change)
  upper = 1.0 + max_change
  factor = tf.random.uniform([b, 1, 1, 1], lower, upper)
  mean = tf.reduce_mean(x, axis=[1, 2], keepdims=True)
  return(tf.clip_by_value((x - mean) * factor + mean, 0.0, 1.0))

def _solarize(x, magnitude):
  threshold = 0.5
  return(tf.where(x < threshold, x, 1.0 - x))

def _posterize(x, magnitude):
  bits = tf.cast(8 - tf.round(magnitude / 5.0), tf.int32)
  bits = tf.clip_by_value(bits, 1, 8)
  shift = 8 - bits
  x_u8 = tf.cast(x * 255.0, tf.uint8)
  shift_u8 = tf.cast(shift, tf.uint8)
  x_q = tf.bitwise.right_shift(x_u8, shift_u8)
  x_q = tf.bitwise.left_shift(x_q, shift_u8)
  return(tf.cast(x_q, tf.float32) / 255.0)

def _invert(x, magnitude):
  return(1.0 - x)

def _autocontrast(x, magnitude):
  lo = tf.reduce_min(x, axis=[1, 2, 3], keepdims=True)
  hi = tf.reduce_max(x, axis=[1, 2, 3], keepdims=True)
  return(tf.clip_by_value((x - lo) / (hi - lo + 1e-6), 0.0, 1.0))

def _cutout(x, magnitude):
  b, h, w = _shape(x)
  frac = magnitude / 30.0 * 0.5
  size = tf.random.uniform([b, 1, 1], 0.0, frac)
  cut_h = size * tf.cast(h, tf.float32)
  cut_w = size * tf.cast(w, tf.float32)
  cy = tf.random.uniform([b, 1, 1], 0.0, tf.cast(h, tf.float32))
  cx = tf.random.uniform([b, 1, 1], 0.0, tf.cast(w, tf.float32))
  ys = tf.cast(tf.range(h)[None, :, None], tf.float32)
  xs = tf.cast(tf.range(w)[None, None, :], tf.float32)
  mask_y = tf.abs(ys - cy) <= (cut_h / 2.0)
  mask_x = tf.abs(xs - cx) <= (cut_w / 2.0)
  mask = tf.expand_dims(mask_y & mask_x, -1)
  mask = tf.cast(mask, x.dtype)
  return(x * (1.0 - mask))

def _equalize(x, magnitude):
  return(_autocontrast(x, magnitude))
    
def _shear_x_batch(x, mag):
  # mag in [0..30] → shear factor ≈ [-0.3 .. 0.3]
  shear = (mag / 30.0) * tf.random.uniform([], -0.3, 0.3)
  shear = tf.cast(shear, tf.float32)
  batch = tf.shape(x)[0]
  # Transform: [a0, a1, a2, b0, b1, b2, c0, c1]
  transform = tf.stack([
    1.0, shear, 0.0,
    0.0, 1.0  , 0.0,
    0.0, 0.0], axis=0)
  transform = tf.tile(transform[None, :], [batch, 1])
  return(tf.raw_ops.ImageProjectiveTransformV3(
    images=x,
    transforms=transform,
    fill_value=128.0,
    output_shape=tf.shape(x)[1:3],
    interpolation="BILINEAR",
  ))
  
def _shear_y_batch(x, mag):
  shear = (mag / 30.0) * tf.random.uniform([], -0.3, 0.3)
  shear = tf.cast(shear, tf.float32)
  batch = tf.shape(x)[0]
  transform = tf.stack([
    1.0, 0.0 , 0.0,
    shear, 1.0, 0.0,
    0.0 , 0.0], axis=0)
  transform = tf.tile(transform[None, :], [batch, 1])
  return(tf.raw_ops.ImageProjectiveTransformV3(
    images=x,
    transforms=transform,
    fill_value=128.0,
    output_shape=tf.shape(x)[1:3],
    interpolation="BILINEAR",
  ))
    
def _sharpness(x, mag):
  # mag 0..30 → factor 0..1
  factor = tf.cast(mag, tf.float32) / 30.0
  # Simple box blur kernel (3x3)
  kernel = tf.constant([[1/9, 1/9, 1/9],
                        [1/9, 1/9, 1/9],
                        [1/9, 1/9, 1/9]], dtype=tf.float32)
  kernel = tf.reshape(kernel, [3, 3, 1, 1])
  kernel = tf.tile(kernel, [1, 1, tf.shape(x)[-1], 1])
  blurred = tf.nn.depthwise_conv2d(x, kernel, strides=[1,1,1,1], padding="SAME")
  return(tf.clip_by_value(x + factor * (x - blurred), 0.0, 1.0))

def _saturation(x, mag):
  # mag is a tensor → normalize first (0..30 → 0..1)
  delta = (tf.cast(mag, tf.float32) / 30.0) * 0.3   # max ±30% change
  # Random factor in [1-delta, 1+delta]
  factor = tf.random.uniform(
    [],
    minval=1.0 - delta,
    maxval=1.0 + delta
  )
  mean = tf.reduce_mean(x, axis=-1, keepdims=True)
  out = (x - mean) * factor + mean
  return(tf.clip_by_value(out, 0.0, 1.0))
  
def _hue(x, mag):
  max_hue = 0.2 * (tf.cast(mag, tf.float32) / 30.0)
  # delta in [-max_hue, +max_hue]
  delta = tf.random.uniform(
    [],
    minval=-max_hue,
    maxval=max_hue     # no unary + !
  )
  return(tf.image.adjust_hue(x, delta))

def _color_jitter(x, mag):
  x = _saturation(x, mag)
  x = _hue(x, mag)
  return(x)

# ================================================================
# Geometric ops with per-sample random parameters
# (wrapped so that every op has the signature fn(x, M))
# ================================================================

def _rotate_op(x, M):
  b = tf.shape(x)[0]
  deg = tf.random.uniform([b], -M, M)          # shape [B]
  return(_rotate(x, deg))

def _translate_x_op(x, M):
  b = tf.shape(x)[0]
  width = tf.cast(tf.shape(x)[2], tf.float32)
  dx = tf.random.uniform([b], -M, M) / 30.0 * width * 0.3
  return(_translate_x(x, dx))

def _translate_y_op(x, M):
  b = tf.shape(x)[0]
  height = tf.cast(tf.shape(x)[1], tf.float32)
  dy = tf.random.uniform([b], -M, M) / 30.0 * height * 0.3
  return(_translate_y(x, dy))

# ================================================================
# Op registry
# The order defines the bit position in a bitmask: bit i ↔ OP_LIST[i]
# ================================================================

OP_LIST = (
  ("rotate", _rotate_op),
  ("translate_x", _translate_x_op),
  ("translate_y", _translate_y_op),
  ("brightness", _brightness),
  ("contrast", _contrast),
  ("solarize", _solarize),
  ("posterize", _posterize),
  ("invert", _invert),
  ("cutout", _cutout),
  ("autocontrast", _autocontrast),
  ("equalize", _equalize),
  ("shear_x", _shear_x_batch),
  ("shear_y", _shear_y_batch),
  ("sharpness", _sharpness),
  ("color_jitter", _color_jitter),
)
OP_NAMES = tuple(name for name, _ in OP_LIST)
NUM_OPS = len(OP_LIST)
ALL_OPS_MASK = (1 << NUM_OPS) - 1

def ops_to_mask(active_ops):
  """
  Convert an op specification to a bitmask.

  active_ops may be:
  - None → all ops active
  - int → already a bitmask
  - iterable of op names or op indices
  """
  if active_ops is None:
    return(ALL_OPS_MASK)
  if isinstance(active_ops, int):
    return(active_ops & ALL_OPS_MASK)
  mask = 0
  for item in active_ops:
    if isinstance(item, int):
      if not (0 <= item < NUM_OPS):
        raise ValueError(f"Op index out of range: {item}")
      mask |= (1 << item)
    elif item in OP_NAMES:
      mask |= (1 << OP_NAMES.index(item))
    else:
      raise ValueError(f"Unknown augmentation op: {item!r}. Known: {OP_NAMES}")
  return(mask)

def mask_to_ops(mask):
  """Convert a bitmask back to a list of op names."""
  return([name for i, name in enumerate(OP_NAMES) if mask & (1 << i)])

def mask_to_vector(mask):
  """Convert a bitmask to a float list of length NUM_OPS with 0/1 entries."""
  return([1.0 if mask & (1 << i) else 0.0 for i in range(NUM_OPS)])

# ================================================================
# RandAugment (Google) – graph-safe version
# ================================================================

@register_keras_serializable(package="CAMAI")
class CAMAI_RandAugment(keras.layers.Layer):
  """
  Google Model Garden RandAugment – graph-safe version.

  N = num_layers
  M = magnitude (0..30)
  active_ops = which ops may be applied (None = all, bitmask, or list of
               names / indices, see OP_NAMES). Stored as a non-trainable
               weight so it can be changed at runtime via set_active_ops().

  Each active op is applied per sample with probability
  N / (number of active ops), so the expected number of applied ops per
  sample stays N regardless of how many ops are enabled.
  """

  def __init__(self, num_layers=2.0, magnitude=10.0, active_ops=None, **kwargs):
    super().__init__(**kwargs)
    self._init_num_layers = float(num_layers)
    self._init_magnitude = float(magnitude)
    self._init_op_mask = ops_to_mask(active_ops)

  def build(self, input_shape):
    self.num_layers = self.add_weight(
      name="num_layers",
      shape=(),
      dtype=tf.float32,
      initializer=tf.constant_initializer(self._init_num_layers),
      trainable=False,
    )
    self.magnitude = self.add_weight(
      name="magnitude",
      shape=(),
      dtype=tf.float32,
      initializer=tf.constant_initializer(self._init_magnitude),
      trainable=False,
    )
    # One 0/1 entry per op, ordered like OP_LIST
    self.op_mask = self.add_weight(
      name="op_mask",
      shape=(NUM_OPS,),
      dtype=tf.float32,
      initializer=tf.constant_initializer(mask_to_vector(self._init_op_mask)),
      trainable=False,
    )
    super().build(input_shape)

  # ---------------------------------------------------------------
  # Runtime configuration
  # ---------------------------------------------------------------

  def set_active_ops(self, active_ops):
    """Enable a set of ops (None, bitmask, or list of names / indices)."""
    mask = ops_to_mask(active_ops)
    self._init_op_mask = mask
    if self.built:
      self.op_mask.assign(mask_to_vector(mask))

  def get_active_ops(self):
    """Return the currently active ops as a list of names."""
    if self.built:
      vector = self.op_mask.numpy()
      return([name for i, name in enumerate(OP_NAMES) if vector[i] > 0.5])
    return(mask_to_ops(self._init_op_mask))

  # ---------------------------------------------------------------
  # Forward pass
  # ---------------------------------------------------------------

  def call(self, x, training=None):
    if not training:
      return(x)
    # convert to [0,1]
    x = tf.cast(x, tf.float32) / 255.0
    b = tf.shape(x)[0]
    M = tf.cast(self.magnitude, tf.float32)
    # Probability per active op so that E[#ops] == num_layers
    active_count = tf.maximum(tf.reduce_sum(self.op_mask), 1.0)
    p = self.num_layers / active_count
    p = tf.clip_by_value(p, 0.0, 1.0)
    for i, (name, fn) in enumerate(OP_LIST):
      # Sample mask is multiplied by the op's enable flag (0 or 1)
      m = _bernoulli_mask(b, p) * self.op_mask[i]
      x = x * (1.0 - m) + fn(x, M) * m
    return(tf.clip_by_value(x * 255.0, 0.0, 255.0))

  # ---------------------------------------------------------------
  # Serialization
  # ---------------------------------------------------------------

  def get_config(self):
    config = super().get_config()
    config.update({
      "num_layers": self._init_num_layers,
      "magnitude": self._init_magnitude,
      "active_ops": mask_to_ops(self._init_op_mask),
    })
    return(config)

  @classmethod
  def from_config(cls, config):
    return(cls(**config))
