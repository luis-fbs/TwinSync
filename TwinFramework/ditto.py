import requests

class Ditto:
    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port
        self.basic_auth = None

    def set_basic_auth(self, user, password):
        self.basic_auth = (user, password)

    def create_thing(self, thing):
        url = f"http://{self.host}:{self.port}/api/2/things/{thing.id.get_id()}" #todo: TLS on Ditto to use HTTPS
        response = requests.put(url, json=thing.json(), auth=self.basic_auth or None)
        return response.status_code, response.text

    def create_policy(self, policy):
        url = f"http://{self.host}:{self.port}/api/2/policies/{policy.id.get_id()}"
        response = requests.put(url, json=policy.json(), auth=self.basic_auth or None)
        return response.status_code, response.text

