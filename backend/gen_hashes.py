from passlib.context import CryptContext
import json

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

users = ["admin", "analyst", "viewer"]
passwords = ["admin123", "analyst123", "viewer123"]

hashes = {}
for user, pwd in zip(users, passwords):
    hashes[user] = pwd_context.hash(pwd)

with open('hashes.json', 'w') as f:
    json.dump(hashes, f)

print('Hashes generados:')
for user in users:
    print(f'  {user}: {hashes[user]}')
