import logging, os, copy, sys
from django import forms
from django.forms import ModelMultipleChoiceField, inlineformset_factory, TextInput, RadioSelect, Textarea, ModelChoiceField, BaseInlineFormSet
from django.contrib.postgres.fields import ArrayField
#from .models import Manuscript, Submission, Edition, Curation, Verification, User, Note, GitFile
#from invitations.models import Invitation
from guardian.shortcuts import get_perms
from invitations.utils import get_invitation_model
from django.conf import settings
from . import constants as c
from corere.main import models as m
from django.contrib.auth.models import Group
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import FieldDoesNotExist, ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, ButtonHolder, Submit, Div
from crequest.middleware import CrequestMiddleware
from guardian.shortcuts import get_objects_for_user, assign_perm, remove_perm
from django.http import Http404
logger = logging.getLogger(__name__)

### NOTE: Changing the name of any form that end in "_[ROLE]" (e.g. ManuscriptForm_Admin)
###  will break logic for generating form/formset lists

#------------ Base -------------

class ReadOnlyFormMixin(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ReadOnlyFormMixin, self).__init__(*args, **kwargs)
        
        for key in self.fields.keys():
            self.fields[key].disabled = True

    def save(self, *args, **kwargs):
        pass # do not do anything

class GenericFormSetHelper(FormHelper):
     def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_tag = False

