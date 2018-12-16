# coding=utf-8
from flask import Flask, request, render_template, redirect, jsonify, json, make_response, session, url_for, \
    send_from_directory, abort
from flask_cors import CORS
import os, time, sched
from datetime import timedelta, datetime
from decorators import login_required
import pymysql



db = pymysql.connect("localhost", "user", "user", "db1")

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.permanent_session_lifetime = timedelta(days=7)
CORS(app, resources=r'/*')
CORS(app, supports_credentials=True)
basedir = os.path.abspath(os.path.dirname(__file__))


# 一些函数
# 查找consign_id
def get_consign_id(user_id):
    Cursor = db.cursor()
    sql = "select consign_id from consigns where user_id='%s'" % (user_id)
    db.ping(reconnect=True)
    result = Cursor.execute(sql)
    if result:
        consign_id = Cursor.fetchall()[-1][0]
        Cursor.close()
        return consign_id
    else:
        Cursor.close()
        print("consign_id查找失败")
        return -1




# 定时访问数据库用
@app.route('/R9CXjrcx9vNvG8NepiyY13et')
def timing():
    Cursor_ = db.cursor()
    sql = "select * from users"
    db.ping(reconnect=True)
    Cursor_.execute(sql)
    Cursor_.close()
    abort(404)


# 主页
@app.route('/', methods=["GET"])
@login_required
def index():
    username = session.get("username")
    return render_template('index.html', username=username)


@app.route('/index', methods=["GET"])
@login_required
def Index():
    return redirect(url_for('index'))


# 用户登录
@app.route('/login', methods=["POST", "GET"])
def login():
    if (request.method == 'GET'):
        return render_template('login.html')
    else:
        cursor = db.cursor()
        # #form
        username = request.form.get('username')
        password = request.form.get('password')
        # 检查是否存在用户名和密码
        if not username or not password:
            cursor.close()
            return jsonify({
                "status": 0,
                "message": "提交信息有误！"
            })
        # 登录
        sql = "select user_id from users where username='%s' and `password`='%s'" % \
              (username, password)
        db.ping(reconnect=True)
        result = cursor.execute(sql)
        if result:
            user_id = cursor.fetchall()[0][0]
            # 储存user_id,用户名进入session
            session["user_id"] = user_id
            session["username"] = username
            cursor.close()
            session.permanent = True
            return render_template('index.html')
        else:
            cursor.close()
            return jsonify({
                "status": 0,
                "message": "用户名或密码错误！"
            })


# 用户注册
@app.route('/signup', methods=["POST", "GET"])
def signup():
    if (request.method == 'GET'):
        return render_template('signup.html')
    else:
        cursor = db.cursor()
        #  form
        username = request.form.get('username')
        password = request.form.get('password')
        password1 = request.form.get('password1')
        # 检查是否有用户名和密码
        if not username or not password:
            cursor.close()
            return jsonify({
                "status": 0,
                "message": "提交信息有误！"
            })
        # 检查是否两次密码是否相同
        if (password != password1):
            return jsonify({
                "status": 0,
                "message": "两次密码不相同！"
            })
        # 检查用户是否已经存在
        sql = "select * from users where username='%s'" % (username)
        db.ping(reconnect=True)
        result = cursor.execute(sql)
        if result:
            cursor.close()
            return jsonify({
                "status": 0,
                "message": "用户已存在！"
            })
        # 创建用户
        sql = """INSERT INTO users(username,`password`)
                     VALUES ('%s', '%s')""" % (username, password)
        try:
            cursor.execute(sql)
            db.commit()
            sql = "select user_id from users where username='%s' and `password`='%s'" % \
                  (username, password)
            cursor.execute(sql)
            user_id = cursor.fetchall()[0][0]
            # 储存user_id,用户名进入session
            session["user_id"] = user_id
            session["username"] = username
            session.permanent = True
            cursor.close()
            return redirect(url_for('index'))
        except:
            db.rollback()
            cursor.close()
            return jsonify({
                "status": 0,
                "message": "添加错误！"
            })



# 退出
@app.route('/logout', methods=["GET"])
def logout():
    session.clear()  # 删除所有session
    return redirect(url_for('index'))


