from app.models import db
from app.utils.base_logger import BaseLogger
from sqlalchemy.exc import SQLAlchemyError

app_logger = BaseLogger(logger_name="BaseService").get_logger()


class BaseService:

    @staticmethod
    def _add_instance(instance):
        """
        Adds an instance to the session.
        """
        try:
            db.session.add(instance)
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            app_logger.error(f"Error adding instance {instance}: {e}")
            return False

    @staticmethod
    def _commit_session():
        """
        Handles committing the session, rolling back in case of failure.
        """
        try:
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            app_logger.error(f"Error during commit: {e}")
            return False
        
    @staticmethod
    def rollback_session():
        """
        Rolls back the current session.
        """
        db.session.rollback()
        app_logger.info("Session has been rolled back")
        
    @staticmethod
    def save_instance(instance):
        """
        Save a new instance to the database by adding and committing.
        """
        try:
            # Add the instance to the session
            if BaseService._add_instance(instance):
                # Commit the session to persist the instance
                if BaseService._commit_session():
                    return instance
            return None
        except SQLAlchemyError as e:
            app_logger.error(f"Unexpected error saving instance: {e}")
            return None

    @staticmethod
    def get(model, **filters):
        """
        Fetches a single record that matches the provided filters.
        """
        try:
            return model.query.filter_by(**filters).first()
        except SQLAlchemyError as e:
            app_logger.error(f"Error fetching {model.__name__}: {e}")
            return None

    @staticmethod
    def get_all(model, **filters):
        """
        Fetches all records that match the provided filters.
        """
        try:
            return model.query.filter_by(**filters).all()
        except SQLAlchemyError as e:
            app_logger.error(f"Error fetching all {model.__name__}: {e}")
            return []

    @staticmethod
    def create(model, **data):
        """
        Creates a new instance of the model. 
        """
        try:
            # Instantiate the model with the provided data
            instance = model(**data)
            
            # Add the instance to the session and commit
            db.session.add(instance)
            if BaseService._commit_session():
                app_logger.info(f"{model.__name__} created successfully with data: {data}")
                return instance
            else:
                return None
        except SQLAlchemyError as e:
            db.session.rollback()  # Rollback the session on error
            app_logger.error(f"Error creating {model.__name__} with data {data}: {e}")
            return None

    @staticmethod
    def update(model, id, **updates):
        """
        Updates an existing record by its ID.
        """
        try:
            instance = model.query.get(id)
            if instance:
                for key, value in updates.items():
                    setattr(instance, key, value)
                if BaseService._commit_session():
                    return instance
            return None
        except SQLAlchemyError as e:
            db.session.rollback()
            app_logger.error(f"Error updating {model.__name__} with id {id}: {e}")
            return None

    @staticmethod
    def delete(model, id):
        """
        Deletes an existing record by its ID.
        """
        try:
            instance = model.query.get(id)
            if instance:
                db.session.delete(instance)
                if BaseService._commit_session():
                    return instance
            return None
        except SQLAlchemyError as e:
            db.session.rollback()
            app_logger.error(f"Error deleting {model.__name__} with id {id}: {e}")
            return None
        

    @staticmethod
    def delete_by_filters(model, **filters):
        """
        Deletes an existing record by the provided filters.
        """
        try:
            instance = model.query.filter_by(**filters).first()  
            if instance:
                db.session.delete(instance)  
                if BaseService._commit_session():  
                    app_logger.info(f"{model.__name__} deleted successfully with filters: {filters}")
                    return instance  
            else:
                app_logger.info(f"No matching {model.__name__} found with filters: {filters}")
                return None  
        except SQLAlchemyError as e:
            db.session.rollback() 
            app_logger.error(f"Error deleting {model.__name__} with filters {filters}: {e}")
            return None  