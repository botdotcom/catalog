#!/usr/bin/python

# All imports
from flask import Flask, request, redirect, url_for, make_response, render_template, jsonify, flash
from flask import session as login_session
#from flask_sqlalchemy import SQLAlchemy #not using this currently

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.client import AccessTokenCredentials

import json
import random
import string
import httplib2
import requests
from functools import wraps

from database_setup import Base, Items, Categories, Users

# App configuration
app = Flask(__name__)
app.secret_key = 'secret'

G_CLIENT_ID = json.loads(open('client_secret_g.json', 'r').read())['web']['client_id'] # Google client secret based

# Database configuration --> bind the engine to the metadata of the Base class so that the declaratives can be accessed through a DBSession instance
engine = create_engine('sqlite:///itemcatalog.db', connect_args={'check_same_thread': False}, echo=True)
Base.metadata.bind = engine

#db = SQLAlchemy(app) #not using this currently

DBSession = scoped_session(sessionmaker(bind=engine)) #scoped_session() is used to handle creating unique session for each thread
session = DBSession()

# 'Login required' decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in login_session:
            return redirect(url_for('showLogin'))
        return f(*args, **kwargs)
    return decorated_function


# Helper functions
def getUserID(email):
    try:
        user = session.query(Users).filter_by(email=email).one()
        return user.id
    except:
        return None

def getUserInfo(user_id):
    user = session.query(Users).filter_by(id=user_id).one()
    return user

