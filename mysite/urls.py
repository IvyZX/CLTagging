from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

from polls.views import *

urlpatterns = patterns('',

    url(r'^$', LoginPage),
    url(r'^entry/$', EntryPage),
    url(r'^new/$', NewEntryPage),
    url(r'^login/$', LoginPage),
    url(r'^register/$', register, name='register'),
    url(r'^passage/$', AssignPassage),
    
    url(r'^add/(?P<es_id>[-\w]+)$', addTag),
    url(r'^addNewEntryFunc/$', addEntry),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^next/$', nextEntry),
    url(r'^prev/$', previousEntry),
    url(r'^completed/$', completedPage),

    url(r'^increment/$', Increment),
    url(r'^decrement/$', Decrement),

    url(r'^output/$', OutputData),
    url(r'^output_users/$', OutputUsersInfo),
    url(r'^output_passages/$', OutputPassagesInfo),
    url(r'^output_tags/$', OutputTagsInfo),
    url(r'^output_user/$', OutputUserInfo),
    url(r'^output_tag/$', OutputTagInfo),
)

# add new entry - PAGE
# view the entry - PAGE
# add tags for the entry
# view tags for the entry
# upvote/downvote tags for the entry

# render newly added tags for entry