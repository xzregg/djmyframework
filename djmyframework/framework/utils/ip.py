# coding:utf-8
try:
    import fcntl
except:
    # 不支持windows
    class fcntl:
        @staticmethod
        def flock(*args):
            return 0
import os
import pathlib
import socket
import struct
from dataclasses import dataclass

import ipaddress
from .xdbSearcher import XdbSearcher


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  # SIOCGIFADDR
            struct.pack('256s', ifname[:15])
    )[20:24])


def get_host_ip():
    '''这个方法是目前见过最优雅获取本机服务器的IP方法了。没有任何的依赖，也没有去猜测机器上的网络设备信息。
而且是利用 UDP 协议来实现的，生成一个UDP包，把自己的 IP 放如到 UDP 协议头中，然后从UDP包中获取本机的IP。
这个方法并不会真实的向外部发包，所以用抓包工具是看不到的。但是会申请一个 UDP 的端口，所以如果经常调用也会比较耗时的，这里如果需要可以将查询到的IP给缓存起来，性能可以获得很大提升。
    '''
    return [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]


def guess_ipaddres(ifnames=['eth0', 'eth1', 'eth2', 'em1', 'em2']):
    for i in ifnames:
        try:
            return get_ip_address(i)
        except:
            pass
    else:
        return ''


HOST_IP = get_host_ip()

ip_db = None


def ip_transform(ip):
    import ipdb
    global ip_db
    if not ip_db:
        # 服务依赖：https://www.ipip.net/product/client.html IPv4 免费地址库
        file_path = os.path.join(os.path.dirname(__file__), "ipipfree.ipdb")
        ip_db = ipdb.BaseStation(file_path)
    location = ip_db.find_map(ip, "CN")
    return "{country_name}|{region_name}|{city_name}".format(**location)


@dataclass
class RegionData:
    country: str
    province: str
    city: str
    provider: str
    region: str


class IpRegion(object):
    def __init__(self):
        dbPath = pathlib.Path(__file__).parents[0] / "ip2region.xdb"
        cb = XdbSearcher.loadContentFromFile(dbfile=dbPath)
        self.searcher = XdbSearcher(contentBuff=cb)

    def search(self, ip) -> RegionData:
        region_text = self.searcher.search(ip)
        region_text_split = [item if item != '0' else '' for item in region_text.split('|')]
        data = RegionData(
                country=region_text_split[0],
                province=region_text_split[2],
                city=region_text_split[3],
                provider=region_text_split[4],
                region='-'.join(item for item in region_text_split[:-1] if item),
        )
        return data

    def __del__(self):
        self.searcher.close()


_ip_region = IpRegion()


def ip2region(ip: str):
    return _ip_region.search(ip)


def is_private(ip):
    try:
        network = ipaddress.ip_network(ip)
        return network.is_private
    except ValueError as e:
        print("Invalid IP address")
        return False


if __name__ == '__main__':
    print(ip_transform('219.135.210.50'))
