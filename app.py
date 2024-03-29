#>>>>>>>>>>--------IMPORT LIBRARIES---------<<<<<<<<<<#

from flask import render_template,request,redirect, flash, session
from flask import Flask
import flask_restful
from matplotlib.figure import Figure
from numpy import true_divide
from Db_setup.module import User as user_model, tracker, logs, db
import matplotlib.pyplot as plt



#>>>>>>>>--------CREATE a Flask Instance-------<<<<<<<<#


app=Flask(__name__)


#>>>>>>>>--------DATABASE-------<<<<<<<<#


app.secret_key = "itisasecret"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.sqlite3'
db.init_app(app)


#>>>>>>>>---------ROUTES---------<<<<<<<<<<#


@app.before_first_request
def create_tables():
    db.create_all()



#>>>>>>>>-------INDEX-------<<<<<<<<<<#



@app.route('/', methods=["GET"])
def index():

    return render_template('index.html')



#>>>>>>>>>>-------ABOUT-------<<<<<<<<<<#



@app.route('/about_us')
def about():
    return render_template('About.html')



#>>>>>>>>>>-------CONTACT-------<<<<<<<<<<#



@app.route('/contact')
def contact():
    return render_template('contact.html')



#>>>>>>>>>>--------LOGIN-------<<<<<<<<<<#



