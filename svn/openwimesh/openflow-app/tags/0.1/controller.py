class Controller():
    def __init__(self):
        self.ofctl_id = None
        self.ofctl_hwaddr = None
        self.ofctl_ipaddr = None
        self.global_ofctl_hwaddr = None
        self.global_ofctl_ipaddr = None
        self.global_ofctl_id = None

    def add_global_ofctl(self, cid, hwaddr, ipaddr):
        self.global_ofctl_hwaddr = hwaddr
        self.global_ofctl_ipaddr = ipaddr
        self.global_ofctl_id = cid

    def get_hw_global_ofctl(self):
        return self.global_ofctl_hwaddr

    def get_ip_global_ofctl(self):
        return self.global_ofctl_ipaddr

    def add_ofctl(self, cid, hwaddr, ipaddr):
        self.ofctl_id = cid
        self.ofctl_hwaddr = hwaddr
        self.ofctl_ipaddr = ipaddr

    def get_cid_ofctl(self):
        return self.ofctl_id

    def get_hw_ofctl(self):
        return self.ofctl_hwaddr

    def get_ip_ofctl(self):
        return self.ofctl_ipaddr