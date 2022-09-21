from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

client = MongoClient('mongodb+srv://sparta:test@cluster0.ywf5v3w.mongodb.net/?retryWrites=true&w=majority')
db = client.dbsparta_plus_week4

#################################
####         로그인           ####
#################################

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


@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


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


@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "profile_name": username_receive,                           # 프로필 이름 기본값은 아이디
        "profile_pic": "",                                          # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지
        "profile_info": ""                                          # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/update_profile', methods=['POST'])
def save_img():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 프로필 업데이트
        return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/posting', methods=['POST'])
def posting():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        comment_receive = request.form["comment_give"]
        date_receive = request.form["date_give"]
        doc = {
            "username": user_info["username"],
            "profile_name": user_info["profile_name"],
            "profile_pic_real": user_info["profile_pic_real"],
            "comment": comment_receive,
            "date": date_receive
        }
        db.posts.insert_one(doc)
        return jsonify({"result": "success", 'msg': '포스팅 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route("/get_posts", methods=['GET'])
def get_posts():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        posts = list(db.posts.find({}).sort("date", -1).limit(20))
        for post in posts:
            post["_id"] = str(post["_id"])
        return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다.", "posts":posts})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route('/update_like', methods=['POST'])
def update_like():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        # 좋아요 수 변경
        return jsonify({"result": "success", 'msg': 'updated'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


################################
###         검색/클릭         ####
################################



@app.route('/main', methods=['GET'])
def show_diary():
    sample_receive = request.args.get('sample_give')
    print(sample_receive)
    return jsonify({'msg': 'GET 연결 완료!'})





#################################
####         작성/수정         ####
#################################



@app.route('/write')
def write():
    return render_template('write.html')

@app.route('/post/<num>')
def post(num):
    information = db.jeogi.find_one({'num':'num_give'})
    title = information['title']
    file = information['file']
    map = information['map']
    post = information['post']

    doc = {
        'title':title,
        'file':file,
        'map':map,
        'post':post
    }


    return render_template("post.html", num=num, result=doc)

@app.route('/write', methods=['POST'])
def save_diary():
    #user_info = db.jeogi.find_one({"user_name": payload["id"]})
    title_receive = request.form['title_give']
    post_receive = request.form['post_give']
    map_receive = request.form['map_give']

    file = request.files["file_give"]

    extension = file.filename.split('.')[-1]

    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

    filename = f'file-{mytime}'

    save_to = f'static/{filename}.{extension}'
    file.save(save_to)

    post_list = list(db.jeogi.find({}, {'_id': False}))
    count = len(post_list) + 1

    doc = {
        #'user_name':user_info['user_name'],
        'num': count,
        'file' : f'{filename}.{extension}',
        'title' : title_receive,
        'map' : map_receive,
        'post': post_receive
    }

    db.jeogi.insert_one(doc)
    return jsonify({'msg': '저장 완료!'})

@app.route('/post-edit', methods=['POST'])
def edit_post():
    title_receive = request.form["title_give"]
    post_receive = request.form["post_give"]
    new_doc = {
        "title": title_receive,
        "post": post_receive
    }
    if 'file_give' in request.files:
        file = request.files["file_give"]
        filename = f'file-{mytime}'
        extension = file.filename.split('.')[-1]
        file_path = f'static/{filename}.{extension}'
        file.save(file_path)
        new_doc["profile_pic"] = filename
    db.jeogi.update_one({'username': payload['id']}, {'$set':new_doc})
    return jsonify({"result": "success", 'msg': '포스트 수정 완료!'})

@app.route('/post-delete', methods=['POST'])
def delete_post():
    num_receive = request.form["num_give"]
    db.jeogi.delete_one({'num':num_receive})
    return jsonify({"result": "success", 'msg': '포스트 삭제 완료!'})


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
    all_posts = list(db.post.find({}, {'_id': False}))

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
    comment_receive = request.form['comment_give']  # this must be the new comment
    username_receive = request.form['username_give']
    time_receive = request.form['time_give']  # must be in %Y-%m-%d-%H-%M-%S form
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
    time_receive = request.form['time_give']  # must be in %Y-%m-%d-%H-%M-%S form
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