class GenericInlineFormSetHelper(FormHelper):
     def __init__(self, form_id="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_class = 'form-inline'
        self.template = 'bootstrap4/table_inline_formset.html'#'main/crispy_templates/bootstrap4_table_inline_formset_custom_notes.html'
        self.form_tag = False
        # if 'form_id' in kwargs:
        self.form_id = form_id
        # self.layout = Layout(

        #     Field('path', th_class="w-50"),
        #     Field('tag'),
        #     Field('description'),
        # )
        self.render_required_fields = True

list_of_roles = ["Admin","Author","Editor","Curator","Verifier"]

# Helper that adds all help text as a popover.
# This also adds stars for required fields. We can't rely on the normal required functionality because we require fields depending on user-role/object-phase
# NOTE: My use of marking required with this is flawed. Right now we are enforcing requirements on a per-phase basis, while we are showing requirements on a per-role basis.
#       This works fine for our needs, but will likely scale poorly if we ever need to get more nuanced.
#       Also worth noting that for formsets off the main form, we set the required "*" in the template.
def label_gen(model, field_strings, required=[]):
    fields_html = {}
    for field_string in field_strings:
        try:
            field = model._meta.get_field(field_string)
        except FieldDoesNotExist:
            continue #if custom field we skip it

        html = '<span >'+field.verbose_name+'</span>'
        if(field_string in required):
            html += "* "
        if(field.help_text != ""):
            html += '<span class="fas fa-question-circle tooltip-icon" data-toggle="tooltip" data-placement="auto" title="'+field.help_text+'"></span>'
            #html += '<button type="button" class="btn btn-secondary btn-sm" data-toggle="tooltip" data-placement="auto" title="'+field.help_text+'">?</button>'

            #html += '<a tabindex="0" role="button" data-toggle="tooltip" data-placement="auto" data-content="' + field.help_text + '"> test <span class="glyphicon glyphicon-info-sign"></span></a>'
        fields_html[field.name] = html
    return fields_html

#-------------------------


class UserByRoleAddFormHelper(FormHelper):
     def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_tag = False

        self.layout = Layout(
            Div(
                Div('first_name',css_class='col-md-6',),
                Div('last_name',css_class='col-md-6',),
                css_class='row',
            ),
            'email'
        )

#For editors adding authors during manuscript creation
class AuthorAddForm(forms.Form):
    first_name = forms.CharField(label='Invitee first name', max_length=150, required=True)
    last_name = forms.CharField(label='Invitee last name', max_length=150, required=True)
    email = forms.EmailField(label='Invitee email', max_length=settings.INVITATIONS_EMAIL_MAX_LENGTH, required=True)

class CustomSelect2UserWidget(forms.SelectMultiple):
    class Media:
        js = ('main/select2_table.js',)

    def render(self, name, value, attrs=None, renderer=None):
        return super().render(name, value, attrs, renderer)

#For admins add/removing authors
class AuthorInviteAddForm(forms.Form):
    # TODO: If we do keep this email field we should make it accept multiple. But we should probably just combine it with the choice field below
    email = forms.EmailField(label='Invitee email', max_length=settings.INVITATIONS_EMAIL_MAX_LENGTH, required=False)
    users_to_add = ModelMultipleChoiceField(queryset=m.User.objects.filter(invite_key='', groups__name=c.GROUP_ROLE_AUTHOR), widget=CustomSelect2UserWidget(), required=False)

class EditorAddForm(forms.Form):
    users_to_add = ModelMultipleChoiceField(queryset=m.User.objects.filter(invite_key='', groups__name=c.GROUP_ROLE_EDITOR), widget=CustomSelect2UserWidget(), required=False)

class CuratorAddForm(forms.Form):
    users_to_add = ModelMultipleChoiceField(queryset=m.User.objects.filter(invite_key='', groups__name=c.GROUP_ROLE_CURATOR), widget=CustomSelect2UserWidget(), required=False)

class VerifierAddForm(forms.Form):
    users_to_add = ModelMultipleChoiceField(queryset=m.User.objects.filter(invite_key='', groups__name=c.GROUP_ROLE_VERIFIER), widget=CustomSelect2UserWidget(), required=False)

class EditUserForm(forms.ModelForm):
    class Meta:
        model = m.User
        fields = ['username', 'email', 'first_name', 'last_name']

#Note: not used on Authors, as we always want them assigned when created
class UserInviteForm(forms.Form):
    first_name = forms.CharField(label='Invitee first name', max_length=150, required=True)
    last_name = forms.CharField(label='Invitee last name', max_length=150, required=True)
    email = forms.CharField(label='Invitee email', max_length=settings.INVITATIONS_EMAIL_MAX_LENGTH, required=False)

#No actual editing is done in this form, just uploads
#We just leverage the existing form infrastructure for perm checks etc
class SubmissionUploadFilesForm(ReadOnlyFormMixin, forms.ModelForm):
    class Meta:
        model = m.Submission
        fields = []#['pub_name','doi','open_data']#,'authors']
    pass

############# Manuscript Views Forms #############
#-------------

#No actual editing is done in this form, just uploads
#We just leverage the existing form infrastructure for perm checks etc
class ManuscriptFilesForm(ReadOnlyFormMixin, forms.ModelForm):
    class Meta:
        model = m.Manuscript
        fields = []#['pub_name','doi','open_data']#,'authors']
    pass

class ManuscriptFormHelperMain(FormHelper):
     def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_tag = False

        self.layout = Layout(
            'pub_name','pub_id','description','subject', 'additional_info',
            Div(
                Div('qual_analysis',css_class='col-md-6',),
                Div('qdr_review',css_class='col-md-6',),
                css_class='row',
            ),
            Div(
                Div('contact_first_name',css_class='col-md-6',),
                Div('contact_last_name',css_class='col-md-6',),
                Div('contact_email',css_class='col-md-6',),
                css_class='row',
            )
        )

class ManuscriptFormHelperEditor(FormHelper):
     def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_tag = False

        self.layout = Layout(
            'pub_name','pub_id','additional_info',
            Div(
                Div('qual_analysis',css_class='col-md-6',),
                Div('qdr_review',css_class='col-md-6',),
                css_class='row',
            ),
            Div(
                Div('contact_first_name',css_class='col-md-6',),
                Div('contact_last_name',css_class='col-md-6',),
                Div('contact_email',css_class='col-md-6',),
                css_class='row',
            )
        )

#------------- Base Manuscript -------------

class ManuscriptBaseForm(forms.ModelForm):
    class Meta:
        abstract = True
        model = m.Manuscript
        fields = ['pub_name','pub_id','qual_analysis','qdr_review','contact_first_name','contact_last_name','contact_email',
            'description','subject','additional_info']#, 'manuscript_authors', 'manuscript_data_sources', 'manuscript_keywords']#,'keywords','data_sources']
        always_required = ['pub_name', 'pub_id', 'contact_first_name', 'contact_last_name', 'contact_email'] # Used to populate required "*" in form. We have disabled the default crispy functionality because it isn't dynamic enough for our per-phase requirements
        labels = label_gen(model, fields, always_required)

    def clean(self):
        # print(self.Meta.role_required)

        #We run this clean if the manuscript is progressed, or after being progressed it is being edited.
        if("submit_progress_manuscript" in self.data.keys() or self.instance._status != m.Manuscript.Status.NEW):
            description = self.cleaned_data.get('description')
            if(not description):
                self.add_error('description', 'This field is required.')

            subject = self.cleaned_data.get('subject')
            if(not subject):
                self.add_error('subject', 'This field is required.')

            contact_first_name = self.cleaned_data.get('contact_first_name')
            if(not contact_first_name):
                self.add_error('contact_first_name', 'This field is required.')

            contact_last_name = self.cleaned_data.get('contact_last_name')
            if(not contact_last_name):
                self.add_error('contact_last_name', 'This field is required.')

            contact_email = self.cleaned_data.get('contact_email')
            if(not contact_email):
                self.add_error('contact_email', 'This field is required.')

            validation_errors = [] #we store all the "generic" errors and raise them at once
            if(self.data['author_formset-0-first_name'] == "" or self.data['author_formset-0-last_name'] == "" #or self.data['author_formset-0-identifier'] == "" or self.data['author_formset-0-identifier_scheme'] == ""
                ):
                validation_errors.append(ValidationError("You must specify an author."))
            # if(self.data['data_source_formset-0-text'] == ""):
            #     validation_errors.append(ValidationError("You must specify a data source."))
            if(self.data['keyword_formset-0-text'] == ""):
                validation_errors.append(ValidationError("You must specify a keyword."))    

            validation_errors.extend(self.instance.can_begin_return_problems())

            if validation_errors:
                #If we don't raise the error here the formset errors don't raise up
                #But if we return any contents the error shows in the top errors field and in the formset field, and we don't want that
                #So we return an empty list
                raise ValidationError([])

#All Manuscript fields are visible to all users, so no role-based forms
class ReadOnlyManuscriptForm(ReadOnlyFormMixin, ManuscriptBaseForm):
    pass

class ManuscriptForm_Admin(ManuscriptBaseForm):
    pass

class ManuscriptForm_Author(ManuscriptBaseForm):
    class Meta(ManuscriptBaseForm.Meta):
        role_required = ['pub_name','description','subject','contact_first_name','contact_last_name','contact_email']
        labels = label_gen(ManuscriptBaseForm.Meta.model, ManuscriptBaseForm.Meta.fields, role_required)

    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pub_id'].disabled = True
        self.fields['qdr_review'].disabled = True

class ManuscriptForm_Editor(ManuscriptBaseForm):
    class Meta(ManuscriptBaseForm.Meta):
        fields = ['pub_name','pub_id','qual_analysis','qdr_review','contact_first_name','contact_last_name','contact_email','additional_info']

    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['description'].disabled = True
        # self.fields['subject'].disabled = True
        # self.fields['contact_first_name'].disabled = True
        # self.fields['contact_last_name'].disabled = True
        # self.fields['contact_email'].disabled = True

class ManuscriptForm_Curator(ManuscriptBaseForm):

    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pub_id'].disabled = True

class ManuscriptForm_Verifier(ManuscriptBaseForm):

    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pub_id'].disabled = True
        self.fields['pub_name'].disabled = True
        self.fields['qual_analysis'].disabled = True
        self.fields['qdr_review'].disabled = True
        self.fields['contact_first_name'].disabled = True
        self.fields['contact_last_name'].disabled = True
        self.fields['contact_email'].disabled = True
        self.fields['description'].disabled = True
        self.fields['additional_info'].disabled = True
        self.fields['subject'].disabled = True

ManuscriptForms = {
    "Admin": ManuscriptForm_Admin,
    "Author": ManuscriptForm_Author,
    "Editor": ManuscriptForm_Editor,
    "Curator": ManuscriptForm_Curator,
    "Verifier": ManuscriptForm_Verifier,
}
#------------- Data Source -------------

#Doing this check in "is_valid" is probably not the right spot. We raise a validation error instead of letting the function complete.
class DataSourceBaseForm(forms.ModelForm):
    # def __init__ (self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.empty_permitted = False

    class Meta:
        model = m.DataSource
        fields = ["text"]
        labels = label_gen(model, fields)

    def is_valid(self):
        result = super(DataSourceBaseForm, self).is_valid()

        #This data probably is untrustworthy, but if the user munges it all that happens is they are required to add another field.
        if(self.fields.get("manuscript").parent_instance._status != m.Manuscript.Status.NEW):
            validation_errors = [] #we store all the "generic" errors and raise them at once
            if(self.data['data_source_formset-0-text'] == ""):
                validation_errors.append(ValidationError("You must specify a data source."))

            if validation_errors:
                result = True
                raise ValidationError(validation_errors)

        return result


class DataSourceForm_Admin(DataSourceBaseForm):
    pass

class DataSourceForm_Author(DataSourceBaseForm):
    pass

class DataSourceForm_Editor(DataSourceBaseForm):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].disabled = True

