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

''' Core exceptions raised by the ONVIF Client '''

#from suds import WebFault, MethodNotFound, PortNotFound, \
#        ServiceNotFound, TypeNotFound, BuildError, \
#        SoapHeadersNotPermitted
#TODO: Translate these errors into ONVIFError instances, mimicking the original 'suds' behaviour
#from zeep.exceptions import XMLSyntaxError, XMLParseError, UnexpectedElementError, \
#         WsdlSyntaxError, TransportError, LookupError, NamespaceError, Fault, ValidationError, \
#        SignatureVerificationFailed, IncompleteMessage, IncompleteOperation
# Error codes setting
# Error unknown, e.g, HTTP errors
ERR_ONVIF_UNKNOWN = 1
# Protocol error returned by WebService,
# e.g:DataEncodingUnknown, MissingAttr, InvalidArgs, ...
ERR_ONVIF_PROTOCOL = 2
# Error about WSDL instance
ERR_ONVIF_WSDL     = 3
# Error about Build
ERR_ONVIF_BUILD    = 4


class ONVIFError(Exception):
    def __init__(self, err):
#        if isinstance(err, (WebFault, SoapHeadersNotPermitted) if with_soap_exc else WebFault):
#            self.reason = err.fault.Reason.Text
#            self.fault = err.fault
#            self.code = ERR_ONVIF_PROTOCOL
#        elif isinstance(err, (ServiceNotFound, PortNotFound,
#                              MethodNotFound, TypeNotFound)):
#            self.reason = str(err)
#            self.code = ERR_ONVIF_PROTOCOL
#        elif isinstance(err, BuildError):
#            self.reason = str(err)
#            self.code = ERR_ONVIF_BUILD
#        else:
            self.reason = 'Unknown error: ' + str(err)
            self.code = ERR_ONVIF_UNKNOWN

    def __str__(self):
        return self.reason