# 发布委托
@app.route('/consign', methods=["POST", "GET"])
@login_required
def consign():
    if (request.method == 'GET'):
        return render_template('consign.html')
    else:
        cursor = db.cursor()
        # form
        consign_name = request.form.get('consign_name')
        desc = request.form.get('desc')
        contact = request.form.get('contact')
        partition = request.form.get('partition')
        user_id = session.get('user_id')
        username = session.get('username')
        Time = datetime.now()
        print(Time)
        # print(user_id)
        if not consign_name or not desc or not contact or not partition:
            cursor.close()
            return jsonify({
                "status": 0,
                "message": "提交信息有误！"
            })
        sql = """INSERT INTO consigns(user_id,username,consign_name,`desc`,`time`,contact,`partition`)
                             VALUES ('%s', '%s','%s','%s', '%s','%s','%s');""" \
              % (user_id, username, consign_name, desc, Time, contact, partition)
        try:
            db.ping(reconnect=True)
            cursor.execute(sql)
            db.commit()
            cursor.close()
            # consign_id = get_consign_id(user_id)
            return redirect(url_for('index'))
        except:
            db.rollback()
            cursor.close()
            return jsonify({
                "status": 0,
                "message": "添加错误！"
            })



# 委托状态变更（是否已完成）
@app.route('/consign/finish', methods=["POST"])
@login_required
def finish_change():
    cursor = db.cursor()
    consign_id = request.form.get('consign_id')
    finish = request.form.get('finish')
    username = session.get('username')
    sql = "select * from consigns where consign_id='%s' and username='%s'" \
          % (consign_id, username)
    db.ping(reconnect=True)
    result = cursor.execute(sql)
    if result:
        sql = "update consigns set finished = '%s' where consign_id='%s' and username='%s'" \
              % (finish, consign_id, username)
        try:
            cursor.execute(sql)
            db.commit()
            cursor.close()
            return redirect(url_for('history'))
        except:
            db.rollback()
            cursor.close()
            return jsonify({
                "status": 0,
                "message": "变更状态错误！"
            })
    else:
        cursor.close()
        return jsonify({
            "status": 0,
            "message": "委托不存在！"
        })


# 委托删除
@app.route('/consign/delete/', methods=["GET"])
@login_required
def consign_delete():
    cursor = db.cursor()
    consign_id = request.args.get('consign_id')
    username = session.get('username')
    sql = "select * from consigns where consign_id='%s' and username='%s'" \
          % (consign_id, username)
    db.ping(reconnect=True)
    result = cursor.execute(sql)
    if result:
        sql = "delete from consigns where consign_id='%s' and username='%s'" \
              % (consign_id, username)
        try:
            cursor.execute(sql)
            db.commit()
            sql = "delete from collects where consign_id='%s'" \
              % (consign_id)
            cursor.execute(sql)
            db.commit()
        except:
            db.rollback()
            cursor.close()
            return jsonify({
                "status": 0,
                "message": "删除错误！"
            })

    else:
        cursor.close()
        return jsonify({
            "status": 0,
            "message": "委托不存在！"
        })


# 已发布
@app.route('/history', methods=["GET"])
@login_required
def history():
    return render_template('history.html')


# 获取已发布（未被接受）
@app.route('/get_consign/2', methods=["GET"])
@login_required
def get_consign():
    DB= pymysql.connect("localhost", "user", "user", "db1")
    Cursor = DB.cursor()
    user_id = session.get('user_id')
    sql = "select * from consigns where user_id='%s'" % (user_id)
    DB.ping(reconnect=True)
    results = Cursor.execute(sql)
    output = []
    if results:
        results = Cursor.fetchall()
        for result in results:
            cache = {}
            consign_id = result[0]
            collected = "select * from collects where consign_id='%s'" \
                        % (consign_id)
            if Cursor.execute(collected):
                continue
            else:
                cache['consign_id'] = result[0]
                cache['consign_name'] = result[3]
                cache['desc'] = result[4]
                cache['contact'] = result[6]
                Time = str(result[5])[:-3]
                cache['time'] = time.strftime("%Y/%m/%d %H:%M", time.strptime(Time, '%Y-%m-%d %H:%M'))
                # cache['time'] = str(result[5])
            output.append(cache)
        Cursor.close()
        DB.close()
        return jsonify(output)
    else:
        Cursor.close()
        DB.close()
        return jsonify(output)


