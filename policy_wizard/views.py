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
from .utils import role_identifier, validate_request
from .forms import PolicyTemplateForm, NewPolicyForm
from django.views.decorators.clickjacking import xframe_options_exempt
from .decorators import require_role_admin


@csrf_exempt
@xframe_options_exempt #Allows rendering in Canvas frame
def process_lti_launch_request_view(request):
    '''
    Processes launch request and redirects to appropriate view depending on the role of the launcher
    '''

    #True if this is a typical lti launch. False if not.
    is_basic_lti_launch = request.method == 'POST' and request.POST.get(
        'lti_message_type') == 'basic-lti-launch-request'

    #True if this request is valid. False if not.
    request_is_valid = validate_request(request)

    if is_basic_lti_launch and request_is_valid: #if typical lti launch and request is valid ...

        #Store the context_id in the request's session attribute.
        #A 'context_id' represents a particular course.
        request.session['context_id'] = request.POST.get('context_id')

        #Figure out role of launcher and store the role in the request's session attribute
        request.session['role'] = role_identifier(request.POST.get('ext_roles'))

        #Store the 'lis_person_sourcedid', a unique identifier of the launcher, in the request's session attribute.
        #This is used later to indicate the author of a course policy.
        request.session['lis_person_sourcedid'] = request.POST.get('lis_person_sourcedid')

        #Using the role, e.g. 'Administrator', 'Instructor', or 'Student', determine route to take
        role = request.session['role']
        if role=='Administrator' or role=='Instructor':
            return redirect('policy_templates_list')
        elif role=='Student':
            return redirect('student_published_policy')
    else: #if not typical lti launch or if request is not valid ...
        raise PermissionDenied

@xframe_options_exempt
def policy_templates_list_view(request):
    '''
    Displays list of policy templates
    '''

    #Fetch role from session attribute. It should be either 'Administrator' or 'Instructor'.
    role = request.session['role']

    if role=='Instructor' or role=='Administrator':

        if role=='Instructor':
            try: #if a policy has already been published for this course ...
                #Get the published policy
                publishedPolicy = Policies.objects.get(context_id=request.session['context_id'])
                #Render the published policy
                return render(request, 'instructor_published_policy.html', {'publishedPolicy': publishedPolicy})
            except Policies.DoesNotExist: #If no such policy exists ...
                pass

        #Fetch each policy template from the `PolicyTemplates` table in the database and store as a variable
        written_work_policy_template = PolicyTemplates.objects.get(name="Collaboration Permitted: Written Work")
        problem_sets_policy_template = PolicyTemplates.objects.get(name="Collaboration Permitted: Problem Sets")
        collaboration_prohibited_policy_template = PolicyTemplates.objects.get(name="Collaboration Prohibited")
        custom_policy_template = PolicyTemplates.objects.get(name="Custom Policy")

        if role=='Administrator':
            #Django template to use
            template_to_use = 'admin_level_template_list.html'
        else: #role=='Instructor'
            # Django template to use
            template_to_use = 'instructor_level_template_list.html'

        #Render the policy templates
        return render(
            request,
            template_to_use,
            {
                'written_work_policy_template': written_work_policy_template,
                'problem_sets_policy_template': problem_sets_policy_template,
                'collaboration_prohibited_policy_template': collaboration_prohibited_policy_template,
                'custom_policy_template': custom_policy_template
            })

    else: #i.e. 'Student'
        raise PermissionDenied


@xframe_options_exempt
@require_role_admin
def admin_level_template_edit_view(request, pk):
    '''
    Presents the text editor to an administrator so they can edit and update a policy template
    '''

    templateToUpdate = get_object_or_404(PolicyTemplates, pk=pk)

    if request.method == 'POST':
        form = PolicyTemplateForm(request.POST)
        if form.is_valid():
            templateToUpdate.body = form.cleaned_data.get('body')
            templateToUpdate.save()
            return redirect('policy_templates_list')
    else:
        form = PolicyTemplateForm(initial={'body': templateToUpdate.body})
    return render(request, 'admin_level_template_edit.html', {'form': form})


@xframe_options_exempt
def instructor_level_policy_edit_view(request, pk):
    '''
    Presents the text editor to an instructor so they can edit and publish a policy
    '''
    role = request.session['role']

    if role == 'Instructor':
        policyTemplate = get_object_or_404(PolicyTemplates, pk=pk)

        if request.method == 'POST':
            form = NewPolicyForm(request.POST)
            if form.is_valid():
                finalPolicy = Policies.objects.create(
                    context_id=request.session['context_id'],
                    body=form.cleaned_data.get('body'),
                    related_template = policyTemplate,
                    published_by = request.session['lis_person_sourcedid'],
                    is_published = True,
                )

                return redirect('instructor_published_policy', pk=finalPolicy.pk)
        else:
            form = NewPolicyForm(initial={'body': policyTemplate.body})
        return render(request, 'instructor_level_policy_edit.html', {'policyTemplate': policyTemplate, 'form': form})
    else: #i.e. 'Administrator' or 'Student'
        raise PermissionDenied

@xframe_options_exempt
def instructor_published_policy(request, pk):
    '''
    Displays to the instructor the policy they just prepared
    '''
    role = request.session['role']

    if role == 'Instructor':
        publishedPolicy = Policies.objects.get(pk=pk)
        return render(request, 'instructor_published_policy.html', {'publishedPolicy': publishedPolicy})
    else: #i.e. 'Administrator' or 'Student'
        raise PermissionDenied

@xframe_options_exempt
def edit_published_policy(request, pk):
    '''
    Provides an instructor the capability to edit a policy they already published
    '''
    role = request.session['role']

    if role == 'Instructor':
        policyToEdit = Policies.objects.get(pk=pk)
        if request.method == 'POST':
            form = NewPolicyForm(request.POST)
            if form.is_valid():
                policyToEdit.body = form.cleaned_data.get('body')
                policyToEdit.save()
                return redirect('instructor_published_policy', pk=policyToEdit.pk)
        else:
            form = NewPolicyForm(initial={'body': policyToEdit.body})
        return render(request, 'instructor_level_policy_edit.html', {'policyTemplate': policyToEdit, 'form': form})
    else: #i.e. 'Administrator' or 'Student'
        raise PermissionDenied

@xframe_options_exempt
def instructor_delete_old_publish_new_view(request, pk):
    '''
    From the published policy page, this view enables an instructor to prepare a new course policy from
    the list of policy templates. The old published policy is deleted.
    '''
    role = request.session['role']

    if role == 'Instructor':
        #Delete old policy
        Policies.objects.filter(pk=pk).delete()
        #Redirect to list of templates
        return redirect('policy_templates_list')
    else: #i.e. 'Administrator' or 'Student'
        raise PermissionDenied

@xframe_options_exempt
def student_published_policy_view(request):
    '''
    Displays to the student the policy for the course, if one exists, and an appropriate message if one doesn't
    '''
    role = request.session['role']

    if role == 'Student':
        try:
            publishedPolicy = Policies.objects.get(context_id=request.session['context_id'])
        except ObjectDoesNotExist:
            return HttpResponse("There is no published academic integrity policy in record for this course.")

        return render(request, 'student_published_policy.html', {'publishedPolicy': publishedPolicy})
    else: #i.e. 'Administrator' or 'Instructor'
        raise PermissionDenied










