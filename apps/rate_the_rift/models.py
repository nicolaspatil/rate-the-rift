"""
This file defines the database models
"""

from .common import db, Field
from pydal.validators import *
import datetime

def get_time():
    return datetime.datetime.utcnow()

# User table stores user references (even if they haven't signed up!)
#   This allows for "anonymous" users who have not signed up to still have ratings associated with them
#   Main challenge - how to handle users who sign up later?
#   Solution - when a user signs up, check if there are any ratings associated with their riot username
db.define_table("users",
                Field ("user_id", "reference auth_user", writable=False, readable=False, hidden=True),
                Field ("username", "reference auth_user", requires=IS_NOT_EMPTY()), # MUST match in-game username, so this has to be authenticated through Riot API
                                                           # presents new challenge: what if a user has multiple Riot accounts? handle with array potentiallys
                Field ("riot_api_key", "string"), # Riot API key for this user, can be empty up until point where they have signed up
                Field ("reviewer_id"), # unique identifier for this user, used to identify them as reviewers anonymously
                Field ("created_at", "datetime", default=get_time(), writable=False, readable=False, hidden=True),
)

db.define_table("reviews",
                Field ("review_id", "id", writable=False, readable=False, hidden=True),
                Field ("game_id", "string"), # Riot API game ID
                Field ("reviewer_id", "string"), # unique identifier for the reviewing user, used to identify them as reviewers anonymously
                Field ("user_id", "reference users"), # reference to the user who is being reviewed (references users rather than auth since they don't necessarily have a rate_the_rift account)
                Field ("performance_rating", "integer"), # rating of the user's performance in the game
                Field ("tilt_rating", "integer"), # rating of the user's tilt (anger level) in the game
                Field ("personality_rating", "integer"), # rating of the user's personality in the game
                Field ("body", "text"), # body of the review (not required)
                Field ("stars", "integer", requires=IS_NOT_EMPTY()), # rating of the user overall (required)
                Field ("created_at", "datetime", default=get_time(),readable=False),
)

