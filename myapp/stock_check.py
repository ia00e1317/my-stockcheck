from flask import Flask, flash, request, render_template, redirect, url_for
import pymysql
import datetime
import time
app = Flask(__name__)
app.config["SECRET_KEY"] = "stock_check"


import requests
from bs4 import BeautifulSoup
from pathlib import Path
import urllib


def getConnection():
    return pymysql.connect(
        host='localhost',
        #db='mydb',
        db='stockdb',
        user='root',
        password='',
        charset='utf8',
        cursorclass=pymysql.cursors.DictCursor
    )


def checkKeywords(url,check_list):
    html = requests.get(url)
    #html = requests.get(url,verify=False)
    soup = BeautifulSoup(html.content, "html.parser")

    flg = True
    for check in check_list:
        classname = check[0]
        tagtype = check[1]
        attribute = check[2]
        keyword = check[3]

        txt_list = []
        for target in soup.find_all(class_=classname):
            for element in target.find_all(tagtype):
                if attribute:
                    txt_list.append(element.get(attribute))
                else:
                    txt_list.append(element.text)

        if keyword in txt_list:
            pass
        else:
            flg = False

    if flg:
        return "〇"
    else:
        return "×"


def outputType(typeCode):
    val = ""
    if typeCode:
        connection = getConnection()
        cursor = connection.cursor()
        sql = "SELECT site FROM tag_def WHERE type = %s"
        #SELECT tag_def.site FROM tag_def INNER JOIN products_url ON tag_def.type = products_url.type WHERE tag_def.type = 1;
        cursor.execute(sql,(typeCode))
        typeDic = cursor.fetchone()
        cursor.close()
        connection.close()

        val = typeDic['site']
    return val


def outputTypeList():
    connection = getConnection()
    cursor = connection.cursor()
    sql = "SELECT type,site FROM tag_def ORDER BY type"
    cursor.execute(sql)
    typeList = cursor.fetchall()
    cursor.close()
    connection.close()

    return typeList


def findEntered(dic,targets):
    flag = False
    for target in targets:
        if dic[target] != '':
            flag = True
    return flag


def findEmpty(dic,targets):
    flag = False
    for target in targets:
        if dic[target] == '':
            flag = True
    return flag


@app.route('/')
def select_sql():
    connection = getConnection()
    cursor = connection.cursor()
    sql = "SELECT DISTINCT date FROM products_url ORDER BY date DESC"
    cursor.execute(sql)
    executedate = cursor.fetchone()
    sql = "SELECT * FROM products_url"
    cursor.execute(sql)
    products = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('index.html', products = products, executedate = executedate)


@app.route('/stockcheck')
def stock_check():
    connection = getConnection()
    cursor = connection.cursor()
    sql = "SELECT A.id, A.type, A.site, name, url, result, date, classname_1, tagtype_1, attribute_1, keyword_1, classname_2, tagtype_2, attribute_2, keyword_2 FROM products_url AS A LEFT JOIN tag_def AS B ON B.type = A.type"
    cursor.execute(sql)
    products = cursor.fetchall()

    today = datetime.date.today()

    for product in products:
        if not product['type']:
            continue
        url = product['url']
        check_list = [ [ product['classname_1'],product['tagtype_1'],product['attribute_1'],product['keyword_1'] ] ]
        if product['classname_2'] and product['classname_2']:
            check_list.append( [ product['classname_2'],product['tagtype_2'],product['attribute_2'],product['keyword_2'] ] )        
        resultVal = checkKeywords(url,check_list)
        sql = "UPDATE products_url SET result = %s, date = %s WHERE id = %s"
        cursor.execute(sql,(resultVal,today,product['id']))

    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for("select_sql"))


@app.route('/edit')
def edit_url():
    typeList = outputTypeList()

    connection = getConnection()
    cursor = connection.cursor()
    sql = "SELECT * FROM products_url"
    cursor.execute(sql)
    products = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('edit.html', products = products, typeList = typeList)


@app.route('/update', methods=['POST'])
def update_url():
    typeList = outputTypeList()

    connection = getConnection()
    cursor = connection.cursor()
    sql = "SELECT * FROM products_url"
    cursor.execute(sql)
    products = cursor.fetchall()

    data = {}
    currentFields = []
    for i,product in enumerate(products):
        cd = str(i+1)
        data['siteDrop'+cd] = request.form['siteDrop'+cd] or ""
        data['name'+cd] = request.form['name'+cd] or ""
        data['url'+cd] = request.form['url'+cd] or ""

        dic = {}
        dic['type'] = request.form['siteDrop'+cd] or ""
        dic['name'] = request.form['name'+cd] or ""
        dic['url'] = request.form['url'+cd] or ""
        currentFields.append(dic)

    flag = False
    for i,product in enumerate(products):
        cd = str(i+1)
        if (data['siteDrop'+cd] == '0' and data['name'+cd] == '' and data['url'+cd] == ''):
            pass
        elif (data['siteDrop'+cd] != '0' and data['name'+cd] != '' and data['url'+cd] != ''):
            pass
        else:
            message = "No" + cd + ".[サイト種類]、[商品名]、[URL]を全て入力するか、または全て未入力にしてください。"
            flash(message, "failed")
            flag = True
    if flag:
        cursor.close()###
        connection.close()###
        return render_template("edit.html", products = currentFields, typeList = typeList)

    for i,product in enumerate(products):
        idx = i+1
        cd = str(i+1)
        val1 = request.form['siteDrop'+cd] or ""
        if val1 == '0':
            val1 = ''
        val2 = outputType(val1)
        val3 = request.form['name'+cd] or "" 
        val4 = request.form['url'+cd] or "" 

        sql = "UPDATE products_url SET type = '', site = '', name = '', url = '', result = '', date = '' WHERE id = %s"
        cursor.execute(sql,(idx))
        sql = "UPDATE products_url SET type = %s, site = %s, name = %s, url = %s WHERE id = %s"
        cursor.execute(sql,(val1,val2,val3,val4,idx))

    connection.commit()
    products = cursor.fetchall()
    cursor.close()
    connection.close()

    return redirect(url_for("select_sql"))


