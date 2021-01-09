#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
import logging
import sys

from flask import Flask, request, Response
from flask_restful import reqparse, Api, Resource, abort

import remote_module
import traceback

print('initializing models')
print(remote_module.model.device)
print('initialized models')

app = Flask("remote module")
api = Api(app)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)

class RemoteModule(Resource):

    def get(self):
        return 200

    def post(self):
        t0 = time.time()
        
        args = request.get_json(force=True)
        print(args)
        validation = self.__validate_input(args)
        if validation:
            return validation, 500

        ret = {}

        try:
            ret.update(
                self.__get_response(args)
                )
            ret['performance'] = time.time() - t0,
            ret['error'] = False
            return ret, 200
        except Exception as e:
            ret['performance'] = time.time() - t0,
            ret['error'] = True
            ret['stack_trace'] = traceback.format_exc()
            return ret, 500

    @staticmethod
    def __validate_input(args):
        message = ""
        for ctx in remote_module.get_required_context():
            if not args.get(ctx):
                message = "Context missing: "+ctx
        if message:
            return {
                'message': message,
                'error': True
            }
        return None

    @staticmethod
    def __get_response(msg):
        response = remote_module.handle_message(msg)
        if isinstance(response, dict):
            ret = response
        else:
            # convert it to dict if the response from remote_module is not a dict
            ret = {
                'response': response
            }

        app.logger.info("result: %s", ret)
        return ret

api.add_resource(RemoteModule, '/')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=os.environ.get('REMOTE_MODULE_PORT') or 5001)
