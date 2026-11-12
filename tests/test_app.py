import unittest,tempfile
from pathlib import Path
from app import create_app
from database.db import db
from database.models import User,Project,ProjectMember
class SecurityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name)
  self.app=create_app({'TESTING':True,'SQLALCHEMY_DATABASE_URI':'sqlite:///'+str(root/'test.db'),'UPLOAD_FOLDER':str(root/'uploads'),'CHROMA_PATH':str(root/'chroma'),'SECRET_KEY':'test-only'})
  with self.app.app_context():
   db.drop_all();db.create_all()
   a=User(employee_id='A',name='Admin',username='admin_test',email='a@test.local',role='Admin');a.set_password('strongpass')
   e=User(employee_id='E',name='Employee',username='emp_test',email='e@test.local',role='New Employee');e.set_password('strongpass')
   db.session.add_all([a,e]);db.session.commit()
   p=Project(project_code='P',project_name='Test');db.session.add(p);db.session.commit()
  self.client=self.app.test_client()
 def tearDown(self):
  with self.app.app_context():db.session.remove();db.engine.dispose()
  self.tmp.cleanup()
 def login(self,username):
  self.client.get('/login')
  with self.client.session_transaction() as s:token=s['csrf_token']
  return self.client.post('/login',data={'username':username,'password':'strongpass','csrf_token':token})
 def test_admin_login(self):self.assertEqual(self.login('admin_test').status_code,302)
 def test_employee_cannot_access_admin(self):
  self.login('emp_test');self.assertEqual(self.client.get('/admin/dashboard').status_code,403)
 def test_unassigned_project_hidden(self):
  self.login('emp_test');self.assertNotIn(b'Test',self.client.get('/employee/projects').data)
 def test_unassigned_chat_forbidden(self):
  self.login('emp_test')
  with self.client.session_transaction() as s:token=s['csrf_token']
  response=self.client.post('/employee/chat/send',json={'project_id':1,'question':'secret'},headers={'X-CSRF-Token':token})
  self.assertEqual(response.status_code,403)
 def test_csrf_rejected(self):
  self.client.get('/login');self.assertEqual(self.client.post('/login',data={'username':'admin_test','password':'strongpass'}).status_code,403)
if __name__=='__main__':unittest.main()
