from flask import Flask, render_template, jsonify, request
app = Flask(__name__)
from pymongo import MongoClient
import certifi

from datetime import datetime

from operator import attrgetter # used for sorting post by likes
import login

ca = certifi.where()

client = MongoClient("mongodb+srv://test:sparta@cluster0.2iwz0e2.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=ca)
db = client.webproject_plus

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login_page.html')
def login():
   return render_template('login_page.html')

@app.route('/signup_page.html')
def signup():
   return render_template('signup_page.html')

@app.route('/user_info.html')
def user_info():
   return render_template('user_info.html')

@app.route('/edit_profile.html')
def edit_profile():
   return render_template('edit_profile.html')

@app.route('/post/<post_id>')
def load_post(post_id):
   return render_template('post.html', post_id=post_id)

# TODO: render template for the post_page

####### Log in/Sign up #########

@app.route("/check_duplicate", methods=["POST"])
def check_duplicate():
    username_receive = request.form['username_give']
    username = db.users.find_one({'username':username_receive})

    if username is None:
        return jsonify({'msg': 'Username Available!'})
    else:
        return jsonify({'msg': 'Username Taken!'})

@app.route("/signup", methods=["POST"])
def user_signup():
    first_name_receive = request.form['first_name_give']
    last_name_receive = request.form['last_name_give']
    username_receive = request.form['username_give']
    email_receive = request.form['email_give']
    pw_receive = request.form['pw_give']
    location_receive = request.form['location_give']

    # TODO: use location API to validate the location

    if len(first_name_receive) == 0 or len(last_name_receive) == 0:
        return jsonify({'msg': 'Name is missing!'})
    elif len(username_receive) == 0:
        return jsonify({'msg': 'Username is missing!'})
    elif len(email_receive) == 0:
        return jsonify({'msg': 'Email is missing!'})
    elif len(pw_receive) == 0:
        return jsonify({'msg': 'Password is missing!'})
    elif len(location_receive) == 0:
        return jsonify({'msg': 'Location is missing!'})

    if db.users.find_one({'username':username_receive}) is not None:
        return jsonify({"msg":"username already exist!"})

    doc = {
        'first_name': first_name_receive,
        'last_name': last_name_receive,
        'username' : username_receive,
        'email' : email_receive,
        'password' : pw_receive,
        'location': location_receive
    }
    db.users.insert_one(doc)

    return jsonify({'msg': 'Sign up completed!'})

@app.route("/login", methods=["POST"])
def user_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    user = db.users.find_one({'username':id_receive, 'password' : pw_receive})

    if user is not None:
        return jsonify({'msg': ['Login Success!', user['first_name'], user['last_name'], user['email'], user['location']]})

    else:
        return jsonify({'msg': 'Login Failure'})

@app.route("/update-profile", methods=["POST"])
def update_profile():
    username_receive = request.form['username_give']
    first_name_receive = request.form['firstname_give']
    last_name_receive = request.form['lastname_give']
    email_receive = request.form['email_give']
    password_receive = request.form['password_give']

    if len(first_name_receive) > 0:
        db.users.update_one({'username': username_receive}, {'$set': {'first_name': first_name_receive}})
    if len(last_name_receive) > 0:
        db.users.update_one({'username': username_receive}, {'$set': {'last_name': last_name_receive}})
    if len(email_receive) > 0:
        db.users.update_one({'username': username_receive}, {'$set': {'email': email_receive}})
    if len(password_receive) > 0:
        db.users.update_one({'username': username_receive}, {'$set': {'password': password_receive}})
    
    return jsonify({'msg': 'Profile Successfully Updated!'})

####### POST SECTION ###########

@app.route('/post', methods=['POST'])
def add_post():
    username_receive = request.form['username_give']
    location_receive = request.form['location_give']
    title_receive = request.form['title_give']
    desc_receive = request.form['desc_give']
    time_receive = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"

    image = request.files["image_give"]

    extension = image.filename.split('.')[-1] # jpg, png, etc

    filename = f"{username_receive} - {title_receive} - {datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.{extension}"

    save_to = f"static/{filename}" # dir
    image.save(save_to)

    doc = {
        'username': username_receive,
        'location': location_receive,
        'title': title_receive,
        'desc': desc_receive,
        'like_dict': {},
        'image': filename,
        'time': time_receive
    }
    db.post.insert_one(doc)

    return jsonify({'msg': '등록 완료!'})

@app.route('/search', methods=['GET'])
def find_location():
    location_receive = request.form['location_give']
    post_list = list(db.post.find(
        {'location': location_receive},
        {'_id':False})
    )

    return jsonify({'msg': post_list})

@app.route('/load-profile', methods=['POST'])
def post_by_user():
    username_receive = request.form['username_give']
    post_list = list(db.post.find(
        {'username': username_receive},
        {'_id':False})
    )

    return jsonify({'post_list': post_list})

@app.route('/', methods=['GET'])
def get_all_posts():
    post_list = list(db.post.find(
        {}, {'_id':False})
    )

    return jsonify({'list': post_list})

@app.route('/edit-post', methods=['POST'])
def edit_post():
    username_receive = request.form['username_give']
    location_receive = request.form['location_give']
    title_receive = request.form['title_give']
    desc_receive = request.form['desc_give']
    # need to be in f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}" format
    time_receive = request.form['time_give'] 

    image = request.files["image_give"]

    post = db.post.find_one({
        'username': username_receive,
        'location': location_receive,
        'time': time_receive
    })

    if post is None:
        return jsonify({'msg': '없는 포스트 입니다!'})
    else:

        extension = image.filename.split('.')[-1] # jpg, png, etc

        filename = f"{username_receive} - {title_receive} - {datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.{extension}"

        save_to = f"static/{filename}" # dir
        image.save(save_to)

        db.post.update_one({
        'username': username_receive,
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

@app.route('/delete-post', methods=['POST'])
def delete_post():
    # TODO: how to delete the images of the post
    # from the static folder?

    username_receive = request.form['username_give']
    location_receive = request.form['location_give']
    # need to be in f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}" format
    time_receive = request.form['time_give'] 

    post = db.post.find_one({
        'username': username_receive,
        'location': location_receive,
        'time': time_receive
    })

    if post is None:
        return jsonify({'msg': '없는 포스트 입니다!'})
    else:

        db.post.delete_one({
            'username': username_receive,
            'location': location_receive,
            'time': time_receive
        })

        return jsonify({'msg': '삭제 완료!'})

####### LIKE SECTION ###########
@app.route('/like', methods=['POST'])
def add_like():    
    # user that pressed like
    username_receive = request.form['username_give']
    # post that the user liked
    post_id_receive = request.form['post_id_give']

    post = db.post.find_one({
        'post_id': post_id_receive,
    })

    if post is None:
        return jsonify({'msg': '없는 글 입니다!'})
    else:
        post['like_dict'][username_receive] = True
        db.post.update_one(
            {'post_id': post_id_receive}, 
            {'$set': {'like_dict': post['like_dict']}}
        )
        return jsonify({'msg': '좋아요 완료!'})

@app.route('/delete-like', methods=['POST'])
def delete_like():    
    # user that unliked the post
    username_receive = request.form['username_give']
    # post that the user unliked
    post_id_receive = request.form['post_id_give']

    post = db.post.find_one({
        'post_id': post_id_receive,
    })

    if post is None:
        return jsonify({'msg': '없는 글 입니다!'})
    else:
        del post['like_dict'][username_receive]
        db.post.update_one(
            {'post_id': post_id_receive}, 
            {'$set': {'like_dict': post['like_dict']}}
        )
        return jsonify({'msg': '좋아요 취소 완료'})

@app.route('/sort-like', methods=['GET'])
def sort_by_likes():
    all_posts = list(db.post.find({},{'_id':False}))

    sorted_posts = sorted(all_posts, key=len(attrgetter('like_dict')))
        

####### COMMENT SECTION ###########

# We identify comment by triplet of 
# a) username
# b) time comment was posted/last edited
# c) post-id
# this is b/c of the assumption that no same user will
# post two comments at the exact time at the 
# exact same post

@app.route('/comment', methods=['POST'])
def add_comment():
    post_id_receive = request.form['post_id_give']
    comment_receive = request.form['comment_give']
    username_receive = request.form['username_give']
    
    doc = {
        'post_id': post_id_receive,
        'comment': comment_receive,
        'username': username_receive,
        'time': f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
    }

    db.comments.insert_one(doc)

    return jsonify({'msg': 'POST 요청 완료!'})

@app.route('/edit-comment', methods=['POST'])
def edit_comment():
    post_id_receive = request.form['post_id_give']
    comment_receive = request.form['comment_give'] # this must be the new comment
    username_receive = request.form['username_give']
    time_receive = request.form['time_give'] # must be in %Y-%m-%d-%H-%M-%S form
    # js must send the time that the comment has been posted
    # We suppose that the time is displayed in the html

    comment = db.comments.find_one({
        'username': username_receive,
        'post_id': post_id_receive,
        'time': time_receive
    })

    if comment is None:
        return jsonify({'msg': '없는 댓글입니다!'})
    else:
        db.comments.update_one({
            'username': username_receive,
        'time': time_receive
        }, {
            '$set': {
                'comment': comment_receive
            }
        })
        return jsonify({'msg': '댓글 업데이트 완료!'})

@app.route('/delete-comment', methods=['POST'])
def delete_comment():
    post_id_receive = request.form['post_id_give']
    username_receive = request.form['username_give']
    time_receive = request.form['time_give'] # must be in %Y-%m-%d-%H-%M-%S form
    # js must send the time that the comment has been posted
    # We suppose that the time is displayed in the html

    comment = db.comments.find_one({
        'username': username_receive,
        'post_id': post_id_receive,
        'time': time_receive
    })

    if comment is None:
        return jsonify({'msg': '없는 댓글입니다!'})
    else:
        db.comments.delete_one({
        'username': username_receive,
        'post_id': post_id_receive,
        'time': time_receive
    })
        return jsonify({'msg': '댓글 삭제 완료!'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)