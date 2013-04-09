from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.utils import override_settings

import mock

from .auth.backends import CombinedAuthBackend
from ..core.models import Image, Pin
from .models import User


class CreateUserTest(TestCase):
    def test_create_post(self):
        data = {
            'username': 'jdoe',
            'email': 'jdoe@example.com',
            'password': 'password'
        }
        response = self.client.post(reverse('users:register'), data=data)
        self.assertRedirects(response, reverse('core:recent-pins'))
        self.assertIn('_auth_user_id', self.client.session)

    @override_settings(ALLOW_NEW_REGISTRATIONS=False)
    def test_create_post_not_allowed(self):
        response = self.client.get(reverse('users:register'))
        self.assertRedirects(response, reverse('core:recent-pins'))


class LogoutViewTest(TestCase):
    def setUp(self):
        User.objects.create_user(username='jdoe', password='password')
        self.client.login(username='jdoe', password='password')

    def test_logout_view(self):
        response = self.client.get(reverse('users:logout'))
        self.assertRedirects(response, reverse('core:recent-pins'))
