from django.shortcuts import render, get_object_or_404, redirect, render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core import serializers
from django.views import generic
from django.forms.models import model_to_dict
from polls.forms import *
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core.exceptions import ObjectDoesNotExist
from polls.models import *
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import RequestContext
from ast import literal_eval

import json
import datetime
import random
import csv


def LoginPage(request):
    # Like before, obtain the context for the user's request.
    context = RequestContext(request)

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        user = User.objects.get(username=username)
        user.backend='django.contrib.auth.backends.ModelBackend'

        # If we have a User object, the details are correct.
        # If None (Python's way of representing the absence of a value), no user
        # with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the account is valid and active, we can log the user in.
                # We'll send the user back to the homepage.
                login(request, user)
                return HttpResponseRedirect('/entry/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your account is disabled.")
        else:
            return HttpResponse("Invalid login details supplied.")

    # The request is not a HTTP POST, so display the login form.
    # This scenario would most likely be a HTTP GET.
    else:
        # No context variables to pass to the template system, hence the
        # blank dictionary object...
        return render_to_response('login.html', {}, context)


def register(request):
    # Like before, get the request's context.
    context = RequestContext(request)

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    registered = False
    entries = Entry.objects.filter(practice=False)

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)

        if user_form.is_valid():
            user = user_form.save()
            user.backend='django.contrib.auth.backends.ModelBackend'
            user.save()

            '''
            eids = request.POST.getlist("entry")
            for e in eids:
                e = int(e)
            # eids = random.sample([e.eid for e in entries], 5)
            '''
            profile = UserProfile(user=user,
                                  date_created=datetime.datetime.utcnow(),
                                  designated_entries=[],
                                  index_of_last_completed_entry=0,
                                  is_expert=user_form.cleaned_data["expert"],
                                  is_nominal=user_form.cleaned_data["nominal"])
            profile.save()

            login(request, user)

            return HttpResponseRedirect('/passage/')

        else:
            print user_form.errors

    else:
        user_form = UserForm()
        user_form.fields['expert'].label = "Expertise Status"
        user_form.fields['nominal'].label = "Experimental Setup"

    # Render the template depending on the context.
    return render_to_response(
        'register.html',
        {'user_form': user_form, 'registered': registered, 'entries': entries}, context)


def AssignPassage(request):
    # Like before, get the request's context.
    context = RequestContext(request)

    # A boolean value for telling the template whether the registration was successful.
    # Set to False initially. Code changes value to True when registration succeeds.
    #registered = False
    entries = Entry.objects.filter(practice=False)

    # If it's a HTTP POST, we're interested in processing data.
    if request.method == 'POST':
        eids = request.POST.getlist("entries")
        p = UserProfile.objects.get(user=request.user)
        p.designated_entries = [41, 42] + eids
        p.save()

        return HttpResponseRedirect('/login/')

    # Else, we set up the page for entering data.
    else:
        ups = UserProfile.objects.all()
        # assume a maximum of 50 entries here
        userlist = [None] * 50
        for e in entries:
            userlist[e.eid] = {"entry": e, "users": []}
        for up in ups:
            for eid in list(literal_eval(up.designated_entries))[2:]:
                userlist[int(eid)]['users'].append(up.user.username)


    return render_to_response(
        'passage-assign.html',
        {'userlist': userlist, 'user': request.user}, context)


