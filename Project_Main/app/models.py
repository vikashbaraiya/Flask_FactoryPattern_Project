# models.py

from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from sqlalchemy import UniqueConstraint
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Role(db.Model):
    __tablename__ = 'roles'  # Explicitly set table name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    users = db.relationship('User', secondary='user_roles', back_populates='roles')

    def __repr__(self):
        return f'<Role {self.name}>'
    

user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    accounts = db.relationship('Account', back_populates='user', lazy=True)
    roles = db.relationship('Role', secondary=user_roles, back_populates='users')
    confirmed = db.Column(db.Boolean, default=False) 
    otp = db.Column(db.String(6), nullable=True)  # Field for OTP
    otp_generated_at = db.Column(db.DateTime, nullable=True)  # New field for OTP timestamp
    file_name = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)
    
    def serialize(self):
        # Construct the image URL only if the file_name is provided
        image_url = None
        if self.file_name:
            image_url = url_for('static', filename=f"images/{self.file_name.split('/')[-1]}", _external=True)

        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'roles': [role.name for role in self.roles],  # Returns list of roles
            'confirmed': self.confirmed,
            'image_url': image_url  # Dynamically generate the image URL
        }


class ErrorLog(db.Model):
    __tablename__ = 'error_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot_data.id'), nullable=False)
    level_name = db.Column(db.String(50), nullable=False)
    msg = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.Float, nullable=False)
    # Relationship back to BotData
    bot_data = db.relationship('BotData', back_populates='error_logs', lazy=True)
    
    def __str__(self):
        return f"<ErrorLog id={self.id} bot_id={self.bot_id} level_name={self.level_name}>"
    
    def serialize(self):
        return {
            'id': self.id,
            'bot_id': self.bot_id,
            'level_name': self.level_name,
            'msg': self.msg,
            'timestamp': self.timestamp,
            'timestamp_human': self.timestamp_human
        }
    
    @property
    def timestamp_human(self):
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


class GeneralLog(db.Model):
    __tablename__ = 'general_logs'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot_data.id'), nullable=False)
    level_name = db.Column(db.String(50), nullable=False)
    msg = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.Float, nullable=False)
    # Relationship back to BotData
    bot_data = db.relationship('BotData', back_populates='general_logs', lazy=True)
    
    def __str__(self):
        return f"<GeneralLog id={self.id} bot_id={self.bot_id} level_name={self.level_name}>"
    
    def serialize(self):
        return {
            'id': self.id,
            'bot_id': self.bot_id,
            'level_name': self.level_name,
            'msg': self.msg,
            'timestamp': self.timestamp,
            'timestamp_human': self.timestamp_human
        }
    
    @property
    def timestamp_human(self):
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


