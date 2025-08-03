from app.extensions import db
from datetime import datetime

class Refinement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_prompt = db.Column(db.Text, nullable=False)
    final_solution = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    session_data = db.Column(db.JSON, nullable=True) # To store the full history

    def __repr__(self):
        return f'<Refinement {self.id}>'
