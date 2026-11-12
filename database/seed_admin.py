import os
from database.db import db
from database.models import User,Project,ProjectMember,Decision

def seed():
 admin=User.query.filter_by(username=os.getenv('ADMIN_USERNAME','admin')).first()
 if not admin:
  admin=User(employee_id='ADMIN001',name='System Administrator',username=os.getenv('ADMIN_USERNAME','admin'),email='admin@decimemora.local',role='Admin')
  admin.set_password(os.getenv('ADMIN_PASSWORD','ChangeMe@12345'))
  db.session.add(admin);db.session.commit()
 if not Project.query.filter_by(project_code='BANK-001').first():
  project=Project(project_code='BANK-001',project_name='Banking Payment System',description='Payment gateway integration and incident knowledge',department='Engineering',created_by=admin.id)
  db.session.add(project);db.session.flush()
  db.session.add(Decision(project_id=project.id,problem='Payment API timeout during peak traffic',context='Payment service experienced timeout errors during high traffic.',options='Increase timeout; Add retry mechanism; Change provider',decision='Implement retry mechanism',reason='API normally recovered after a short delay.',action_taken='Implemented exponential backoff retry.',outcome='Payment failures reduced.',status='Resolved',created_by=admin.id))
  db.session.commit()
