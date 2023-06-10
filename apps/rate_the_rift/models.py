"""
This file defines the database models
"""

from .common import db, Field, auth
from pydal.validators import *
from py4web.utils.populate import FIRST_NAMES, LAST_NAMES, IUP
import datetime
import uuid
import random

def get_time():
    return datetime.datetime.utcnow()

def generate_uuid():
    return str(uuid.uuid4())

db.define_table("game",
                Field ("game_id", "id"),
                Field ("username1", "string"),
                Field ("username1_stats", "string"),
                Field ("username2", "string"),
                Field ("username2_stats", "string"),
                Field ("username3", "string"),
                Field ("username3_stats", "string"),
                Field ("username4", "string"),
                Field ("username4_stats", "string"),
                Field ("username5", "string"),
                Field ("username5_stats", "string"),
                Field ("username6", "string"),
                Field ("username6_stats", "string"),
                Field ("username7", "string"),
                Field ("username7_stats", "string"),
                Field ("username8", "string"),
                Field ("username8_stats", "string"),
                Field ("username9", "string"),
                Field ("username9_stats", "string"),
                Field ("username10", "string"),
                Field ("username10_stats", "string"),
                Field ("created_at", "datetime", default=get_time(),readable=False),
)
db.define_table("review",
                Field ("review_id", "id"),
                Field ("game_id", "reference game"),
                Field ("reviewer_id", "reference auth_user"), # user_id of the reviewer
                Field ("user_id", "reference auth_user"), # reference to the user who is being reviewed (references users rather than auth since they don't necessarily have a rate_the_rift account)
                Field ("performance_rating", "integer"), # rating of the user's performance in the game
                Field ("tilt_rating", "integer"), # rating of the user's tilt (anger level) in the game
                Field ("personality_rating", "integer"), # rating of the user's personality in the game
                Field ("stars", "integer", requires=IS_NOT_EMPTY()), # rating of the individaul review
                Field ("created_at", "datetime", default=get_time(),readable=False),
)


db.commit()

# Generate some fake users and game data using their names
def generate_data(num_users, num_games):
    db(db.auth_user.username.startswith("_")).delete()
    db(db.game.username1.startswith("_")).delete()
    db(db.game.username2.startswith("_")).delete()

    num_test_users = db(db.auth_user.username.startswith("_")).count()
    num_new_users = num_users - num_test_users
    print("Adding", num_new_users, "users.")

    usernames = []

    # Creates users and adds to database
    for k in range(num_test_users, num_users):
        first_name = random.choice(FIRST_NAMES)
        last_name = first_name = random.choice(LAST_NAMES)
        username =  "_%s%.2i" % (first_name.lower(), k)
        user = dict(
            username=username,
            email=username + "@ucsc.edu",
            first_name=first_name,
            last_name=last_name,
            password=username,  # To facilitate testing.
        )
        usernames.append(username)
        auth.register(user, send=False)

    # Creates games and adds to database
    game_ids = []
    for k in range(num_games):
        # Use a random combination of usernames to fill username1-10
        random.shuffle(usernames)

        # Create random scorelines (format: K/D/A)
        scorelines = []
        for i in range(10):
            scoreline = str(random.randint(0, 20)) + "/" + str(random.randint(0, 20)) + "/" + str(random.randint(0, 20))
            scorelines.append(scoreline)
        game_id = db.game.insert(
            username1=usernames[0],
            username1_stats=scorelines[0],
            username2=usernames[1],
            username2_stats=scorelines[1],
            username3=usernames[2],
            username3_stats=scorelines[2],
            username4=usernames[3],
            username4_stats=scorelines[3],
            username5=usernames[4],
            username5_stats=scorelines[4],
            username6=usernames[5],
            username6_stats=scorelines[5],
            username7=usernames[6],
            username7_stats=scorelines[6],
            username8=usernames[7],
            username8_stats=scorelines[7],
            username9=usernames[8],
            username9_stats=scorelines[8],
            username10=usernames[9],
            username10_stats=scorelines[9],
        )
        game_ids.append(game_id)
    
    # Generate reviews for each player in each game
    for game_id in game_ids:
        # Get the usernames for the game
        game = db(db.game.game_id == game_id).select().first()

        usernames = []
        for i in range(10):
            username = game["username" + str(i + 1)]
            if username != None:
                usernames.append(username)
        
        # Generate a review for each player in the game on a random player
        for i in range(10):
            # Get the username of the player reviewing
            username = usernames[i]

            # Get the username of the user to be reviewed
            review_username = random.choice(usernames)

            # Get the game_id
            game_id = game["game_id"]

            # Get the user_id of the reviewer
            reviewer = db(db.auth_user.username == username).select().first()
            reviewer_id = reviewer["id"]

            # Get the user_id of the player being reviewed
            user = db(db.auth_user.username == username).select().first()
            user_id = user["id"]

            # Generate random ratings
            performance_rating = random.randint(1, 5)
            tilt_rating = random.randint(1, 5)
            personality_rating = random.randint(1, 5)
            stars = random.randint(1, 5)

            # Generate a random time of creation

            # Insert the review into the database
            db.review.insert(
                game_id=game_id,
                reviewer_id=reviewer_id,
                user_id=user_id,
                performance_rating=performance_rating,
                tilt_rating=tilt_rating,
                personality_rating=personality_rating,
                stars=stars,
            )
    print("Game IDs: " + str(game_ids)), 

    print("Usernames: " + str(usernames))
    db.commit()

generate_data(10, 11)