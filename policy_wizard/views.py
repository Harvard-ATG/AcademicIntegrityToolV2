import logging

from pylti.common import LTIException

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from .models import PolicyTemplates, Policies
from .utils import role_identifier, validate_request
from .forms import PolicyTemplateForm, NewPolicyForm
from django.views.decorators.clickjacking import xframe_options_exempt
from .decorators import require_role_administrator, require_role_instructor, require_role_student
from . import roles
logger = logging.getLogger(__name__)

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
    try:
        request_is_valid = validate_request(request)
    except LTIException: # oauth session may have timed out
        return redirect('refresh_browser_view')

    if is_basic_lti_launch and request_is_valid: #if typical lti launch and request is valid ...

        #Store the context_id in the request's session attribute.
        #A 'context_id' is a unique opaque identifier for the context from which this wizard is launched.
        #Thus, if the wizard is launched from a canvas course site, the context_id will point to the canvas
        #course site.
        request.session['context_id'] = request.POST.get('context_id')

        # Store the custom_canvas_course_id in the request's session attribute.
        # A custom_canvas_course_id is a unique identifier for a canvas course site.
        # You can find the Canvas course associated with it more easily than you can with a course's context_id.
        request.session['course_id'] = request.POST.get('custom_canvas_course_id')

        #Figure out role of launcher and store the role in the request's session attribute
        request.session['role'] = role_identifier(request.POST.get('ext_roles'))

        #Store the 'lis_person_sourcedid', a unique identifier of the launcher, in the request's session attribute.
        #This is used later to indicate the author of a course policy.
        request.session['lis_person_sourcedid'] = request.POST.get('lis_person_sourcedid')

        #Using the role, e.g. 'Administrator', 'Instructor', or 'Student', determine route to take
        role = request.session.get('role')
        if role==roles.ADMINISTRATOR or role==roles.INSTRUCTOR:
            return redirect('policy_templates_list')
        elif role==roles.STUDENT:
            return redirect('student_published_policy')
    else: #if not typical lti launch or if request is not valid ...
        raise PermissionDenied

@xframe_options_exempt
def refresh_browser_view(request):
    return render(request, 'refresh.html', {})

@xframe_options_exempt
def policy_templates_list_view(request):
    '''
    Displays list of policy templates
    '''

    #Fetch role from session attribute. It should be either 'Administrator' or 'Instructor'.
    role = request.session.get('role')

    if role==roles.INSTRUCTOR or role==roles.ADMINISTRATOR:

        if role==roles.INSTRUCTOR:
            try: #If there is an active published policy for this course, get it. (Only 1 active published policy expected.)
                publishedPolicy = Policies.objects.get(course_id=request.session['course_id'], is_active=True)
                # Render the active published policy
                return render(request, 'instructor_published_policy.html', {'publishedPolicy': publishedPolicy})
            except Policies.MultipleObjectsReturned: #If multiple active published policies exist (which should never happen)...
                return HttpResponseServerError("Something went wrong #@$%. Contact the site admin at " + settings.SECURE_SETTINGS['help_email_address'])
            except Policies.DoesNotExist: #If no active published policy exists ...
                pass


        #Fetch each policy template from the `PolicyTemplates` table in the database and store as a variable
        written_work_policy_template = PolicyTemplates.objects.get(name="Collaboration Permitted: Written Work")
        problem_sets_policy_template = PolicyTemplates.objects.get(name="Collaboration Permitted: Problem Sets")
        collaboration_prohibited_policy_template = PolicyTemplates.objects.get(name="Collaboration Prohibited")
        custom_policy_template = PolicyTemplates.objects.get(name="Custom Policy")

        if role==roles.ADMINISTRATOR:
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
@require_role_administrator
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
            return redirect('admin_updated_template', pk=templateToUpdate.pk)
    else:
        form = PolicyTemplateForm(initial={'body': templateToUpdate.body})
    return render(request, 'admin_level_template_edit.html', {'form': form, 'templateToUpdate': templateToUpdate})

@xframe_options_exempt
@require_role_administrator
def admin_updated_template_view(request, pk):
    '''
    Present the updated template to the administrator
    '''
    updatedTemplate = PolicyTemplates.objects.get(pk=pk)
    return render(request, 'admin_updated_template.html', {'updatedTemplate': updatedTemplate})

@xframe_options_exempt
@require_role_administrator
def admin_edit_updated_template_view(request, pk):
    '''
    Present administrator with editor so they can edit a template they just updated
    '''
    templateToUpdate = get_object_or_404(PolicyTemplates, pk=pk)

    if request.method == 'POST':
        form = PolicyTemplateForm(request.POST)
        if form.is_valid():
            templateToUpdate.body = form.cleaned_data.get('body')
            templateToUpdate.save()
            return redirect('admin_updated_template', pk=templateToUpdate.pk)
    else:
        form = PolicyTemplateForm(initial={'body': templateToUpdate.body})
    return render(request, 'admin_edit_updated_template.html', {'form': form, 'templateToUpdate': templateToUpdate})

@xframe_options_exempt
@require_role_instructor
def instructor_level_policy_edit_view(request, pk):
    '''
    Presents the text editor to an instructor so they can edit and publish a policy
    '''

    policyTemplate = get_object_or_404(PolicyTemplates, pk=pk)

    if request.method == 'POST':
        form = NewPolicyForm(request.POST)
        if form.is_valid():
            finalPolicy = Policies.objects.create(
                course_id=request.session['course_id'],
                context_id=request.session['context_id'],
                body=form.cleaned_data.get('body'),
                related_template = policyTemplate,
                published_by = request.session['lis_person_sourcedid'],
                is_published = True,
                is_active=True,
            )

            return redirect('instructor_published_policy', pk=finalPolicy.pk)
    else:
        form = NewPolicyForm(initial={'body': policyTemplate.body})
    return render(request, 'instructor_level_policy_edit.html', {'policyTemplate': policyTemplate, 'form': form})

@xframe_options_exempt
@require_role_instructor
def instructor_published_policy(request, pk):
    '''
    Displays to the instructor the policy they just prepared
    '''
    publishedPolicy = Policies.objects.get(pk=pk)
    return render(request, 'instructor_published_policy.html', {'publishedPolicy': publishedPolicy})

@xframe_options_exempt
@require_role_instructor
def edit_published_policy(request, pk):
    '''
    Provides an instructor the capability to edit a policy they already published
    '''
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

@xframe_options_exempt
@require_role_instructor
def instructor_inactivate_old_prepare_new_view(request, pk):
    '''
    From the published policy page, this view enables an instructor to inactivate an already published policy and prepare
    a new course policy from the list of policy templates.
    '''
    policyToEdit = Policies.objects.get(pk=pk)
    #Inactivate old policy
    policyToEdit.is_active = False
    policyToEdit.save()
    #Redirect to list of templates
    return redirect('policy_templates_list')

@xframe_options_exempt
@require_role_student
def student_published_policy_view(request):
    '''
    Displays to the student the policy for the course if one exists
    '''
    try:
        # If an active published policy exists (Only 1 expected)...
        publishedPolicy = Policies.objects.get(course_id=request.session['course_id'], is_active=True)
        # Render the policy
        return render(request, 'student_published_policy.html', {'publishedPolicy': publishedPolicy})
    except Policies.DoesNotExist: #If no active published policy exists ...
        return HttpResponse("There is no published academic integrity policy in record for this course.")
    except Policies.MultipleObjectsReturned: #If multiple active published policies present (which should never happen) ...
        return HttpResponseServerError("Something went wrong #@$%. Contact the site admin at " + settings.SECURE_SETTINGS['help_email_address'])
