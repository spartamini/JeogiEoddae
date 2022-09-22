from pymongo import MongoClient
from bson.objectid import ObjectId
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import certifi

from datetime import datetime

from operator import attrgetter # used for sorting post by likes

ca = certifi.where()

client = MongoClient("mongodb+srv://test:sparta@cluster0.2iwz0e2.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=ca)
db = client.webproject_plus

SECRET_KEY = "SPARTA_MINI_PROJECT"
app = Flask(__name__)

####### Routing #########

# route to login page, if no tokens are given
@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        return render_template('index.html', user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/search/<search_query>')
def home_with_search(search_query):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        return render_template('search.html', user_info=user_info, search_query=str(search_query))
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

# msg depend on the cookie state
@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/signup')
def signup():
   return render_template('signup.html')

@app.route('/user/<username>')
def user(username):
    # 각 사용자의 프로필과 글을 모아볼 수 있는 공간
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False

        user_info = db.users.find_one({"username": username}, {"_id": False})
        return render_template('user.html', user_info=user_info, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/edit_profile/<username>')
def edit_profile(username):
   return render_template('edit_profile.html', username=username)

@app.route('/post/<post_id>')
def load_post(post_id):
   return render_template('post.html', post_id=post_id)


####### Log in/Sign up #########

# TODO: regex for password

@app.route("/signup", methods=["POST"])
def user_signup():
    first_name_receive = request.form['first_name_give']
    last_name_receive = request.form['last_name_give']
    username_receive = request.form['username_give']
    email_receive = request.form['email_give']
    password_receive = request.form['pw_give']
    location_receive = request.form['location_give']

    # TODO: use location API to validate the location

    if len(first_name_receive) == 0 or len(last_name_receive) == 0:
        return jsonify({'msg': 'Name is missing!'})
    elif len(username_receive) == 0:
        return jsonify({'msg': 'Username is missing!'})
    elif len(email_receive) == 0:
        return jsonify({'msg': 'Email is missing!'})
    elif len(password_receive) == 0:
        return jsonify({'msg': 'Password is missing!'})
    elif len(location_receive) == 0:
        return jsonify({'msg': 'Location is missing!'})

    if db.users.find_one({'username':username_receive}) is not None:
        return jsonify({"msg":"username already exist!"})

    # encode given password via hash function
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    doc = {
        'first_name': first_name_receive,
        'last_name': last_name_receive,
        'username' : username_receive,
        'email' : email_receive,
        'password' : password_hash,
        'location': location_receive,
        'profile_pic':"profile_picture.png"
    }
    db.users.insert_one(doc)

    return jsonify({'msg': 'Sign up completed!'})

@app.route("/check_duplicate", methods=["POST"])
def check_duplicate():
    username_receive = request.form['username_give']
    username = db.users.find_one({'username':username_receive})

    if username is None:
        return jsonify({'msg': 'Username Available!'})
    else:
        return jsonify({'msg': 'Username Taken!'})

@app.route("/login", methods=["POST"])
def user_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    # encoded password via hash function
    pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

    user = db.users.find_one({'username':id_receive, 'password' : pw_hash})

    if user is not None:
        payload = {
            'id': id_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # remain logged in for 1 day
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'msg': 'Login Success!', 'token': token})

    else:
        return jsonify({'msg': 'Login Failure'})

# TODO: UPDATE PROFILE WITH JWT

@app.route("/update-profile", methods=["POST"])
def update_profile():
    username_receive = request.form['username_give']
    first_name_receive = request.form['firstname_give']
    last_name_receive = request.form['lastname_give']
    email_receive = request.form['email_give']
    password_receive = request.form['password_give']
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    if len(first_name_receive) > 0:
        db.users.update_one({'username': username_receive}, {'$set': {'first_name': first_name_receive}})
    if len(last_name_receive) > 0:
        db.users.update_one({'username': username_receive}, {'$set': {'last_name': last_name_receive}})
    if len(email_receive) > 0:
        db.users.update_one({'username': username_receive}, {'$set': {'email': email_receive}})
    if len(password_receive) > 0:
        db.users.update_one({'username': username_receive}, {'$set': {'password': pw_hash}})
    
    return jsonify({'msg': 'Profile Successfully Updated!'})

####### POST SECTION ###########

@app.route('/get-post', methods=['POST'])
def get_post():
    post_id_receive = request.form['post_id_give']
    post = db.post.find_one({"_id": ObjectId(post_id_receive)})
    post["_id"] = str(post["_id"])

    return jsonify({"post": post})


@app.route('/post', methods=['POST'])
def add_post():
    token_receive = request.cookies.get('mytoken')
    try:
        # TODO: add name to doc
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        username_receive = request.form['username_give']
        location_receive = request.form['location_give']
        title_receive = request.form['title_give']
        desc_receive = request.form['desc_give']
        time_receive = request.form['time_give']

        image = request.files["image_give"]

        extension = image.filename.split('.')[-1] # jpg, png, etc

        filename = f"{username_receive} - {title_receive} - {datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.{extension}"

        save_to = f"static/post_images/{filename}" # dir
        image.save(save_to)

        doc = {
            'username': username_receive,
            'location': location_receive,
            'title': title_receive,
            'desc': desc_receive,
            'image': filename,
            'time': time_receive,
            'count_heart':0,
            'count_comment':0
        }
        db.post.insert_one(doc)

        post = db.post.find_one(doc)
        print(post)
        post['_id'] = str(post['_id'])

        return jsonify({'msg': '등록 완료!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/search', methods=['POST'])
def find_location():
    location_receive = request.form['location_give']
    post_list = list(db.post.find(
        {'location':  { 
            "$regex": location_receive,
            "$options" :'i' # case-insensitive
            } 
        })
    )
    post_list2 = list(db.post.find(
        {'title':  { 
            "$regex": location_receive,
            "$options" :'i' # case-insensitive
            } 
        })
    )
    post_list3 = list(db.post.find(
        {'username':  { 
            "$regex": location_receive,
            "$options" :'i' # case-insensitive
            } 
        })
    )
    post_list = post_list + post_list2 + post_list3
    
    for post in post_list:
        post['_id'] = str(post['_id'])

    return jsonify({'posts': post_list})

@app.route('/load-profile', methods=['POST'])
def post_by_user():
    username_receive = request.form['username_give']
    post_list = list(db.post.find(
        {'username': username_receive}
    ))

    for post in post_list:
        post["_id"] = str(post["_id"])

    return jsonify({'post_list': post_list})

@app.route('/all-posts', methods=['GET'])
def get_all_posts():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 포스팅 목록 받아오기
        posts = list(db.post.find({}).sort("time", -1).limit(20))
        for post in posts:
            post["_id"] = str(post["_id"])
            post["count_heart"] = db.likes.count_documents({"post_id": post["_id"]})
            post["heart_by_me"] = bool(db.likes.find_one({"post_id": post["_id"], "username": payload['id']}))
            post["count_comment"] = db.comments.count_documents({"post_id": post["_id"]})
        return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", "posts": posts})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/edit-post', methods=['POST'])
def edit_post():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        post_id = request.form["post_id_give"]
        location_receive = request.form['location_give']
        title_receive = request.form['title_give']
        desc_receive = request.form['desc_give']
        # need to be in f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}" format
        time_receive = request.form['time_give'] 

        image = request.files["image_give"]

        post = db.post.find_one({
            "post_id": post_id
        })

        if post is None:
            return jsonify({'msg': '없는 포스트 입니다!'})
        else:
            extension = image.filename.split('.')[-1] # jpg, png, etc

            filename = f"{payload['id']} - {title_receive} - {datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.{extension}"

            save_to = f"static/{filename}" # dir
            image.save(save_to)

            db.post.update_one({
            'username': payload["id"],
            'location': location_receive,
            'time': time_receive
            }, {
                '$set': {
                    'title': title_receive,
                    'desc': desc_receive,
                    'image': filename,
                    'time': f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
                }
            })

            return jsonify({'msg': '수정 완료!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/delete-post', methods=['POST'])
def delete_post():
    # TODO: how to delete the images of the post
    # from the static folder?

    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        post_id = request.form["post_id_give"]
        db.post.delete_one({"post_id": post_id})
        return jsonify({'msg': '삭제 완료!'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

####### LIKE SECTION ###########
@app.route('/update_like', methods=['POST'])
def update_like():
    # covers both like & cancelling a like
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 좋아요 수 변경
        user_info = db.users.find_one({"username": payload["id"]})
        post_id_receive = request.form["post_id_give"]
        action_receive = request.form["action_give"]
        doc = {
            "post_id": post_id_receive,
            "username": user_info["username"]
        }
        if action_receive =="like":
            db.likes.insert_one(doc)
        else:
            db.likes.delete_one(doc)
        count = db.likes.count_documents({"post_id": post_id_receive})
        return jsonify({"result": "success", 'msg': 'updated', "count": count})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/sort-like', methods=['GET'])
def sort_by_likes():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # shows top 20 posts
        sorted_list = list(db.likes.find({}).sort("count", -1).limit(20))
        return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", "posts": sorted_list})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


####### COMMENT SECTION ###########

@app.route('/comment', methods=['POST'])
def update():
    # covers both adding/editing/deleting a comment
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 좋아요 수 변경
        user_info = db.users.find_one({"username": payload["id"]})
        post_id_receive = request.form["post_id_give"]
        comment_id_receive = request.form["comment_id_give"]
        action_receive = request.form["action_give"]
        comment_receive = request.form["comment_give"]

        doc = {
            "post_id": post_id_receive,
            "comment_id": comment_id_receive,
            "username": user_info["username"],
            "comment": comment_receive
        }
        if action_receive is "add":
            db.comments.insert_one(doc)
        elif action_receive is "edit":
            db.comments.update_one({"comment_id": comment_id_receive},{'$set':{"comment": comment_receive}})
        else:
            db.comments.delete_one(doc)
        
        count = db.comments.count_documents({"post_id": post_id_receive, "comment_id": comment_id_receive})
        return jsonify({"result": "success", 'msg': 'updated', "count": count})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)