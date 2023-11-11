# Copyright (C) 2023 Ludger Hellerhoff, ludger@cam-ai.de
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Flatten, Dense

def make_model(spec, classes_count=10):
  if spec == 'efficientnetv2-b0':
    from tensorflow.keras.applications.efficientnet_v2 import EfficientNetV2B0
    base_model = EfficientNetV2B0(weights='imagenet', include_top=False,
      input_shape=(224, 224, 3))
  elif spec == 'efficientnetv2-b1':
    from tensorflow.keras.applications.efficientnet_v2 import EfficientNetV2B1
    base_model = EfficientNetV2B1(weights='imagenet', include_top=False,
      input_shape=(240, 240, 3))
  elif spec == 'efficientnetv2-b2':
    from tensorflow.keras.applications.efficientnet_v2 import EfficientNetV2B2
    base_model = EfficientNetV2B2(weights='imagenet', include_top=False,
      input_shape=(260, 260, 3))
  elif spec == 'efficientnetv2-b3':
    from tensorflow.keras.applications.efficientnet_v2 import EfficientNetV2B3
    base_model = EfficientNetV2B3(weights='imagenet', include_top=False,
      input_shape=(300, 300, 3))
  elif spec == 'efficientnetv2-s':
    from tensorflow.keras.applications.efficientnet_v2 import EfficientNetV2S
    base_model = EfficientNetV2S(weights='imagenet', include_top=False,
      input_shape=(384, 384, 3))
  elif spec == 'efficientnetv2-m':
    from tensorflow.keras.applications.efficientnet_v2 import EfficientNetV2M
    base_model = EfficientNetV2M(weights='imagenet', include_top=False,
      input_shape=(480, 480, 3))
  elif spec == 'efficientnetv2-l':
    from tensorflow.keras.applications.efficientnet_v2 import EfficientNetV2L
    base_model = EfficientNetV2L(weights='imagenet', include_top=False,
      input_shape=(480, 480, 3))

  model = Sequential()
  base_model.trainable = False
  model.add(base_model)
  model.add(Flatten(name="CAM-AI_Flatten", ))
  model.add(Dense(128, activation="relu", name="CAM-AI_Dense1"))
  model.add(Dense(64,activation="relu", name="CAM-AI_Dense2"))
  model.add(Dense(classes_count, activation='sigmoid', name="CAM-AI_Dense3"))
  return(model)

