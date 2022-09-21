import jwt
from datetime import datetime, timedelta

SECRET_KEY = "SPARTA_MINI_PROJECT"

payload = {
            'id': "username",
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60)  # remain logged in for 1 hr
        }
token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

print(token)

print(type(token))

payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

print(payload)