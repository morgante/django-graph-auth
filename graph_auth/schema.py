from django.conf import settings
from graphene import relay, AbstractType, Mutation, Node
from graphql_relay.node.node import from_global_id
import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django import DjangoObjectType
import django_filters
import logging
from django.db import models
import django.contrib.auth
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from rest_framework_jwt.settings import api_settings
from django.utils.http import urlsafe_base64_decode as uid_decoder
from django.utils.encoding import force_text

from graph_auth.settings import graph_auth_settings

class UserNode(DjangoObjectType):
    class Meta:
        model = django.contrib.auth.get_user_model()
        interfaces = (Node, )
        only_fields = graph_auth_settings.USER_FIELDS

    @classmethod
    def get_node(cls, id, context, info):
        user = super(UserNode, cls).get_node(id, context, info)
        if context.user.id and user.id == context.user.id:
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
    class Input:
        username = graphene.String()
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()

    ok = graphene.Boolean()
    user = graphene.Field(UserNode)

    @classmethod
    def mutate_and_get_payload(cls, input, context, info):
        model = django.contrib.auth.get_user_model()

        email = input.pop('email')
        username = input.pop('username', email)
        password = input.pop('password')

        user = model.objects.create_user(username, email, password, **input)
        user.is_current_user = True

        return RegisterUser(ok=True, user=user)

class LoginUser(relay.ClientIDMutation):
    class Input:
        username = graphene.String()
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()
    user = graphene.Field(UserNode)

    @classmethod
    def mutate_and_get_payload(cls, input, context, info):
        model = django.contrib.auth.get_user_model()

        params = {
            model.USERNAME_FIELD: input.get(model.USERNAME_FIELD, input.get('email')),
            'password': input.get('password')
        }

        user = django.contrib.auth.authenticate(**params)

        if user:
            user.is_current_user = True
            return LoginUser(ok=True, user=user)
        else:
            return LoginUser(ok=False, user=None)

class ResetPasswordRequest(relay.ClientIDMutation):
    class Input:
        email = graphene.String(required=True)

    ok = graphene.Boolean()

    @classmethod
    def mutate_and_get_payload(cls, input, context, info):
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
        Model = django.contrib.auth.get_user_model()

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

class UpdateUser(relay.ClientIDMutation):
    class Input:
        username = graphene.String()
        email = graphene.String()
        password = graphene.String()
        current_password = graphene.String()
        first_name = graphene.String()
        last_name = graphene.String()

    ok = graphene.Boolean()
    result = graphene.Field(UserNode)

    @classmethod
    def mutate_and_get_payload(cls, input, context, info):
        Model = django.contrib.auth.get_user_model()
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
    user = graphene.Field(UserNode)
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
