from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='post_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
        )
        cls.post_url = f'/posts/{cls.post.id}/'
        cls.group_url = f'/group/{cls.group.slug}/'
        cls.profile_url = f'/profile/{cls.user.username}/'
        cls.templates_urls_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.user.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            f'/posts/{cls.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = PostURLTests.user
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)
        self.user_not_author = User.objects.create(username='Test_not_author')
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.user_not_author)

    def test_urls_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        urls_names = [
            '/',
            self.group_url,
            self.profile_url,
            self.post_url,
        ]
        for address in urls_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_exists_at_desired_location_not_author(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client_not_author.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_exists_at_desired_location_guest(self):
        """Страница /create/ недоступна неавторизованному пользователю."""
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_postid_edit_url_exists_at_desired_location_for_author(self):
        """Страница /post_id/edit/ доступна автору."""
        response = self.authorized_client_author.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_postid_edit_url_exists_at_desired_location_for_n0t_author(self):
        """
        Страница /post_id/edit/ недоступна другому авторизованому пользователю.
        """
        response = self.authorized_client_not_author.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_postid_edit_url_exists_at_desired_location_for_guest(self):
        """Страница /post_id/edit/ недоступна другому гостю."""
        response = self.guest_client.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting_page(self):
        """Выдача ошибки 404 несуществующему URL."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.templates_urls_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_comment_url_exists_at_desired_location_for_guest(self):
        """Страница /post_id/comment/ недоступна другому гостю."""
        response = self.guest_client.get('/posts/1/comment/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_error_page_404_uses_correct_template(self):
        """Несуществующий URL-адрес использует шаблон core/404.html."""
        response = self.guest_client.get('/nonexist-page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
