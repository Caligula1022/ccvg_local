import mysql.connector
from flask import Blueprint, jsonify, request
from openpyxl import *

village_blueprint = Blueprint("village", __name__)


@village_blueprint.route("/forAll12Tables", methods=["GET", "POST"], strict_slashes=False)
def village():
    if request.method == "POST":
        data = request.get_data()
        json_data = json.loads(data.decode("utf-8"))
        name = json_data.get("name")
        province = json_data.get("province")
        city = json_data.get("city")
        county = json_data.get("county")

    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        port=3307,  # My own localhost port is 3307, default is 3307
        database="ccvg")
    mycursor = mydb.cursor()
    mycursor.execute("SELECT * FROM village_村 WHERE nameChineseCharacters_村名汉字={}".format(name))
    res = mycursor.fetchall()  # [("2", 2, "4.20116E+11", "叶店村", "Yedian Cun")]

    gazetteerId = res[0][1]
    viliageId = res[0][2]

    mycursor.execute(
        "SELECT gazetteerTitle_村志书名 FROM gazetteerinformation_村志信息 WHERE gazetteerId_村志代码={}".format(gazetteerId))
    gazetteerName = mycursor.fetchone()[0]  # 获得 list的第一个

    mycursor.execute(
        "SELECT a.data_数据, b.name_名称, c.name_名称 FROM villagegeography_村庄地理 as a ,villagegeographycategory_村庄地理类 as b, villagegeographyunit_村庄地理单位 as c WHERE a.villageInnerId_村庄内部代码={} AND a.categoryId_类别代码 = b.categoryId_类别代码 AND a.unitId_单位代码=c.unitId_单位代码".format(
            gazetteerId))
    geographyList = mycursor.fetchall()
    # [("7.5", "村庄总面积 Total Area", "平方千米 / 平方公里 square kilometers"),
    #  ("30°47′N", "纬度 Latitude", "度分秒 DMS (degrees-minutes-seco", "经度 Longitude", "度分秒 DMS (degrees-minutes-seconds)"),
    #  ("5", "距隶属县城距离 Distance to Affiliated to the county town", "公里/千米

    # 定义总table
    table = {}
    table["tables"] = [{
        "field": ["gazetteerId", "gazetteerName", "villageId", "villageName", "province", "city", "county", "category",
                  "data", "unit"],
        "data": []
    }]

    # table1 村庄信息

    for item in geographyList:
        d = {}
        d["gazetteerId"] = gazetteerId
        d["gazetteerName"] = gazetteerName
        d["villageId"] = viliageId
        d["villageName"] = name
        d["province"] = province
        d["county"] = county
        d["city"] = city
        d["category"] = item[1]
        d["data"] = item[0]
        d["unit"] = item[2]
        table["tables"][0]["data"].append(d)

    # table2 村志信息
    # TODO Not setting the same gazetteerName

    table["tables"].append({
        "field": ["villageId", "villageName", "gazetteerId", "gazetteerName", "publishYear", "publishType"],
        "data": []
    })
    mycursor.execute(
        "SELECT yearOfPublication_出版年, publicationType_出版类型 FROM gazetteerinformation_村志信息 WHERE gazetteerId_村志代码={}".format(
            gazetteerId))
    publicationList = mycursor.fetchone()
    d = {}
    d["villageId"] = viliageId
    d["villageName"] = name
    d["gazetteerId"] = gazetteerId
    d["gazetteerName"] = gazetteerName
    d["publishYear"] = publicationList[0]
    d["publishType"] = publicationList[1]

    table["tables"][1]["data"] = d

    # table3 自然灾害

    table["tables"].append({
        "field": ["gazetteerName", "gazetteerId", "year", "category"],
        "data": []
    })
    mycursor.execute(
        "SELECT b.name_名称, a.year_年份 FROM naturaldisasters_自然灾害 as a, naturaldisasterscategory_自然灾害类 as b WHERE villageInnerId_村庄内部代码={} AND a.categoryId_类别代码=b.categoryId_类别代码".format(
            gazetteerId))
    disasterList = mycursor.fetchall()

    for item in disasterList:
        d = {}
        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = gazetteerId
        d["year"] = item[1]
        d["category"] = item[0]
        table["tables"][2]["data"].append(d)

    # table4 自然环境
    table["tables"].append({
        "field": ["gazetteerName", "gazetteerId", "category", "data", "unit"],
        "data": []
    })
    mycursor.execute(
        "SELECT a.data_数据, b.name_名称, c.name_名称 FROM naturalenvironment_自然环境 as a, naturalenvironmentcategory_自然环境类 as b,naturalenvironmentunit_自然环境单位 as c \
        WHERE villageInnerId_村庄内部代码={} AND a.categoryId_类别代码=b.categoryId_类别代码 \
        AND a.unitId_单位代码=c.unitId_单位代码".format(
            gazetteerId))
    naturalList = mycursor.fetchall()

    for item in naturalList:
        d = {}
        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = gazetteerId
        d["category"] = item[0]
        d["data"] = item[1]
        d["unit"] = item[2]
        table["tables"][3]["data"].append(d)

    # table5 军事政治
    table["tables"].append({
        "field": ["gazetteerName", "gazetteerId", "category1", "category2", "startYear", "endYear", "data", "unit"],
        "data": []
    })
    mycursor.execute(
        "SELECT mc.categoryId_类别代码 as mcid, mc.parentId_父类代码 as pid, mc.name_名称 as name,m.startYear_开始年,\
        m.endYear_结束年, data_数据, mu.name_名称\
     FROM  military_军事 as m JOIN militarycategory_军事类 as mc  ON  m.categoryId_类别代码=mc.categoryId_类别代码\
     JOIN militaryunit_军事单位 as mu on m.unitId_单位代码=mu.unitId_单位代码 \
     WHERE gazetteerId_村志代码={}".format(gazetteerId))
    militraryList = mycursor.fetchall()

    parentIdList = []
    for i, item in enumerate(militraryList):
        if item[1] != None:
            mycursor.execute("SELECT name_名称 FROM militarycategory_军事类 WHERE categoryId_类别代码={}".format(item[1]))
            parentIdList.append(mycursor.fetchone())
        else:
            parentIdList.append(["null"])
        d = {}
        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = gazetteerId
        d["category1"] = parentIdList[-1][0]
        d["category2"] = item[2]
        d["startYear"] = item[3]
        d["endYear"] = item[4]
        d["data"] = item[5]
        d["unit"] = item[6]
        table["tables"][4]["data"].append(d)

    # table6 教育
    table["tables"].append({
        "field": ["gazetteerName", "gazetteerId", "category1", "category2", "category3", "startYear", "endYear", "data",
                  "unit"],
        "data": []
    })

    mycursor.execute("SELECT  e.categoryId_类别代码 cat1, ec.parentId_父类代码 ca2, ec.name_名称, e.startYear_开始年,\
  e.endYear_结束年,e.data_数据 ,eu.name_名称 FROM education_教育 e JOIN educationcategory_教育类 ec\
  ON e.categoryId_类别代码= ec.categoryId_类别代码 JOIN educationunit_教育单位 eu \
  ON e.unitId_单位代码=eu.unitId_单位代码 \
  WHERE e.gazetteerId_村志代码={}".format(gazetteerId))

    educationList = mycursor.fetchall()
    for item in educationList:
        d = {}
        if item[1] != None:
            d["category2"] = "受教育程度 Highest Level of Education"
        else:
            d["category2"] = "null"
        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = gazetteerId
        d["category3"] = "null"
        d["category1"] = item[2]
        d["startYear"] = item[3]
        d["endYear"] = item[4]
        d["data"] = item[5]
        d["unit"] = item[6]
        table["tables"][5]["data"].append(d)

    # table7 经济
    # TODO the order of cat 1,2,3
    table["tables"].append({
        "field": ["gazetteerName", "gazetteerId", "category1", "category2", "category3", "startYear", "endYear", "data",
                  "unit"],
        "data": []
    })
    mycursor.execute("SELECT  e.categoryId_类别代码 cat1, ec.parentId_父类代码 ca2, ec.name_名称, e.startYear_开始年,\
e.endYear_结束年,e.data_数据 ,eu.name_名称 FROM economy_经济 e JOIN economycategory_经济类 ec \
ON e.categoryId_类别代码=ec.categoryId_类别代码 JOIN economyunit_经济单位 eu \
ON e.unitId_单位代码=eu.unitId_单位代码 \
WHERE e.gazetteerId_村志代码 ={}".format(gazetteerId))
    econmialList = mycursor.fetchall()
    for item in econmialList:
        d = {}
        # the category2 also has two upper layer
        if item[1] not in [1, 19, 37.38, 39, 40, 41, 47, 56, 62] and item[1] != None:
            mycursor.execute(
                "SELECT parentId_父类代码,name_名称 FROM economycategory_经济类 WHERE categoryId_类别代码={}".format(item[1]))
            categoryList = mycursor.fetchone()
            categoryId, d["category2"] = categoryList[0], categoryList[1]

            mycursor.execute("SELECT name_名称 FROM economycategory_经济类 WHERE categoryId_类别代码={}".format(categoryId))
            d["category3"] = mycursor.fetchone()[0]

        # the category2 has no upper layer
        elif item[1] == None:
            d["category3"] = "null"
            d["category2"] = "null"

        # the category2 has onw upper layers
        else:
            mycursor.execute("SELECT name_名称 FROM economycategory_经济类 WHERE categoryId_类别代码={}".format(item[1]))
            d["category2"] = mycursor.fetchone()[0]
            d["category3"] = "null"

        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = gazetteerId
        d["category1"] = item[2]
        d["startYear"] = item[3]
        d["endYear"] = item[4]
        d["data"] = item[5]
        d["unit"] = item[6]
        table["tables"][6]["data"].append(d)

    # table8 计划生育
    # field: ["gazetteerName", "gazetteerId", "category", "startYear", "endYear", "data", "unit"],

    table["tables"].append({
        "field": ["gazetteerName", "gazetteerId", "category", "startYear", "endYear", "data", "unit"],
        "data": []
    })

    mycursor.execute("SELECT  fc.name_名称, f.startYear_开始年,\
f.endYear_结束年,f.data_数据 ,fu.name_名称 \
FROM familyplanning_计划生育 f JOIN familyplanningcategory_计划生育类 fc \
ON f.categoryId_类别代码= fc.categoryId_类别代码 JOIN familyplanningunit_计划生育单位 fu \
ON f.unitId_单位代码=fu.unitId_单位代码 \
WHERE f.gazetteerId_村志代码 ={}".format(gazetteerId))

    familyplanningList = mycursor.fetchall()

    for item in familyplanningList:
        d = {}
        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = gazetteerId
        d["category"] = item[0]
        d["startYear"] = item[1]
        d["endYear"] = item[2]
        d["data"] = item[3]
        d["unit"] = item[4]

        table["tables"][7]["data"].append(d)

    # table9 人口
    # field: ["gazetteerName", "gazetteerId", "category1", "category2", "startYear", "endYear", "data", "unit"],
    table["tables"].append({
        "field": ["gazetteerName", "gazetteerId", "category1", "category2", "startYear", "endYear", "data", "unit"],
        "data": []
    })

    mycursor.execute("SELECT  p.categoryId_类别代码 cid, pc.parentId_父类代码 pid,  pc.name_名称, p.startYear_开始年,\
p.endYear_结束年,p.data_数据 ,pu.name_名称 \
FROM population_人口 p JOIN populationcategory_人口类 pc \
ON p.categoryId_类别代码= pc.categoryId_类别代码 JOIN populationunit_人口单位 pu \
ON p.unitId_单位代码=pu.unitId_单位代码 \
WHERE p.gazetteerId_村志代码 ={}".format(gazetteerId))

    populationList = mycursor.fetchall()

    for item in populationList:
        d = {}
        if item[1] != None:
            mycursor.execute("SELECT name_名称 FROM populationcategory_人口类 WHERE categoryId_类别代码={}".format(item[1]))
            d["category2"] = mycursor.fetchone()[0]
        else:
            d["category2"] = "null"

        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = gazetteerId
        d["category1"] = item[2]
        d["startYear"] = item[3]
        d["endYear"] = item[4]
        d["data"] = item[5]
        d["unit"] = item[6]
        table["tables"][8]["data"].append(d)

    # table10 民族
    # field: ["gazetteerName", "gazetteerId", "category", "startYear", "endYear", "data", "unit"],

    table["tables"].append({
        "field": ["gazetteerName", "gazetteerId", "category", "startYear", "endYear", "data", "unit"],
        "data": []
    })

    mycursor.execute("SELECT   ethc.name_名称, eth.startYear_开始年,\
eth.endYear_结束年,eth.data_数据 ,ethu.name_名称 \
FROM ethnicgroups_民族 eth JOIN ethnicgroupscategory_民族类 ethc \
ON eth.categoryId_类别代码= ethc.categoryId_类别代码 JOIN ethnicgroupsunit_民族单位 ethu \
ON eth.unitId_单位代码=ethu.unitId_单位代码 \
WHERE eth.gazetteerId_村志代码 =2;")

    ethnicgroupList = mycursor.fetchall()
    for item in ethnicgroupList:
        d = {}
        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = gazetteerId
        d["category"] = item[0]
        d["startYear"] = item[1]
        d["endYear"] = item[2]
        d["data"] = item[3]
        d["unit"] = item[4]
        table["tables"][9]["data"].append(d)

    # table11 姓氏
    table["tables"].append({
        "field": ["gazetteerName", "gazetteerId", "firstLastNameId", "secondLastNameId", "thirdLastNameId",
                  "fourthLastNameId",
                  "fifthLastNameId", "totalNumberOfLastNameInVillage"],
        "data": []
    })

    mycursor.execute("SELECT firstlastNamesId_姓氏代码, secondlastNamesId_姓氏代码, thirdlastNamesId_姓氏代码, \
  fourthlastNamesId_姓氏代码, fifthlastNamesId_姓氏代码, totalNumberofLastNamesinVillage_姓氏总数 \
  FROM lastname_姓氏 WHERE gazetteerId_村志代码={}".format(gazetteerId))

    nameList = mycursor.fetchall()

    l = []
    for z in range(len(nameList[0]) - 1):
        if nameList[0][z] == None:
            l.append("")
        else:
            mycursor.execute(
                "SELECT nameChineseCharacters_姓氏汉字 FROM lastnamecategory_姓氏类别 WHERE categoryId_类别代码 ={}".format(
                    nameList[0][z]))
            l.append(mycursor.fetchone()[0])

    d = {}
    d["gazetteerName"] = gazetteerName
    d["gazetteerId"] = gazetteerId
    d["firstLastNameId"] = l[0]
    d["secondLastNameId"] = l[1]
    d["thirdLastNameId"] = l[2]
    d["fourthLastNameId"] = l[3]
    d["fifthlastNamesId_姓氏代码"] = l[4]
    d["totalNumberOfLastNameInVillage"] = nameList[0][-1]

    table["tables"][10]["data"].append(d)

    # table12 第一次拥有或购买年份
    table["tables"].append({
        "field": ["gazetteerName", "gazetteerId", "category", "year"],
        "data": []
    })

    mycursor.execute("SELECT f.year_年份,fc.name_名称 FROM firstavailabilityorpurchase_第一次购买或拥有年份 f JOIN firstavailabilityorpurchasecategory_第一次购买或拥有年份类 fc \
   ON f.categoryId_类别代码=fc.categoryId_类别代码 WHERE f.gazetteerId_村志代码={}".format(gazetteerId))

    firstList = mycursor.fetchall()

    for i in firstList:
        d = {}
        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = gazetteerId
        d["category"] = i[0] if i[0] != None else None
        d["year"] = i[1] if i[1] != None else None
        table["tables"][11]["data"].append(d)

    return jsonify(table)