class DataSourceForm_Curator(DataSourceBaseForm):
    pass

class DataSourceForm_Verifier(DataSourceBaseForm):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].disabled = True

DataSourceManuscriptFormsets = {}
for role_str in list_of_roles:
    DataSourceManuscriptFormsets[role_str] = inlineformset_factory(
        m.Manuscript,
        m.DataSource,  
        extra=1 if(role_str == "Admin" or role_str == "Author" or role_str == "Curator") else 0,
        form=getattr(sys.modules[__name__], "DataSourceForm_"+role_str),
        can_delete = True if(role_str == "Admin" or role_str == "Author" or role_str == "Curator") else False,
    ) 

#All Manuscript fields are visible to all users, so no role-based forms
class ReadOnlyDataSourceForm(ReadOnlyFormMixin, DataSourceBaseForm):
    pass

ReadOnlyDataSourceFormSet = inlineformset_factory(
    m.Manuscript,
    m.DataSource,  
    extra=0,
    form=ReadOnlyDataSourceForm,
    can_delete=False,
)

#------------- Keyword -------------

#Doing this check in "is_valid" is probably not the right spot. We raise a validation error instead of letting the function complete.
class KeywordBaseForm(forms.ModelForm):
    # def __init__ (self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.empty_permitted = False

    class Meta:
        model = m.Keyword
        fields = ["text"]
        labels = label_gen(model, fields)

    def is_valid(self):
        result = super(KeywordBaseForm, self).is_valid()

        #This data probably is untrustworthy, but if the user munges it all that happens is they are required to add another field.
        if(self.fields.get("manuscript").parent_instance._status != m.Manuscript.Status.NEW):
            validation_errors = [] #we store all the "generic" errors and raise them at once
            if(self.data['keyword_formset-0-text'] == ""):
                validation_errors.append(ValidationError("You must specify a keyword."))    

            if validation_errors:
                result = True
                raise ValidationError(validation_errors)

        return result

class KeywordForm_Admin(KeywordBaseForm):
    pass

class KeywordForm_Author(KeywordBaseForm):
    pass

class KeywordForm_Editor(KeywordBaseForm):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].disabled = True

class KeywordForm_Curator(KeywordBaseForm):
    pass

class KeywordForm_Verifier(KeywordBaseForm):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].disabled = True

KeywordManuscriptFormsets = {}
for role_str in list_of_roles:
    KeywordManuscriptFormsets[role_str] = inlineformset_factory(
        m.Manuscript,
        m.Keyword,  
        extra=1 if(role_str == "Admin" or role_str == "Author" or role_str == "Curator") else 0,
        form=getattr(sys.modules[__name__], "KeywordForm_"+role_str),
        can_delete = True if(role_str == "Admin" or role_str == "Author" or role_str == "Curator") else False,
    ) 

#All Manuscript fields are visible to all users, so no role-based forms
class ReadOnlyKeywordForm(ReadOnlyFormMixin, KeywordBaseForm):
    pass

ReadOnlyKeywordFormSet = inlineformset_factory(
    m.Manuscript,
    m.Keyword,  
    extra=0,
    form=ReadOnlyKeywordForm,
    can_delete=False,
)

#------------- Author (Connected to manuscript, Not User Model) -------------

class AuthorBaseForm(forms.ModelForm):
    # def __init__ (self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.empty_permitted = False

    class Meta:
        model = m.Author
        fields = ["first_name","last_name","identifier_scheme", "identifier"]
        labels = label_gen(model, fields)

    #Doing this check in "is_valid" is probably not the right spot. We raise a validation error instead of letting the function complete.
    def is_valid(self):
        result = super(AuthorBaseForm, self).is_valid()

        #This data probably is untrustworthy, but if the user munges it all that happens is they are required to add another field.
        if(self.fields.get("manuscript").parent_instance._status != m.Manuscript.Status.NEW):
            validation_errors = [] #we store all the "generic" errors and raise them at once
            if(self.data['author_formset-0-first_name'] == "" or self.data['author_formset-0-last_name'] == "" 
                #or self.data['author_formset-0-identifier'] == "" or self.data['author_formset-0-identifier_scheme'] == "" #or self.data['author_formset-0-position'] == ""
                ):
                validation_errors.append(ValidationError("You must specify an author."))

            if validation_errors:
                result = True
                raise ValidationError(validation_errors)

        return result

class AuthorForm_Admin(AuthorBaseForm):
    pass

class AuthorForm_Author(AuthorBaseForm):
    pass

class AuthorForm_Editor(AuthorBaseForm):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].disabled = True
        self.fields["last_name"].disabled = True
        self.fields["identifier_scheme"].disabled = True
        self.fields["identifier"].disabled = True

class AuthorForm_Curator(AuthorBaseForm):
    pass

class AuthorForm_Verifier(AuthorBaseForm):
    def __init__ (self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].disabled = True
        self.fields["last_name"].disabled = True
        self.fields["identifier_scheme"].disabled = True
        self.fields["identifier"].disabled = True
        #self.fields["position"].disabled = True

class BaseAuthorManuscriptFormset(BaseInlineFormSet):
    pass
    # def clean(self):
    #     position_list = []
    #     try:
    #         for fdata in self.cleaned_data:
    #             if('position' in fdata): #skip empty form
    #                 position_list.append(fdata['position'])
    #         if(len(position_list) != 0 and ( sorted(position_list) != list(range(min(position_list), max(position_list)+1)) or min(position_list) != 1)):
    #             raise forms.ValidationError("Positions must be consecutive whole numbers and start with 1 (e.g. [1, 2, 3, 4, 5], [3, 1, 2, 4], etc)", "error")
    #     except AttributeError:
    #         pass #sometimes there is no cleaned data

AuthorManuscriptFormsets = {}
for role_str in list_of_roles:
    AuthorManuscriptFormsets[role_str] = inlineformset_factory(
        m.Manuscript,
        m.Author,  
        extra=1 if(role_str == "Admin" or role_str == "Author" or role_str == "Curator") else 0,
        form=getattr(sys.modules[__name__], "AuthorForm_"+role_str),
        can_delete = True if(role_str == "Admin" or role_str == "Author" or role_str == "Curator") else False,
        formset=BaseAuthorManuscriptFormset
    )

#All Manuscript fields are visible to all users, so no role-based forms
class ReadOnlyAuthorForm(ReadOnlyFormMixin, AuthorBaseForm):
    pass

ReadOnlyAuthorFormSet = inlineformset_factory(
    m.Manuscript,
    m.Author,  
    extra=0,
    form=ReadOnlyAuthorForm,
    can_delete=False,
)

############# Note Forms ############# (PROBABLY COLLAPSE INTO TOP)

