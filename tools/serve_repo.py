#!/usr/bin/env python3
"""Serve a real LAN repository; generate URLs for this computer before starting."""
import argparse
import functools
import http.server
import ipaddress
from pathlib import Path
import socket
from build_repo import build,ROOT
p=argparse.ArgumentParser();p.add_argument('--ip');p.add_argument('--port',type=int,default=8765);a=p.parse_args()
ip=a.ip
if not ip:
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    try:s.connect(('192.0.2.1',1));ip=s.getsockname()[0]
    except OSError:ip='127.0.0.1'
    finally:s.close()
ipaddress.ip_address(ip)
if ip.startswith('127.'):raise SystemExit('Chưa xác định được IP LAN. Chạy lại với --ip DIA_CHI_IP_MAY_TINH')
base='http://%s:%s/'%(ip,a.port);out=ROOT/'lan-dist';build(out,base)
handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=str(out/'site'))
print('Trên Kodi / File manager / Add source, nhập: '+base)
print('Máy tính phải bật và cùng mạng với TV. Nhấn Ctrl+C để dừng.')
http.server.ThreadingHTTPServer(('0.0.0.0',a.port),handler).serve_forever()
