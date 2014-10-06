from django.contrib import admin
from polls.models import *

# Register your models here.

class TagInline(admin.TabularInline):
	model = Tag
	extra = 5

class EntryInline(admin.TabularInline):
	model = Entry
	extra = 5

class UserInline(admin.TabularInline):
	model = User
	extra = 5

class EntrySpecificsInline(admin.TabularInline):
    model = EntrySpecifics
    extra = 5

class TagSpecificsInline(admin.TabularInline):
    model = TagSpecifics
    extra = 5

class EntryAdmin(admin.ModelAdmin):
	fieldsets = [
		(None,				{'fields':['eid']}),
		(None,		 		{'fields':['entry']}),
		(None,	 			{'fields':['pub_date']}),
	]
	inlines = [TagInline]
	
class UserProfileInline(admin.TabularInline):
	model = UserProfile
	extra = 5

class UserProfileAdmin(admin.ModelAdmin):
	fieldsets = []


class BaseModelAdmin(admin.ModelAdmin):
	fieldsets = [
		(None, 				{'fields':['designated_entries']}),
	]

admin.site.register(Entry, EntryAdmin)
admin.site.register(EntrySpecifics)
admin.site.register(Tag)
admin.site.register(TagSpecifics)
admin.site.register(UserProfile, UserProfileAdmin)



# class ChoiceInLine(admin.TabularInline):
# 	model = Choice
# 	extra = 3

# class PollAdmin(admin.ModelAdmin):
# 	#fields = ['pub_date', 'question']
# 	fieldsets = [
# 		(None, 				 {'fields':['question']}),
# 		('Date information', {'fields':['pub_date'], 'classes':['collapse']}),
# 	]
# 	inlines=[ChoiceInLine]
# 	list_display = ('question', 'pub_date', 'was_published_recently')
# 	list_filter = ['pub_date']
# 	search_fields = ['question']

# admin.site.register(Poll, PollAdmin)