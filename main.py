import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import auth
from flask import Flask, request, jsonify, make_response
from math import radians, cos, sin, asin, sqrt
import logging

app = Flask(_name_)
cred = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

@app.route('/')
def index():
    return '<h1>Server Up!</h1>'

#REGISTRATION
@app.route('/register', methods=['POST'])
def register():
     phno = request.values.get('phone_number')
     password = request.values.get('password')
     type = request.values.get('type')
     try:
      res=auth.create_user(phone_number=phno,password=password)
      print(res.uid)
      data = {
        'phone_number':phno,
        'password':password,
        'store_name':request.args.get('store_name'),
        'lat' : request.args.get('lat'),
        'lon' : request.args.get('lon'),
        'food-items':[]
        }
      db.collection(type).document(res.uid).set(data)
      return {"message":"success","token":res.uid,"response":data}
     except auth.PhoneNumberAlreadyExistsError as exc:
      print(exc.code)
      return {"message":"failure"}

#LOGIN
@app.route('/login', methods=['POST'])
def login():
      data = request.values
      phno = data.get('phone_number')
      password = data.get('password')
      type = data.get('type')
      try:
        user = auth.get_user_by_phone_number(phno)
        res = db.collection(type).document(user.uid).get()
        if res.to_dict()['password']==password:
            return {"message":"success","token":user.uid,"response":res.to_dict()}
      except auth.UserNotFoundError as expt:
        print(expt)
        return {"message":"failure"}
           
#VERIFY_FOODITEM_ALREADY_EXIST_OR_NOT
@app.route('/verify_barcode', methods=['GET'])
def barcodeverify():
    barcodeid = request.args.get('barcode')
    food_item = db.collection('food_items').document(barcodeid).get()
    res = 0
    mes=""
    if food_item.exists :
        res = -100
        mes="AlreadyExist"       
    else :
        res = 100
        mes="Not Available"
    logging.info(res+":" + mes)        
    return jsonify(code=res,message=mes) 

#GET_FOOD_IN_STORE
@app.route('/get_inventory', methods=['GET'])
def getInventory():
    print("YES")
    token = request.values.get('authorization')
    doc = db.collection('sellers').document(token).get()
    if not doc.exists:
       return {"message":"unauthorized"}      
    list =[]
    foods = doc.to_dict()['food-items']
    for food in foods:
        item = db.collection("food_items").document(food).get()
        list.append(item.to_dict())
    return {"message":"success","response": list}    

#POST_FOODITEM_WITH_NUTRITIONAL_VALUE
@app.route('/post_foodinfo', methods=['POST'])
def postfoodinfo():
    barcodeid = request.args.get('barcode')
    food_item = db.collection('food_items').document(barcodeid).get()
    res = -100
    mes="Failed"
    if not food_item.exists :
        db.collection('food_items').document(barcodeid).set(jsonify(request.form))
        res=100
        mes="Success"
    logging.info(res+":"+ mes)    
    return jsonify(code=res,message=mes)

#ADD_FOODITEMS_OF_SELLER
@app.route('/add_seller_items',methods=['POST'])
async def addFood():
      barcodeid = request.args.get('barcode')
      sellerid = request.args.get('id')
      data = db.collection('sellers').document(sellerid).get()
      arr = data.to_dict()['food_items']
      arr.append(barcodeid)
      await db.collection('sellers').document(sellerid).set({'food_items':arr})

#FEEDS_SHOWING_NEAR_BY_STORE
@app.route('/near_by_store',methods=['GET'])
def nearbystore():
    token = request.headers.get('authorization')
    check = db.collection('sellers').document(token).get()
    if not check.exists:
       return {"message":"unauthorized"}
    r = 6371
    blon= radians(float(request.args.get('lon')))
    blat= radians(float(request.args.get('lat')))
    docs = db.collection('sellers').get()
    list=[]
    
    for doc in docs:    
      slon=radians(float(doc.to_dict()['lon']))
      slat=radians(float(doc.to_dict()['lat']))
      d=(sin((slat-blat) / 2)*2 + cos(blat) * cos(slat) * sin((slon-blon) / 2)*2)*r
      list.append({"distance":d,"details":doc.to_dict()})  
    list.sort(key=extract_time)          
    return {"message":"success","respone":list}

def extract_time(json):
    try:
        return float(json['distance'])
    except KeyError:
        return 0

#GET_FOOD_LIST
@app.route('/get_foodlist',methods=['GET'])
def getfoodlist():
    token =request.headers.get('authorization')
    codes = request.values.getlist('list')
    foods=[]
    print(codes)
    #return  {"message":"success","response":codes}
    for code in codes:
       doc = db.collection('food_items').document(code).get()
       foods.append({"foods":doc.to_dict()})
    return  {"message":"success","response":foods}

#SEARCH_FOODITEM_OF_BUYER
@app.route('/get_searched_food',methods=['GET'])
def getsearchedfood():
    token = request.headers.get('authorization')
    check = db.collection('sellers').document(token).get()
    if not check.exists:
       return {"message":"unauthorized"}
    r = 6371
    blon= radians(float(request.args.get('lon')))
    blat= radians(float(request.args.get('lat')))
    food = request.args.get('food')
    docs = db.collection('sellers').get()
    list=[]
    for doc in docs:   
       if food in doc.to_dict()['food-items']:
        slon=radians(float(doc.to_dict()['lon']))
        slat=radians(float(doc.to_dict()['lat'])) 
        d=(sin((slat-blat) / 2)*2 + cos(blat) * cos(slat) * sin((slon-blon) / 2)*2)*r
        list.append({"distance":d,"details":doc.to_dict()})
    list.sort(key=extract_time)    
    return {"message":"success","response":list}         

@app.route('/admin',methods=['GET'])
def admin():
   docs = db.collection('sellers').get()
   alon = radians(float(request.values.get('lon')))
   alat = radians(float(request.values.get('lat')))
   r=float(request.values.get('rad'))
   R= 6371
   map = {}
   users = []
   for doc in docs:
      blat=radians(float(doc.to_dict()['lat']))
      blon=radians(float(doc.to_dict()['lon']))
      d=(sin((alat-blat) / 2)*2 + cos(blat) * cos(alat) * sin((alon-blon) / 2)*2)*R
      if d<=r:
         print(doc.to_dict()['store_name'])
         users.append(doc.to_dict())
   for user in users:   
       foods=user['food-items']
       for food in foods:
          if food in map:
             map[food]+=1
          else:
             map[food]=1 
   max=0 
   foodid = "123456"        
   for i in map:
        if map[i] != 0:
            print("{}{}".format(i,map[i]), end =" ")
            if(map[i]>max):
                max=map[i]
                foodid=i
                print(i)
            map[i] = 0
   obj = db.collection('food_items').document(foodid).get()
   return {"response":obj.to_dict()}