@app.route("/login", methods= ['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method=='POST':
        my_username=request.form['username']
        my_password=request.form['password']

        check=user_model.query.filter_by(username = my_username).first()
        if check:
            if check.password!=my_password:
                return render_template('login.html',info='Sorry, your password was incorrect. Please double-check your password.')
            else:
                
                return redirect(f"/{my_username}/dashboard")
        else:
            return render_template('login.html',info='The username you entered doesn\'t belong to an account. Please check your username and try again')



#>>>>>>>>>>--------SIGNUP-------<<<<<<<<<<#



@app.route("/sign_up", methods=["GET", "POST"])
def signup():
    if request.method=='POST':
        my_name=request.form['name']
        my_username=request.form['username']
        my_password=request.form['password']

        check=user_model.query.filter_by(username=my_username).first()
        if check:
           return render_template('sign_up.html',info='Username you entered already belongs to an account. Try another Username.')
        else:
            # If user does not exists
            if my_name:
                if my_username:
                    if my_password:
                        user=user_model(name=my_name,username=my_username,password=my_password)
                        db.session.add(user)
                        db.session.commit()
                        user_model.query.all()
                        return login()
                    else: 
                        return render_template('sign_up.html',info='Password cannot be empty. Please enter a valid Password')
                else:
                    return render_template('sign_up.html',info='Username cannot be empty. Please Enter Username')
            else:
                return render_template('sign_up.html',info='Name cannot be empty. Please enter a valid name')
    else:
        return render_template('sign_up.html')




#>>>>>>>>>>--------DASHBOARD-------<<<<<<<<<<#




@app.route("/<string:username>/dashboard")
def dashboard(username):
    
    user = user_model.query.filter_by(username=username).first()
    tracks  = user.trackers
    
    return render_template('dashboard.html',tracks=tracks,username=username)


#>>>>>>>>>>--------LOGOUT--------------#


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/login")



#>>>>>>>>>>--------CREATE TRACKER-------<<<<<<<<<<#



@app.route("/<string:username>/create_tracker",methods=["GET", "POST"])  
def create(username):
    if request.method == 'GET':
        return render_template('create_tracker.html',username=username)
    if request.method=="POST":
        Name=request.form.get("_name_")
        Description=request.form.get("_description_")
        Tracker_type=request.form.get("_type_")

        new_tracker=tracker(name=Name, description=Description, tracker_type=Tracker_type)
        user = user_model.query.filter_by(username=username).first()
        user.trackers.append(new_tracker)
        db.session.add(new_tracker)
        db.session.commit()
        return redirect(f"/{username}/dashboard")



#>>>>>>>>>>--------UPDATE TRACKER-------<<<<<<<<<<#



@app.route("/<string:username>/update/<int:id>", methods=["GET", "POST"])  
def update(username,id=None):
    trackers=tracker.query.filter_by(id=id).first()
    if request.method=="POST":
        if trackers:
            Tracker_type=trackers.tracker_type
            db.session.delete(trackers)
            db.session.commit()
            Name=request.form.get("_name_")
            Description=request.form.get("_description_")

            new_tracker=tracker(name=Name, description=Description, tracker_type=Tracker_type)
            user = user_model.query.filter_by(username=username).first()
            user.trackers.append(new_tracker)
            db.session.add(new_tracker)
            db.session.commit()
            flash("User Added Successfully!")
            return redirect(f"/{username}/dashboard")
    return render_template("update.html", trackers=trackers, username=username)



#>>>>>>>>>>--------DELETE TRACKER-------<<<<<<<<<<#



@app.route('/<string:username>/<int:id>/delete', methods=['GET','POST'])
def delete(id,username):
    new_tracker = tracker.query.get_or_404(id)

    try:
            db.session.delete(new_tracker)
            db.session.commit()
            return redirect(f"/{username}/dashboard")
    except:        

        return "There was a problem deleting that task."



#>>>>>>>>>>--------CREATE TRACKER LOG-------<<<<<<<<<<#



@app.route("/<string:username>/<int:id>/logs",methods=["GET", "POST"])  
def log(username,id):
    str=""
    parent_tracker=tracker.query.filter_by(id=id).first()
    if request.method=="GET":
        all_logs  = parent_tracker.logs
        if parent_tracker.tracker_type=="Numeric":
            data={x.timestamp:x.value for x in all_logs}
            fig = Figure()
            axis = fig.add_subplot(1, 1, 1)
            axis.plot(data.keys(),data.values())
            axis.set(xlabel="Time Stamp", ylabel="Value")
            fig.savefig('static/graph.png')
            return render_template("numerical.html", tracks=all_logs, str=str, src='static/graph.png', parent_tracker=parent_tracker, username=username)
        if parent_tracker.tracker_type=="Boolean":
            return render_template("boolean.html", tracks=all_logs, str=str, parent_tracker=parent_tracker, username=username)
    
    elif request.method=="POST":
        Timestamp=logs.query.get("timestamp")
        my_log=parent_tracker.tracker_type
        my_value=request.form.get("_value_")
        my_note=request.form.get("_note_")
        
        new_log=logs(log=my_log, value=my_value, note=my_note, timestamp=Timestamp)
        parent_tracker.logs.append(new_log)
        db.session.add(new_log)
        db.session.commit()
        str="Log Added Successfully"

        return redirect(f"/{username}/{id}/logs")
     
    

#>>>>>>>>>>--------DELETE TRACKER LOG-------<<<<<<<<<<#



@app.route('/<string:username>/<int:tracker_id>/<int:log_id>/delete', methods=['GET'])
def delete_log(username,tracker_id,log_id):
    log_needed = logs.query.get_or_404(log_id)

    try:
            db.session.delete(log_needed)
            db.session.commit()
            return redirect(f"/{username}/{tracker_id}/logs")
    except:        

        return "There was a problem deleting that task."



#>>>>>>>>>>--------UPDATE TRACKER LOG-------<<<<<<<<<<#



@app.route("/<string:username>/<int:tracker_id>/<int:log_id>/update", methods=["GET","POST"])  
def update_log(username,tracker_id,log_id):
    log_needed=logs.query.filter_by(id=log_id).first()
    if request.method=="POST":
        if log_needed:
            Tracker_type=log_needed.log
            db.session.delete(log_needed)
            db.session.commit()
            val=request.form.get("_value_")
            note=request.form.get("_note_")
            
            new_log=logs(log=Tracker_type, value=val, note=note)
            parent_tracker = tracker.query.filter_by(id=tracker_id).first()
            parent_tracker.logs.append(new_log)
            db.session.add(new_log)
            db.session.commit()
            flash("Log updated Successfully!")
            return redirect(f"/{username}/{tracker_id}/logs")
    return render_template("update_log.html", log=log_needed, tracker_id=tracker_id, username=username)


#>>>>>>>>>>------MAIN-------<<<<<<<<<<#


if __name__ == "__main__":
    app.run(debug=True) 