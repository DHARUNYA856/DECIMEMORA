from flask import Blueprint,render_template,request,abort,redirect,url_for,flash,jsonify,send_file
from flask_login import login_required,current_user
from database.db import db
from database.models import Project,ProjectMember,Document,Decision,PermissionRequest,ChatHistory
from rag.retriever import can_read
bp=Blueprint('employee',__name__,url_prefix='/employee')
def project_access(user,pid,write=False):
 p=Project.query.get(pid)
 if not p or p.status!='active':return False
 if user.role=='Admin':return True
 q=ProjectMember.query.filter_by(user_id=user.id,project_id=pid).first()
 return bool(q and (not write or q.access_level in ('write','manage')))
def projects():
 if current_user.role=='Admin':return Project.query.filter_by(status='active').all()
 ids=[m.project_id for m in ProjectMember.query.filter_by(user_id=current_user.id).all()]
 return Project.query.filter(Project.id.in_(ids),Project.status=='active').all()
@bp.route('/dashboard')
@login_required
def dashboard():
 ps=projects();hist=ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.id.desc()).limit(6).all()
 return render_template('employee_dashboard.html',projects=ps,history=hist)
@bp.route('/projects')
@login_required
def my_projects():return render_template('my_projects.html',projects=projects())
@bp.route('/documents')
@login_required
def documents():
 ps=projects();ids=[p.id for p in ps];docs=Document.query.filter(Document.project_id.in_(ids)).order_by(Document.id.desc()).all()
 return render_template('documents.html',documents=docs,projects=ps,admin=False,can_read=can_read)
@bp.route('/documents/<int:id>/download')
@login_required
def download(id):
 d=Document.query.get_or_404(id)
 if not project_access(current_user,d.project_id) or not can_read(current_user,d):abort(403)
 return send_file(d.file_path,as_attachment=True,download_name=d.file_name)
@bp.route('/decisions')
@login_required
def decisions():
 ids=[p.id for p in projects()]
 return render_template('decisions.html',decisions=Decision.query.filter(Decision.project_id.in_(ids)).all(),projects=projects(),admin=False)
@bp.route('/permission-request',methods=['POST'])
@login_required
def permission_request():
 d=Document.query.get_or_404(request.form.get('document_id',type=int))
 if not project_access(current_user,d.project_id):abort(403)
 if not d.restricted or can_read(current_user,d):flash('You already have access.');return redirect(url_for('employee.documents'))
 if not PermissionRequest.query.filter_by(user_id=current_user.id,document_id=d.id,status='pending').first():
  db.session.add(PermissionRequest(user_id=current_user.id,project_id=d.project_id,document_id=d.id,reason=request.form.get('reason','')[:1000]));db.session.commit()
 flash('Permission request submitted.');return redirect(url_for('employee.documents'))
@bp.route('/chat')
@login_required
def chat():
 return render_template('chat.html',projects=projects(),history=ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.id.desc()).limit(20).all())
@bp.route('/chat/send',methods=['POST'])
@login_required
def chat_send():
 payload=request.get_json(silent=True) or {};question=str(payload.get('question','')).strip();pid=payload.get('project_id')
 if not question:return jsonify(error='Please enter a question.'),400
 try:pid=int(pid)
 except (TypeError,ValueError):return jsonify(error='Select a project.'),400
 if not project_access(current_user,pid):abort(403)
 from query.query_engine import answer_query
 try:return jsonify(answer_query(current_user,pid,question[:2000]))
 except Exception:
  from flask import current_app
  current_app.logger.exception('Chat query failed')
  return jsonify(error='Knowledge service is temporarily unavailable. Check local models and indexing.'),503

@bp.route('/documents/upload',methods=['POST'])
@login_required
def upload_document():
 from pathlib import Path
 from uuid import uuid4
 from werkzeug.utils import secure_filename
 from flask import current_app
 from admin.routes import process_document
 pid=request.form.get('project_id',type=int)
 if not project_access(current_user,pid,write=True):abort(403)
 file=request.files.get('file');name=secure_filename(file.filename or '') if file else ''
 if not name or Path(name).suffix.lower() not in ('.pdf','.docx','.txt'):
  flash('Invalid file type.','error');return redirect(url_for('employee.documents'))
 folder=Path(current_app.config['UPLOAD_FOLDER']);folder.mkdir(exist_ok=True,parents=True)
 path=folder/(uuid4().hex+Path(name).suffix.lower());file.save(path)
 d=Document(project_id=pid,uploaded_by=current_user.id,file_name=name,file_path=str(path),file_type=path.suffix.lower()[1:],restricted=False)
 db.session.add(d);db.session.commit();process_document(d)
 return redirect(url_for('employee.documents'))
