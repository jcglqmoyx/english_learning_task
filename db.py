import pymysql


def remove_user(handle: str) -> None:
    db = pymysql.connect(host='localhost', user='root', password='Admin1', database='task', charset='utf8')
    cursor = db.cursor()
    sql = 'update member set is_active=false where handle="%s"' % handle
    cursor.execute(sql)
    db.commit()
    db.close()


def add_user(wechat_id: str, handle: str) -> None:
    db = pymysql.connect(host='localhost', user='root', password='Admin1', database='task', charset='utf8')
    cursor = db.cursor()
    sql = 'insert into member values("%s", "%s", NOW(), null , true)' % (wechat_id, handle)
    cursor.execute(sql)
    db.commit()
    db.close()


def update_user(wechat_id: str, handle: str) -> None:
    db = pymysql.connect(host='localhost', user='root', password='Admin1', database='task', charset='utf8')
    cursor = db.cursor()
    sql = 'update member set handle="%s" where wechat_id"%s"' % (handle, wechat_id)
    cursor.execute(sql)
    db.commit()
    db.close()


def get_all_users():
    users = []
    db = pymysql.connect(host='localhost', user='root', password='Admin1', database='task', charset='utf8')
    cursor = db.cursor()
    sql = 'select wechat_id, handle from member where is_active=true'
    cursor.execute(sql)
    res = cursor.fetchall()
    for record in res:
        users.append([record[0], record[1]])
    db.close()
