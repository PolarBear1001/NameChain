from datetime import datetime
from app import db

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    games = db.relationship('GameHistory', backref='player', lazy=True)

    def __repr__(self):
        return f'<Player {self.username}>'

class GameHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    start_name = db.Column(db.String(50), nullable=False)
    target_name = db.Column(db.String(50), nullable=False)
    name_chain = db.Column(db.Text, nullable=False)  # Store as JSON string
    chain_length = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    target_reached = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<GameHistory {self.id} - Chain length: {self.chain_length}>'

class HighScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    chain_length = db.Column(db.Integer, nullable=False)
    date_achieved = db.Column(db.DateTime, default=datetime.utcnow)
    
    player = db.relationship('Player', backref=db.backref('high_scores', lazy=True))

    def __repr__(self):
        return f'<HighScore {self.score} by {self.player.username}>'