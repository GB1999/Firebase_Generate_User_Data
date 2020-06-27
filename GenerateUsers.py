import random
import requests
import pandas as pd
import pyrebase

from urllib.error import HTTPError
from faker import Faker
from faker.providers import BaseProvider

config = {
    "apiKey": "AIzaSyDvYLjgtWFM2_v7EE7uGZMPLBkuGS3N_1I",
    "authDomain": "visacharity.firebaseapp.com",
    "databaseURL": "https://visacharity.firebaseio.com/",
    "projectId": "visacharity",
    "storageBucket": "visacharity.appspot.com",
    "messagingSenderId": "508896557325",
    "appId": "1:508896557325:web:7cc92e67c2df2c022fd844",
    "measurementId": "G-3VL2WDL31R"
  }

firebase = pyrebase.initialize_app(config)
storage = firebase.storage()
auth = firebase.auth()
database = firebase.database()
fake = Faker()

storage_path = 'images/profile_images/'
charity_ids = ['-MAZlWFt1Wv_ijoyI4ap', '-MAZqkWEQXcHkJKj-dST', '-MAZqkWEQXcHkJKj-dST']

class AdditionalInfoProvider(BaseProvider):
    def custom_email(self, email, name):
        domain = email.split('@')[1]
        first_prefixes = [name.split()[0], name.split()[0][0], ]
        last_prefixes = [name.split()[1], name.split()[1][0],]
        indexes = ['', str(random.randint(1,20))]
        return random.choice(first_prefixes) + random.choice(last_prefixes) + random.choice(indexes) + '@' + domain

    def payment_method(self, name):
        return {
            'card_holder' : random.choice([name, fake.name()]),
            'card_number' : fake.credit_card_number()
        }
    def donation(self, charities):
        return {
            'charity_id': random.choice(charities),
            'amount': str(random.randint(1,100) * 5),
            'date_donated': str(fake.date_between(start_date = '-1y', end_date ='today')),
        }

fake.add_provider(AdditionalInfoProvider)

user_data = []

for i in range(10):
    name = fake.name()
    email = fake.email()

    user =   {'user_ID' : '',
              'first_name': name.split()[0],
              'last_name': name.split()[1],
              'email_address': fake.custom_email(email, name),
              'password': fake.password(),
              'payment_methods': [fake.payment_method(name) for _ in range(random.randint(1,4))],
              'total_amount_donated': random.randint(10,10000),
              'donation_history': [fake.donation(charity_ids) for _ in range(random.randint(1,20))],
              'interests': [fake.word() for _ in range(random.randint(1,7))],
              'profile_image': '',
              }

    try:
        #create firebase user from generated user
        firebase_user = auth.create_user_with_email_and_password(user['email_address'],user['password'])
        user['user_ID'] = firebase_user['localId']

        file_name = name+'.jpg'
        file_path = 'ProfileImages/' + file_name
        r = requests.get("https://thispersondoesnotexist.com/image", headers={'User-Agent': 'My User Agent 1.0'}).content
        with open(file_path, "wb") as f:
            f.write(r)

        #return storage url from database and store it under user profile image
        storage.child(storage_path + user['user_ID'] + '/' + file_name).put(file_path)
        image_url = storage.child(storage_path + user['user_ID'] + '/' + file_name).get_url(token=firebase_user['idToken'])
        user["profile_image"] = image_url



        #push user to firebase using their token
        database.child('Users/' + firebase_user['localId']).push(user, firebase_user['idToken'])

        #check that user was pushed successfully
        users = database.child('Users/' + firebase_user['localId']).get(firebase_user['idToken'])
        print(users.val())

    except FileNotFoundError as err:
        print(err)  # something wrong with local path
    except HTTPError as err:
        print(err)

    user_data.append(user)

print(user_data)
user_DataFrame = pd.DataFrame(user_data)
user_DataFrame.to_csv('user_data.csv')
