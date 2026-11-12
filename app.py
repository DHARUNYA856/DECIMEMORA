import os
import secrets
import hmac
from flask import Flask,redirect,url_for,render_template,request,abort,session,flash
from flask_login import LoginManager,current_user
from config import Config
from database.db import db
from database.models import User
from database.seed_admin import seed
from auth.routes import bp as auth_bp
from admin.routes import bp as admin_bp
from employee.routes import bp as employee_bp

def create_app(test_config=None):
 app=Flask(__name__);app.config.from_object(Config)
 if test_config:app.config.update(test_config)
 os.makedirs(app.config['UPLOAD_FOLDER'],exist_ok=True)
 os.makedirs(app.config['CHROMA_PATH'],exist_ok=True)
 db.init_app(app)
 login=LoginManager(app);login.login_view='auth.login'
 @login.user_loader
 def load_user(uid):return db.session.get(User,int(uid))
 app.register_blueprint(auth_bp);app.register_blueprint(admin_bp);app.register_blueprint(employee_bp)
 app.jinja_env.globals['csrf_token']=lambda:session.get('csrf_token','')
 @app.route('/')
 def home():
  if not current_user.is_authenticated:return redirect(url_for('auth.login'))
  return redirect(url_for('admin.dashboard' if current_user.role=='Admin' else 'employee.dashboard'))
 @app.before_request
 def csrf_check():
  if 'csrf_token' not in session:session['csrf_token']=secrets.token_hex(24)
  if request.method in ('POST','PUT','PATCH','DELETE'):
   token=request.headers.get('X-CSRF-Token') or request.form.get('csrf_token','')
   if not hmac.compare_digest(token,session['csrf_token']):abort(403)
 @app.errorhandler(403)
 @app.errorhandler(404)
 @app.errorhandler(413)
 @app.errorhandler(500)
 def error(e):return render_template('error.html',message={403:'You do not have permission to access this resource.',404:'The requested page was not found.',413:'File exceeds upload limit.',500:'An unexpected error occurred.'}.get(getattr(e,'code',500),'Error')),getattr(e,'code',500)
 with app.app_context():
  db.create_all()
  if not app.config.get('TESTING'):seed()
 return app
app=create_app()
if __name__=='__main__':app.run(host='127.0.0.1',port=5000,debug=False)