@village_blueprint.route("/search", methods=["POST"])
def getPopulation():
    data = request.get_data()
    json_data = json.loads(data.decode("utf-8"))
    villageid = json_data.get("villageid")
    topic = json_data.get("population")

    # 定义Table
    table = {}
    table["field"] = ["gazetteerId", "gazetteerName", "villageId", "villageName", "province", "city", "county",
                      "category",
                      "data", "unit"]
    table["data"] = []

    # 获得连接
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        port=3307,  # My own localhost port is 3307, default is 3307
        database="ccvg")
    mycursor = mydb.cursor()

    mycursor.execute(
        "SELECT gazetteerTitle_村志书名 FROM gazetteerinformation_村志信息 WHERE gazetteerId_村志代码={}".format(villageid))
    gazetteerName = mycursor.fetchone()[0]  # 获得 list的第一个

    # table10 人口
    # field: ["gazetteerName", "gazetteerId", "category1", "category2", "startYear", "endYear", "data", "unit"],

    mycursor.execute("SELECT  p.categoryId_类别代码 cid, pc.parentId_父类代码 pid,  pc.name_名称, p.startYear_开始年,\
p.endYear_结束年,p.data_数据 ,pu.name_名称 \
FROM population_人口 p JOIN populationcategory_人口类 pc \
ON p.categoryId_类别代码= pc.categoryId_类别代码 JOIN populationunit_人口单位 pu \
ON p.unitId_单位代码=pu.unitId_单位代码 \
WHERE p.gazetteerId_村志代码 ={}".format(villageid))

    populationList = mycursor.fetchall()

    for item in populationList:
        d = {}
        if item[1] != None:
            mycursor.execute("SELECT name_名称 FROM populationcategory_人口类 WHERE categoryId_类别代码={}".format(item[1]))
            d["category2"] = mycursor.fetchone()[0]
        else:
            d["category2"] = "null"

        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = villageid
        d["category1"] = item[2]
        d["startYear"] = item[3]
        d["endYear"] = item[4]
        d["data"] = item[5]
        d["unit"] = item[6]
        table["data"].append(d)
    return jsonify(table)


