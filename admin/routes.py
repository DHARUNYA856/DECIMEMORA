from pathlib import Path
from uuid import uuid4
from functools import wraps
from flask import Blueprint,render_template,request,redirect,url_for,flash,abort,current_app
from flask_login import login_required,current_user
from werkzeug.utils import secure_filename
from database.db import db
from database.models import User,Project,ProjectMember,Document,Decision,PermissionRequest,now
from rag.document_loader import extract,chunks
from rag.vector_store import index,remove
from decision_memory.memory import index_decision
bp=Blueprint('admin',__name__,url_prefix='/admin')
def admin_only(f):
 @wraps(f)
 @login_required
 def wrapped(*a,**kw):
  if current_user.role!='Admin':abort(403)
  return f(*a,**kw)
 return wrapped
@bp.route('/dashboard')
@admin_only
def dashboard():
 counts={'Employees':User.query.count(),'Projects':Project.query.count(),'Documents':Document.query.count(),'Decisions':Decision.query.count(),'Pending Requests':PermissionRequest.query.filter_by(status='pending').count()}
 return render_template('admin_dashboard.html',counts=counts)
@bp.route('/employees')
@admin_only
def employees():return render_template('employees.html',users=User.query.order_by(User.id.desc()).all())
@bp.route('/employees/create',methods=['GET','POST'])
@bp.route('/employees/edit/<int:id>',methods=['GET','POST'])
@admin_only
def employee_form(id=None):
 u=User.query.get_or_404(id) if id else None
 if request.method=='POST':
  if not u:u=User(employee_id=request.form['employee_id'],created_by=current_user.id);db.session.add(u)
  for key in ['name','username','email','department','role','status']:setattr(u,key,request.form[key].strip())
  if request.form.get('password'):u.set_password(request.form['password'])
  if not u.password_hash:flash('Password is required.','error');return render_template('employee_form.html',user=u)
  try:db.session.commit();flash('Employee saved.');return redirect(url_for('admin.employees'))
  except Exception:db.session.rollback();flash('Username, email or employee ID already exists.','error')
 return render_template('employee_form.html',user=u)
@bp.route('/projects')
@admin_only
def projects():return render_template('projects.html',projects=Project.query.order_by(Project.id.desc()).all())
@bp.route('/projects/create',methods=['GET','POST'])
@bp.route('/projects/edit/<int:id>',methods=['GET','POST'])
@admin_only
def project_form(id=None):
 p=Project.query.get_or_404(id) if id else None
 if request.method=='POST':
  if not p:p=Project(project_code=request.form['project_code'].strip(),created_by=current_user.id);db.session.add(p)
  for k in ['project_name','description','department','status']:setattr(p,k,request.form[k].strip())
  try:db.session.commit();flash('Project saved.');return redirect(url_for('admin.projects'))
  except Exception:db.session.rollback();flash('Project code already exists.','error')
 return render_template('project_form.html',project=p)
@bp.route('/projects/<int:id>/members',methods=['GET','POST'])
@admin_only
def members(id):
 p=Project.query.get_or_404(id)
 if request.method=='POST':
  uid=request.form.get('user_id',type=int);u=User.query.get_or_404(uid)
  m=ProjectMember.query.filter_by(project_id=id,user_id=uid).first()
  if request.form.get('action')=='remove':
   if m:db.session.delete(m)
  else:
   if not m:m=ProjectMember(project_id=id,user_id=uid,assigned_by=current_user.id);db.session.add(m)
   m.access_level=request.form.get('access_level','read')
  db.session.commit();return redirect(url_for('admin.members',id=id))
 memberships=ProjectMember.query.filter_by(project_id=id).all()
 return render_template('members.html',project=p,memberships=[(m,db.session.get(User,m.user_id)) for m in memberships],users=User.query.filter(User.role!='Admin').all())
