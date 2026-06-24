from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.set_password('Admin@1234')
        db.session.commit()
        print("✅ Admin password securely updated to: Admin@1234")
    else:
        print("❌ Admin user not found!")
