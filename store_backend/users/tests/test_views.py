
import logging
import json

from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework import status

from plugins.models import PluginMeta, PluginMetaStar


class UserViewTests(TestCase):
    """
    Generic user view tests' setup and tearDown
    """

    def setUp(self):
        # avoid cluttered console output (for instance logging all the http requests)
        logging.disable(logging.WARNING)

        self.content_type = 'application/vnd.collection+json'
        self.username = 'cube'
        self.password = 'cubepass'
        self.email = 'dev@babymri.org'

    def tearDown(self):
        # re-enable logging
        logging.disable(logging.NOTSET)


class UserCreateViewTests(UserViewTests):
    """
    Test the user-create view
    """

    def setUp(self):
        super(UserCreateViewTests, self).setUp()
        self.create_url = reverse("user-create")
        self.post = json.dumps(
            {"template": {"data": [{"name": "username", "value": self.username},
                                   {"name": "password", "value": self.password},
                                   {"name": "email", "value": self.email}]}})

    def test_user_create_success(self):
        response = self.client.post(self.create_url, data=self.post,
                                    content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], self.username)
        self.assertEqual(response.data["email"], self.email)

    def test_user_create_failure_already_exists(self):
        User.objects.create_user(username=self.username,
                                 email=self.email,
                                 password=self.password)
        response = self.client.post(self.create_url, data=self.post,
                                    content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_create_failure_bad_password(self):
        post = json.dumps(
            {"template": {"data": [{"name": "username", "value": "new_user"},
                                   {"name": "email", "value": self.email},
                                   {"name": "password", "value": "small"}]}})
        response = self.client.post(self.create_url, data=post,
                                    content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserDetailViewTests(UserViewTests):
    """
    Test the user-detail view
    """

    def setUp(self):
        super(UserDetailViewTests, self).setUp()
        user = User.objects.create_user(username=self.username,
                                        email=self.email,
                                        password=self.password)
        self.read_update_url = reverse("user-detail", kwargs={"pk": user.id})
        self.put = json.dumps({
            "template": {"data": [{"name": "password", "value": "updated_pass"},
                                  {"name": "email", "value": "dev1@babymri.org"}]}})

    def test_user_detail_success(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.read_update_url)
        self.assertContains(response, self.username)
        self.assertContains(response, self.email)

    def test_user_detail_failure_unauthenticated(self):
        response = self.client.get(self.read_update_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_update_success(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.put(self.read_update_url, data=self.put,
                                   content_type=self.content_type)
        self.assertContains(response, self.username)
        self.assertContains(response, "dev1@babymri.org")

    def test_user_update_failure_unauthenticated(self):
        response = self.client.put(self.read_update_url, data=self.put,
                                   content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_update_failure_access_denied(self):
        User.objects.create_user(username="other_username", email="dev2@babymri.org",
                                 password="other_password")
        self.client.login(username="other_username", password="other_password")
        response = self.client.put(self.read_update_url, data=self.put,
                                   content_type=self.content_type)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserOwnedPluginMetaListViewTests(UserViewTests):
    """
    Test the user-ownedpluginmeta-list view.
    """

    def setUp(self):
        super(UserOwnedPluginMetaListViewTests, self).setUp()

        user = User.objects.create_user(username=self.username, email=self.email,
                                        password=self.password)
        self.list_url = reverse("user-ownedpluginmeta-list", kwargs={"pk": user.id})

        # create a plugin meta
        self.plugin_name = 'simplefsapp'
        (meta, tf) = PluginMeta.objects.get_or_create(name=self.plugin_name,
                                                      type='fs',
                                                      public_repo='http://gitgub.com')
        meta.owner.set([user])

    def test_plugin_parameter_list_success_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.list_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_parameter_list_failure_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserFavoritePluginMetaListViewTests(UserViewTests):
    """
    Test the user-favoritepluginmeta-list view.
    """

    def setUp(self):
        super(UserFavoritePluginMetaListViewTests, self).setUp()

        user = User.objects.create_user(username=self.username, email=self.email,
                                        password=self.password)
        self.list_url = reverse("user-favoritepluginmeta-list", kwargs={"pk": user.id})

        # create a plugin meta
        self.plugin_name = 'simplefsapp'
        (meta, tf) = PluginMeta.objects.get_or_create(name=self.plugin_name,
                                                      type='fs',
                                                      public_repo='http://gitgub.com')
        meta.owner.set([user])

    def test_plugin_parameter_list_success_authenticated(self):
        user = User.objects.get(username=self.username)
        meta = PluginMeta.objects.get(name=self.plugin_name)
        PluginMetaStar.objects.get_or_create(user=user, meta=meta)
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(self.list_url)
        self.assertContains(response, self.plugin_name)

    def test_plugin_parameter_list_failure_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
