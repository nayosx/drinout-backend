from sqlalchemy import CheckConstraint
from db import db

class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    document_id = db.Column(db.String(50))
    is_deleted = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer)
    updated_by = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    addresses = db.relationship(
        "ClientAddress",
        back_populates="client",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    phones = db.relationship(
        "ClientPhone",
        back_populates="client",
        lazy="selectin",
        cascade="all, delete-orphan"
    )


class ClientAddress(db.Model):
    __tablename__ = 'client_addresses'
    __table_args__ = (
        CheckConstraint('latitude BETWEEN -90 AND 90', name='chk_latitude'),
        CheckConstraint('longitude BETWEEN -180 AND 180', name='chk_longitude')
    )

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', onupdate='CASCADE'), nullable=False)
    address_text = db.Column(db.String(500), nullable=False)
    latitude = db.Column(db.Numeric(10,8))
    longitude = db.Column(db.Numeric(11,8))
    map_link = db.Column(db.String(500))
    image_path = db.Column(db.String(500))
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    client = db.relationship(
        "Client",
        back_populates="addresses"
    )


class ClientPhone(db.Model):
    __tablename__ = 'client_phones'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', onupdate='CASCADE'), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(100))
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    client = db.relationship(
        "Client",
        back_populates="phones"
    )
