import gitlab, logging, os, re, random, string
logger = logging.getLogger(__name__)  

#https://docs.gitlab.com/ee/api/users.html#user-creation
def gitlab_create_user(django_user):
    gl = gitlab.Gitlab(os.environ["GIT_LAB_URL"], private_token=os.environ["GIT_PRIVATE_ADMIN_TOKEN"])
    #gl.enable_debug()
    gitlab_user = gl.users.create({
                        'email': "fakeemail"+str(django_user.id)+"@odum.unc.edu", #we set this wrong as a security measure
                        'force_random_password': True,
                        'username': django_user.username,
                        'name': django_user.email, #We use email becasue when we create the user there is no username info.
                        'external':True, 
                        'private_profile':True , 
                        'skip_confirmation':True,
                         #TODO: Once this issue is fixed, remove our random password generation. https://gitlab.com/gitlab-org/gitlab/-/issues/25802
                        'password' : ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(20))})
    django_user.gitlab_id = gitlab_user.id                   
    django_user.save()

#TODO: Add update user command to update on users.account_user_details() changes
def gitlab_update_user(django_user):
    gl = gitlab.Gitlab(os.environ["GIT_LAB_URL"], private_token=os.environ["GIT_PRIVATE_ADMIN_TOKEN"])
    #gl.enable_debug()
    logger.debug(django_user.__dict__)

    #TODO: is this efficient? I feel like it may be doing multiple calls under the hood...

    gl_user = gl.users.get(django_user.gitlab_id)
    if(not django_user.first_name or not django_user.last_name):
        gl_user.name = django_user.first_name + " " + django_user.last_name
    else: #this case should never hit on update, but just in case
        gl_user.name = django_user.email
    gl_user.username = django_user.username
    gl_user.save()


#https://docs.gitlab.com/ee/api/members.html#add-a-member-to-a-group-or-project
#https://docs.gitlab.com/ee/api/members.html top has info on access levels
#http://vlabs.iitb.ac.in/gitlab/help/user/permissions.md useful about access levels
def gitlab_add_user_to_manuscript_repo(django_user, manuscript):
    gl = gitlab.Gitlab(os.environ["GIT_LAB_URL"], private_token=os.environ["GIT_PRIVATE_ADMIN_TOKEN"])
    #gl.enable_debug()
    gl_project = gl.projects.get(manuscript.gitlab_id)
    #TODO: what happens if a member already exists?
    gl_project.members.create({'user_id': django_user.gitlab_id, 'access_level':
                                gitlab.DEVELOPER_ACCESS})


def gitlab_remove_user_from_manuscript_repo(django_user, manuscript):
    pass

def gitlab_create_manuscript_repo(manuscript):
    gl = gitlab.Gitlab(os.environ["GIT_LAB_URL"], private_token=os.environ["GIT_PRIVATE_ADMIN_TOKEN"])
    gitlab_project = gl.projects.create({'name': str(manuscript.id) + " - " + re.sub('[^a-zA-Z0-9_. -]' ,'' ,manuscript.title)}) #gitlab only allows certain characters for titles
    manuscript.gitlab_id = gitlab_project.id
    manuscript.save()

#TODO: What is the output of this?
#TODO: I think this errors if there are no files in the repo? "tree not found"
def gitlab_repo_get_file_folder_list(manuscript):
    logger.debug(manuscript.__dict__)
    gl = gitlab.Gitlab(os.environ["GIT_LAB_URL"], private_token=os.environ["GIT_PRIVATE_ADMIN_TOKEN"])
    gl.enable_debug()
    try:
        repo_tree = gl.projects.get(manuscript.gitlab_id).repository_tree()
    except gitlab.GitlabGetError:
        repo_tree = []
    logger.debug(repo_tree)
    return repo_tree
    #GET /projects/:id/repository/tree
    #items = project.repository_tree(path='docs', ref='branch1')
    

# There is no api for this, impersonation tokens generated by the admin must be used
# def gitlab_generate_access_token(user, timeout=1):
#     pass

# This endpoint is so the admin can generate an access token as a different user
# This will be used by the end-user as well, as there is no way for admin to generate a normal access token via API (in April 2020)
# The difference between an impersonation token and a normal access token is nothing for our user cases
# The only difference is that the user can't see impersonation tokens via the UI, but CoReRe users should never see the UI anyways
#
# https://docs.gitlab.com/ee/api/users.html#create-an-impersonation-token
def gitlab_generate_impersonation_token(self, token_user, timeout=1):
    pass