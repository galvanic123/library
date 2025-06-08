from django.shortcuts import get_object_or_404, redirect
from .models import Author, Book
from django.views.generic import ListView, DetailView, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .forms import AuthorForm, BookForm
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseForbidden
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache
from .services import BookService


class ReviewBookView(LoginRequiredMixin, View):
    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)

        if not request.user.has_perm('Library.can_review_book'):
            return HttpResponseForbidden('У вас нет права для рецензирования книги')

        book.review = request.POST.get('review')
        book.save()

        return redirect('library:book_detail', pk=book_id)


class RecommendBookView(LoginRequiredMixin, View):
    def post(self, request, book_id):
        book = get_object_or_404(Book, id=book_id)

        if not request.user.has_perm('Library.can_recommend_book'):
            return HttpResponseForbidden('У вас нет права для рекомендации книги')

        book.recommend = request.POST.get('review')
        book.save()

        return redirect('library:book_detail', pk=book_id)


class AuthorListView(ListView):
    model = Author
    template_name = 'library/authors_list.html'
    context_object_name = 'authors'

    def get_queryset(self):
        queryset = cache.get('authors_queryset')
        if not queryset:
            queryset = super().get_queryset()
            cache.set('authors_queryset', queryset, 60 * 15)
        return queryset


@method_decorator(cache_page(60 * 15), name='dispatch')
class AuthorCreateView(CreateView):
    model = Author
    form_class = AuthorForm
    template_name = 'library/author_form.html'
    success_url = reverse_lazy('library:authors_list')


@method_decorator(cache_page(60 * 15), name='dispatch')
class AuthorUpdateView(UpdateView):
    model = Author
    form_class = AuthorForm
    template_name = 'library/author_form.html'
    success_url = reverse_lazy('library:authors_list')


@method_decorator(cache_page(60 * 15), name='dispatch')
class BooksListView(LoginRequiredMixin, ListView):
    model = Book
    template_name = 'library/books_list.html'
    context_object_name = 'books'
    # permission_required = 'library.view_book'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(publication_date__year__gt=1800)


class BookCreateView(LoginRequiredMixin, CreateView):
    model = Book
    fields = ['title', 'publication_date', 'author']
    template_name = 'library/book_form.html'
    success_url = reverse_lazy('library:books_list')
    permission_required = 'library.add_book'


@method_decorator(cache_page(60 * 15), name='dispatch')
class BookDetailView(LoginRequiredMixin, DetailView):
    model = Book
    template_name = 'library/book_detail.html'
    context_object_name = 'book'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # print(context)
        context['author_books_count'] = Book.objects.filter(author=self.object.author).count()
        # print(context)
        book_id = self.object.id
        context['average_rating'] = BookService.calculate_average_rating(book_id)
        context['is_popular'] = BookService.is_popular(book_id)

        return context


class BookUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    # fields = ['title', 'publication_date', 'author']
    template_name = 'library/book_form.html'
    success_url = reverse_lazy('library:books_list')
    permission_required = 'library.change_book'


class BookDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Book
    template_name = 'library/book_confirm_delete.html'
    success_url = reverse_lazy('library:books_list')
    permission_required = 'library.delete_book'


# def books_list(request):
#     books = Book.objects.all()
#     context = {'books': books}
#     return render(request, 'library/books_list.html', context)
#
# def book_detail(request, book_id):
#     book = Book.objects.get(id=book_id)
#     context = {'book': book}
#     return render(request, 'library/book_detail.html', context)
