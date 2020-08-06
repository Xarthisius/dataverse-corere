from django.urls import path

from corere.main.views import datatables, main, users, classes

urlpatterns = [ 
    path('', main.index),
    path('manuscript_table', datatables.ManuscriptJson.as_view(), name="manuscript_table"),
    path('manuscript/<int:manuscript_id>/submission_table', datatables.SubmissionJson.as_view(), name="submission_table"),
    path('manuscript/create', classes.ManuscriptCreateView.as_view(), name="manuscript_create"),
    path('manuscript/<int:id>/edit', classes.ManuscriptEditView.as_view(), name="manuscript_edit"),
    path('manuscript/<int:id>/editfiles', classes.ManuscriptEditFilesView.as_view(), name="manuscript_editfiles"),
    path('manuscript/<int:id>/view', classes.ManuscriptReadView.as_view(), name="manuscript_read"),
    path('manuscript/<int:id>/addauthor', users.add_author, name="manuscript_addauthor"),
    #TODO: Add deleteauthor and test
    path('manuscript/<int:id>/addcurator', users.add_curator, name="manuscript_addcurator"),
    path('manuscript/<int:id>/deletecurator/<int:user_id>', users.delete_curator, name="manuscript_deletecurator"),
    path('manuscript/<int:id>/addverifier', users.add_verifier, name="manuscript_addverifier"),
    path('manuscript/<int:id>/deleteverifier/<int:user_id>', users.delete_verifier, name="manuscript_deleteverifier"),
    path('manuscript/<int:manuscript_id>/createsubmission', classes.SubmissionCreateView.as_view(), name="manuscript_createsubmission"),
    path('manuscript/<int:manuscript_id>/deletefile', main.delete_file, name="manuscript_deletefile"), #TODO: This currently works on GET with a query param for the file path. Should be changed to delete/post
    path('manuscript/<int:id>/binder', main.open_binder, name="manuscript_binder"),
    path('manuscript/<int:id>/progress', classes.ManuscriptProgressView.as_view(), name="manuscript_progress"),

    path('submission/<int:id>/edit', classes.SubmissionEditView.as_view(), name="submission_edit"),
    path('submission/<int:id>/editfiles', classes.SubmissionEditFilesView.as_view(), name="submission_editfiles"),
    path('submission/<int:id>/view', classes.SubmissionReadView.as_view(), name="submission_read"),
    path('submission/<int:submission_id>/createcuration', classes.CurationCreateView.as_view(), name="submission_createcuration"),
    path('submission/<int:submission_id>/createverification', classes.VerificationCreateView.as_view(), name="submission_createverification"),
    path('submission/<int:submission_id>/createnote', main.edit_note, name="submission_createnote"),
    path('submission/<int:submission_id>/editnote/<int:id>', main.edit_note, name="submission_editnote"),
    path('submission/<int:submission_id>/deletenote/<int:id>', main.delete_note, name="submission_deletenote"),
    path('submission/<int:submission_id>/deletefile', main.delete_file, name="submission_deletefile"), #TODO: This currently works on GET with a query param for the file path. Should be changed to delete/post
    path('submission/<int:id>/progress', classes.SubmissionProgressView.as_view(), name="submission_progress"),

    path('curation/<int:id>/edit', classes.CurationEditView.as_view(), name="curation_edit"),
    path('curation/<int:id>/view', classes.CurationReadView.as_view(), name="curation_read"),
    path('curation/<int:curation_id>/createnote', main.edit_note, name="curation_createnote"),
    path('curation/<int:curation_id>/editnote/<int:id>', main.edit_note, name="curation_editnote"),
    path('curation/<int:curation_id>/deletenote/<int:id>', main.delete_note, name="curation_deletenote"),
    path('curation/<int:id>/progress', classes.CurationProgressView.as_view(), name="curation_progress"),

    path('verification/<int:id>/edit', classes.VerificationEditView.as_view(), name="verification_edit"),
    path('verification/<int:id>/view', classes.VerificationReadView.as_view(), name="verification_read"),
    path('verification/<int:verification_id>/createnote', main.edit_note, name="verification_createnote"),
    path('verification/<int:verification_id>/editnote/<int:id>', main.edit_note, name="verification_editnote"),
    path('verification/<int:verification_id>/deletenote/<int:id>', main.delete_note, name="verification_deletenote"),
    path('verification/<int:id>/progress', classes.VerificationProgressView.as_view(), name="verification_progress"),

    path('logout', users.logout_view),
    path('account_associate_oauth/<str:key>', users.account_associate_oauth),
    path('account_user_details', users.account_user_details),
    path('notifications', users.notifications),
    path('site_actions', main.site_actions),
    path('site_actions/create_editor', users.create_editor),
    path('site_actions/create_curator', users.create_curator),
    path('site_actions/create_verifier', users.create_verifier),

]