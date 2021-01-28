from django.urls import path

from corere.main.views import datatables, main, users, classes

urlpatterns = [ 
    path('', main.index, name="index"),
    path('manuscript_table/', datatables.ManuscriptJson.as_view(), name="manuscript_table"),
    path('manuscript/<int:id>/', main.manuscript_landing, name="manuscript_landing"),
    path('manuscript/<int:manuscript_id>/submission_table/', datatables.SubmissionJson.as_view(), name="submission_table"),
    path('manuscript/create/', classes.ManuscriptCreateView.as_view(), name="manuscript_create"),
    path('manuscript/<int:id>/edit/', classes.ManuscriptEditView.as_view(), name="manuscript_edit"),
    path('manuscript/<int:id>/uploadfiles/', classes.ManuscriptUploadFilesView.as_view(), name="manuscript_uploadfiles"),
    path('manuscript/<int:id>/fileslist/', classes.ManuscriptFilesListAjaxView.as_view(),name="manuscript_fileslist"),
    path('manuscript/<int:id>/view/', classes.ManuscriptReadView.as_view(), name="manuscript_read"),
    path('manuscript/<int:id>/viewfiles/', classes.ManuscriptReadFilesView.as_view(), name="manuscript_readfiles"),
    path('manuscript/<int:id>/inviteassignauthor/', users.invite_assign_author, name="manuscript_inviteassignauthor"),
    path('manuscript/<int:id>/unassignauthor/<int:user_id>/', users.unassign_author, name="manuscript_unassignauthor"),
    path('manuscript/<int:id>/assigneditor/', users.assign_editor, name="manuscript_assigneditor"),
    path('manuscript/<int:id>/unassigneditor/<int:user_id>/', users.unassign_editor, name="manuscript_unassigneditor"),
    path('manuscript/<int:id>/assigncurator/', users.assign_curator, name="manuscript_assigncurator"),
    path('manuscript/<int:id>/unassigncurator/<int:user_id>/', users.unassign_curator, name="manuscript_unassigncurator"),
    path('manuscript/<int:id>/assignverifier/', users.assign_verifier, name="manuscript_assignverifier"),
    path('manuscript/<int:id>/unassignverifier/<int:user_id>/', users.unassign_verifier, name="manuscript_unassignverifier"),
    path('manuscript/<int:manuscript_id>/createsubmission/', classes.SubmissionCreateView.as_view(), name="manuscript_createsubmission"),
    path('manuscript/<int:manuscript_id>/deletefile/', main.delete_file, name="manuscript_deletefile"),
    path('manuscript/<int:id>/binder/', main.open_binder, name="manuscript_binder"),
    path('manuscript/<int:id>/progress/', classes.ManuscriptProgressView.as_view(), name="manuscript_progress"),
    path('manuscript/<int:id>/report/', classes.ManuscriptReportView.as_view(), name="manuscript_report"),

    #TODO: Maybe switch all submission endpoints to be manuscript/<mid>/submission/<version_id>/...
    path('submission/<int:id>/edit/', classes.SubmissionEditView.as_view(), name="submission_edit"),
    path('submission/<int:id>/editfiles/', classes.SubmissionEditFilesView.as_view(), name="submission_editfiles"),
    path('submission/<int:id>/uploadfiles/', classes.SubmissionUploadFilesView.as_view(), name="submission_uploadfiles"),
    path('submission/<int:id>/fileslist/', classes.SubmissionFilesListView.as_view(),name="submission_fileslist"),
    path('submission/<int:id>/view/', classes.SubmissionReadView.as_view(), name="submission_read"),
    path('submission/<int:id>/viewfiles/', classes.SubmissionReadFilesView.as_view(), name="submission_readfiles"),
    path('submission/<int:submission_id>/deletefile/', main.delete_file, name="submission_deletefile"),
    path('submission/<int:submission_id>/deleteallfiles/', main.delete_all_submission_files, name="submission_deleteallfiles"),
    path('submission/<int:id>/progress/', classes.SubmissionProgressView.as_view(), name="submission_progress"),
    path('submission/<int:id>/generatereport/', classes.SubmissionGenerateReportView.as_view(), name="submission_generatereport"),
    path('submission/<int:id>/return/', classes.SubmissionReturnView.as_view(), name="submission_return"),

    path('logout/', users.logout_view, name="logout"),
    path('account_associate_oauth/<str:key>/', users.account_associate_oauth, name="account_associate_oauth"),
    path('account_user_details/', users.account_user_details, name="account_user_details"),
    path('notifications/', users.notifications, name="notifications"),
    path('site_actions/', main.site_actions, name="site_actions"),
    path('site_actions/inviteeditor/', users.invite_editor, name="inviteeditor"),
    path('site_actions/invitecurator/', users.invite_curator, name="invitecurator"),
    path('site_actions/inviteverifier/', users.invite_verifier, name="inviteverifier"),
    path('switch_role/', main.switch_role, name="switch_role"),
]