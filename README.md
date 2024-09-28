# django_fileupload
複数ファイルのアップロードのサンプル。

# 実行
```
git clone https://github.com/circleratio/django_fileupload
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
http://127.0.0.1:8000/file_upload/

# 解説
## upload/settings.py

アップロード先の定義を追加。
BASE_DIRを参照しているので、BASE_DIRの定義より後に記述すること。

```
import os

UPLOAD_ROOT = os.path.join(BASE_DIR, 'uploads')
```

アプリを追加。
```
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'file_upload', # add
]
```

## URLconf (upload/urls.py)
```
from django.urls import path

from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('new/', views.MultipleFileUploadPage.as_view(), name = 'new'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/<int:file_id>/', views.FileDownload, name='download'),
]

```

## モデル(file_upload/models.py)
```
from django.db import models
from django.utils import timezone

class Workflow(models.Model):
    owner = models.CharField(max_length=200)

    files = models.CharField(max_length=1000)
```

## 管理ツールの設定(file_upload/admin.py)
モデルを管理ツールに登録。
```
from django.contrib import admin
from .models import Workflow

admin.site.register(Workflow)
```

## フォーム(file_upload/forms.py)
```
from django.forms import ModelForm
from django import forms

from .models import Workflow

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class WorkflowForm(forms.Form):
    owner = forms.CharField(max_length=200)

    files = MultipleFileField(label='複数のファイルを選択', required=False)
```

cleaned_data とは「あるオブジェクトの属性値の中で、バリデーションをクリアしたものだけを辞書形式で格納したもの」である。

## ビュー(file_upload/views.py)
```
from django.http import HttpResponse
from django.template import loader
from django.views import generic
from django.views.generic import FormView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.conf import settings
import os
import json
import shutil
import mimetypes

from .models import Workflow
from .forms import WorkflowForm

class DetailView(generic.DetailView):
    model = Workflow
    template_name = 'file_upload/detail.html'

class IndexView(generic.ListView):
    template_name = "file_upload/index.html"
    context_object_name = "workflow_list"

    def get_queryset(self):
        """Return the approval requsts by myself."""
        return Workflow.objects.filter()

    def get_context_data(self):
        ctx = super().get_context_data()
        ctx['tab_selection'] = 'index'
        return ctx

class MultipleFileUploadPage(FormView):
    template_name = 'file_upload/upload.html'
    form_class = WorkflowForm
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        files = form.cleaned_data['files']
        files_dict = {}

        wf = Workflow()
        tmp_id = id(wf)
        from_dir = f'{settings.UPLOAD_ROOT}/{tmp_id}'
        os.makedirs(from_dir, exist_ok=True)

        wf.owner = form.cleaned_data['owner']
        i = 0
        for f in files:
            self.handle_uploaded_file(f, from_dir, str(i))
            files_dict[str(i)] = f.name
            wf.files = json.dumps(files_dict)
            i += 1
        wf.save()

        to_dir = f'{settings.UPLOAD_ROOT}/{wf.id}'
        os.rename(from_dir, to_dir)

        return super().form_valid(form)

    def handle_uploaded_file(self, f, dir, file_name):

        with open(dir + '/' + file_name, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

def FileDownload(request, pk, file_id):
    file_path = f'{settings.UPLOAD_ROOT}/{pk}/{file_id}'

    if not os.path.isfile(file_path):
        return HttpResponse(f'{pk}:{file_id} is not found.')

    wf = Workflow.objects.get(id=pk)
    d = json.loads(wf.files)
    name = d[str(file_id)]
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type=mimetypes.guess_type(name)[0] or 'application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename={name}'

    return(response)
```

## テンプレートタグ(templatetags/file_upload_extra.py)
準備。
```
mkdir touchtemplatetags
touch templatetags/__init__.py
```

```
from django import template
import json

register = template.Library()

def file_format(value):
    result = ''
    d = json.loads(value)

    result += '<ul>'
    for k in d.keys():
        result += f'<li><a href="{k}">{d[k]}</a></li>'
    result += '</ul>'

    return(result)

register.filter('file_format', file_format)
```

## テンプレート(templates/file_upload/upload.html)
HTMLのformタグではenctype="multipart/form-data"をセットする必要がある。

```
{% extends 'base.html' %}

{% block title %}
New Approval Request
{% endblock %}

{% block contents %}
<form method="POST" enctype="multipart/form-data">
  {% csrf_token %}
  {{ form.as_p }}
  <button type="submit">申請</button>
</form>
{% endblock %}
```

## テンプレート(file_upload/templates/file_upload/index.html)
```
{% extends 'base.html' %}

{% block title %}
Workflows
{% endblock %}

{% block contents %}
<a href="/file_upload/new/">New</a>

{% if workflow_list %}
  <table class="table table-striped">
  {% for workflow in workflow_list %}
      <tr><td><a href="/file_upload/{{ workflow.id }}/">{{ workflow.id }}</a></td><td>{{ workflow.owner }}</td></tr>
  {% endfor %}
  </table>
{% else %}
  <p>No workflow is available.</p>
{% endif %}

{% endblock %}
```

## テンプレート(file_upload/templates/file_upload/detail.html)
```
{% extends 'base.html' %}
{% load file_upload_extra %}

{% block title %}
Approve Details
{% endblock %}

{% block contents %}
{% if workflow %}
  <table>
    <tr><td>承認者</td><td>{{ workflow.owner }}</td></tr>
    <tr><td>ファイル</td><td>{% autoescape off %}{{ workflow.files|file_format }}{% endautoescape %}</td></tr>
  </table>
{% else %}
  <p>No workflow is available.</p>
{% endif %}
{% endblock %}
```

## テンプレート(templates/base.html)
```
{% load static %}
<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <title>{% block title %}{% endblock %}</title>
</head>
<body>
  {% block contents %}{% endblock %}
</body>
</html>
```

# 参考
- https://ryougodesign.com/blog/django-formview-multiple-file-upload/
- https://docs.djangoproject.com/en/5.0/topics/http/file-uploads/