@village_blueprint.route("/namesearch", methods=["GET", "POST"], strict_slashes=False)
def getByName():
    table = {}
    table["data"] = []
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        port=3307,  # My own localhost port is 3307, default is 3307
        database="ccvg")
    mycursor = mydb.cursor()

    if request.method == "GET":
        mycursor.execute("SELECT village.nameChineseCharacters_村名汉字, county.nameChineseCharacters_县或区汉字, city.nameChineseCharacters_市汉字, province.nameChineseCharacters_省汉字, jointable.villageInnerId_村庄内部代码 \
     FROM county_县 county JOIN villagecountycityprovince_村县市省 jointable ON county.countyDistrictId_县或区代码=jointable.countyDistrictId_县或区代码 \
    JOIN  city_市 city ON city.cityId_市代码 = jointable.cityId_市代码 JOIN province_省 province ON province.provinceId_省代码=jointable.provinceId_省代码 JOIN  village_村 village ON village.villageInnerId_村庄内部代码= jointable.villageInnerId_村庄内部代码 LIMIT 100;")
        nameList = mycursor.fetchall()

    else:
        data = request.get_data()
        json_data = json.loads(data.decode("utf-8"))
        namefilter = json_data.get("namefilter")

        mycursor.execute("SELECT village.nameChineseCharacters_村名汉字, county.nameChineseCharacters_县或区汉字, city.nameChineseCharacters_市汉字, province.nameChineseCharacters_省汉字, jointable.villageInnerId_村庄内部代码 \
         FROM county_县 county JOIN villagecountycityprovince_村县市省 jointable ON county.countyDistrictId_县或区代码=jointable.countyDistrictId_县或区代码 \
        JOIN  city_市 city ON city.cityId_市代码 = jointable.cityId_市代码 JOIN province_省 province ON province.provinceId_省代码=jointable.provinceId_省代码 JOIN  village_村 village ON village.villageInnerId_村庄内部代码= jointable.villageInnerId_村庄内部代码 WHERE village.nameChineseCharacters_村名汉字 LIKE '%{}%';".format(
            namefilter))
        nameList = mycursor.fetchall()

    for item in nameList:
        temp = {}
        temp["name"] = item[0]
        temp["county"] = item[1]
        temp["city"] = item[2]
        temp["province"] = item[3]
        temp["id"] = item[4]
        table["data"].append(temp)

    return jsonify(table)