class NoteForm(forms.ModelForm):
    class Meta:
        model = m.Note
        fields = ['text','scope','creator','note_replied_to','note_reference']
        labels = label_gen(model, fields)

    SCOPE_OPTIONS = (('public','Public'),('private','Private'))

    scope = forms.ChoiceField(widget=forms.RadioSelect,
                                        choices=SCOPE_OPTIONS, required=False)

    note_reference = forms.CharField(label='File/Category', widget=forms.Select()) #TODO: This should actually be populated during the init

    #Checker is for passing prefeteched django-guardian permissions
    #https://django-guardian.readthedocs.io/en/stable/userguide/performance.html?highlight=cache#prefetching-permissions
    #Other args are also passed in for performance improvements across all the notes
    def __init__ (self, *args, checkers, manuscript, submission, sub_files, **kwargs):
        super(NoteForm, self).__init__(*args, **kwargs)
        #For some reason I can't fathom, accessing any note info via self.instance causes many extra calls to this method.
        #It also causes the end form to not populate. So we are getting the info we need on the manuscript via crequest

        user = CrequestMiddleware.get_request().user
        path_obj_name = CrequestMiddleware.get_request().resolver_match.url_name.split("_")[0] #CrequestMiddleware.get_request().resolver_match.func.view_class.object_friendly_name

        if(not (user.has_any_perm(c.PERM_MANU_CURATE, manuscript) or user.has_any_perm(c.PERM_MANU_VERIFY, manuscript))):
            self.fields.pop('scope')
        else:       
            #Populate scope field depending on existing roles
            role_count = 0
            for checker in checkers:
                if(checker.has_perm(c.PERM_NOTE_VIEW_N, self.instance)):
                    role_count += 1
            if(role_count == 4): #pretty crude check, if all roles then its public. Using a magic number (4) instead of len(c.get_roles()) because its already hardcoded other places.
                self.fields['scope'].initial = 'public'
            else:
                self.fields['scope'].initial = 'private'

        self.fields['creator'].disabled = True
        if(self.instance.id): #if based off existing note
            if(self.instance.creator != user): #If the user is not the creator of the note
                for fkey, fval in self.fields.items():
                    fval.widget.attrs['disabled']=True #you have to disable this way for scope to disable

        #Initialize note_reference
        #Note: I tried moving this to classes.py to not repeat it, but it didn't get faster. So leaving it here.
        note_ref_choices = [('---','---')]
        note_ref_choices = note_ref_choices + m.GitFile.FileTag.choices
        files = []
        if submission:
            files = sub_files
        for file in files:
            note_ref_choices = note_ref_choices + [( file.path+file.name, file.name)]
            
        self.fields['note_reference'].widget.choices = note_ref_choices

        #Populate the existing values for note_reference
        if(self.instance.ref_file_type in m.GitFile.FileTag.values):
            self.fields['note_reference'].initial = self.instance.ref_file_type
        elif(self.instance.ref_file and self.instance.ref_file.path + self.instance.ref_file.name in dict(note_ref_choices)):
            self.fields['note_reference'].initial = self.instance.ref_file.path + self.instance.ref_file.name
        else:
            self.fields['note_reference'].initial = '---'

    def save(self, commit, *args, **kwargs):
        if(self.has_changed()):
            user = CrequestMiddleware.get_request().user
            if(self.cleaned_data['creator'] != user):
                pass #Do not save
        super(NoteForm, self).save(commit, *args, **kwargs)
        if('scope' in self.changed_data):
            #Somewhat inefficient, but we just delete all perms and readd new ones. Safest.
            for role in c.get_roles():
                group = Group.objects.get(name=role)
                remove_perm(c.PERM_NOTE_VIEW_N, group, self.instance)
            if(self.cleaned_data['scope'] == 'public'):
                for role in c.get_roles():
                    group = Group.objects.get(name=role)
                    assign_perm(c.PERM_NOTE_VIEW_N, group, self.instance)
            else:
                if(user.has_any_perm(c.PERM_MANU_CURATE, self.instance.manuscript) or user.has_any_perm(c.PERM_MANU_VERIFY, self.instance.manuscript)): #only users with certain roles can set private
                    for role in c.get_private_roles():
                        group = Group.objects.get(name=role)
                        assign_perm(c.PERM_NOTE_VIEW_N, group, self.instance)
                else:
                    #At this point we've saved already, maybe we shouldn't?
                    logger.warning("User id:{0} attempted to set note id:{1} to private, when they do not have the required permissions. They may have tried hacking the form.".format(user.id, self.instance.id))
                    raise Http404()
        if('note_reference' in self.changed_data):
            #TODO: If we open up notes to other types again, we need to check if submission is set here
            files = self.instance.parent_submission.submission_files.all()
            file_full_paths = []
            for file in files:
                file_full_paths = file_full_paths + [file.path+file.name]
            self.instance.ref_file_type = ''
            self.instance.ref_file = None

            if(self.cleaned_data['note_reference'] in m.GitFile.FileTag.values):
                self.instance.ref_file_type = self.cleaned_data['note_reference']
            elif(self.cleaned_data['note_reference'] in file_full_paths):
                file_folder, file_name = self.cleaned_data['note_reference'].rsplit('/', 1)
                file = m.GitFile.objects.get(name=file_name, path=file_folder+'/', parent_submission=self.instance.parent_submission)
                self.instance.ref_file = file

            self.instance.save()

class BaseNoteFormSet(BaseInlineFormSet):
    #only allow deleting of user-owned notes. we also disable the checkbox via JS
    @property
    def deleted_forms(self):
        deleted_forms = super(BaseNoteFormSet, self).deleted_forms
        user = CrequestMiddleware.get_request().user
        for i, form in enumerate(deleted_forms):
            if(not m.Note.objects.filter(id=form.instance.id, creator=user).exists()): #If the user is not the creator of the note
                deleted_forms.pop(i) #Then we remove the note from the delete list, to not delete the note

        return deleted_forms

    #only show private notes if user is curator/verifier on manuscript
    def get_queryset(self):
        if not hasattr(self, '_queryset'):
            self._queryset = get_objects_for_user(CrequestMiddleware.get_request().user, c.PERM_NOTE_VIEW_N, klass=self.queryset.filter())
            if not self._queryset.ordered:
                self._queryset = self._queryset.order_by(self.model._meta.pk.name)                
        return self._queryset

class NoteFormSetHelper(FormHelper):
     def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_class = 'form-inline'
        self.template = 'bootstrap4/table_inline_formset.html'
        self.form_tag = False
        self.form_id = 'note'
        self.render_required_fields = True

