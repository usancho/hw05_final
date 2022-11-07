from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post

from ..models import Follow, Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='post_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст пост №1.',
            group=cls.group,
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = PostPagesTests.user
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)
        self.user_not_author = User.objects.create(username='Test_not_author')
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.user_not_author)

    def test_pages_uses_correct_template(self):
        '''URL-адрес использует соответствующий шаблон.'''
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{self.group.slug}'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': f'{self.user}'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.id}'}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        '''Шаблон index сформирован с правильным контекстом.'''
        response = self.authorized_client_author.get(reverse('posts:index'))
        self.assertIn(self.post, response.context['page_obj'])
        first_object = response.context['page_obj'][0]
        first_text = first_object.text
        first_author = first_object.author
        self.assertEqual(first_text, self.post.text)
        self.assertEqual(first_author, self.user)

    def test_group_posts_page_show_correct_context(self):
        '''Шаблон group_list сформирован с правильным контекстом.'''
        response = self.authorized_client_author.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertIn(self.post, response.context['page_obj'])
        first_object = response.context['page_obj'][0]
        first_author = first_object.author
        first_text = first_object.text
        first_group = first_object.group
        self.assertEqual(first_author, self.user)
        self.assertEqual(first_text, self.post.text)
        self.assertEqual(first_group, self.post.group)

    def test_profile_page_show_correct_context(self):
        '''Шаблон profile сформирован с правильным контекстом.'''
        response = self.authorized_client_author.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertIn(self.post, response.context['page_obj'])
        first_object = response.context['page_obj'][0]
        first_author = first_object.author
        first_text = first_object.text
        first_group = first_object.group
        self.assertEqual(first_author, self.user)
        self.assertEqual(first_text, self.post.text)
        self.assertEqual(first_group, self.post.group)

    def test_post_detail_page_show_correct_context(self):
        '''Шаблон post_detail сформирован с правильным контекстом.'''
        response = self.authorized_client_author.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(response.context.get('post').id, self.post.id)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get(
            'post').author, self.post.author)
        self.assertEqual(response.context.get(
            'post').group, self.post.group)

    def test_post_create_page_show_correct_context(self):
        '''Шаблон create_post сформирован с правильным контекстом.'''
        response = self.authorized_client_author.get(
            reverse('posts:post_create'))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        '''Шаблон post_edit сформирован с правильным контекстом.'''
        response = self.authorized_client_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='post_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы',
        )
        Post.objects.bulk_create(
            [
                Post(
                    author=cls.user,
                    text=f'Тестовый текст поста #{post_number}',
                    group=cls.group,
                )
                for post_number in range(1, 16)
            ]
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = PaginatorViewsTest.user
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user)
        self.user_not_author = User.objects.create(username='Test_not_author')
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.user_not_author)

    def test_index_first_page_contains_ten_records(self):
        '''Пагинатор index работает корректно с 1 страницей.'''
        response = self.authorized_client_author.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_index_second_page_contains_five_records(self):
        '''Пагинатор index работает корректно со 2 страницей.'''
        response = self.authorized_client_author.get(
            reverse('posts:index') + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 5)

    def test_group_posts_first_page_contains_ten_records(self):
        '''Пагинатор group_posts работает корректно с 1 страницей.'''
        response = self.authorized_client_author.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_group_posts_second_page_contains_five_records(self):
        '''Пагинатор group_posts работает корректно со 2 страницей.'''
        response = self.authorized_client_author.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 5)

    def test_profile_first_page_contains_ten_records(self):
        '''Пагинатор profile работает корректно с 1 страницей.'''
        response = self.authorized_client_author.get(reverse(
            'posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_profile_second_page_contains_five_records(self):
        '''Пагинатор profile работает корректно со 2 страницей.'''
        response = self.authorized_client_author.get(reverse(
            'posts:profile', kwargs={'username': self.user}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 5)


class CacheViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='post_author')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст пост №1.',
        )

    def setUp(self):
        self.user = CacheViewTests.user
        self.client = Client()
        self.client.force_login(self.user)

    def test_post_in_cache_first(self):
        '''Тест кэша №1.'''
        response_1 = self.client.get(reverse('posts:index')).content
        Post.objects.all().delete
        response_2 = self.client.get(reverse('posts:index')).content
        self.assertEqual(response_1, response_2)

    def test_post_in_cache_second(self):
        '''Тест кэша №2.'''
        response_1 = self.client.get(reverse('posts:index')).content
        Post.objects.all().delete
        cache.clear()
        response_2 = self.client.get(reverse('posts:index')).content
        self.assertNotEqual(response_1, response_2)


class FollowTests(TestCase):
    def setUp(self):
        self.authorized_client_follower = Client()
        self.authorized_client_not_follower = Client()
        self.authorized_client_following = Client()
        self.user_follower = User.objects.create_user(
            username='follower',
            email='follower_mail@yandex.ru',
            password='1234',
        )
        self.user_following = User.objects.create_user(
            username='following',
            email='following_mail@yandex.ru',
            password='1234',
        )
        self.user_not_follower = User.objects.create_user(
            username='not_follower',
            email='not_follower@yandex.ru',
            password='1234',
        )
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовый текст'
        )
        self.authorized_client_follower.force_login(self.user_follower)
        self.authorized_client_following.force_login(self.user_following)
        self.authorized_client_not_follower.force_login(self.user_not_follower)

    def test_follow(self):
        '''
        Авторизованный пользователь может подписываться
        на других пользователей.
        '''
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        self.authorized_client_follower.get(
            reverse('posts:profile',
                    kwargs={'username':
                            self.user_follower.username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        '''
        Авторизованный пользователь может удалять пользователей из подписок.
        '''
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        '''
        self.authorized_client_follower.get(
            reverse('posts:profile_follow',
                    kwargs={'username':
                            self.user_following.username}))
        '''
        self.authorized_client_follower.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username':
                            self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_new_following_post_added_in_followers_list(self):
        '''Новая запись пользователя появляется в ленте подписчиков.'''
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.authorized_client_follower.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_new_following_post_not_added_in_followers_list(self):
        '''
        Новая запись пользователя не появляется в ленте пользователей,
        которые не подписны на автора.
        '''
        response = self.authorized_client_not_follower.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), 0)
