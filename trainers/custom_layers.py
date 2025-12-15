"""
Copyright (C) 2025 by the CAM-AI team, info@cam-ai.de
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

    def __init__(self, gamma=2.0, name="adaptive_focal_loss"):
        super().__init__(name=name)
        self.gamma = gamma

    def call(self, y_true, y_pred):
        # Always compute using current gamma
        return tf.keras.losses.binary_focal_crossentropy(
            y_true, y_pred, gamma=self.gamma
        )

    def get_config(self):
        return {"gamma": self.gamma, "name": self.name}

    @classmethod
    def from_config(cls, config):
        return cls(**config)

# ================================================================
# Utility functions
# ================================================================

PI = 3.141592653589793

def _shape(x):
    s = tf.shape(x)
    return s[0], s[1], s[2]

def _random_sign(b):
    return tf.where(
        tf.random.uniform([b, 1, 1, 1]) < 0.5,
        -tf.ones([b, 1, 1, 1]),
        tf.ones([b, 1, 1, 1]),
    )

def _bernoulli_mask(batch_size, p):
    # Bernoulli mask ∈ {0,1}
    r = tf.random.uniform([batch_size, 1, 1, 1], 0.0, 1.0)
    return tf.cast(r < p, tf.float32)

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
        axis=1                                # → [B,8]
    )
    return tf.raw_ops.ImageProjectiveTransformV3(
        images=x,
        transforms=transforms,
        output_shape=tf.stack([h, w]),
        interpolation="BILINEAR",
        fill_value=0.0,
    )



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
    return tf.raw_ops.ImageProjectiveTransformV3(
        images=x,
        transforms=transforms,
        output_shape=tf.stack([h, w]),
        interpolation="BILINEAR",
        fill_value=0.0,
    )


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
    return tf.raw_ops.ImageProjectiveTransformV3(
        images=x,
        transforms=transforms,
        output_shape=tf.stack([h, w]),
        interpolation="BILINEAR",
        fill_value=0.0,
    )

# ================================================================
# Color / contrast / brightness ops (Google style)
# ================================================================

def _brightness(x, magnitude):
    b = tf.shape(x)[0]
    max_delta = magnitude / 30.0 * 0.5
    delta = tf.random.uniform([b, 1, 1, 1], -max_delta, max_delta)
    return tf.clip_by_value(x + delta, 0.0, 1.0)

def _contrast(x, magnitude):
    b = tf.shape(x)[0]
    max_change = magnitude / 30.0 * 0.75
    lower = tf.maximum(0.0, 1.0 - max_change)
    upper = 1.0 + max_change
    factor = tf.random.uniform([b, 1, 1, 1], lower, upper)
    mean = tf.reduce_mean(x, axis=[1, 2], keepdims=True)
    return tf.clip_by_value((x - mean) * factor + mean, 0.0, 1.0)

def _solarize(x, magnitude):
    threshold = 0.5
    return tf.where(x < threshold, x, 1.0 - x)

def _posterize(x, magnitude):
    bits = tf.cast(8 - tf.round(magnitude / 5.0), tf.int32)
    bits = tf.clip_by_value(bits, 1, 8)
    shift = 8 - bits
    x_u8 = tf.cast(x * 255.0, tf.uint8)
    shift_u8 = tf.cast(shift, tf.uint8)
    x_q = tf.bitwise.right_shift(x_u8, shift_u8)
    x_q = tf.bitwise.left_shift(x_q, shift_u8)
    return tf.cast(x_q, tf.float32) / 255.0

def _invert(x, magnitude):
    return 1.0 - x

def _autocontrast(x, magnitude):
    lo = tf.reduce_min(x, axis=[1, 2, 3], keepdims=True)
    hi = tf.reduce_max(x, axis=[1, 2, 3], keepdims=True)
    return tf.clip_by_value((x - lo) / (hi - lo + 1e-6), 0.0, 1.0)

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
    return x * (1.0 - mask)

def _equalize(x, magnitude):
    return _autocontrast(x, magnitude)
    
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
    return tf.raw_ops.ImageProjectiveTransformV3(
        images=x,
        transforms=transform,
        fill_value=128.0,
        output_shape=tf.shape(x)[1:3],
        interpolation="BILINEAR",
    )
  
def _shear_y_batch(x, mag):
    shear = (mag / 30.0) * tf.random.uniform([], -0.3, 0.3)
    shear = tf.cast(shear, tf.float32)
    batch = tf.shape(x)[0]
    transform = tf.stack([
        1.0, 0.0 , 0.0,
        shear, 1.0, 0.0,
        0.0 , 0.0], axis=0)
    transform = tf.tile(transform[None, :], [batch, 1])
    return tf.raw_ops.ImageProjectiveTransformV3(
        images=x,
        transforms=transform,
        fill_value=128.0,
        output_shape=tf.shape(x)[1:3],
        interpolation="BILINEAR",
    )
    
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
    return tf.clip_by_value(x + factor * (x - blurred), 0.0, 1.0)

def _saturation(x, mag):
    # mag ist Tensor → zuerst normalisieren (0..30 → 0..1)
    delta = (tf.cast(mag, tf.float32) / 30.0) * 0.3   # max ±30% Änderung
    # Random factor in [1-delta, 1+delta]
    factor = tf.random.uniform(
        [],
        minval=1.0 - delta,
        maxval=1.0 + delta
    )
    mean = tf.reduce_mean(x, axis=-1, keepdims=True)
    out = (x - mean) * factor + mean
    return tf.clip_by_value(out, 0.0, 1.0)
  
def _hue(x, mag):
    max_hue = 0.2 * (tf.cast(mag, tf.float32) / 30.0)
    # delta in [-max_hue, +max_hue]
    delta = tf.random.uniform(
        [],
        minval=-max_hue,
        maxval=max_hue     # kein unary + !
    )
    return tf.image.adjust_hue(x, delta)

def _color_jitter(x, mag):
    x = _saturation(x, mag)
    x = _hue(x, mag)
    return x

# ================================================================
# RandAugment (Google) – graph-safe version
# ================================================================

@register_keras_serializable(package="CAMAI")
class CAMAI_RandAugment(keras.layers.Layer):
    """
    Google Model Garden RandAugment – graph-safe version.

    N = num_layers
    M = magnitude (0..30)
    """

    def __init__(self, num_layers=2.0, magnitude=10.0, **kwargs):
        super().__init__(**kwargs)
        self._init_num_layers = float(num_layers)
        self._init_magnitude = float(magnitude)

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
        super().build(input_shape)

    def call(self, x, training=None):
        if not training:
            return x
        # convert to [0,1]
        x = tf.cast(x, tf.float32) / 255.0
        b = tf.shape(x)[0]
        M = tf.cast(self.magnitude, tf.float32)
        NUM_OPS = 15
        p = self.num_layers / float(NUM_OPS)
        p = tf.clip_by_value(p, 0.0, 1.0)
        mask = lambda: _bernoulli_mask(b, p)
        # -------------------------------
        # OP 1: Rotate
        # -------------------------------
        m = mask()
        deg = tf.random.uniform([b], -M, M)          # shape [B]
        x_aug = _rotate(x, deg)                      # deg: [B]
        x = x * (1.0 - m) + x_aug * m
        # -------------------------------
        # OP 2: TranslateX
        # -------------------------------
        m = mask()
        dx = tf.random.uniform([b], -M, M) / 30.0 * tf.cast(tf.shape(x)[2], tf.float32) * 0.3
        x_aug = _translate_x(x, dx)
        x = x * (1.0 - m) + x_aug * m
        # -------------------------------
        # OP 3: TranslateY
        # -------------------------------
        m = mask()
        dy = tf.random.uniform([b], -M, M) / 30.0 * tf.cast(tf.shape(x)[1], tf.float32) * 0.3
        x_aug = _translate_y(x, dy)
        x = x * (1.0 - m) + x_aug * m
        # OP 4
        m = mask()
        x = x * (1.0 - m) + _brightness(x, M) * m
        # OP 5
        m = mask()
        x = x * (1.0 - m) + _contrast(x, M) * m
        # OP 6
        m = mask()
        x = x * (1.0 - m) + _solarize(x, M) * m
        # OP 7
        m = mask()
        x = x * (1.0 - m) + _posterize(x, M) * m
        # OP 8
        m = mask()
        x = x * (1.0 - m) + _invert(x, M) * m
        # OP 9
        m = mask()
        x = x * (1.0 - m) + _cutout(x, M) * m
        # OP 10
        m = mask()
        x = x * (1.0 - m) + _autocontrast(x, M) * m
        # OP 11
        m = mask()
        x = x * (1.0 - m) + _equalize(x, M) * m
        # -------------------------------
        # OP 12: ShearX
        # -------------------------------
        m = mask()
        x = x * (1.0 - m) + _shear_x_batch(x, M) * m
        # -------------------------------
        # OP 13: ShearY
        # -------------------------------
        m = mask()
        x = x * (1.0 - m) + _shear_y_batch(x, M) * m
        # -------------------------------
        # OP 14: Sharpness
        # -------------------------------
        m = mask()
        x = x * (1.0 - m) + _sharpness(x, M) * m
        # -------------------------------
        # OP 15: ColorJitter
        # -------------------------------
        m = mask()
        x = x * (1.0 - m) + _color_jitter(x, M) * m
        return tf.clip_by_value(x * 255.0, 0.0, 255.0)

