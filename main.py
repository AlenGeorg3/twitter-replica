from datetime import datetime
import re
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.auth.transport import requests
from google.cloud import firestore, storage
import google.oauth2.id_token
import local_constants


# init app
app = FastAPI()

firebase_request_adapter = requests.Request()

firestore_db = firestore.Client()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# get user reference from firestore
def get_user(user_token):
    user_id = user_token["user_id"]
    users = firestore_db.collection("User")
    for user in users.stream():
        if user.id == user_id:
            id = user.id
            user = user.to_dict()
            user["id"] = id
            return user


def validate_username(username):
    # make sure username
    # - starts with character,
    # - has no special characters apart from '-'
    # - is of 12 characters length
    pattern = r"^[a-zA-Z\-][a-zA-Z0-9\-]{0,11}$"
    if not re.match(pattern, username):
        return False

    # check if there is no duplication
    users = firestore_db.collection("User")
    for user in users.stream():
        if user.to_dict()["username"] == username:
            return False
    return True


# search for username or tweet depending on user selection
async def search_db(request):
    form = await request.form()

    query = form["query"].lower()  # Convert the query to lowercase for comparison
    selection = form["searchType"]

    firestore_db = firestore.Client()

    results = []

    if selection == "users":
        # Retrieve all user documents
        users_ref = firestore_db.collection("User")
        users_results = users_ref.stream()

        for user in users_results:
            id = user.id
            user_data = user.to_dict()
            user_data["id"] = id

            # match against start of query
            if user_data.get("username", "").lower().startswith(query):
                results.append(user_data)

    elif selection == "tweets":
        # Retrieve all tweet documents
        tweets_ref = firestore_db.collection("Tweet")
        tweets_results = tweets_ref.stream()

        for tweet in tweets_results:
            tweet_data = tweet.to_dict()

            # match against start of query
            if tweet_data.get("content", "").lower().startswith(query):
                tweet_data["date"] = tweet_data["date"].strftime("%b %d, %Y %H:%M")
                results.append(tweet_data)

    return results


# function to fetch tweets of user[s]
def fetch_tweets(users):

    user_tweets = []

    # retrieve tweets of single user (for user page)
    if type(users) is str:
        doc_ref = firestore_db.collection("User").where("username", "==", users)
        doc = doc_ref.get()[0].to_dict()
        if "tweets" in doc:
            for tweet_id in doc["tweets"]:
                tweet_doc = firestore_db.collection("Tweet").document(tweet_id).get()
                tweet = tweet_doc.to_dict()
                if tweet:
                    tweet["id"] = tweet_doc.id
                    tweet["date"] = tweet["date"].strftime("%b %d, %Y %H:%M")
                    user_tweets.append(tweet)

        # Sort the tweets by timestamp in reverse chronological order
        user_tweets = sorted(user_tweets, key=lambda tweet: tweet["date"], reverse=True)

    else:
        # retrieve tweets of users followed (for main page - timeline)
        for user in users:
            doc_ref = firestore_db.collection("User").where("username", "==", user)
            doc = doc_ref.get()[0].to_dict()
            if "tweets" in doc:
                for tweet_id in doc["tweets"]:
                    tweet_doc = (
                        firestore_db.collection("Tweet").document(tweet_id).get()
                    )
                    tweet = tweet_doc.to_dict()
                    if tweet:
                        tweet["id"] = tweet_doc.id
                        tweet["date"] = tweet["date"].strftime("%b %d, %Y %H:%M")
                        user_tweets.append(tweet)

        # Sort the tweets by timestamp in reverse chronological order
        user_tweets = sorted(user_tweets, key=lambda tweet: tweet["date"], reverse=True)

    return user_tweets


# handles requests to main page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    id_token = request.cookies.get("token")
    error_message = request.cookies.get("message", None)
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )
        except ValueError as err:
            print(str(err))

    else:
        return RedirectResponse("/profile")

    user = get_user(user_token)
    username = None
    tweets = []

    # if username set, fetch following list to generate timeline
    if user:
        username = user["username"]
        users = user["following"]
        users.append(username)
        tweets = fetch_tweets(users)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user_token": user_token,
            "error_message": error_message,
            "username": username,
            "tweets": tweets[:20],
        },
    )


