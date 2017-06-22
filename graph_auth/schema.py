from django.conf import settings
from graphene import relay, AbstractType, Mutation, Node
from graphql_relay.node.node import from_global_id
import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django import DjangoObjectType
import django_filters
import logging
from django.db import models
from django.utils.http import urlsafe_base64_decode as uid_decoder
from django.utils.encoding import force_text

from rest_framework_jwt.settings import api_settings
from graph_auth.settings import graph_auth_settings

import django.contrib.auth
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

UserModel = django.contrib.auth.get_user_model()

class DynamicUsernameMeta(type):
    def __new__(mcs, classname, bases, dictionary):
        dictionary[UserModel.USERNAME_FIELD] = graphene.String(required=True)
        return type.__new__(mcs, classname, bases, dictionary)

class UserNode(DjangoObjectType):
    class Meta:
        model = UserModel
        interfaces = (relay.Node, )
        only_fields = graph_auth_settings.USER_FIELDS
        filter_fields = graph_auth_settings.USER_FIELDS

    @classmethod
    def get_node(cls, id, context, info):
        user = super(UserNode, cls).get_node(id, context, info)
        if context.user.id and (user.id == context.user.id or context.user.is_staff):
            return user
        else:
            return None

    token = graphene.String()
    def resolve_token(self, args, context, info):
        if self.id != context.user.id and not getattr(self, 'is_current_user', False):
            return None

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(self)
        token = jwt_encode_handler(payload)

        return token

class RegisterUser(relay.ClientIDMutation):
    class Input(metaclass=DynamicUsernameMeta):
        email = graphene.String(required=True)
        password = graphene.String()
        first_name = graphene.String()
        last_name = graphene.String()

    ok = graphene.Boolean()
    user = graphene.Field(UserNode)

    @classmethod
    def mutate_and_get_payload(cls, input, context, info):
        model = UserModel
        if graph_auth_settings.ONLY_ADMIN_REGISTRATION and not (context.user.id and context.user.is_staff):
            return RegisterUser(ok=False, user=None)
        if 'clientMutationId' in input:
            input.pop('clientMutationId')
        email = input.pop('email')
        username = input.pop(UserModel.USERNAME_FIELD, email)
        password = input.pop('password') if 'password' in input else model.objects.make_random_password()

        user = model.objects.create_user(username, email, password, **input)
        user.is_current_user = True
        django.contrib.auth.login(context, user)

        if graph_auth_settings.WELCOME_EMAIL_TEMPLATE is not None and graph_auth_settings.EMAIL_FROM is not None:
            from mail_templated import EmailMessage
            input_data = user.__dict__
            input_data['password'] = password
            message = EmailMessage(graph_auth_settings.WELCOME_EMAIL_TEMPLATE, input_data, graph_auth_settings.EMAIL_FROM, [user.email])
            message.send()

        return RegisterUser(ok=True, user=user)

class LoginUser(relay.ClientIDMutation):
    class Input(metaclass=DynamicUsernameMeta):
        password = graphene.String(required=True)

    ok = graphene.Boolean()
    user = graphene.Field(UserNode)

    @classmethod
    def mutate_and_get_payload(cls, input, context, info):
        model = UserModel

        params = {
            model.USERNAME_FIELD: input.get(model.USERNAME_FIELD, ''),
            'password': input.get('password')
        }

        user = django.contrib.auth.authenticate(**params)

        if user:
            user.is_current_user = True
            django.contrib.auth.login(context, user)
            return LoginUser(ok=True, user=user)
        else:
            return LoginUser(ok=False, user=None)

class ResetPasswordRequest(relay.ClientIDMutation):
    class Input:
        email = graphene.String(required=True)

    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, input, context, info):
        if graph_auth_settings.CUSTOM_PASSWORD_RESET_TEMPLATE is not None and graph_auth_settings.EMAIL_FROM is not None and graph_auth_settings.PASSWORD_RESET_URL_TEMPLATE is not None:

            from mail_templated import EmailMessage

            for user in UserModel.objects.filter(email=input.get('email')):
                uid = urlsafe_base64_encode(force_bytes(user.pk)).decode()
                token = token_generator.make_token(user)
                link = graph_auth_settings.PASSWORD_RESET_URL_TEMPLATE.format(token=token, uid=uid)
                input_data = {
                    "email": user.email, 
                    "first_name": user.first_name, 
                    "last_name": user.last_name, 
                    "link": link
                    }
                message = EmailMessage(graph_auth_settings.CUSTOM_PASSWORD_RESET_TEMPLATE, input_data, graph_auth_settings.EMAIL_FROM, [user.email])
                message.send()

        else:
            data = {
                'email': input.get('email'),
            }

            reset_form = PasswordResetForm(data=data)

            if not reset_form.is_valid():
                raise Exception("The email is not valid")

            options = {
                'use_https': context.is_secure(),
                'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL'),
                'request': context
            }

            reset_form.save(**options)

        return ResetPasswordRequest(ok=True)

class ResetPassword(relay.ClientIDMutation):
    class Input:
        password = graphene.String(required=True)
        id = graphene.String(required=True)
        token = graphene.String(required=True)

    ok = graphene.Boolean()
    user = graphene.Field(UserNode)

    @classmethod
    def mutate_and_get_payload(cls, input, context, info):
        Model = UserModel

        try:
            uid = force_text(uid_decoder(input.get('id')))
            user = Model.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Model.DoesNotExist):
            raise Exception('uid has an invalid value')

        data = {
            'uid': input.get('id'),
            'token': input.get('token'),
            'new_password1': input.get('password'),
            'new_password2': input.get('password')
        }

        reset_form = SetPasswordForm(user=user, data=data)

        if not reset_form.is_valid():
            raise Exception("The token is not valid")

        reset_form.save()

        return ResetPassword(ok=True, user=user)

class UpdateUsernameMeta(type):
    def __new__(mcs, classname, bases, dictionary):
        for field in graph_auth_settings.USER_FIELDS:
            dictionary[field] = graphene.String()
        return type.__new__(mcs, classname, bases, dictionary)

class UpdateUser(relay.ClientIDMutation):
    class Input(metaclass=UpdateUsernameMeta):
        password = graphene.String()
        current_password = graphene.String()

    ok = graphene.Boolean()
    result = graphene.Field(UserNode)

    @classmethod
    def mutate_and_get_payload(cls, input, context, info):
        Model = UserModel
        user = context.user
        user.is_current_user = True

        if not user.is_authenticated:
            raise Exception("You must be logged in to update renter profiles.")

        if 'password' in input:
            try:
                current_password = input.pop('current_password')
            except KeyError:
                raise Exception("Please provide your current password to change your password.")

            if user.check_password(current_password):
                user.set_password(input.pop('password'))
            else:
                raise Exception("Current password is incorrect.")

        for key, value in input.items():
            if not key is 'current_password':
                setattr(user, key, value)

        user.save()

        updated_user = Model.objects.get(pk=user.pk)

        return UpdateUser(ok=True, result=updated_user)

class Query(AbstractType):
    user = relay.Node.Field(UserNode)
    users = DjangoFilterConnectionField(UserNode)

    me = graphene.Field(UserNode)
    def resolve_me(self, args, context, info):
        return UserNode.get_node(context.user.id, context, info)

class Mutation(AbstractType):
    register_user = RegisterUser.Field()
    login_user = LoginUser.Field()
    reset_password_request = ResetPasswordRequest.Field()
    reset_password = ResetPassword.Field()
    update_user = UpdateUser.Field()