@app.route('/definition')
def edit_definition():
    connection = getConnection()
    cursor = connection.cursor()
    sql = "SELECT * FROM tag_def"
    cursor.execute(sql)
    definitions = cursor.fetchall()

    return render_template('definition.html', definitions = definitions)


@app.route('/addition', methods=['POST'])
def add_def():
    connection = getConnection()
    cursor = connection.cursor()
    sql = "SELECT * FROM tag_def"
    cursor.execute(sql)
    definitions = cursor.fetchall()

    allFields = ['site','classname_1','tagtype_1','attribute_1','keyword_1','classname_2','tagtype_2','attribute_2','keyword_2',]
    baseFields = ['site','classname_1','tagtype_1','keyword_1',]
    input2Fields = ['classname_2','tagtype_2','attribute_2','keyword_2',]
    need2Fields = ['classname_2','tagtype_2','keyword_2',]

    currentFields = []
    returnFlag = False
    for i,definition in enumerate(definitions):
        cd = str(i+1)
        dic = {}
        dic['type'] = definition['type']
        dic['site'] = request.form['site'+cd] or ""
        dic['classname_1'] = request.form['classname_1'+cd] or ""
        dic['tagtype_1'] = request.form['tagtype_1'+cd] or ""
        dic['attribute_1'] = request.form['attribute_1'+cd] or ""
        dic['keyword_1'] = request.form['keyword_1'+cd] or ""
        dic['classname_2'] = request.form['classname_2'+cd] or ""
        dic['tagtype_2'] = request.form['tagtype_2'+cd] or ""
        dic['attribute_2'] = request.form['attribute_2'+cd] or ""
        dic['keyword_2'] = request.form['keyword_2'+cd] or ""
        currentFields.append(dic)

        #サイトに入力あり
        if request.form['site'+cd]:
            if findEmpty(dic, baseFields):
                message = "No." + cd + "→[サイト名]に入力する場合は【A：必須】の項目は全て入力してください。"
                flash(message, "failed")
                returnFlag = True
            if findEntered(dic, input2Fields):#input2Fieldsに１つでも入力ありなら
                if findEmpty(dic, need2Fields):#need2Fieldsに１つでも空白ありなら
                    message = "No." + cd + "→B(緑)の項目に入力する場合は【B：必須】の項目は全て入力してください。"
                    flash(message, "failed")
                    returnFlag = True
        #サイトに入力なし       
        else:
            if findEntered(dic, allFields):
                message = "No." + cd + "→[サイト名]を空白にする場合は全ての項目を空白にしてください。"
                flash(message, "failed")
                returnFlag = True
    if returnFlag:
        cursor.close()
        connection.close()
        return render_template("definition.html", definitions = currentFields)

    for i,definition in enumerate(definitions):
        idx = i+1
        cd = str(i+1)
        val1 = definition['type'] or ""
        #val1 = request.form['type'+cd] or ""
        val2 = request.form['site'+cd] or ""
        val3 = request.form['classname_1'+cd] or ""
        val4 = request.form['tagtype_1'+cd] or ""
        val5 = request.form['attribute_1'+cd] or ""
        val6 = request.form['keyword_1'+cd] or ""
        val7 = request.form['classname_2'+cd] or ""
        val8 = request.form['tagtype_2'+cd] or ""
        val9 = request.form['attribute_2'+cd] or ""
        val10 = request.form['keyword_2'+cd] or ""

        sql = "UPDATE tag_def SET type = %s, site = %s, classname_1 = %s, tagtype_1 = %s, attribute_1 = %s, keyword_1 = %s, classname_2 = %s, tagtype_2 = %s, attribute_2 = %s, keyword_2 = %s WHERE id = %s"
        cursor.execute(sql,(val1,val2,val3,val4,val5,val6,val7,val8,val9,val10,idx))

    connection.commit()
    definitions = cursor.fetchall()
    cursor.close()
    connection.close()

    flash("保存完了", "success")
    return redirect(url_for("edit_definition"))



if __name__ == "__main__":
    app.debug = True
    app.run(host='127.0.0.1', port=5000)

