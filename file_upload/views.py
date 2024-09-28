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
