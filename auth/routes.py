from flask import Blueprint,render_template,request,redirect,url_for,flash
from flask_login import login_user,logout_user,login_required,current_user
from database.db import db
from database.models import User,now
bp=Blueprint('auth',__name__)
@bp.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  u=User.query.filter_by(username=request.form.get('username','')).first()
  if u and u.is_active and u.check_password(request.form.get('password','')):
   login_user(u);u.last_login=now();db.session.commit()
   return redirect(url_for('admin.dashboard' if u.role=='Admin' else 'employee.dashboard'))
  flash('Invalid credentials or inactive account.','error')
 return render_template('login.html')
@bp.route('/logout',methods=['POST'])
@login_required
def logout():
 logout_user();return redirect(url_for('auth.login'))