# handles post requests to main page
@app.post("/", response_class=HTMLResponse)
async def root(request: Request):
    id_token = request.cookies.get("token")
    message = request.cookies.get("message", None)
    error_message = request.cookies.get("error_message", None)
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )
        except ValueError as err:
            print(str(err))

    else:
        return RedirectResponse("/profile")

    user = get_user(user_token)
    username = None
    tweets = []
    # if username set, fetch following list to generate timeline
    if user:
        username = user["username"]
        users = user["following"]
        users.append(username)
        tweets = fetch_tweets(users)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user_token": user_token,
            "error_message": error_message,
            "username": username,
            "message": message,
            "tweets": tweets[:20],
        },
    )


# handles requests to login page
@app.get("/profile", response_class=HTMLResponse)
async def login(request: Request):
    id_token = request.cookies.get("token")
    error_message = "No error"
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )
        except ValueError as err:
            print(str(err))

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user_token": user_token,
            "error_message": error_message,
        },
    )


# handles requests to set username
@app.post("/set-username", response_class=HTMLResponse)
async def set_username(request: Request):
    id_token = request.cookies.get("token")
    error_message = "No error"
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )
        except ValueError as err:
            print(str(err))

    else:
        return RedirectResponse("/login")

    ## validation code
    user = get_user(user_token)
    form = await request.form()
    username = form["username"]

    if user:
        error_message = "Username already set"
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "user_token": user_token,
                "error_message": error_message,
            },
        )
    elif not validate_username(username):
        error_message = "Error: Invalid username or already exists"
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "user_token": user_token,
                "error_message": error_message,
            },
        )
    # create firebase document for user, provided username is valid
    else:
        data = {"username": username.title(), "tweets": [], "following": []}

        users = firestore_db.collection("User")
        users.add(document_data=data, document_id=user_token["user_id"])

    response = RedirectResponse("/")
    response.set_cookie(key="message", value="Username has been set", max_age=5)
    return response


# handles requests to submit a tweet
@app.post("/submit-post", response_class=HTMLResponse)
async def submit_post(request: Request):
    id_token = request.cookies.get("token")
    error_message = "No error"
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )
        except ValueError as err:
            print(str(err))

    else:
        return RedirectResponse("/login")

    # fetch post input from the form
    form = await request.form()

    username = form["username"]
    date = datetime.now()
    content = form["post"]
    image = form["image"]

    # load coud storage bucket for uploading image
    storage_client = storage.Client(project=local_constants.PROJECT_NAME)
    bucket = storage_client.bucket(local_constants.PROJECT_STORAGE_BUCKET)

    # make sure post is no longer than 140 characters
    if len(content) > 140:
        response = RedirectResponse("/")
        response.set_cookie(
            key="error_message",
            value="Post must be less than 140 characters.",
            max_age=5,
        )
        return response
    else:
        data = {"username": username, "date": date, "content": content, "image": ""}

        # check if user request is to add or update the post
        edit = form["edit"]
        if edit == "True":
            # Edit existing document by using the set method
            tweet_id = form["tweet_id"]
            print(tweet_id)
            tweet_ref = firestore_db.collection("Tweet").document(tweet_id)
            tweet_ref.set(data, merge=True)
            print(tweet_ref.id)

            # update image, if new image provided
            if image.filename != "":
                blob = storage.Blob(tweet_id, bucket)
                blob.upload_from_file(image.file, if_generation_match=None)
                blob.make_public()

                firestore_db.collection("Tweet").document(tweet_id).update(
                    {"image": blob.public_url}
                )

            response = RedirectResponse("/")
            response.set_cookie(
                key="message", value="Tweet updated successfully", max_age=5
            )
            return response
        else:
            # Add new document
            tweet_ref = firestore_db.collection("Tweet").add(data)

            # upload image, if image provided
            if image.filename != "":
                blob = storage.Blob(tweet_ref[1].id, bucket)
                blob.upload_from_file(image.file)
                blob.make_public()
                firestore_db.collection("Tweet").document(tweet_ref[1].id).update(
                    {"image": blob.public_url}
                )

            # add tweet to user document
            user = get_user(user_token)
            user_doc = firestore_db.collection("User").document(user["id"])
            user_doc.update({"tweets": firestore.ArrayUnion([tweet_ref[1].id])})

            response = RedirectResponse("/")
            response.set_cookie(
                key="message", value="Tweet added successfully", max_age=5
            )
            return response


# handles requests to load search interface
@app.get("/search", response_class=HTMLResponse)
async def load_search(request: Request):
    id_token = request.cookies.get("token")
    error_message = "No error"
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )
        except ValueError as err:
            print(str(err))

    else:
        return RedirectResponse("/login")

    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "user_token": user_token,
            "error_message": error_message,
        },
    )


