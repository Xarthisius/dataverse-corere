import logging, json, time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from corere.main import models as m
from corere.main import constants as c
from corere.main import git as g
from corere.main import docker as d
from corere.main.views.datatables import helper_manuscript_columns, helper_submission_columns
from corere.main.forms import * #TODO: bad practice and I don't use them all
from corere.main.utils import get_pretty_user_list_by_group
from django.contrib.auth.models import Permission, Group
from django_fsm import has_transition_perm, TransitionNotAllowed
from django.http import Http404, HttpResponse
from django.contrib.auth.decorators import login_required
from guardian.shortcuts import assign_perm, remove_perm
from corere.main.templatetags.auth_extras import has_group
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)

def index(request):
    if request.user.is_authenticated:
        args = {'user':     request.user, 
                'page_title': _("index_pageTitle"),
                'manuscript_columns':  helper_manuscript_columns(request.user),
                'submission_columns':  helper_submission_columns(request.user),
                'GROUP_ROLE_EDITOR': c.GROUP_ROLE_EDITOR,
                'GROUP_ROLE_AUTHOR': c.GROUP_ROLE_AUTHOR,
                'GROUP_ROLE_VERIFIER': c.GROUP_ROLE_VERIFIER,
                'GROUP_ROLE_CURATOR': c.GROUP_ROLE_CURATOR,
                'ADD_MANUSCRIPT_PERM_STRING': c.perm_path(c.PERM_MANU_ADD_M)
                }
        return render(request, "main/index.html", args)
    else:
        return render(request, "main/login.html")

@login_required
def manuscript_landing(request, id=None):
    manuscript = get_object_or_404(m.Manuscript, id=id)
    manuscript_avail_buttons = []
    if(has_transition_perm(manuscript.edit_noop, request.user)):
        manuscript_avail_buttons.append('editManuscript')
        manuscript_avail_buttons.append('editManuscriptFiles')
    elif(has_transition_perm(manuscript.view_noop, request.user)):
        manuscript_avail_buttons.append('viewManuscript')
        manuscript_avail_buttons.append('viewManuscriptFiles')
    else:
        raise Http404()
    if(has_transition_perm(manuscript.begin, request.user)):
        manuscript_avail_buttons.append('progressManuscript')
    #TODO: add launchNotebook once integration is better
    # MAD: Should we change these to be transitions?
    if(not manuscript.is_complete()):
        if(request.user.has_any_perm(c.PERM_MANU_ADD_AUTHORS, manuscript)):
            manuscript_avail_buttons.append('inviteassignauthor')
        if(request.user.has_any_perm(c.PERM_MANU_MANAGE_EDITORS, manuscript)):
            manuscript_avail_buttons.append('assigneditor')
        if(request.user.has_any_perm(c.PERM_MANU_MANAGE_CURATORS, manuscript)):
            manuscript_avail_buttons.append('assigncurator')
        if(request.user.has_any_perm(c.PERM_MANU_MANAGE_VERIFIERS, manuscript)):
            manuscript_avail_buttons.append('assignverifier')
    if(has_transition_perm(manuscript.add_submission_noop, request.user)):
        manuscript_avail_buttons.append('createSubmission')

    manuscript_authors = get_pretty_user_list_by_group(c.GROUP_MANUSCRIPT_AUTHOR_PREFIX + " " + str(manuscript.id))
    manuscript_editors = get_pretty_user_list_by_group(c.GROUP_MANUSCRIPT_EDITOR_PREFIX + " " + str(manuscript.id))
    manuscript_curators = get_pretty_user_list_by_group(c.GROUP_MANUSCRIPT_CURATOR_PREFIX + " " + str(manuscript.id))
    manuscript_verifiers = get_pretty_user_list_by_group(c.GROUP_MANUSCRIPT_VERIFIER_PREFIX + " " + str(manuscript.id))

    args = {'user':     request.user, 
            "manuscript_id": id,
            "submission_count": manuscript.manuscript_submissions.count(),
            "manuscript_title": manuscript.title,
            "manuscript_authors": manuscript_authors,
            "manuscript_editors": manuscript_editors,
            "manuscript_curators": manuscript_curators,
            "manuscript_verifiers": manuscript_verifiers,
            "manuscript_status": manuscript.get__status_display(),
            "manuscript_has_submissions": (manuscript.get_max_submission_version_id() != None),
            'submission_columns':  helper_submission_columns(request.user),
            'GROUP_ROLE_EDITOR': c.GROUP_ROLE_EDITOR,
            'GROUP_ROLE_AUTHOR': c.GROUP_ROLE_AUTHOR,
            'GROUP_ROLE_VERIFIER': c.GROUP_ROLE_VERIFIER,
            'GROUP_ROLE_CURATOR': c.GROUP_ROLE_CURATOR,
            'manuscript_avail_buttons': json.dumps(manuscript_avail_buttons),
            'ADD_MANUSCRIPT_PERM_STRING': c.perm_path(c.PERM_MANU_ADD_M),
            'page_title': _("manuscript_landing_pageTitle"),
            'create_sub_allowed': str(has_transition_perm(manuscript.add_submission_noop, request.user)).lower
            }
    return render(request, "main/manuscript_landing.html", args)

@login_required
def open_notebook(request, id=None):
    manuscript = get_object_or_404(m.Manuscript, id=id)
    if(has_transition_perm(manuscript.edit_noop, request.user)):
        if(not manuscript.get_max_submission_version_id()):
            raise Http404()
        
        latest_submission = manuscript.get_latest_submission()

        if(hasattr(manuscript, 'manuscript_containerinfo')): 
            if manuscript.manuscript_containerinfo.build_in_progress:
                while manuscript.manuscript_containerinfo.build_in_progress:
                    time.sleep(.1)
                    manuscript.manuscript_containerinfo.refresh_from_db()

            elif(latest_submission.files_changed):
                logger.info("Refreshing docker stack (on main page) for manuscript: " + str(manuscript.id))
                d.refresh_notebook_stack(manuscript)
                latest_submission.files_changed = False
                latest_submission.save()
        else:
            logger.info("Building docker stack (on main page) for manuscript: " + str(manuscript.id))
            d.build_manuscript_docker_stack(manuscript, request)
            latest_submission.files_changed = False
            latest_submission.save()

        print(manuscript.manuscript_containerinfo.container_public_address())
        return redirect(manuscript.manuscript_containerinfo.container_public_address())
    else:
        raise Http404()

@login_required()
def site_actions(request):
    if(has_group(request.user, c.GROUP_ROLE_CURATOR)):
        return render(request, 'main/site_actions.html', {'page_title': "site_actions"})
    else:
        raise Http404()

#NOTE: if we use cookies for session this may no longer be safe
@login_required()
def switch_role(request):
    role_string = request.GET.get('role', '')
    role_full_string = "Role " + role_string
    if(role_string == "Admin"):
        if(request.user.is_superuser):
            request.session['active_role'] = role_string
        else:
            logger.warning("User " + request.user.username + " attempted to switch their active role to admin which they do not have")
    else:
        role = Group.objects.get(name=role_full_string)
        if role in request.user.groups.all():
            request.session['active_role'] = role_string
        else:
            logger.warning("User " + request.user.username + " attempted to switch their active role to a role they do not have ("+ role_full_string +")")
    return redirect(request.GET.get('next', ''))