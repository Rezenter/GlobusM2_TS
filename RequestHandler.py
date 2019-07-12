import json
import datetime
import sys
import math

TEMP_CV_FILE = '../data/TempSeq.seq'
TEMP_RESULT_FILE = 'result.json'


def __init__():
    return

class Handler():

    def __init__(self):
        self.HandlingTable = {
            'getAnalysis': self.GetDocuments
        }
        return


    def HandleRequest (self, req):
        reqtype = req['reqtype']
        if reqtype in self.HandlingTable:
            return self.HandlingTable[reqtype](req)
        else:
            return {'status': 'failure', 'description': 'Failed to dispatch message'}


    def GetDocuments (self, req):
        resp = {};
        resp['status'] = 'success'
        return resp