@bp.route('/documents',methods=['GET','POST'])
@admin_only
def documents():
 if request.method=='POST':
  file=request.files.get('file');pid=request.form.get('project_id',type=int)
  if not Project.query.get(pid):abort(400)
  name=secure_filename(file.filename or '') if file else ''
  if not name or Path(name).suffix.lower() not in ('.pdf','.docx','.txt'):
   flash('Only PDF, DOCX and TXT are allowed.','error');return redirect(url_for('admin.documents'))
  folder=Path(current_app.config['UPLOAD_FOLDER']);folder.mkdir(parents=True,exist_ok=True)
  path=folder/(uuid4().hex+Path(name).suffix.lower());file.save(path)
  d=Document(project_id=pid,uploaded_by=current_user.id,file_name=name,file_path=str(path),file_type=path.suffix.lower()[1:],restricted=bool(request.form.get('restricted')))
  db.session.add(d);db.session.commit();process_document(d)
  return redirect(url_for('admin.documents'))
 return render_template('documents.html',documents=Document.query.order_by(Document.id.desc()).all(),projects=Project.query.all(),admin=True)
def process_document(d):
 try:
  text=extract(d.file_path);parts=chunks(text)
  if not parts:raise ValueError('Document has no extractable text')
  remove('document',d.id)
  index('document',d.id,d.project_id,parts,{'file_name':d.file_name,'document_id':d.id,'uploaded_by':d.uploaded_by,'document_type':d.file_type})
  d.status='indexed';flash('Document indexed successfully.')
 except Exception:
  current_app.logger.exception('Indexing failed');d.status='failed';flash('Indexing failed. Verify document and local embedding model.','error')
 db.session.commit()
@bp.route('/documents/<int:id>/reindex',methods=['POST'])
@admin_only
def reindex(id):process_document(Document.query.get_or_404(id));return redirect(url_for('admin.documents'))
@bp.route('/documents/<int:id>/delete',methods=['POST'])
@admin_only
def delete_document(id):
 d=Document.query.get_or_404(id)
 try:remove('document',d.id)
 except Exception:current_app.logger.exception('Vector deletion failed');flash('Vector deletion failed; document retained.','error');return redirect(url_for('admin.documents'))
 PermissionRequest.query.filter_by(document_id=id).delete();Path(d.file_path).unlink(missing_ok=True);db.session.delete(d);db.session.commit()
 return redirect(url_for('admin.documents'))
@bp.route('/decisions')
@admin_only
def decisions():return render_template('decisions.html',decisions=Decision.query.order_by(Decision.id.desc()).all(),projects=Project.query.all(),admin=True)
@bp.route('/decisions/create',methods=['GET','POST'])
@bp.route('/decisions/edit/<int:id>',methods=['GET','POST'])
@admin_only
def decision_form(id=None):
 d=Decision.query.get_or_404(id) if id else None
 if request.method=='POST':
  if not d:d=Decision(created_by=current_user.id);db.session.add(d)
  d.project_id=request.form.get('project_id',type=int)
  if not Project.query.get(d.project_id):abort(400)
  for k in ['problem','context','options','decision','reason','action_taken','outcome','status']:setattr(d,k,request.form.get(k,'').strip())
  db.session.commit()
  try:index_decision(d);flash('Decision saved and indexed.')
  except Exception:current_app.logger.exception('Decision indexing failed');flash('Decision saved but indexing failed.','error')
  return redirect(url_for('admin.decisions'))
 return render_template('decision_form.html',decision=d,projects=Project.query.all())
@bp.route('/decisions/<int:id>/delete',methods=['POST'])
@admin_only
def delete_decision(id):
 d=Decision.query.get_or_404(id)
 try:remove('decision',d.id)
 except Exception:flash('Could not remove vector; decision retained.','error');return redirect(url_for('admin.decisions'))
 db.session.delete(d);db.session.commit();return redirect(url_for('admin.decisions'))
@bp.route('/permission-requests')
@admin_only
def permissions():
 rows=PermissionRequest.query.order_by(PermissionRequest.id.desc()).all()
 return render_template('permission_requests.html',requests=[(r,db.session.get(User,r.user_id),db.session.get(Document,r.document_id)) for r in rows])
@bp.route('/permission-requests/<int:id>/<action>',methods=['POST'])
@admin_only
def resolve_permission(id,action):
 if action not in ('approve','reject'):abort(404)
 r=PermissionRequest.query.get_or_404(id)
 if r.status!='pending':abort(400)
 r.status='approved' if action=='approve' else 'rejected';r.approved_by=current_user.id;r.approved_at=now();db.session.commit()
 return redirect(url_for('admin.permissions'))
