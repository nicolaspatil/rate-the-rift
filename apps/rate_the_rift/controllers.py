"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from py4web import action, request, abort, redirect, URL, Field
from py4web.utils.form import Form, FormStyleBulma
from yatl.helpers import A
from .common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash
from py4web.utils.url_signer import URLSigner
import arrow

DEV_API_KEY = "RGAPI-3d8d82e8-618f-4617-b059-5ff90adf715b"

url_signer = URLSigner(session)

# Function to format time into human readable format using python arrow library
def format_time_ago(dt):
    current_time = arrow.now()
    dt = arrow.get(dt)
    return dt.humanize(current_time)

def get_stats_from_review(review, username=None):
    # Retrieve the game_id from the review
    game_id = review["game_id"]

    # Retrieve the game object from game id
    game = db(db.game.id == game_id).select().first()
    if (game == None):
        redirect(URL('missing_user'))
    # Figure out which username (username1,2, etc) is the user with username "username"
    user_index = 0
    if game.username1 == username:
        user_index = 1
    elif game.username2 == username:
        user_index = 2
    elif game.username3 == username:
        user_index = 3
    elif game.username4 == username:
        user_index = 4
    elif game.username5 == username:
        user_index = 5
    elif game.username6 == username:
        user_index = 6
    elif game.username7 == username:
        user_index = 7
    elif game.username8 == username:
        user_index = 8
    elif game.username9 == username:
        user_index = 9
    
    # Retrieve the stats object from the game
    stats = []
    for i in range(1, 10):
        stats.append(game["username" + str(i) + "_stats"])
    
    if user_index != 0:
        return (stats, user_index)
    else:
        return (stats, None)

def search_user():
    username = request.params.get("username")
    if username is not None:
        redirect(URL("user/" + username))


@action("index", method=["GET", "POST"])
@action.uses("index.html", auth)
def index():
    # Create URL to allow for redirect to user page
    return dict(search_user=search_user)


# Action to display user profile
@action("user/<username>", method=["GET", "POST"])
@action.uses("user.html", auth, db, url_signer)
def user(username=None):
    # Make sure a username was provided
    if username == None:
        redirect(URL('missing_user'))

    # If the username has not been register, create a new entry that is empty
    if db(db.auth_user.username == username).count() == 0:
        redirect(URL('missing_user'))
    
    # Get the user ID of the user who is being searched
    user_id = db(db.auth_user.username == username).select().first().id
    # Retrieve relevant reviews from database
    db_reviews = db(db.review.user_id == user_id).select()

    # Init ratings
    overall_rating = 0
    personality_rating = 0
    performance_rating = 0
    tilt_rating = 0

    # Init most starred reviews (top 3 reviews)
    most_starred_reviews = []

    # Init recent reviews (last 4 reviews)
    recent_reviews = []

    # One and only review loop
    for review in db_reviews:
        personality_rating += review.personality_rating
        performance_rating += review.performance_rating
        tilt_rating += review.tilt_rating

        # Add to most starred reviews if applicable
        if len(most_starred_reviews) < 3:
            most_starred_reviews.append(review)
            # Sort most starred reviews in reverse by stars
            most_starred_reviews.sort(key=lambda x: x.stars, reverse=True)
        # Check if review has more stars than the least starred review
        elif review.stars > most_starred_reviews[2].stars:
            most_starred_reviews[2] = review
            # Sort most starred reviews in reverse by stars
            most_starred_reviews.sort(key=lambda x: x.stars, reverse=True)

        # Add to recent reviews if applicable
        if len(recent_reviews) < 4:
            recent_reviews.append(review)
            # Sort recent reviews in reverse by created_at
            recent_reviews.sort(key=lambda x: x.created_at, reverse=True)
        # Check if review is more recent than the oldest recent review
        elif review.created_at > recent_reviews[3].created_at:
            recent_reviews[3] = review
            # Sort recent reviews in reverse by created_at
            recent_reviews.sort(key=lambda x: x.created_at, reverse=True)


    # Calculate average ratings
    if len(db_reviews) > 0:
        personality_rating = round(personality_rating / len(db_reviews))
        performance_rating = round(performance_rating / len(db_reviews))
        tilt_rating = round(tilt_rating / len(db_reviews))
    overall_rating = round((personality_rating + performance_rating + tilt_rating) / 3)

    # Negative tags criteria
    tags = []
    if overall_rating <= 2:
        tags.append("Unpopular")
    if personality_rating <= 2:
        tags.append("Toxic")
    if performance_rating <= 2:
        tags.append("Bad")
    if tilt_rating <= 2:
        tags.append("Angry")
    
    # Positive tags criteria
    if overall_rating >= 4:
        tags.append("Popular")
    if personality_rating >= 4:
        tags.append("Friendly")
    if performance_rating >= 4:
        tags.append("Carry")
    if tilt_rating >= 4:
        tags.append("Calm and Collected")

    # Neutral tags criteria
    if overall_rating < 4 and overall_rating > 2:
        tags.append("Average")
    if personality_rating < 4 and personality_rating > 2:
        tags.append("Neutral")
    if performance_rating < 4 and performance_rating > 2:
        tags.append("Average")
    if tilt_rating < 4 and tilt_rating > 2:
        tags.append("Normal Mental")

    def create_star_url(review):
        return URL('add_star/' + str(review.id), signer=url_signer)
    
    def create_review_url(review):
        return URL('review/' + str(review.id))

    # Clean recent and most starred reviews of unnecessary data
    # We don't want to expose the following:
    # review_id, reviewer_id, user_id
    for review in recent_reviews:
        review["created_at"] = format_time_ago(review["created_at"])
        review["add_star"] = create_star_url(review)
        review["url"] = create_review_url(review)
        review["review_id"] = None
        review["reviewer_id"] = None
        review["user_id"]   = None
    for review in most_starred_reviews:
        # In case of repeat (recent/moststarred) reviews
        if type(review["created_at"]) is not str:
            review["created_at"] = format_time_ago(review["created_at"])
        if "url" not in review:
            review["url"] = create_review_url(review)
        review["add_star"] = create_star_url(review)
        review["review_id"] = None
        review["reviewer_id"] = None
        review["user_id"]   = None
        stats, bold_id = get_stats_from_review(review, username)
        review["stats"] = stats
        if bold_id is not None:
            review["bold_id"] = bold_id
        
    
    # Create signed URL to create review for this player
    new_review_url = URL('new_review/' + username, signer=url_signer)

    # Return user profile page
    return dict(username=username,
                overall_rating=overall_rating,
                personality_rating=personality_rating,
                performance_rating=performance_rating,
                tilt_rating=tilt_rating,
                tags=tags,
                most_starred_reviews=most_starred_reviews,
                recent_reviews=recent_reviews,
                new_review_url=new_review_url,
                search_user=search_user,
                )
    

