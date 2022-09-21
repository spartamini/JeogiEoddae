from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

from pymongo import MongoClient
import certifi

ca = certifi.where()

client = MongoClient('mongodb+srv://test:sparta@cluster0.ixwpxfb.mongodb.net/Cluster0?retryWrites=true&w=majority', tlsCAFile=ca)
db = client.dbsparta

from datetime import datetime

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


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)