def createUser(login_session):
    newUser = Users(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(Users).filter_by(email=login_session['email']).one()
    return user.id


# CRUD -- rubric
# CRUD for categories
def getCategories():
    return session.query(Categories).all()

def getCategory(category_id):
    category = session.query(Categories).filter_by(id=category_id).one()
    return category

def addCategory(name, user_id):
    category = Categories(name=name, user_id=user_id)
    session.add(category)
    session.commit()

def delCategory(category):
    session.delete(category)
    session.commit()

# CRUD for items
def getItems():
    return session.query(Items).order_by(Items.id.desc())

def getItemsByCategory(category_id):
    return session.query(Items).filter_by(category_id=category_id).order_by(Items.id.desc())

def getItem(item_id):
    item = session.query(Items).filter_by(id=item_id).one()
    return item

def addItem(name, description, category_id, user_id):
    item = Items(name=name, description=description, category_id=category_id, user_id=user_id)
    session.add(item)
    session.commit()

def deleteItem(item):
    session.delete(item)
    session.commit()


# Routing
# Show the catelog
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    """Returns catalog page with all categories and items"""
    categories = getCategories()
    items = getItems()
    quantity = items.count()
    return render_template('catalog.html', items=items, categories=categories, quantity=quantity)

# Add new category
@app.route('/categories/new', methods=['POST', 'GET'])
@login_required
def newCategory():
    """Allows user to create new category"""
    if request.method == 'POST':
        if 'user_id' not in login_session and 'email' in login_session:
            login_session['user_id'] = getUserID(login_session['email'])
        addCategory(name=request.form['name'], user_id=login_session['user_id'])
        flash("New category added", 'success')
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newCategory.html')

# Edit a category
@app.route('/categories/<int:category_id>/edit/', methods=['GET', 'POST'])
@login_required
def editCategory(category_id):
    """Allows user to edit an existing category"""
    toEdit = getCategory(category_id)
    if toEdit.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized!')}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            toEdit.name = request.form['name'] #edited name of category            
            # addCategory(toEdit) 
            flash("Category edited successfully", 'success')
            return redirect(url_for('showCatalog'))
    else:
        return render_template('editCategory.html', category=toEdit)

# Delete a category
@app.route('/categories/<int:category_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteCategory(category_id):
    """Allows user to delete an existing category"""
    toDelete = getCategory(category_id)
    if toDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized!')}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        delCategory(toDelete)
        flash("Category deleted successfully", 'success')
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteCategory.html', category=toDelete)
        
# Show items by category
@app.route('/categories/<int:category_id>/')
@app.route('/categories/<int:category_id>/items/')
def showCategoryItems(category_id):
    """Returns items in category"""
    category = getCategory(category_id)
    categories = getCategories()
    creator = getUserInfo(category.user_id)
    items = getItemsByCategory(category_id)
    quantity = items.count()
    return render_template('categoryItems.html', categories=categories, category=category, items=items, quantity=quantity, creator=creator)

# Show particular item's details    
@app.route('/categories/<int:category_id>/item/<int:item_id>/')
def showCatalogItem(category_id, item_id):
    """Returns category item details"""        
    category = getCategory(category_id)
    item = getItem(item_id)
    creator = getUserInfo(category.user_id)
    return render_template('itemDetail.html', category=category, item=item, creator=creator)

# Add new item
@app.route('/categories/item/new', methods=['GET', 'POST'])
@login_required
def newCatalogItem():
    """Allows user to create new item"""
    categories = getCategories()
    if request.method == 'POST':
        addItem(name=request.form['name'], description=request.form['description'], category_id=request.form['category'], user_id=login_session['user_id'])
        flash("Item added successfully", 'success')
        return redirect(url_for('showCatalog'))
    else:
        return render_template('newItem.html', categories=categories)

# Edit an item
@app.route('/categories/<int:category_id>/item/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def editCatalogItem(category_id, item_id):
    """Allows user to edit an item"""
    toEdit = getItem(item_id)
    if toEdit.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized!')}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        if request.form['name']:
            toEdit.name = request.form['name']
        if request.form['description']:
            toEdit.description = request.form['description']        
        if request.form['category']:
            toEdit.category = request.form['category']
        addItem(toEdit)
        flash("Item edited successfully", 'success')
        return redirect(url_for('showCatalog'))
    else:
        categories = getCategories()
        return render_template('editItem.html', categories=categories, item=toEdit)

# Delete an item
@app.route('/categories/<int:category_id>/item/<int:item_id>/delete', methods=['GET', 'POST'])
@login_required
def deleteCatalogItem(category_id, item_id):
    """Allows user to delete an item"""
    toDelete = getItem(item_id)        
    if toDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized!')}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        deleteItem(toDelete)
        flash("Item deleted successfully", 'success')
        return redirect(url_for('showCatalog'))
    else:
        return render_template('deleteItem.html', item=toDelete)


# Authentication and Authorization -- rubric
# Login route, along with anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# Logout route
@app.route('/logout')    
def logout():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            if 'gplus_id' in login_session:
                del login_session['gplus_id']
            if 'credentials' in login_session:
                del login_session['credentials']        
        if 'username' in login_session:
            del login_session['username']
        if 'email' in login_session:
            del login_session['email']
        if 'picture' in login_session:
            del login_session['picture']
        if 'user_id' in login_session:
            del login_session['user_id']
        del login_session['provider']
        flash("You are now logged out", 'success')
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in", 'danger')
        return redirect(url_for('showCatalog'))

# Login using Google
@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response.make_response(json.dumps('Invalid State paramenter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data # Obtain authorization code

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret_g.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps("""Failed to upgrade the authorisation code"""), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    header = httplib2.Http()
    result = json.loads(header.request(url, 'GET')[1])

    # Check if there was error in access token
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check if the access token is for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("""Token's user ID does not match given user ID."""), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check if the access token is valid for this app
    if result['issued_to'] != G_CLIENT_ID:
        response = make_response(json.dumps("""Token's client ID does not match app's."""), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in session for later use
    login_session['credentials'] = access_token
    login_session['id'] = gplus_id        

    # Get more info on user
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    # Add provider to login session
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    # Check if user exists; if not, then add
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    flash("You are now logged in as " + login_session['username'], 'success')
    return jsonify(name=login_session['username'], email=login_session['email'], picture=login_session['picture'])


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['credentials']
    # Only disconnect a connected user
    if access_token is None:
        response = make_response(json.dumps({'state': 'notConnected'}), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token)
    header = httplib2.Http()
    result = header.request(url, 'GET')[0]
    
    if result['status'] == '200':
        # Reset the user's session.
        del login_session['credentials']
        del login_session['id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        # del login_session['img']
        login_session['provider'] = 'null'
        response = make_response(json.dumps({'state': 'loggedOut'}), 200)
        response.headers['Content-Type'] = 'application/json'
        flash("You are now logged out", 'success')
        return response
    else:
        # if given token is invalid, unable to revoke token
        response = make_response(json.dumps({'state': 'errorRevoke'}), 200)
        response.headers['Content-Type'] = 'application/json'
        return response


# API endpoints -- rubric
@app.route('/api/v1/items.json')
def showCatalogJSON():
    """Returns JSON of all items in catalog"""
    items = session.query(Items).order_by(Items.id.desc())
    return jsonify(Items=[i.serialize for i in items])

@app.route('/api/v1/categories/<int:category_id>/item/<int:item_id>.json')
def catalogItemJSON(category_id, item_id):
    """Returns JSON of selected item in item catalog"""
    Item = session.query(Items).filter_by(id=item_id).one()
    return jsonify(Items=Item.serialize)

@app.route('/api/v1/categories.json')
def categoriesJSON():
    """Returns JSON of all categories in item catalog"""
    categories = session.query(Categories).all()
    return jsonify(Categories=[c.serialize for c in categories])


# Call Flask app
if __name__ == '__main__':    
    app.run(debug=True, host='0.0.0.0', port=5000)