# Create a new review for a player
@action("new_review/<username>", method=["GET", "POST"])
@action.uses("new_review.html", auth, db, session, url_signer.verify())
def new_review(username=None):
    if username == None:
        redirect(URL('missing_user'))
    
    # Find all games that both users played in together
    game_id = db(((db.game.username1 == username) |
                    (db.game.username2 == username) |
                    (db.game.username3 == username) |
                    (db.game.username4 == username) |
                    (db.game.username5 == username) |
                    (db.game.username6 == username) |
                    (db.game.username7 == username) |
                    (db.game.username8 == username) |
                    (db.game.username9 == username)) &
                    ((db.game.username1 == db.auth_user.username) |
                    (db.game.username2 == db.auth_user.username) |
                    (db.game.username3 == db.auth_user.username) |
                    (db.game.username4 == db.auth_user.username) |
                    (db.game.username5 == db.auth_user.username) |
                    (db.game.username6 == db.auth_user.username) |
                    (db.game.username7 == db.auth_user.username) |
                    (db.game.username8 == db.auth_user.username) |
                    (db.game.username9 == db.auth_user.username))).select().first()
    if game_id is None or "game_id" not in game_id:
        game_id = "55"
    else:
        game_id = game_id["game_id"]

    # Generate a form to create a new review
    form = Form([
        Field('performance_rating'),
        Field('tilt_rating'),
        Field('personality_rating'),
        ],
        csrf_session=session,
        formstyle=FormStyleBulma
    )

    # If form was submitted and was valid,
    # create review and redirect back to user page
    if form.accepted:
        # Get user ID of user being reviewed
        user_id = db(db.auth_user.username == username).select().first()["id"]
        # Get user ID of the reviewer
        reviewer_id = auth.current_user.get("id")

        print(type(user_id))
        print(type(reviewer_id))
        print(type(game_id))

        # Insert review into database
        db.review.insert(
            game_id=game_id,
            user_id=user_id,
            reviewer_id=reviewer_id,
            performance_rating=form.vars["performance_rating"],
            tilt_rating=form.vars["tilt_rating"],
            personality_rating=form.vars["personality_rating"],
            stars=0,
        )
        redirect(URL('user/' + username))

    return locals()

@action("missing_user", method=["GET", "POST"])
@action.uses("missing_user.html", auth)
def missing_user():
    return dict(search_user=search_user)

