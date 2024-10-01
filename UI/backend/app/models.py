from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.String(50), default='default')  # Using a default value for now