NoteSubmissionFormset = inlineformset_factory(
    m.Submission, 
    m.Note, 
    extra=1,
    form=NoteForm,
    formset=BaseNoteFormSet,
    fields=("creator","text"),
    widgets={
        'text': Textarea(attrs={'rows':1, 'placeholder':'Write your new note...'}) }
    )

############# GitFile (File Metadata) Views Forms #############

#TODO: Making this generic may have been pointless, not sure if its needed?
class BaseFileNestingFormSet(BaseInlineFormSet):
    def add_fields(self, form, index):
        super(BaseFileNestingFormSet, self).add_fields(form, index)
        # save the formset in the 'nested' property
        form.nested = self.nested_formset(
            instance=form.instance,
            data=form.data if form.is_bound else None,
            files=form.files if form.is_bound else None,
            prefix='note-%s-%s' % (
                form.prefix,
                self.nested_formset.get_default_prefix()), #Defining prefix seems nessecary for getting save to work
        )
    
    def is_valid(self):
        result = super(BaseFileNestingFormSet, self).is_valid()
        if self.is_bound:
            for form in self.forms:
                if hasattr(form, 'nested'):
                    result = result and form.nested.is_valid()
        return result

    def save(self, commit=True):
        result = super(BaseFileNestingFormSet, self).save(commit=commit)
        for form in self.forms:
            if hasattr(form, 'nested'):
                if not self._should_delete_form(form):
                    form.nested.save(commit=commit)
        return result

