from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
from .utils import paginate

User = get_user_model()


def index(request):
    context = paginate(Post.objects.all(), request)
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'group': group,
        'posts': posts,
    }
    context.update(paginate(posts, request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_count = author.posts.count()
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author,).exists()
    profile = author
    context = {
        'author': author,
        'following': following,
        'profile': profile,
        'post_count': post_count,
    }
    context.update(paginate(author.posts.all(), request))
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post_id_detail = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments_list = post_id_detail.comments.all()
    context = {
        'post': post_id_detail,
        'form': form,
        'comments': comments_list,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    return render(request, 'posts/create_post.html',
                  {'form': form})


@login_required
def post_edit(request, post_id):
    edit_post = get_object_or_404(Post, id=post_id)
    if request.user != edit_post.author:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=edit_post,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html',
                  {'form': form, 'is_edit': True})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'comment': comment,
    }
    return render(request, 'posts:post_detail',
                  {'form': form}, context)


@login_required
def follow_index(request):
    context = paginate(Post.objects.filter(
        author__following__user=request.user), request)
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user == author or Follow.objects.filter(
            user=request.user, author=author).exists():
        return redirect(reverse('posts:profile', args=[username]))
    Follow.objects.get_or_create(user=request.user, author=author)
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=author)
