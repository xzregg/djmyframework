from ..utils.ip import ip2region


def test_ip():
    print(ip2region('1.2.3.4').region)
    print(ip2region('1.0.32.2').region)
