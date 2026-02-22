import requests

class Ditto:
    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port
        self.basic_auth = None

    def set_basic_auth(self, user, password):
        self.basic_auth = (user, password)

    def create_thing(self, attributes, features, namespace=None, name=None, policy_id=None):
        url = f"http://{self.host}:{self.port}/api/2/things" #todo: TLS on Ditto to use HTTPS
        payload = {
            "attributes": attributes,
            "features": features
        }
        if policy_id:
            payload["policyId"] = policy_id

        if namespace and name:
            url += f"/{namespace}:{name}" if namespace and name else ""
            response = requests.put(url, json=payload, auth=self.basic_auth or None)
        else:
            response = requests.post(url, json=payload, auth=self.basic_auth or None)
        return response.status_code, response.text

    def create_policy(self, entries, policy_id=None):
        url = f"http://{self.host}:{self.port}/api/2/policies"
        if policy_id:
            url += f"/{policy_id}"
            response = requests.put(url, json=entries, auth=self.basic_auth or None)
        else:
            response = requests.post(url, json=entries, auth=self.basic_auth or None)
        return response.status_code, response.text

