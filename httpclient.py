#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse

# for testing purpose

BYTES_TO_READ = 4096
def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPClient(object):

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None

    def close(self):
        self.socket.close()

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        part = sock.recv(BYTES_TO_READ)
        buffer.extend(part)
        response = self.__parse_server_response(part.decode('utf-8'))
        header_lines= response['heads'] 
        if not self.__recvall_helper("Content-Length: ", header_lines): # no content-length provided
            while not done:
                part = sock.recv(BYTES_TO_READ)
                if (part):
                    buffer.extend(part)
                else:
                    done = True
            return buffer.decode('utf-8') 
        for line in header_lines:
            if line.startswith("Content-Length: "):
                content_length = int(line[len("Content-Length: "):])
                break
        content_length -= len(response['body'])
        while content_length > 0:
            part = sock.recv(BYTES_TO_READ)
            buffer.extend(part)
            content_length -= len(part) 
        return buffer.decode('utf-8')
    
    def __recvall_helper(self, content: str, lst: list):
        #check if a substirng is in a list of strings
        result = False
        for line in lst:
            if content in line:
                return True
        return result 

    def GET(self, url, args=None):
        o=urllib.parse.urlparse(url)
        host = o.hostname
        port = o.port or 80
        path = o.path or '/'
        self.connect(host,port)
        request = f'GET {path} HTTP/1.1\r\n'
        request += f'HOST: {host}:{port}\r\n'
        request += '\r\n'
        self.socket.send(request.encode('utf-8'))
        results_txt = self.recvall(self.socket)
        self.close()
        parse_result = self.__parse_server_response(results_txt)
        code = int(parse_result['heads'][0].split()[1])
        print(parse_result['heads'])
        body = parse_result['body']
        print(body)
        return HTTPResponse(code, body)

    def POST(self, url, args=None):
        o=urllib.parse.urlparse(url)
        host = o.hostname
        port = o.port or 80
        path = o.path or '/'
        self.connect(host,port)
        encoded_data = None
        if args != None:
            encoded_data = urllib.parse.urlencode(args)
        request = f'POST {path} HTTP/1.1\r\n'
        request += f'HOST: {host}:{port}\r\n'
        request += "Content-Type: application/x-www-form-urlencoded\r\n"
        if args == None:
            request += f"Content-Length: 0\r\n"
        else:
            request += f"Content-Length: {len(encoded_data)}\r\n"
        request += "\r\n" 
        if args != None:
            request += encoded_data
        self.socket.send(request.encode('utf-8'))
        results_txt = self.recvall(self.socket)
        parse_result = self.__parse_server_response(results_txt)
        code = int(parse_result['heads'][0].split()[1])
        body = parse_result['body']
        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
        
    def __parse_server_response(self, response:str) -> dict:
        # parse server response to get header lines and content
        header_end = response.find('\r\n\r\n')
        headers = response[:header_end]
        content = response[header_end + 4:]
        header_lines = headers.split('\r\n')
        result = {}
        result['heads'] = header_lines
        result['body'] = content
        return result 
        
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