# 获取已发布（已被接受）
@app.route('/get_consign/1', methods=["GET"])
@login_required
def got_consign():
    cursor = db.cursor()
    user_id = session.get('user_id')
    sql = "select * from consigns where user_id='%s'" % (user_id)
    db.ping(reconnect=True)
    results = cursor.execute(sql)
    output = []
    if results:
        results = cursor.fetchall()
        for result in results:
            cache = {}
            consign_id=result[0]
            collected = "select * from collects where consign_id='%s'" \
                        % (consign_id)
            if cursor.execute(collected):
                cache['consign_id'] = result[0]
                cache['consign_name'] = result[3]
                cache['desc'] = result[4]
                cache['contact'] = result[6]
                Time = str(result[5])[:-3]
                cache['time'] = time.strftime("%Y/%m/%d %H:%M", time.strptime(Time, '%Y-%m-%d %H:%M'))
                # cache['time'] = str(result[5])
            else:
                continue
            output.append(cache)
        cursor.close()
        return jsonify(output)
    else:
        cursor.close()
        return jsonify(output)

# 判断该委托是否被收藏
@app.route('/consign/<consign_id>', methods=["GET"])
@login_required
def consign_collect(consign_id):
    cursor = db.cursor()
    user_id = session.get("user_id")
    sql = "select * from collects where user_id='%s' and consign_id='%s'"\
          % (user_id, consign_id)
    db.ping(reconnect=True)
    results = cursor.execute(sql)
    if results:
        cursor.close()
        return jsonify({
            "status": 1,
            "message": "该委托已被收藏！"
        })
    else:
        cursor.close()
        return jsonify({
            "status": 0,
            "message": "该委托未被收藏！"
        })


# 收藏添加
@app.route('/add_collect/', methods=["GET"])
@login_required
def add_collect():
    cursor = db.cursor()
    consign_id =str(request.args.get('consign_id'))
    if (consign_id[-1:]=='_'):
        consign_id = str(consign_id[:-1])
    print(consign_id)
    # user_id = 5
    user_id = str(session.get('user_id'))
    print("consign_id=%s,user_id=%s"%(consign_id,user_id))
    sql = "select * from collects where user_id='%s' and consign_id='%s'"\
          % (user_id, consign_id)
    db.ping(reconnect=True)
    results = cursor.execute(sql)
    if results:
        cursor.close()
        return jsonify({
            "status": 0,
            "message": "该委托已被收藏！"
        })
    else:
        sql = """INSERT INTO collects(user_id,consign_id)
                             VALUES ('%s', '%s')""" % (user_id, consign_id)
        try:
            cursor.execute(sql)
            db.commit()
            cursor.close()
            return jsonify({
                "status": 1,
                "message": "添加成功！"
            })
        except:
            # db.rollback()
            cursor.close()
            return jsonify({
                "status": 0,
                "message": "添加错误！"
            })


# 收藏页面获取
@app.route('/collection', methods=["GET"])
@login_required
def collect():
    return render_template('collection.html')


# 获取收藏
@app.route('/get_collect', methods=["GET"])
@login_required
def get_collect():
    cursor = db.cursor()
    user_id = session.get('user_id')
    print("user_id")
    sql = "select * from collects where user_id='%s'" % (user_id)
    db.ping(reconnect=True)
    results = cursor.execute(sql)
    output = []
    if results:
        results = cursor.fetchall()
        for result in results:
            print(result)
            cache = {}
            consign_id = result[2]
            # print(consign_id)
            # print("#############################")
            sql = "select * from consigns where consign_id='%s'" \
                  % (consign_id)
            sql = cursor.execute(sql)
            if sql:
                consign = cursor.fetchall()
                cache["collect_id"] = result[0]
                cache["consign_id"] = result[2]
                cache['consign_name'] = consign[0][3]
                cache['desc'] = consign[0][4]
                cache['contact'] = consign[0][6]
                Time = str(consign[0][5])[:-3]
                cache["time"] = time.strftime("%Y/%m/%d %H:%M", time.strptime(Time, '%Y-%m-%d %H:%M'))
                output.append(cache)
            else:
                continue
        cursor.close()
        return jsonify(output)
    else:
        cursor.close()
        return jsonify(output)