@village_blueprint.route("/getland", methods=["GET"], strict_slashes=False)
def getLand():
    table = {}
    table["field"] = ["gazetteerName", "gazetteerId", "category1", "category2", "category3", "startYear", "endYear",
                      "data",
                      "unit"]
    table["data"] = []

    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        port=3307,  # My own localhost port is 3307, default is 3307
        database="ccvg")
    mycursor = mydb.cursor()

    # for i in [17, 12, 28, 19]:
    mycursor.execute("SELECT e.categoryId_类别代码 cat1, ec.parentId_父类代码 ca2, ec.name_名称, e.startYear_开始年,\
      e.endYear_结束年,e.data_数据 ,eu.name_名称,v.nameChineseCharacters_村名汉字 FROM economy_经济 e JOIN economycategory_经济类 ec \
      ON e.categoryId_类别代码=ec.categoryId_类别代码 JOIN economyunit_经济单位 eu \
      ON e.unitId_单位代码=eu.unitId_单位代码 JOIN villagecountycityprovince_村县市省 vccp ON e.gazetteerId_村志代码=vccp.gazetteerId_村志代码 \
      JOIN village_村 v ON vccp.gazetteerId_村志代码= v.gazetteerId_村志代码 \
      WHERE vccp.provinceId_省代码={}".format(19))
    econmialList = mycursor.fetchall()
    for item in econmialList:
        d = {}
        # the category2 also has two upper layer
        if item[1] not in [1, 19, 37.38, 39, 40, 41, 47, 56, 62] and item[1] != None:
            d["category3"] = item[2]
            mycursor.execute(
                "SELECT parentId_父类代码,name_名称 FROM economycategory_经济类 WHERE categoryId_类别代码={}".format(item[1]))
            categoryList = mycursor.fetchone()
            categoryId, d["category2"] = categoryList[0], categoryList[1]

            mycursor.execute("SELECT name_名称 FROM economycategory_经济类 WHERE categoryId_类别代码={}".format(categoryId))
            d["category1"] = mycursor.fetchone()[0]




        # the category2 has no upper layer
        elif item[1] == None:
            d["category1"] = item[2]

            d["category3"] = "null"
            d["category2"] = "null"

        # the category2 has onw upper layers
        else:
            d["category2"] = item[2]
            mycursor.execute("SELECT name_名称 FROM economycategory_经济类 WHERE categoryId_类别代码={}".format(item[1]))
            d["category1"] = mycursor.fetchone()[0]
            d["category3"] = "null"

        # d["category1"] = item[2]
        d["startYear"] = item[3]
        d["endYear"] = item[4]
        d["data"] = item[5]
        d["unit"] = item[6]
        d["nameChineseCharacters_村名汉字"] = item[7]
        wb = Workbook()
        ws = wb.active
        ws.append(["村名", "耕地面积CultivatedArea", "起始年startYear", "结束年endYear", "单位unit"])

        table["data"].append(d)

        for i in table["data"]:
            if i["category1"] == "耕地面积 Cultivated Area":
                ws.append([i["nameChineseCharacters_村名汉字"], i["data"], i["startYear"], i["endYear"], i["unit"]])

        wb.save('浙江.xlsx')

    return jsonify(table)


