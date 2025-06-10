import ipaddress

def is_not_ip_address(string):
    try:
        ipaddress.ip_address(string)
        return False
    except ValueError:
        return True