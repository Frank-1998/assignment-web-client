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
import ssl

BYTES_TO_READ = 4096
def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPClient(object):
    #def get_host_port(self,url):

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
        handle_301 = {}
        while not done:
            part = sock.recv(BYTES_TO_READ)
            print(part)
            code = self.__parse_server_response(part.decode('utf-8'))['heads'][0].split()[1]
            if int(code) == 301:
                part = part.decode('utf-8')
                part = part.split('\r\n')
                for line in part:
                    if line.startswith("Location: "):
                        new_location = line[len("Location: "):]
                        handle_301['has_301'] = True
                        handle_301['url'] = new_location
                        self.close()
                        return handle_301
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    def GET(self, url, args=None):
        o=urllib.parse.urlparse(url)
        host = o.hostname
        port = o.port or 80
        path = o.path or '/'
        scheme = o.scheme
        self.connect(host,port)
        if scheme == 'http':
            request = f'GET {path} HTTP/1.1\r\n'
        elif scheme == 'https':
            context = ssl.create_default_context()
            ssl_socket = context.wrap_socket(self.socket, server_hostname=host)
            request = f'GET {path} HTTP/1.1\r\n'
        request += f'HOST: {host}:{port}\r\n'
        request += '\r\n'
        print(request)
        if scheme == 'https':
            ssl_socket.send(request.encode('utf-8'))
        elif scheme == 'http':
            self.socket.send(request.encode('utf-8'))
        results_txt = self.recvall(self.socket)
        self.close()
        if type(results_txt) == dict:
            return self.GET(results_txt['url'])
        parse_result = self.__parse_server_response(results_txt)
        code = int(parse_result['heads'][0].split()[1])
        body = parse_result['body']
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