@village_blueprint.route("/advancesearch", methods=["POST", "GET"], strict_slashes=False)
def advanceSearch():
    data = request.get_data()
    json_data = json.loads(data.decode("utf-8"))
    villageid = json_data.get("villageid")
    topic = json_data.get("topic")
    year = json_data.get("year")
    year_range = json_data.get("year_range")

    # Get connection
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        port=3307,
        database="CCVG")
    mycursor = mydb.cursor()

    topics = ["village", "gazetteerinformation", "naturaldisasters", "naturalenvironment", "military", "education",
              "economy", "familyplanning",
              "population", "ethnicgroups", "fourthlastNames", "firstavailabilityorpurchase"]
    # get every topics' index in the
    indexes = []
    for i in topic:
        if i not in topics:
            return "topics is not fullfil requirement"
        else:
            indexes.append(topics.index(i) + 1)

    dicts = {}
    table = []
    year_only = False
    yearRange = False
    if year != None and year_range != None:
        year_only = True
        yearRange = True
    elif year == None and year_range == None:
        year_only = False
        yearRange = False
    elif year != None:
        year_only = False
    elif year_range != None:
        yearRange = True

    table1 = {}
    table1["field"] = ["gazetteerId", "gazetteerName", "villageId", "villageName", "province", "city", "county",
                       "category1",
                       "data", "unit"]
    table1["data"] = []
    table1["tableNameChinese"] = "村庄基本信息"
    dicts[1] = table1

    # 村志信息
    table2 = {}
    table2["field"] = ["villageId", "villageName", "gazetteerId", "gazetteerName", "publishYear", "publishType"]
    table2["data"] = []
    table2["year"] = []
    table2["tableNameChinese"] = "村志基本信息"
    dicts[2] = table2

    # 自然灾害
    table3 = {}
    table3["field"] = ["gazetteerName", "gazetteerId", "year", "category1"],
    table3["data"] = []
    table3["year"] = []
    table3["tableNameChinese"] = "自然灾害"
    dicts[3] = table3

    table4 = {}
    table4["field"] = ["gazetteerName", "gazetteerId", "category1", "data", "unit"]
    table4["data"] = []
    table4["tableNameChinese"] = "自然环境"
    dicts[4] = table4

    # 军事
    table5 = {}
    table5["field"] = ["gazetteerName", "gazetteerId", "category1", "category2", "startYear", "endYear", "data", "unit"]
    table5["data"] = []
    table5["year"] = []
    table5["tableNameChinese"] = "军事政治"
    dicts[5] = table5

    # 教育
    table6 = {}
    table6["field"] = ["gazetteerName", "gazetteerId", "category1", "category2", "startYear", "endYear",
                       "data",
                       "unit"]
    table6["data"] = []
    table6["tableNameChinese"] = "教育"
    table6["year"] = []
    dicts[6] = table6

    # 经济
    table7 = {}
    table7["field"] = ["gazetteerName", "gazetteerId", "category1", "category2", "category3", "startYear", "endYear",
                       "data",
                       "unit"]
    table7["data"] = []
    table7["year"] = []
    table7["tableNameChinese"] = "经济"
    dicts[7] = table7

    # 计划生育
    table8 = {}
    table8["field"] = ["gazetteerName", "gazetteerId", "category", "startYear", "endYear", "data", "unit"]
    table8["data"] = []
    table8["year"] = []
    table8["tableNameChinese"] = "计划生育"
    dicts[8] = table8

    # 人口
    table9 = {}
    table9["field"] = ['gazetteerName', 'gazetteerId', 'category1', 'category2', 'startYear', 'endYear', 'data', 'unit']
    table9["data"] = []
    table9["year"] = []
    table9["tableNameChinese"] = "人口"
    dicts[9] = table9

    # 民族
    table10 = {}
    table10["field"] = ["gazetteerName", "gazetteerId", "category1", "startYear", "endYear", "data", "unit"]
    table10["data"] = []
    table10["year"] = []
    table10["tableNameChinese"] = "民族"
    dicts[10] = table10

    table11 = {}
    table11["field"] = ["gazetteerName", "gazetteerId", "firstLastNameId", "secondLastNameId", "thirdLastNameId",
                        "fourthLastNameId",
                        "fifthLastNameId", "totalNumberOfLastNameInVillage"]
    table11["data"] = []
    table11["tableNameChinese"] = "姓氏"
    dicts[11] = table11

    # 第一次购买年份
    table12 = {}
    table12["field"] = ["gazetteerName", "gazetteerId", "category", "year"]
    table12["data"] = []
    table12["year"] = []
    table12["tableNameChinese"] = "第一次拥有或购买年份"
    dicts[12] = table12

    table2func = {}
    table2func[3] = getNaturalDisaster
    table2func[4] = getNaturalEnvironment
    table2func[5] = getMilitary
    table2func[6] = getEduaction
    table2func[7] = getEconomy
    table2func[8] = getFamilyPlanning
    table2func[9] = getPopulation
    table2func[10] = getEthnicgroups
    table2func[11] = getFourthlastName
    table2func[12] = getFirstAvailabilityorPurchase

    # For every node in the village and we want to change
    temp = {}
    for village_id in villageid:
        mycursor.execute(
            "SELECT gazetteerTitle_村志书名 FROM gazetteerInformation_村志信息 WHERE gazetteerId_村志代码={}".format(village_id))
        gazetteerName = mycursor.fetchone()[0]

        for i in getVillage(mycursor, village_id, gazetteerName)["data"]:
            table1["data"].append(i)
        for i in getGazetteer(mycursor, village_id, gazetteerName)["data"]:
            table2["data"].append(i)

        for index in indexes:
            newTable = dicts[index]  # table3~12
            temp[index] = newTable  # {3: table3...}
            if index == 1 or index == 2:
                continue
            else:
                func = table2func[index]
                for j in func(mycursor, village_id, gazetteerName, year, year_range)["data"]:
                    newTable["data"].append(j)  # table3~12["data"].append(i) =>

    table.append(table1)
    table.append(table2)
    for index in indexes:
        if index == 1 or index == 2:
            continue
        else:
            table.append(temp[index])
    return jsonify(table)