# handles searching functionality
@app.post("/search", response_class=HTMLResponse)
async def search(request: Request):
    id_token = request.cookies.get("token")
    error_message = "No error"
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )
        except ValueError as err:
            print(str(err))

    else:
        return RedirectResponse("/login")

    search_results = await search_db(request)

    form = await request.form()
    type = form["searchType"]

    # if no results found
    if len(search_results) == 0:
        return templates.TemplateResponse(
            "search.html",
            {
                "request": request,
                "user_token": user_token,
                "error_message": error_message,
                "no_results": True,
            },
        )
    # if searching for users
    elif type == "users":
        return templates.TemplateResponse(
            "search.html",
            {
                "request": request,
                "user_token": user_token,
                "error_message": error_message,
                "user_results": search_results,
            },
        )
    # if searching for tweets
    else:

        return templates.TemplateResponse(
            "search.html",
            {
                "request": request,
                "user_token": user_token,
                "error_message": error_message,
                "tweet_results": search_results,
            },
        )


# handles requests to a user page
@app.post("/user/{username}", response_class=HTMLResponse)
async def user_profile(request: Request, username: str):
    id_token = request.cookies.get("token")
    error_message = "No error"
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )
        except ValueError as err:
            print(str(err))

    else:
        return RedirectResponse("/login")

    # set following flag
    user = get_user(user_token)
    following = False
    if username in user["following"]:
        following = True

    # flag to not allow following themselves
    current_user = False
    if username == user["username"]:
        current_user = True

    # Retrieve and process user's tweets
    user_tweets = fetch_tweets(username)

    return templates.TemplateResponse(
        "user.html",
        {
            "request": request,
            "user_token": user_token,
            "error_message": error_message,
            "user_tweets": user_tweets[:10],
            "username": username,
            "total_tweets": len(user_tweets),
            "following": following,
            "current_user": current_user,
        },
    )


# handles requests to a user page
@app.post("/follow/{username}", response_class=HTMLResponse)
async def follow(request: Request, username: str):
    id_token = request.cookies.get("token")
    error_message = "No error"
    user_token = None
    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )
        except ValueError as err:
            print(str(err))

    else:
        return RedirectResponse("/login")

    # fetch the users following list
    user = get_user(user_token)

    user_doc = firestore_db.collection("User").document(user["id"])
    user_info = user_doc.get().to_dict()
    following = user_info.get("following", [])

    # make sure the current user is not the same as the one to be followed
    if username not in following and username != user_info["username"]:
        user_doc.update({"following": firestore.ArrayUnion([username])})
        return RedirectResponse(f"/user/{username}")

    # if unfollow action is to be performed
    elif username in following:
        user_doc.update({"following": firestore.ArrayRemove([username])})
        return RedirectResponse(f"/user/{username}")

    else:
        return RedirectResponse(f"/user/{username}")


# handles post requests to main page
@app.post("/edit-tweet", response_class=HTMLResponse)
async def edit_tweet(request: Request):
    id_token = request.cookies.get("token")
    error_message = None
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )
        except ValueError as err:
            print(str(err))

    else:
        return RedirectResponse("/profile")

    # retrieve data from the form, to populate the edit page with existing data
    form = await request.form()
    tweet = {
        "id": form["tweet_id"],
        "content": form["tweet_content"],
        "image": form.get("image", ""),
    }

    username = form["username"]

    return templates.TemplateResponse(
        "edit.html",
        {
            "request": request,
            "user_token": user_token,
            "error_message": error_message,
            "username": username,
            "tweet": tweet,
        },
    )


# handles requests to delete a tweet
@app.post("/delete-tweet", response_class=HTMLResponse)
async def delete_tweet(request: Request):
    id_token = request.cookies.get("token")
    user_token = None

    if id_token:
        try:
            user_token = google.oauth2.id_token.verify_firebase_token(
                id_token, firebase_request_adapter
            )
        except ValueError as err:
            print(str(err))

    else:
        return RedirectResponse("/login")

    form = await request.form()

    # remove tweet from the collection
    tweet_id = form["tweet_id"]

    tweet_ref = firestore_db.collection("Tweet").document(tweet_id)
    tweet_ref.delete()

    # remove tweet reference from user document
    user = get_user(user_token)
    user_id = user["id"]
    user_doc = firestore_db.collection("User").document(user_id)
    user_doc.update({"tweets": firestore.ArrayRemove([tweet_id])})

    response = RedirectResponse("/")
    response.set_cookie(key="message", value="Tweet deleted successfully", max_age=5)
    return response
