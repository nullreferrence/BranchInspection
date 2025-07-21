import csv
import hashlib
from django.conf import settings
import os
os.environ['DJANGO_SETTINGS_MODULE'] ='settings'

from django.contrib.auth.hashers import make_password
from django.utils.crypto import (
    constant_time_compare, get_random_string, pbkdf2,
)

password = '12345678'
with open('AllBr.csv') as csvfile:

    with open('user data.csv', 'w') as newfile:

        reader = csv.DictReader(csvfile)

        for i, r in enumerate(reader):
            #  writing csv headers
            if i is 0:
                newfile.write(','.join(r) + '\n')

            # hashing the 'Password' column
            #r['password'] = pbkdf2((r['password']).encode('utf-8'), salt=32, iterations=100)
            r['password']= make_password(password, salt=None, hasher='default')

            # writing the new row to the file with hashed 'Password'
            newfile.write(','.join(r.values()) + '\n')
