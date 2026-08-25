"""
repositories/user_repository.py - Requêtes SQL liées aux utilisateurs
Aucune logique métier ici, uniquement des accès à la base.
"""

from database.database import db
from models.User import User


class UserRepository:

    @staticmethod
    def create(name: str, email: str, password: str) -> User:
        """Crée et persiste un nouvel utilisateur."""
        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def find_by_id(user_id: int) -> User | None:
        return User.query.get(user_id)

    @staticmethod
    def find_by_email(email: str) -> User | None:
        return User.query.filter_by(email=email.lower().strip()).first()

    @staticmethod
    def email_exists(email: str) -> bool:
        return User.query.filter_by(email=email.lower().strip()).count() > 0

    @staticmethod
    def update(user: User, **kwargs) -> User:
        """Met à jour les champs fournis en kwargs."""
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.session.commit()
        return user

    @staticmethod
    def update_password(user: User, new_password: str) -> User:
        user.set_password(new_password)
        db.session.commit()
        return user

    @staticmethod
    def delete(user: User) -> None:
        db.session.delete(user)
        db.session.commit()