# 收藏删除
@app.route('/collect/delete', methods=["GET"])
@login_required
def collect_delete():
    cursor = db.cursor()
    consign_id = request.args.get('consign_id')
    user_id = session.get('user_id')
    sql = "select * from collects where user_id='%s' and consign_id='%s'" \
          % (user_id, consign_id)
    db.ping(reconnect=True)
    result = cursor.execute(sql)
    if result:
        sql = "delete from collects where user_id='%s' and consign_id='%s'" \
              % (user_id, consign_id)
        try:
            cursor.execute(sql)
            db.commit()
            cursor.close()
            return jsonify({
                "status": 1,
                "message": "删除成功！"
            })
        except:
            db.rollback()
            cursor.close()
            return jsonify({
                "status": 0,
                "message": "删除错误！"
            })

    else:
        cursor.close()
        return jsonify({
            "status": 0,
            "message": "收藏不存在！"
        })


# 搜索网页获取
@app.route('/search/', methods=["GET"])
@login_required
def search_():
    return render_template('search.html')


@app.route('/search/<search_str>', methods=["GET"])
@login_required
def search(search_str):
    return render_template('search.html', search_str=search_str)


# 搜索功能
@app.route('/Search/<search_str>', methods=["GET"])
@login_required
def Search(search_str):
    cursor = db.cursor()
    user_id = session.get('user_id')
    search_str = str(search_str)
    search_list = search_str.split()
    output = []
    Cache = []
    db.ping(reconnect=True)
    for char in search_list:
        sql = "select * from consigns where `consign_name` like '%{}%'".format(char)
        cursor.execute(sql)
        results = cursor.fetchall()
        if Cache:
            Cache = [val for val in Cache if val in results]
        else:
            Cache += results[:]
    for val in Cache:
        cache = {}
        cache['consign_id'] = str(str(val[0])+'_')
        cache['consign_name'] = val[3]
        cache['desc'] = val[4]
        Time = str(val[5])[:-3]
        cache['time'] = time.strftime("%Y/%m/%d %H:%M", time.strptime(Time, '%Y-%m-%d %H:%M'))
        sql = "select * from collects where user_id='%s' and consign_id='%s'"\
              % (user_id, val[0])
        sql = cursor.execute(sql)
        if sql:
            cache['collected'] = 1
        else:
            cache['collected'] = 0
        output.append(cache)
    cursor.close()
    print(output)
    return jsonify(output)


# 最新委托
@app.route('/newest_consign', methods=["GET"])
@login_required
def new_consign():
    cursor = db.cursor()
    user_id = session.get('user_id')
    sql = "select * from consigns where finished='0' order by `time` desc limit 12"
    db.ping(reconnect=True)
    cursor.execute(sql)
    results = cursor.fetchall()
    output = []
    for result in results:
        cache = {}
        cache['consign_id'] = str(str(result[0]) + '_')
        cache['consign_name'] = result[3]
        cache['desc'] = result[4]
        Time = str(result[5])[:-3]
        cache['time'] = time.strftime("%Y/%m/%d %H:%M", time.strptime(Time, '%Y-%m-%d %H:%M'))
        sql = "select * from collects where user_id='%s' and consign_id='%s'" \
              % (user_id, result[0])
        sql = cursor.execute(sql)
        if sql:
            cache['collected'] = 1
        else:
            cache['collected'] = 0
        output.append(cache)
    cursor.close()
    return jsonify(output)


# 获取分区委托
@app.route('/get_partition/<partition_num>', methods=["GET"])
@login_required
def partition(partition_num):
    cursor = db.cursor()
    user_id = session.get('user_id')
    sql = "select * from consigns where `partition`='%s' order by `time` desc" % (partition_num)
    db.ping(reconnect=True)
    results = cursor.execute(sql)
    output = []
    if results:
        results = cursor.fetchall()
        for result in results:
            cache = {}
            cache['consign_id'] = result[0]
            cache['consign_name'] = result[3]
            cache['desc'] = result[4]
            Time = str(result[5])[:-3]
            cache['time'] = time.strftime("%Y/%m/%d %H:%M", time.strptime(Time, '%Y-%m-%d %H:%M'))
            # cache['time'] = str(result[5])
            sql = "select * from collects where user_id='%s' and consign_id='%s'"\
                  % (user_id, cache['consign_id'])
            sql = cursor.execute(sql)
            if sql:
                cache['collected'] = 1
            else:
                cache['collected'] = 0
            output.append(cache)
        cursor.close()
        return jsonify(output)
    else:
        cursor.close()
        return jsonify(output)


# 获取分区网页
@app.route('/partition/<n>', methods=["GET"])
@login_required
def get_partition(n):
    return render_template("partition_{}.html".format(n))


if (__name__ == '__main__'):
    app.run(debug=True, port=80, host='0.0.0.0')