@action("add_star/<review_id>", method=["GET", "POST"])
@action.uses("add_star.html", auth, db, session, url_signer.verify())
def add_star(review_id=None):
    if review_id == None:
        redirect(URL('missing_user'))
    
    # Get review from database
    review = db(db.review.id == review_id).select().first()
    if review == None:
        redirect(URL('missing_user'))

    # Increment review stars by 1
    review.stars += 1
    review.update_record()

    # Redirect back to user page
    redirect(URL('user/' + review.user_id.username))

@action("my_profile", method=["GET", "POST"])
@action.uses("my_profile.html", auth, db, session, url_signer.verify())
def my_profile():
    # Retrieve id of auth user
    user_id = auth.current_user.get("id")

    # Retrieve 3 most recent reviews for this user
    db_reviews = db(db.review.reviewer_id == user_id).select()
    recent_reviews = []
    for review in db_reviews:
        # Add to recent reviews if applicable
        if len(recent_reviews) < 3:
            recent_reviews.append(review)
            # Sort recent reviews in reverse by created_at
            recent_reviews.sort(key=lambda x: x.created_at, reverse=True)
        # Check if review is more recent than the oldest recent review
        elif review.created_at > recent_reviews[2].created_at:
            recent_reviews[2] = review
            # Sort recent reviews in reverse by created_at
            recent_reviews.sort(key=lambda x: x.created_at, reverse=True)
        
    return dict(
        search_user=search_user,
    )

    
    
@action("review/<review_id>", method=["GET", "POST"])
@action.uses("review.html", auth, db, session)
def review(review_id=None):
    if review_id == None:
        redirect(URL('missing_user'))
    
    # Get review from database
    review = db(db.review.id == review_id).select().first()
    if review == None:
        redirect(URL('missing_user'))
    
    bold_user = None
    stats_col_1 = []
    stats_col_2 = []

    # Get user being reviewed
    user = db(db.auth_user.id == review.user_id).select().first()
    if user == None:
        redirect(URL('missing_user'))


    # Get review object for review_id
    db_review = db(db.review.id == review_id).select().first()

    # Get ratings from review
    personality_rating = db_review.personality_rating
    performance_rating = db_review.performance_rating
    tilt_rating = db_review.tilt_rating
    overall_rating = (personality_rating + performance_rating + tilt_rating) / 3
    
    # Get the game this review is for
    game = db(db.game.id == review.game_id).select().first()
    if game == None:
        redirect(URL('missing_user'))

    stats, i = get_stats_from_review(review, user["username"])
    bold_user = { "username": user["username"], "stats": game["username" + str(i) + "_stats"] }
    # If i in the first half (team 1), put the rest of the players on that team into col1
    if int(i) <= 5:
        for j in range(1, 6):
            if j != int(i):
                stats_col_1.append({ "username": game["username"+str(j)], "stats": game["username"+str(j)+"_stats"] })
        for j in range(6, 11):
            stats_col_2.append({ "username": game["username"+str(j)], "stats": game["username"+str(j)+"_stats"] })
    else:
        for j in range(1, 6):
            stats_col_2.append({ "username": game["username"+str(j)], "stats": game["username"+str(j)+"_stats"] })
        for j in range(6, 11):
            if j != int(i):
                stats_col_1.append({ "username": game["username"+str(j)], "stats": game["username"+str(j)+"_stats"] })
            
    
    return dict(
        bold_user=bold_user,
        stats_col_1=stats_col_1,
        stats_col_2=stats_col_2,
        overall_rating=overall_rating,
        personality_rating=personality_rating,
        performance_rating=performance_rating,
        tilt_rating=tilt_rating,
        username=user["username"],
        search_user=search_user,
    )


@action("recent_games", method=["GET", "POST"])
@action.uses("recent_games.html", auth, db, session)
def recent_games():
    # Get all games from database
    games = []
    games_search = db(db.game).select()


    # Get 10 most recent games and extract information to return
    for game in games_search[:10]:
        games.append(
            {
                "id": game.id,
                "team1": [game.username1, game.username2, game.username3, game.username4, game.username5],
                "team2": [game.username6, game.username7, game.username8, game.username9, game.username10],
                "created_at": game.created_at,
                "team1_stats": [game.username1_stats, game.username2_stats, game.username3_stats, game.username4_stats, game.username5_stats],
                "team2_stats": [game.username6_stats, game.username7_stats, game.username8_stats, game.username9_stats, game.username10_stats],
            }
        )
    # Sort games in reverse by created_at
    games.sort(key=lambda x: x["created_at"], reverse=True)

    # Convert created_at to string
    for game in games:
        game["created_at"] = format_time_ago(game["created_at"])
    
    return dict(
        games=games,
        search_user=search_user,
    )