# @village_blueprint.route("/download/<path:path>", methods=["GET"], strict_slashes=False)
# def downloadData(path):
#     single_dir = "/home/yuelv/CCVG/app_func/single_csv"
#     is_single = True
#     if "&" in path:
#         is_single = False
#     if os.path.exists(single_dir + "/" + path) and is_single:
#         return send_from_directory(single_dir + "/", path, as_attachment=True)
#     return "File is not exist or file can't download"


def getVillage(mycursor, village_id, gazetteerName, year, year_range):
    table = {}
    table["data"] = []
    # Get province county villageName city
    mycursor.execute(
        "SELECT p.nameChineseCharacters_省汉字, ci.nameChineseCharacters_市汉字 , co.nameChineseCharacters_县或区汉字, v.nameChineseCharacters_村名汉字  FROM villageCountyCityProvince_村县市省 vccp JOIN village_村 v ON vccp.gazetteerId_村志代码=v.gazetteerId_村志代码 JOIN city_市 ci ON vccp.cityId_市代码=ci.cityId_市代码 JOIN county_县 co ON co.countyDistrictId_县或区代码=vccp.countyDistrictId_县或区代码 JOIN province_省 p ON p.provinceId_省代码=vccp.provinceId_省代码 WHERE vccp.gazetteerId_村志代码={};".format(
            village_id))
    allNames = mycursor.fetchone()
    province = allNames[0]
    city = allNames[1]
    county = allNames[2]
    villageName = allNames[3]

    mycursor.execute(
        "SELECT a.data_数据, b.name_名称, c.name_名称 FROM villageGeography_村庄地理 as a ,villageGeographyCategory_村庄地理类 as b, villageGeographyUnit_村庄地理单位 as c WHERE a.villageInnerId_村庄内部代码={} AND a.categoryId_类别代码 = b.categoryId_类别代码 AND a.unitId_单位代码=c.unitId_单位代码".format(
            village_id))
    geographyList = mycursor.fetchall()
    for item in geographyList:
        d = {}
        d["gazetteerId"] = village_id
        d["gazetteerName"] = gazetteerName
        d["villageId"] = village_id
        d["villageName"] = villageName
        d["province"] = province
        d["county"] = county
        d["city"] = city
        d["category1"] = item[1]
        d["data"] = item[0]
        d["unit"] = item[2]
        table["data"].append(d)
    return table


def getGazetteer(mycursor, village_id, gazetteerName, year, year_range):
    mycursor.execute(
        "SELECT yearOfPublication_出版年, publicationType_出版类型 FROM gazetteerInformation_村志信息 WHERE gazetteerId_村志代码={}".format(
            village_id))
    publicationList = mycursor.fetchall()
    table = {}
    table["data"] = []

    mycursor.execute("SELECT nameChineseCharacters_村名汉字 FROM village_村 WHERE gazetteerId_村志代码={}".format(village_id))
    name = mycursor.fetchone()[0]
    for item in publicationList:
        d = {}
        d["villageId"] = village_id
        d["villageName"] = name
        d["gazetteerId"] = village_id
        d["gazetteerName"] = gazetteerName
        d["publishYear"] = item[0]
        d["publishType"] = item[1]
        table["data"].append(d)
    return table


def getNaturalDisaster(mycursor, village_id, gazetteerName, year, year_range):
    table = {}
    table["data"] = []
    mycursor.execute(
        "SELECT b.name_名称, a.year_年份 FROM naturalDisasters_自然灾害 as a, naturalDisastersCategory_自然灾害类 as b WHERE villageInnerId_村庄内部代码={} AND a.categoryId_类别代码=b.categoryId_类别代码".format(
            village_id))
    disasterList = mycursor.fetchall()

    for item in disasterList:
        d = {}
        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = village_id
        d["year"] = item[1]
        d["category1"] = item[0]
        table["data"].append(d)
    return table


