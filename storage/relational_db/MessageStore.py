from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# SQLAlchemy base model
Base = declarative_base()

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    channel_id = Column(Integer, ForeignKey('channels.id'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", back_populates="messages")
    channel = relationship("Channel", back_populates="messages")

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    messages = relationship("Message", back_populates="sender")

class Channel(Base):
    __tablename__ = 'channels'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)
    messages = relationship("Message", back_populates="channel")

class MessageStore:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def store_message(self, content, sender_id, channel_id):
        session = self.Session()
        try:
            new_message = Message(content=content, sender_id=sender_id, channel_id=channel_id)
            session.add(new_message)
            session.commit()
            return new_message.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_messages_by_channel(self, channel_id, limit=50, offset=0):
        session = self.Session()
        try:
            messages = session.query(Message).filter_by(channel_id=channel_id).order_by(Message.timestamp.desc()).limit(limit).offset(offset).all()
            return messages
        finally:
            session.close()

    def get_messages_by_user(self, user_id, limit=50, offset=0):
        session = self.Session()
        try:
            messages = session.query(Message).filter_by(sender_id=user_id).order_by(Message.timestamp.desc()).limit(limit).offset(offset).all()
            return messages
        finally:
            session.close()

    def delete_message(self, message_id):
        session = self.Session()
        try:
            message = session.query(Message).filter_by(id=message_id).first()
            if message:
                session.delete(message)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_message(self, message_id, new_content):
        session = self.Session()
        try:
            message = session.query(Message).filter_by(id=message_id).first()
            if message:
                message.content = new_content
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_message_by_id(self, message_id):
        session = self.Session()
        try:
            message = session.query(Message).filter_by(id=message_id).first()
            return message
        finally:
            session.close()

    def get_message_count_by_channel(self, channel_id):
        session = self.Session()
        try:
            count = session.query(Message).filter_by(channel_id=channel_id).count()
            return count
        finally:
            session.close()

    def get_message_count_by_user(self, user_id):
        session = self.Session()
        try:
            count = session.query(Message).filter_by(sender_id=user_id).count()
            return count
        finally:
            session.close()

    def get_recent_messages(self, limit=10):
        session = self.Session()
        try:
            messages = session.query(Message).order_by(Message.timestamp.desc()).limit(limit).all()
            return messages
        finally:
            session.close()

# Usage
if __name__ == "__main__":
    db_url = "sqlite:///message_store.db" 
    store = MessageStore(db_url)

    # Storing a message
    message_id = store.store_message("Hello, World!", sender_id=1, channel_id=1)

    # Fetching messages by channel
    messages = store.get_messages_by_channel(channel_id=1)
    for message in messages:
        print(f"Message {message.id} from {message.sender_id}: {message.content}")

    # Updating a message
    store.update_message(message_id=message_id, new_content="Hello, updated world!")

    # Deleting a message
    store.delete_message(message_id=message_id)