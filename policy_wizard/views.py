from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views.generic.edit import UpdateView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from .forms import NewPolicyForm
from .models import PolicyTemplates, Policies
from .middleware import role_identifier, validate_request, lti_launch_params_dict


# Create your views here.
@csrf_exempt
def process_lti_launch_request_view(request):

    is_basic_lti_launch = request.method == 'POST' and request.POST.get(
        'lti_message_type') == 'basic-lti-launch-request'

    request_is_valid = validate_request(request)

    if is_basic_lti_launch and request_is_valid:

        #store context_id in dictionary
        lti_launch_params_dict['context_id'] = request.POST.get('context_id')

        #Figure out role of launcher and path to take
        role = role_identifier(request.POST.get('ext_roles'))

        if role=='Instructor':
            return redirect('policy_templates_list', role='Instructor')
        elif role=='Student':
            return redirect('student_published_policy')
        elif role=='Administrator':
            return redirect('policy_templates_list', role='Administrator')
    else:
        raise PermissionDenied

def policy_templates_list_view(request, role):

    written_work_policy_template = PolicyTemplates.objects.get(name="Collaboration Permitted: Written Work")
    problem_sets_policy_template = PolicyTemplates.objects.get(name="Collaboration Permitted: Problem Sets")
    collaboration_prohibited_policy_template = PolicyTemplates.objects.get(name="Collaboration Prohibited")
    custom_policy_template = PolicyTemplates.objects.get(name="Custom Policy")

    if role=='Administrator':
        template_to_use = 'admin_level_template_list.html'
    else: #role=='Instructor'
        template_to_use = 'instructor_level_template_list.html'

    return render(
        request,
        template_to_use,
        {
            'written_work_policy_template': written_work_policy_template,
            'problem_sets_policy_template': problem_sets_policy_template,
            'collaboration_prohibited_policy_template': collaboration_prohibited_policy_template,
            'custom_policy_template': custom_policy_template
        })

class AdminLevelTemplateUpdateView(UpdateView):
    model = PolicyTemplates
    #fields = ['name', 'body']
    fields = ['body']
    template_name = 'admin_level_template_edit.html'
    success_url = reverse_lazy('policy_templates_list', kwargs={'role': 'Administrator'})

def instructor_level_policy_edit_view(request, pk):
    policyTemplate = get_object_or_404(PolicyTemplates, pk=pk)

    #Arbitrary user selection
    user = User.objects.first()

    if request.method == 'POST':
        form = NewPolicyForm(request.POST)
        if form.is_valid():
            finalPolicy = Policies.objects.create(
                context_id=lti_launch_params_dict['context_id'],
                body=form.cleaned_data.get('body'),
                related_template = policyTemplate,
                published_by = user,
                is_published = True,
            )

            return redirect('instructor_published_policy', pk=finalPolicy.pk)
    else:
        form = NewPolicyForm(initial={'body': policyTemplate.body})
    return render(request, 'instructor_level_policy_edit.html', {'policyTemplate': policyTemplate, 'form': form})

def instructor_published_policy(request, pk):
    publishedPolicy = Policies.objects.get(pk=pk)
    return render(request, 'instructor_published_policy.html', {'publishedPolicy': publishedPolicy})

def student_published_policy_view(request):
    try:
        publishedPolicy = Policies.objects.get(context_id=lti_launch_params_dict['context_id'])
    except ObjectDoesNotExist:
        return HttpResponse("There is no published academic integrity policy in record for this course.")

    return render(request, 'student_published_policy.html', {'publishedPolicy': publishedPolicy})

def edit_published_policy(request, pk):
    policyToEdit = Policies.objects.get(pk=pk)
    if request.method == 'POST':
        form = NewPolicyForm(request.POST)
        if form.is_valid():
            policyToEdit.body = form.cleaned_data.get('body')
            policyToEdit.save()
            return redirect('instructor_published_policy', pk=policyToEdit.pk)
    else:
        form = NewPolicyForm(initial={'body': policyToEdit.body})
    return render(request, 'instructor_level_policy_edit.html', {'policyTemplate': policyToEdit, 'form': form}) #body=123 -> 12345






