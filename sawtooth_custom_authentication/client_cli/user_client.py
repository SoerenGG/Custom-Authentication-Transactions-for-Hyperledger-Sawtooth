from Crypto.Util import number
from os import urandom
from pathlib import Path
import json


class UserClient:
    def __init__(self, username):
        self.security_lambda2048 = 128
        self.name = username
        if Path('{}.json'.format(self.name)).is_file():       #checken ob username schon angelegt ist, reinladen wenn username schon geaddet
            file = open('{}.json'.format(self.name), )
            data = json.load(file)
            self.prime = data['prime']
            self.wit = data['wit']
        else:
            self.prime = number.getPrime(self.security_lambda2048, urandom)
            self.wit = None
            data = {'prime':self.prime, 'wit': self.wit}
            with open('{}.json'.format(self.name), 'x') as f:
                json.dump(data, f)
                f.close()

    def store_wit(self, wit):
        self.wit = wit
        data = {'prime': self.prime, 'wit': self.wit}
        with open('{}.json'.format(self.name), 'w') as f:
            json.dump(data, f)
            f.close


    def authenticate_me(self):
        return self.prime, self.wit

    def get_prime(self):
        return self.prime

if __name__ == '__main__':
    ersterUser = UserClient("user1")
    ersterUser.store_wit(12345)