class GitFileForm(forms.ModelForm):
    class Meta:
        model = m.GitFile
        fields = ['name','path','tag','description','md5','size','date']

    def __init__ (self, *args, **kwargs):
        super(GitFileForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.object_instance = self.instance
        self.fields['name'].disabled = True
        self.fields['path'].disabled = True
        self.fields['md5'].disabled = True
        self.fields['size'].disabled = True
        self.fields['date'].disabled = True

class GitFileReadOnlyFileForm(forms.ModelForm):
    class Meta:
        model = m.GitFile
        fields = ['name','path','tag','description','md5','size','date']

    def __init__ (self, *args, **kwargs):
        super(GitFileReadOnlyFileForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.object_instance = self.instance
        self.fields['name'].disabled = True
        self.fields['path'].disabled = True
        self.fields['md5'].disabled = True
        self.fields['size'].disabled = True
        self.fields['date'].disabled = True
        # All fields read only
        self.fields['tag'].disabled = True
        self.fields['description'].disabled = True

class DownloadGitFileWidget(forms.widgets.TextInput):
    template_name = 'main/widget_download.html'

    def get_context(self, name, value, attrs):
        try:
            self.download_url = "/submission/"+str(self.object_instance.parent_submission.id)+"/downloadfile/?file_path="+self.object_instance.path + self.object_instance.name
        except AttributeError as e:
            #TODO: I think this error occurs sometimes during form loading, because these widgets get called multiple times.
            #      Not sure though. Even if that is true, it seems like a code smell.
            logger.error("error adding download url to editfiles widget: " + str(e))
            self.download_url = ""
        return {
            'widget': {
                'name': name,
                'is_hidden': self.is_hidden,
                'required': self.is_required,
                'value': self.format_value(value),
                'attrs': self.build_attrs(self.attrs, attrs),
                'template_name': self.template_name,
                'download_url': self.download_url 
            },
        }

GitFileFormSet = inlineformset_factory(
    m.Submission,
    m.GitFile,
    form=GitFileForm,
    fields=('name','path','tag','description','md5','size','date'),
    extra=0,
    can_delete=False,
    widgets={
        'name': DownloadGitFileWidget(),
        'description': Textarea(attrs={'rows':1, 'class': 'shortarea'}) }
)

GitFileReadOnlyFileFormSet = inlineformset_factory(
    m.Submission,
    m.GitFile,
    form=GitFileReadOnlyFileForm,
    fields=('name','path','tag','description','md5','size','date'),
    extra=0,
    can_delete=False,
    widgets={
        'name': DownloadGitFileWidget(),
        'description': Textarea(attrs={'rows':1, 'class': 'shortarea'})}
)

class GitFileFormSetHelper(FormHelper):
     def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form_method = 'post'
        self.form_class = 'form-inline'
        self.template = 'main/crispy_templates/table_inline_formset_custom_gitfile.html'
        self.form_tag = False
        self.layout = Layout(
            Field('path', th_class="w-50"),
            Field('tag'),
            Field('description'),
        )
        self.render_required_fields = True

############# Submission/Edition/Curation/Verification Views Forms #############

#------------- Base Submission -------------

# def popover_html(field):
#     html = field.verbose_name
#     if(field.help_text != ""):
#         html += '<button type="button" class="btn btn-secondary" data-toggle="tooltip" data-placement="top" title="'+field.help_text+'">?</button>'
#     return html

# def popover_html(label, content):
#     return label + '<button type="button" class="btn btn-secondary" data-toggle="tooltip" data-placement="top" title="'+content+'">?</button>'
    # ' <a tabindex="0" role="button" data-toggle="popover" data-html="true" \
    #                         data-trigger="hover" data-placement="auto" data-content="' + content + '"> \
    #                         <span class="glyphicon glyphicon-info-sign"></span></a>'

class SubmissionBaseForm(forms.ModelForm):
    class Meta:
        model = m.Submission
        fields = ['high_performance','contents_gis','contents_proprietary','contents_proprietary_sharing']
        labels = label_gen(model, fields)

class SubmissionForm_Admin(SubmissionBaseForm):
    pass

class SubmissionForm_Author(SubmissionBaseForm):
    pass

class SubmissionForm_Editor(ReadOnlyFormMixin, SubmissionBaseForm):
    pass

class SubmissionForm_Curator(ReadOnlyFormMixin, SubmissionBaseForm):
    pass

class SubmissionForm_Verifier(ReadOnlyFormMixin, SubmissionBaseForm):
    pass

SubmissionForms = {
    "Admin": SubmissionForm_Admin,
    "Author": SubmissionForm_Author,
    "Editor": SubmissionForm_Editor,
    "Curator": SubmissionForm_Curator,
    "Verifier": SubmissionForm_Verifier,
}

class ReadOnlySubmissionForm(ReadOnlyFormMixin, SubmissionBaseForm):
    pass

#------------- Edition -------------

class EditionBaseForm(forms.ModelForm):
    class Meta:
        model = m.Edition
        fields = ['_status','report']
        labels = label_gen(model, fields)

    def __init__ (self, *args, previous_vmetadata=None, **kwargs):
        super(EditionBaseForm, self).__init__(*args, **kwargs)
        # self.fields['report'].widget.attrs['class'] = 'smallerarea'
        # self.helper = FormHelper(self)
        # self.helper.form_show_errors = False
        # self.form_show_errors = False

    def has_changed(self, *args, **kwargs):
        return True #this is to ensure the form is always saved, so that notes created will be connected to the right part of the cycle

    def clean(self):
        form_data = self.cleaned_data
        if form_data['_status'] == m.Edition.Status.NEW:
            self._errors['_status'] = ['Review must have a status other than ' + m.Edition.Status.NEW + '.']
        

class EditionForm_Admin(EditionBaseForm):
    pass

# #TODO: I'm not sure that we need an Author form for this objects, as they never see it.
# class EditionForm_Author(ReadOnlyFormMixin, EditionBaseForm):
#     class Meta:
#         model = m.Edition
#         fields = []

class EditionForm_Editor(EditionBaseForm):
    pass

class EditionForm_Curator(ReadOnlyFormMixin, EditionBaseForm):
    pass

class EditionForm_Verifier(ReadOnlyFormMixin, EditionBaseForm):
    pass

EditionSubmissionFormsets = {}
for role_str in list_of_roles:
    try:
        EditionSubmissionFormsets[role_str] = inlineformset_factory(
            m.Submission, 
            m.Edition, 
            extra=1 if(role_str == "Admin" or role_str == "Editor") else 0,
            form=getattr(sys.modules[__name__], "EditionForm_"+role_str),
            can_delete = False,
        ) 
    except AttributeError:
        pass #If no form for role we should never show the form, so pass

#We just hide edition entirely when its not readable, so no role-based forms
class ReadOnlyEditionForm(ReadOnlyFormMixin, EditionBaseForm):
    pass

ReadOnlyEditionSubmissionFormset = inlineformset_factory(
    m.Submission, 
    m.Edition, 
    extra=0,
    form=ReadOnlyEditionForm,
    can_delete = False,
)

#------------- Curation -------------

class CurationBaseForm(forms.ModelForm):
    class Meta:
        model = m.Curation
        fields = ['_status','report','needs_verification']
        labels = label_gen(model, fields)

    def __init__ (self, *args, previous_vmetadata=None, **kwargs):
        super(CurationBaseForm, self).__init__(*args, **kwargs)
        # self.fields['report'].widget.attrs['class'] = 'smallerarea'

    def has_changed(self, *args, **kwargs):
        return True #this is to ensure the form is always saved, so that notes created will be connected to the right part of the cycle

    def clean(self):
        form_data = self.cleaned_data
        if form_data['_status'] == m.Curation.Status.NEW:
            self._errors['_status'] = ['Review must have a status other than ' + m.Curation.Status.NEW + '.']

class CurationForm_Admin(CurationBaseForm):
    pass

# #TODO: I'm not sure that we need an Author/Editor form for these objects, as they never see them.
# class CurationForm_Author(ReadOnlyFormMixin, CurationBaseForm):
#     class Meta:
#         model = m.Curation
#         fields = []

# #TODO: I'm not sure that we need an Author/Editor form for these objects, as they never see them.
# class CurationForm_Editor(ReadOnlyFormMixin, CurationBaseForm):
#     class Meta:
#         model = m.Curation
#         fields = []

class CurationForm_Curator(CurationBaseForm):
    pass

class CurationForm_Verifier(ReadOnlyFormMixin, CurationBaseForm):
    pass

CurationSubmissionFormsets = {}
for role_str in list_of_roles:
    try:
        CurationSubmissionFormsets[role_str] = inlineformset_factory(
            m.Submission, 
            m.Curation, 
            extra=1 if(role_str == "Admin" or role_str == "Curator") else 0,
            form=getattr(sys.modules[__name__], "CurationForm_"+role_str),
            can_delete = False,
        ) 
    except AttributeError:
        pass #If no form for role we should never show the form, so pass

#We just hide curation entirely when its not readable, so no role-based forms
class ReadOnlyCurationForm(ReadOnlyFormMixin, CurationBaseForm):
    pass

ReadOnlyCurationSubmissionFormset = inlineformset_factory(
    m.Submission, 
    m.Curation, 
    extra=0,
    form=ReadOnlyCurationForm,
    can_delete = False,
)

#------------- Verification -------------

class VerificationBaseForm(forms.ModelForm):
    class Meta:
        model = m.Verification
        fields = ['_status','code_executability','report']
        labels = label_gen(model, fields)
    
    def __init__ (self, *args, previous_vmetadata=None, **kwargs):
        super(VerificationBaseForm, self).__init__(*args, **kwargs)
        # self.fields['report'].widget.attrs['class'] = 'smallerarea'
        
    def has_changed(self, *args, **kwargs):
        return True #this is to ensure the form is always saved, so that notes created will be connected to the right part of the cycle

    def clean(self):
        form_data = self.cleaned_data
        if form_data['_status'] == m.Verification.Status.NEW:
            self._errors['_status'] = ['Review must have a status other than ' + m.Verification.Status.NEW + '.']

class VerificationForm_Admin(VerificationBaseForm):
    pass

# #TODO: I'm not sure that we need an Author/Editor form for these objects, as they never see them.
# class VerificationForm_Author(ReadOnlyFormMixin, VerificationBaseForm):
#     class Meta:
#         model = m.Verification
#         fields = []

# #TODO: I'm not sure that we need an Author/Editor form for these objects, as they never see them.
# class VerificationForm_Editor(ReadOnlyFormMixin, VerificationBaseForm):
#     class Meta:
#         model = m.Verification
#         fields = []

class VerificationForm_Curator(ReadOnlyFormMixin, VerificationBaseForm):
    pass

class VerificationForm_Verifier(VerificationBaseForm):
    pass

VerificationSubmissionFormsets = {}
for role_str in list_of_roles:
    try:
        VerificationSubmissionFormsets[role_str] = inlineformset_factory(
            m.Submission, 
            m.Verification, 
            extra=1 if(role_str == "Admin" or role_str == "Verifier") else 0,
            form=getattr(sys.modules[__name__], "VerificationForm_"+role_str),
            can_delete = False,
        ) 
    except AttributeError:
        pass #If no form for role we should never show the form, so pass

#We just hide verification entirely when its not readable, so no role-based forms
class ReadOnlyVerificationForm(ReadOnlyFormMixin, VerificationBaseForm):
    pass

ReadOnlyVerificationSubmissionFormset = inlineformset_factory(
    m.Submission, 
    m.Verification, 
    extra=0,
    form=ReadOnlyVerificationForm,
    can_delete = False,
)

#------------ Verification Metadata - Main -------------

class VMetadataBaseForm(forms.ModelForm):
    class Meta:
        model = m.VerificationMetadata
        fields = ["operating_system", "packages_info", "software_info", "machine_type", "scheduler", "platform", "processor_reqs", "host_url", "memory_reqs"]
        #Note that many of these fields are actually hidden unless a user required high-performance compute. We don't enforce the requirement unless that is checked.
        always_required = ["operating_system", "machine_type", "scheduler", "platform", "processor_reqs", "host_url", "memory_reqs", "packages_info", "software_info"]
        labels = label_gen(model, fields, always_required)

    #NOTE: This is a hacky way to pass our vmetadata to be populated. It doesn't scale to formsets with more than one object.
    #      Eventually we'll have to copy all the vmetadatas, and that will probably require a refactor to pre-save all these objects and pass them as querysets.
    #      But I don't want to do this until things are more stable and I have tests working again.
    def __init__ (self, *args, previous_vmetadata=None, **kwargs):
        super(VMetadataBaseForm, self).__init__(*args, **kwargs)
        self.empty_permitted = False
        # self.fields['packages_info'].widget.attrs['class'] = 'smallerarea'
        # self.fields['software_info'].widget.attrs['class'] = 'smallerarea'

        if(previous_vmetadata):
            self.fields['operating_system'].initial = previous_vmetadata.operating_system
            self.fields['machine_type'].initial = previous_vmetadata.machine_type
            self.fields['scheduler'].initial = previous_vmetadata.scheduler
            self.fields['platform'].initial = previous_vmetadata.platform
            self.fields['processor_reqs'].initial = previous_vmetadata.processor_reqs
            self.fields['host_url'].initial = previous_vmetadata.host_url
            self.fields['memory_reqs'].initial = previous_vmetadata.memory_reqs
            self.fields['packages_info'].initial = previous_vmetadata.packages_info
            self.fields['software_info'].initial = previous_vmetadata.software_info

    def clean(self):
        #Accessing data without clean is sketchy, but since we are just checking the variable's existence (which only happens if its checked) its ok.
        if("high_performance" in self.data.keys()):
            machine_type = self.cleaned_data.get('machine_type')
            if(not machine_type):
                self.add_error('machine_type', 'This field is required.')

            scheduler = self.cleaned_data.get('scheduler')
            if(not scheduler):
                self.add_error('scheduler', 'This field is required.')

            platform = self.cleaned_data.get('platform')
            if(not platform):
                self.add_error('platform', 'This field is required.')

            processor_reqs = self.cleaned_data.get('processor_reqs')
            if(not processor_reqs):
                self.add_error('processor_reqs', 'This field is required.')

            host_url = self.cleaned_data.get('host_url')
            if(not host_url):
                self.add_error('host_url', 'This field is required.')

            memory_reqs = self.cleaned_data.get('memory_reqs')
            if(not memory_reqs):
                self.add_error('memory_reqs', 'This field is required.')


class VMetadataForm_Admin(VMetadataBaseForm):
    pass

class VMetadataForm_Author(VMetadataBaseForm):
    pass

class VMetadataForm_Editor(ReadOnlyFormMixin, VMetadataBaseForm):
    pass

class VMetadataForm_Curator(VMetadataBaseForm):
    pass

class VMetadataForm_Verifier(VMetadataBaseForm):
    pass

VMetadataSubmissionFormsets = {}
for role_str in list_of_roles:
    try:
        VMetadataSubmissionFormsets[role_str] = inlineformset_factory(
            m.Submission, 
            m.VerificationMetadata, 
            extra=1 if(role_str == "Admin" or role_str == "Author" or role_str == "Curator" or role_str == "Verifier") else 0,
            form=getattr(sys.modules[__name__], "VMetadataForm_"+role_str),
            can_delete = False,
        ) 
    except AttributeError:
        pass #If no form for role we should never show the form, so pass

class ReadOnlyVMetadataForm(ReadOnlyFormMixin, VMetadataBaseForm):
    pass

ReadOnlyVMetadataSubmissionFormset = inlineformset_factory(
    m.Submission, 
    m.VerificationMetadata, 
    extra=0,
    form=ReadOnlyVMetadataForm,
    can_delete = False,
)

# VMetadataSubmissionFormset = inlineformset_factory(
#     m.Submission,
#     m.VerificationMetadata,  
#     extra=1,
#     form=VMetadataForm,
#     fields=("operating_system","machine_type", "scheduler", "platform", "processor_reqs", "host_url", "memory_reqs"),
#     can_delete = True,
# )

#------------ Verification Metadata - Software -------------

class VMetadataSoftwareBaseForm(forms.ModelForm):
    class Meta:
        model = m.VerificationMetadataSoftware
        fields = ["name","version"]
        labels = label_gen(model, fields)

    # def __init__ (self, *args, **kwargs):
    #     super(VMetadataSoftwareForm, self).__init__(*args, **kwargs)

class VMetadataSoftwareForm_Admin(VMetadataSoftwareBaseForm):
    pass

class VMetadataSoftwareForm_Author(VMetadataSoftwareBaseForm):
    pass

class VMetadataSoftwareForm_Editor(ReadOnlyFormMixin, VMetadataSoftwareBaseForm):
    pass

class VMetadataSoftwareForm_Curator(VMetadataSoftwareBaseForm):
    pass

class VMetadataSoftwareForm_Verifier(VMetadataSoftwareBaseForm):
    pass

VMetadataSoftwareVMetadataFormsets = {}
for role_str in list_of_roles:
    try:
        VMetadataSoftwareVMetadataFormsets[role_str] = inlineformset_factory(
            m.VerificationMetadata,  
            m.VerificationMetadataSoftware,  
            extra=1 if(role_str == "Admin" or role_str == "Author" or role_str == "Curator" or role_str == "Verifier") else 0,
            form=getattr(sys.modules[__name__], "VMetadataSoftwareForm_"+role_str),
            can_delete = True,
        ) 
    except AttributeError:
        pass #If no form for role we should never show the form, so pass

# VMetadataSoftwareVMetadataFormset = inlineformset_factory(
#     m.VerificationMetadata,  
#     m.VerificationMetadataSoftware,  
#     extra=1,
#     form=VMetadataSoftwareForm,
#     fields=("name","version", "code_repo_url"),
#     can_delete = True,
# )

class ReadOnlyVMetadataSoftwareForm(ReadOnlyFormMixin, VMetadataSoftwareBaseForm):
    pass

ReadOnlyVMetadataSoftwareVMetadataFormset = inlineformset_factory(
    m.VerificationMetadata,  
    m.VerificationMetadataSoftware,  
    extra=0,
    form=ReadOnlyVMetadataSoftwareForm,
    can_delete = False,
)

#------------ Verification Metadata - Badge -------------

class VMetadataBadgeBaseForm(forms.ModelForm):
    class Meta:
        model = m.VerificationMetadataBadge
        fields = ["name","badge_type","version","definition_url","logo_url","issuing_org","issuing_date","verification_metadata"]
        labels = label_gen(model, fields)

    # def __init__ (self, *args, **kwargs):
    #     super(VMetadataBadgeForm, self).__init__(*args, **kwargs)

class VMetadataBadgeForm_Admin(VMetadataBadgeBaseForm):
    pass

class VMetadataBadgeForm_Curator(VMetadataBadgeBaseForm):
    pass

#No forms for other roles as they cannot view

VMetadataBadgeVMetadataFormsets = {}
for role_str in list_of_roles:
    try:
        VMetadataBadgeVMetadataFormsets[role_str] = inlineformset_factory(
            m.VerificationMetadata,  
            m.VerificationMetadataBadge,  
            extra=1 if(role_str == "Admin" or role_str == "Curator" ) else 0,
            form=getattr(sys.modules[__name__], "VMetadataBadgeForm_"+role_str),
            can_delete = False,
        ) 
    except AttributeError:
        pass #If no form for role we should never show the form, so pass

# VMetadataBadgeVMetadataFormset = inlineformset_factory(
#     m.VerificationMetadata,  
#     m.VerificationMetadataBadge,  
#     extra=1,
#     form=VMetadataBadgeForm,
#     fields=("name","type","version","definition_url","logo_url","issuing_org","issuing_date","verification_metadata"),
#     can_delete = True,
# )

class ReadOnlyVMetadataBadgeForm(ReadOnlyFormMixin, VMetadataBadgeBaseForm):
    pass

ReadOnlyVMetadataBadgeVMetadataFormset = inlineformset_factory(
    m.VerificationMetadata,  
    m.VerificationMetadataBadge,  
    extra=0,
    form=ReadOnlyVMetadataBadgeForm,
    can_delete = False,
)

#------------ Verification Metadata - Audit -------------

class VMetadataAuditBaseForm(forms.ModelForm):
    class Meta:
        model = m.VerificationMetadataAudit
        fields = ["name","version","url","organization","verified_results","exceptions","exception_reason"]
        labels = label_gen(model, fields)

    # def __init__ (self, *args, **kwargs):
    #     super(VMetadataAuditForm, self).__init__(*args, **kwargs)


class VMetadataAuditForm_Admin(VMetadataAuditBaseForm):
    pass

class VMetadataAuditForm_Curator(VMetadataAuditBaseForm):
    pass

#No forms for other roles as they cannot view

VMetadataAuditVMetadataFormsets = {}
for role_str in list_of_roles:
    try:
        VMetadataAuditVMetadataFormsets[role_str] = inlineformset_factory(
            m.VerificationMetadata,  
            m.VerificationMetadataAudit,  
            extra=1 if(role_str == "Admin" or role_str == "Curator") else 0,
            form=getattr(sys.modules[__name__], "VMetadataAuditForm_"+role_str),
            can_delete = False,
        ) 
    except AttributeError:
        pass #If no form for role we should never show the form, so pass


# VMetadataAuditVMetadataFormset = inlineformset_factory(
#     m.VerificationMetadata,  
#     m.VerificationMetadataAudit,  
#     extra=1,
#     form=VMetadataAuditForm,
#     fields=("name","version","url","organization","verified_results","code_executability","exceptions","exception_reason"),
#     can_delete = True,
# )

class ReadOnlyVMetadataAuditForm(ReadOnlyFormMixin, VMetadataAuditBaseForm):
    pass

ReadOnlyVMetadataAuditVMetadataFormset = inlineformset_factory(
    m.VerificationMetadata,  
    m.VerificationMetadataAudit,  
    extra=0,
    form=ReadOnlyVMetadataAuditForm,
    can_delete = False,
)








#OK, so my code is able to create a new form with changed fields and then pass it to a dynamically created formset
#The next question becomes whether its really worth it?
#... well, we can use the "non-dynamic" forms for admin and just generate one for each of the four roles
#... meh, I think its actually better to just re-define the form for admin with no changes
#... This also scales ok because it preserves any other configuration done in the base form
#... ... Well except for the formset_factory which is defined twice currently. Maybe I can use type() to subclass it as well.
#... ... Doesn't seem to work as expected. I don't understand factory functions

# What is my plan?
# Define all forms manually, using inheritance
# Define formsets programatically, using type?






##### SEMI WORKING TEST

# testfactorydict = {}
# for x in range(5):
#     afield = VMetadataForm.base_fields['operating_system']
#     afield.disabled = True
#     field_defs = {
#         'operating_system': afield
#         }
#     DynamicFormClass = type("DynamicForm"+str(x), (VMetadataForm,), field_defs)

#     # formset_defs = {
#     #     'form': DynamicFormClass
#     #     }
#     # testfactorydict[str(x)] = type("DynamicFormset"+str(x), (VMetadataSubmissionFormset,), formset_defs)
#     testfactorydict[str(x)] = inlineformset_factory(
#         m.Submission,
#         m.VerificationMetadata,  
#         extra=1,
#         form=VMetadataForm,
#         fields=("operating_system","machine_type", "scheduler", "platform", "processor_reqs", "host_url", "memory_reqs"),
#         can_delete = True,
#     )


##### NOT WORKING JUNK

#Input: takes your inlineformset_factory, a list of disabled fields, a list of fields to remove
#Output: a new inlineformset_factory with these fields changed
# def inlineformset_factory_restrictor(if_factory, disable_fields, remove_fields):
#     altered_if_factory = copy.deepcopy(if_factory)
#     altered_if_form = copy.deepcopy(altered_if_factory.form)
#     #print(altered_if_factory.form.base_fields)
#     altered_if_factory.form = altered_if_form
#     #altered_if_factory.form.base_fields['host_url'].disabled = True
#     return altered_if_factory  

#VMetadataSubmissionFormsetRestrictTest = inlineformset_factory_restrictor(VMetadataSubmissionFormset, [], [])

    #testfactorydict[str(x)] = VMetadataSubmissionFormset

    # testfactorydict[str(x)] = inlineformset_factory(
    #     m.Submission,
    #     m.VerificationMetadata,  
    #     extra=1,
    #     form=DynamicFormClass,
    #     fields=("operating_system","machine_type", "scheduler", "platform", "processor_reqs", "host_url", "memory_reqs"),
    #     can_delete = True,
    # )


# class GitFileForm(forms.ModelForm):
#     class Meta:
#         model = m.GitFile
#         fields = ['path']

#     def __init__ (self, *args, **kwargs):
#         super(GitFileForm, self).__init__(*args, **kwargs)
#         self.fields['path'].widget.object_instance = self.instance
#         self.fields['path'].disabled = True
#         self.fields['md5'].disabled = True
#         self.fields['size'].disabled = True
#         self.fields['date'].disabled = True