def getNaturalEnvironment(mycursor, village_id, gazetteerName, year, year_range):
    table = {}
    table["data"] = []
    mycursor.execute(
        "SELECT a.data_数据, b.name_名称, c.name_名称 FROM naturalEnvironment_自然环境 as a, naturalEnvironmentCategory_自然环境类 as b,naturalEnvironmentUnit_自然环境单位 as c \
        WHERE villageInnerId_村庄内部代码={} AND a.categoryId_类别代码=b.categoryId_类别代码 \
        AND a.unitId_单位代码=c.unitId_单位代码".format(
            village_id))
    naturalList = mycursor.fetchall()

    for item in naturalList:
        d = {}
        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = village_id
        d["category1"] = item[0]
        d["data"] = item[1]
        d["unit"] = item[2]
        table["data"].append(d)
    return table


def getMilitary(mycursor, village_id, gazetteerName, year, year_range):
    table = {}
    table["data"] = []
    mycursor.execute(
        "SELECT mc.categoryId_类别代码 as mcid, mc.parentId_父类代码 as pid, mc.name_名称 as name,m.startYear_开始年,\
        m.endYear_结束年, data_数据, mu.name_名称\
     FROM  military_军事 as m JOIN militarycategory_军事类 as mc  ON  m.categoryId_类别代码=mc.categoryId_类别代码\
     JOIN militaryunit_军事单位 as mu on m.unitId_单位代码=mu.unitId_单位代码 \
     WHERE gazetteerId_村志代码={}".format(village_id))
    militraryList = mycursor.fetchall()

    parentIdList = []
    for i, item in enumerate(militraryList):
        if item[1] != None:
            mycursor.execute("SELECT name_名称 FROM militarycategory_军事类 WHERE categoryId_类别代码={}".format(item[1]))
            parentIdList.append(mycursor.fetchone())
        else:
            parentIdList.append(["null"])
        d = {}
        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = village_id
        d["category1"] = item[2]
        d["category2"] = parentIdList[-1][0]
        d["startYear"] = item[3]
        d["endYear"] = item[4]
        d["data"] = item[5]
        d["unit"] = item[6]
        table["data"].append(d)
    return table


def getEduaction(mycursor, village_id, gazetteerName, year, year_range):
    table = {}
    table["data"] = []
    mycursor.execute("SELECT  e.categoryId_类别代码 cat1, ec.parentId_父类代码 ca2, ec.name_名称, e.startYear_开始年, e.endYear_结束年,e.data_数据 ,eu.name_名称 FROM education_教育 e JOIN educationCategory_教育类 ec \
        ON e.categoryId_类别代码= ec.categoryId_类别代码 JOIN educationUnit_教育单位 eu \
        ON e.unitId_单位代码=eu.unitId_单位代码 \
        WHERE e.gazetteerId_村志代码={}".format(int(village_id)))

    educationList = mycursor.fetchall()

    for item in educationList:
        d = {}
        if item[1] != None:
            d["category1"] = "受教育程度 Highest Level of Education"
            d["category2"] = item[2]
        else:
            d["category1"] = item[2]
            d["category2"] = "null"
        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = village_id

        # d["category1"] = item[2]
        d["startYear"] = item[3]
        d["endYear"] = item[4]
        d["data"] = item[5]
        d["unit"] = item[6]
        table["data"].append(d)
    return table


def getEconomy(mycursor, village_id, gazetteerName, year, year_range):
    table = {}
    table["data"] = []
    mycursor.execute("SELECT  e.categoryId_类别代码 cat1, ec.parentId_父类代码 ca2, ec.name_名称, e.startYear_开始年,\
      e.endYear_结束年,e.data_数据 ,eu.name_名称 FROM economy_经济 e JOIN economyCategory_经济类 ec \
      ON e.categoryId_类别代码=ec.categoryId_类别代码 JOIN economyUnit_经济单位 eu \
      ON e.unitId_单位代码=eu.unitId_单位代码 \
      WHERE e.gazetteerId_村志代码 ={}".format(village_id))
    econmialList = mycursor.fetchall()
    for item in econmialList:
        d = {}
        # the category2 also has two upper layer
        if item[1] not in [1, 19, 37.38, 39, 40, 41, 47, 56, 62] and item[1] != None:
            d["category3"] = item[2]
            mycursor.execute(
                "SELECT parentId_父类代码,name_名称 FROM economyCategory_经济类 WHERE categoryId_类别代码={}".format(item[1]))
            categoryList = mycursor.fetchone()
            categoryId, d["category2"] = categoryList[0], categoryList[1]

            mycursor.execute("SELECT name_名称 FROM economyCategory_经济类 WHERE categoryId_类别代码={}".format(categoryId))
            d["category1"] = mycursor.fetchone()[0]

        # the category2 has no upper layer
        elif item[1] == None:
            d["category1"] = item[2]
            d["category3"] = "null"
            d["category2"] = "null"

        # the category2 has onw upper layers
        else:
            d["category2"] = item[2]
            mycursor.execute("SELECT name_名称 FROM economyCategory_经济类 WHERE categoryId_类别代码={}".format(item[1]))
            d["category1"] = mycursor.fetchone()[0]
            d["category3"] = "null"

        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = village_id
        # d["category1"] = item[2]
        d["startYear"] = item[3]
        d["endYear"] = item[4]
        d["data"] = item[5]
        d["unit"] = item[6]
        table["data"].append(d)
    return table


