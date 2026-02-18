"""
This file implements user registration.
"""
from flask import request
from flask_restx import Resource, Namespace, fields
from werkzeug.security import generate_password_hash
import data.db_connect as dbc

USERS_RESP = 'user'
COLLECTION = 'users'
NAME = 'name'
EMAIL = 'email'
PASSWORD = 'password'

api = Namespace('users', description='User operations')

register_model = api.model('Register', {
    NAME: fields.String(required=True, description='Full name'),
    EMAIL: fields.String(required=True, description='Email address'),
    PASSWORD: fields.String(required=True, description='Password'),
})


@api.route('/register')
class UserRegister(Resource):
    @api.expect(register_model)
    @api.doc('register_user')
    def post(self):
        data = request.json

        name = data.get(NAME, '').strip()
        email = data.get(EMAIL, '').strip().lower()
        password = data.get(PASSWORD, '')

        if not name or not email or not password:
            api.abort(400, 'name, email, and password are required')

        existing = dbc.read_one(COLLECTION, {EMAIL: email})
        if existing:
            api.abort(409, 'An account with that email already exists')

        hashed_pw = generate_password_hash(password)
        dbc.create(COLLECTION, {
            NAME: name,
            EMAIL: email,
            PASSWORD: hashed_pw,
        })

        return {USERS_RESP: {NAME: name, EMAIL: email}}, 201
