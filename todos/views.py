from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from .models import Todo
from django.http import JsonResponse
import json


class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'todos/index.html'
    context_object_name = 'todo_all'
    login_url = '/home/entry/'

    def get_queryset(self):
        user = self.request.user
        return Todo.objects.filter(user=user).order_by('isCompleted', '-created_at')


@require_POST
def add(request):
    response_data = {'success': False}

    try:
        data = json.loads(request.body)
        title = data['title']
        new_todo = Todo.objects.create(user=request.user, title=title)
        response_data = {
            'id': new_todo.id,
            'title': new_todo.title,
            'created_at': new_todo.created_at.isoformat(),
            'success': True,
        }
    except Exception as e:
        response_data['error'] = str(e)

    return JsonResponse(response_data)


@require_POST
def archive(request, todo_id):
    try:
        todo = Todo.objects.get(id=todo_id, user=request.user)
        todo.hide = True
        todo.save()
        return JsonResponse({'success': True})
    except Todo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Задача не найдена.'})


@require_POST
def update(request, todo_id):
    todo = get_object_or_404(Todo, pk=todo_id)
    try:
        # Принимаем и обрабатываем JSON данные.
        data = json.loads(request.body)
        is_completed = data.get('isCompleted', False)

        # Устанавливаем новое значение и сохраняем объект.
        todo.isCompleted = is_completed
        todo.save()

        # Возвращаем успешный ответ.
        return JsonResponse({'success': True, 'isCompleted': is_completed})

    except ValidationError as e:
        # Обработка ошибки валидации данных.
        return JsonResponse({'success': False, 'error': str(e)})