@login_required
def EntryPage(request):
    data = {}

    p = UserProfile.objects.get(user=request.user)
    rand_entries = list(literal_eval(p.designated_entries))
    plen = len(rand_entries)
    if plen == 0:
        return HttpResponseRedirect("/login/")
    if plen == p.index_of_last_completed_entry:
        p.index_of_last_completed_entry = 2
        p.save()
        return HttpResponseRedirect("/completed/")
    else:
        e_id = rand_entries[p.index_of_last_completed_entry]
        e = Entry.objects.get(eid=e_id)
        for t in Tag.objects.filter(num_votes=0):
            t.delete()
        try:
            es = EntrySpecifics.objects.get(entry=e, user=request.user)
        except ObjectDoesNotExist:
            # initialize the entry_specifics and tag_specifics of this page
            es = EntrySpecifics(entry=e, date_time=datetime.datetime.utcnow(), user=request.user)
            es.save()
            if p.is_nominal == False:
                tags = Tag.objects.filter(entry=e)
                for tag in tags:
                    ts = TagSpecifics(entry_specifics=es, tag=tag, entry_date=datetime.datetime.utcnow(),
                                      upvoted=False)
                    ts.save()
        data["entry_id"] = e.eid
        data["es_id"] = es.euuid
        if e.practice:
            data["title"] = "PRACTICE PASSAGE #" + str(e.eid-40)
        else:
            data["title"] = "PASSAGE #" + str(p.index_of_last_completed_entry-1)
        data["entry"] = e.entry
        data["tag_specifics"] = TagSpecifics.objects.filter(entry_specifics=es)

    # Add tag form
    add_tag_form = AddTagForm()
    add_tag_form.es_id = es.euuid
    return render_to_response(
        'entry.html',
        {"data": data, 'add_tag_form': add_tag_form, "es_id": es.euuid},
        context_instance=RequestContext(request, {'euuid': es.euuid}))

    return render(request, "entry.html", {})


def NewEntryPage(request):
    data = []
    return render(request, "new_entry.html", {"data": data})


def completedPage(request):
    return render(request, "completed.html")


@ensure_csrf_cookie
def nextEntry(request):
    p = UserProfile.objects.get(user=request.user)
    p.index_of_last_completed_entry = p.index_of_last_completed_entry + 1
    p.save()
    return HttpResponseRedirect('/entry/')


@ensure_csrf_cookie
def previousEntry(request):
    p = UserProfile.objects.get(user=request.user)
    if p.index_of_last_completed_entry != 0:
        p.index_of_last_completed_entry = p.index_of_last_completed_entry - 1
        p.save()
    return HttpResponseRedirect('/entry/')


@ensure_csrf_cookie
def addEntry(request):
    newEntry = request.POST.get("input_text")
    entryNumber = request.POST.get("entry_number")
    responseData = {}
    try:
        e = Entry.objects.get(eid=entryNumber)
        e.entry = newEntry
        e.pub_date = datetime.datetime.utcnow()
        e.save()
        responseData["success"] = True
        responseData["entry_existed"] = True
    except ObjectDoesNotExist:
        e = Entry(eid=entryNumber, entry=newEntry, pub_date=datetime.datetime.utcnow(), practice=False)
        e.save()
        responseData["success"] = True
        responseData["entry_existed"] = False
    return HttpResponse(json.dumps(responseData), content_type="application/json")


def scroll(request):
    e = request.POST.get("entry")
    e.scroll = True
    return


# exception: here in nominal group, if someone add a tag that others have added (but he cannot see it)
# another Tag object will be created.
@ensure_csrf_cookie
def addTag(request, es_id):
    add_tag_form = AddTagForm(data=request.POST)
    es = EntrySpecifics.objects.get(euuid=es_id)
    text = request.POST.get("tag")
    try:
        t = Tag.objects.get(tag=text)
        # only happen when someone in nominal group added a tag that someone have added before
        # (cause he can't see it and he should not know that someone else have added the same thing)
        if TagSpecifics.objects.get(entry_specifics=es, tag=t) is None:
            t.num_votes += 1
            t.save()
            ts = TagSpecifics(entry_specifics=es, tag=t, entry_date=datetime.datetime.utcnow(),
                              upvoted=True)
            ts.save()
    except ObjectDoesNotExist:
        t = Tag(entry=es.entry, tag=text, num_votes=1)
        t.save()
        ts = TagSpecifics(entry_specifics=es, tag=t, entry_date=datetime.datetime.utcnow(),
                          upvoted=True)
        ts.save()
    return HttpResponseRedirect('/entry/')


def Increment(request):
    responseData = {}
    tsid = request.POST.get("tid")
    ts = TagSpecifics.objects.get(tsid=tsid)
    t = ts.tag
    if ts.upvoted is False:
        t.num_votes = t.num_votes + 1
        t.save()
        ts.upvoted = True
        ts.entry_date = datetime.datetime.utcnow()
        ts.save()
        responseData["success"] = True
    else:
        responseData["success"] = False
    return HttpResponse(json.dumps(responseData), content_type="application/json")


