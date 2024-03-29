#The MIT License (MIT)

#Copyright (c) 2014 Quatanium Co., Ltd.

#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.

#Github: https://github.com/FalkTannhaeuser/python-onvif-zeep

SERVICES = {
        # Name                              namespace                           wsdl file                      binding name
        'devicemgmt': {'ns': 'http://www.onvif.org/ver10/device/wsdl',    'wsdl': 'devicemgmt.wsdl', 'binding' : 'DeviceBinding'},
        'media'     : {'ns': 'http://www.onvif.org/ver10/media/wsdl',     'wsdl': 'media.wsdl',      'binding' : 'MediaBinding'},
        'ptz'       : {'ns': 'http://www.onvif.org/ver20/ptz/wsdl',       'wsdl': 'ptz.wsdl',        'binding' : 'PTZBinding'},
        'imaging'   : {'ns': 'http://www.onvif.org/ver20/imaging/wsdl',   'wsdl': 'imaging.wsdl',    'binding' : 'ImagingBinding'},
        'deviceio'  : {'ns': 'http://www.onvif.org/ver10/deviceIO/wsdl',  'wsdl': 'deviceio.wsdl',   'binding' : 'DeviceIOBinding'},
        'events'    : {'ns': 'http://www.onvif.org/ver10/events/wsdl',    'wsdl': 'events.wsdl',     'binding' : 'EventBinding'},
        'pullpoint' : {'ns': 'http://www.onvif.org/ver10/events/wsdl',    'wsdl': 'events.wsdl',     'binding' : 'PullPointSubscriptionBinding'},
        'analytics' : {'ns': 'http://www.onvif.org/ver20/analytics/wsdl', 'wsdl': 'analytics.wsdl',  'binding' : 'AnalyticsEngineBinding'},
        'recording' : {'ns': 'http://www.onvif.org/ver10/recording/wsdl', 'wsdl': 'recording.wsdl',  'binding' : 'RecordingBinding'},
        'search'    : {'ns': 'http://www.onvif.org/ver10/search/wsdl',    'wsdl': 'search.wsdl',     'binding' : 'SearchBinding'},
        'replay'    : {'ns': 'http://www.onvif.org/ver10/replay/wsdl',    'wsdl': 'replay.wsdl',     'binding' : 'ReplayBinding'},
        'receiver'  : {'ns': 'http://www.onvif.org/ver10/receiver/wsdl',  'wsdl': 'receiver.wsdl',   'binding' : 'ReceiverBinding'},
        }

#
#NSMAP = { }
#for name, item in SERVICES.items():
#    NSMAP[item['ns']] = name