def getFamilyPlanning(mycursor, village_id, gazetteerName, year, year_range):
    table = {}
    table["data"] = []
    mycursor.execute("SELECT  fc.name_名称, f.startYear_开始年,\
      f.endYear_结束年,f.data_数据 ,fu.name_名称 \
      FROM familyplanning_计划生育 f JOIN familyplanningcategory_计划生育类 fc \
      ON f.categoryId_类别代码= fc.categoryId_类别代码 JOIN familyplanningunit_计划生育单位 fu \
      ON f.unitId_单位代码=fu.unitId_单位代码 \
      WHERE f.gazetteerId_村志代码 ={}".format(village_id))

    familyplanningList = mycursor.fetchall()

    for item in familyplanningList:
        d = {}
        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = village_id
        d["category"] = item[0]
        d["startYear"] = item[1]
        d["endYear"] = item[2]
        d["data"] = item[3]
        d["unit"] = item[4]
        table["data"].append(d)
    return table


def getPopulation(mycursor, village_id, gazetteerName, year, year_range):
    table = {}
    table["field"] = ['gazetteerName', 'gazetteerId', 'category1', 'category2', 'startYear', 'endYear', 'data', 'unit']
    table["data"] = []
    table["tableNameChinese"] = "人口"
    mycursor.execute("SELECT  p.categoryId_类别代码 cid, pc.parentId_父类代码 pid,  pc.name_名称, p.startYear_开始年,\
    p.endYear_结束年,p.data_数据 ,pu.name_名称 \
    FROM population_人口 p JOIN populationcategory_人口类 pc \
    ON p.categoryId_类别代码= pc.categoryId_类别代码 JOIN populationunit_人口单位 pu \
    ON p.unitId_单位代码=pu.unitId_单位代码 \
    WHERE p.gazetteerId_村志代码 ={}".format(village_id))

    populationList = mycursor.fetchall()

    for item in populationList:
        d = {}
        if item[1] != None:
            mycursor.execute("SELECT name_名称 FROM populationcategory_人口类 WHERE categoryId_类别代码={}".format(item[1]))
            d["category2"] = mycursor.fetchone()[0]
        else:
            d["category2"] = "null"

        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = village_id
        d["category1"] = item[2]
        d["startYear"] = item[3]
        d["endYear"] = item[4]
        d["data"] = item[5]
        d["unit"] = item[6]
        table["data"].append(d)
    return table


def getEthnicgroups(mycursor, village_id, gazetteerName, year, year_range):
    table = {}
    table["data"] = []
    mycursor.execute("SELECT ethc.name_名称, eth.startYear_开始年,\
      eth.endYear_结束年,eth.data_数据 ,ethu.name_名称 \
      FROM ethnicGroups_民族 eth JOIN ethnicGroupsCategory_民族类 ethc \
      ON eth.categoryId_类别代码= ethc.categoryId_类别代码 JOIN ethnicGroupsUnit_民族单位 ethu \
      ON eth.unitId_单位代码=ethu.unitId_单位代码 \
      WHERE eth.gazetteerId_村志代码 ={};".format(village_id))

    ethnicgroupList = mycursor.fetchall()
    for item in ethnicgroupList:
        d = {}
        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = village_id
        d["category1"] = item[0]
        d["startYear"] = item[1]
        d["endYear"] = item[2]
        d["data"] = item[3]
        d["unit"] = item[4]
        table["data"].append(d)
    return table


def getFourthlastName(mycursor, village_id, gazetteerName, year, year_range):
    table = {}
    table["data"] = []
    mycursor.execute("SELECT firstlastNamesId_姓氏代码, secondlastNamesId_姓氏代码, thirdlastNamesId_姓氏代码, \
        fourthlastNamesId_姓氏代码, fifthlastNamesId_姓氏代码, totalNumberofLastNamesinVillage_姓氏总数 \
        FROM lastName_姓氏 WHERE gazetteerId_村志代码={}".format(village_id))
    nameList = mycursor.fetchall()

    l = []
    for z in range(len(nameList[0]) - 1):
        if nameList[0][z] == None:
            l.append("")
        else:
            mycursor.execute(
                "SELECT nameChineseCharacters_姓氏汉字 FROM lastNameCategory_姓氏类别 WHERE categoryId_类别代码 ={}".format(
                    nameList[0][z]))
            l.append(mycursor.fetchone()[0])

    d = {}
    d["gazetteerName"] = gazetteerName
    d["gazetteerId"] = village_id
    d["firstLastNameId"] = l[0]
    d["secondLastNameId"] = l[1]
    d["thirdLastNameId"] = l[2]
    d["fourthLastNameId"] = l[3]
    d["fifthlastNamesId_姓氏代码"] = l[4]
    d["totalNumberOfLastNameInVillage"] = nameList[0][-1]

    table["data"].append(d)
    return table


def getFirstAvailabilityorPurchase(mycursor, village_id, gazetteerName, year, year_range):
    table = {}
    table["data"] = []
    mycursor.execute("SELECT f.year_年份,fc.name_名称 FROM firstAvailabilityorPurchase_第一次购买或拥有年份 f JOIN firstAvailabilityorPurchaseCategory_第一次购买或拥有年份类 fc \
         ON f.categoryId_类别代码=fc.categoryId_类别代码 WHERE f.gazetteerId_村志代码={}".format(village_id))

    firstList = mycursor.fetchall()

    for i in firstList:
        d = {}
        d["gazetteerName"] = gazetteerName
        d["gazetteerId"] = village_id
        d["category"] = i[0] if i[0] != None else None
        d["year"] = i[1] if i[1] != None else None
        table["data"].append(d)

    return table