def Decrement(request):
    responseData = {}
    tsid = request.POST.get("tid")
    ts = TagSpecifics.objects.get(tsid=tsid)
    t = ts.tag
    if ts.upvoted is True:
        t.num_votes = t.num_votes - 1
        t.save()
        ts.upvoted = False
        ts.entry_date = datetime.datetime.utcnow()
        ts.save()
        responseData["success"] = True
    else:
        responseData["success"] = False
    return HttpResponse(json.dumps(responseData), content_type="application/json")



def OutputData(request):
    context = RequestContext(request)
    ups = UserProfile.objects.all()
    tags = Tag.objects.all()
    return render_to_response('output.html', {'ups': ups, 'tags': tags}, context)

def OutputUsersInfo(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="user_info.csv"'
    writer = csv.writer(response)
    writer.writerow(['User ID', 'Expertise Level', 'Experimental Setup', 'Time Created', 'Entries assigned'])
    for up in UserProfile.objects.all():
        if up.designated_entries != '[]':
            if up.is_expert:
                el = 'expert'
            else:
                el = 'novice'
            if up.is_nominal:
                es = 'nominal'
            else:
                es = 'social'
            entries = []
            for eid in list(literal_eval(up.designated_entries))[2:]:
                entries.append(int(eid))
            writer.writerow([up.user_id, el, es, str(up.date_created), str(entries)])
    return response

def OutputPassagesInfo(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="passage_info.csv"'
    writer = csv.writer(response)
    writer.writerow(['Passage ID', 'User IDs', 'Title'])
    entrylist = [None] * 50
    for e in Entry.objects.filter(practice=False):
        entrylist[e.eid] = {'entry': e, 'users': []}
    for up in UserProfile.objects.all():
        for eid in list(literal_eval(up.designated_entries))[2:]:
            entrylist[int(eid)]['users'].append(up.user_id)
    for eobj in entrylist:
        if eobj:
            e = eobj['entry']
            title = ""
            for t in e.title:
                if t == "'":
                    title = title + '\''
                elif t == '"':
                    title = title + '\"'
                else:
                    title = title + t
            writer.writerow([e.eid, str(eobj['users']), title])
    return response

def OutputTagsInfo(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tag_info.csv"'
    writer = csv.writer(response)
    writer.writerow(['Tag ID', 'Tag', 'Votes', 'Entry ID'])
    for t in Tag.objects.all():
        writer.writerow([t.tid, t.tag, t.num_votes, t.entry.eid])
    return response

def OutputUserInfo(request):
    if request.method == 'POST':
        userid = request.POST.get('user')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="user_' + userid + '_info.csv"'
        writer = csv.writer(response)
        writer.writerow(['Entry ID', 'Tag ID', 'Tag', 'Time Updated'])
        ess = EntrySpecifics.objects.filter(user_id=userid)
        for es in ess:
            tss = TagSpecifics.objects.filter(entry_specifics_id=es.euuid, upvoted=True)
            for ts in tss:
                writer.writerow([es.entry_id, ts.tag_id, ts.tag.tag, ts.entry_date])
        return response
    else:
        return HttpResponse("Wrong data. No user selected. ")

def OutputTagInfo(request):
    if request.method == 'POST':
        tid = request.POST.get('tag')
        tag = Tag.objects.get(tid=tid)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tag_' + tag.tag + '_info.csv"'
        writer = csv.writer(response)
        writer.writerow(['User ID', 'Expertise Level', 'Experimental Setup', 'Time Updated'])
        tss = TagSpecifics.objects.filter(tag=tag)
        for ts in tss:
            es = EntrySpecifics.objects.get(euuid=ts.entry_specifics_id)
            up = UserProfile.objects.get(user_id=es.user_id)
            if up.is_expert:
                el = 'expert'
            else:
                el = 'novice'
            if up.is_nominal:
                es = 'nominal'
            else:
                es = 'social'
            writer.writerow([up.user_id, el, es, ts.entry_date])
        return response
    else:
        return HttpResponse("Wrong data. No tag selected. ")