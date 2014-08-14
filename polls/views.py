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
        p.designated_entries = [0, 1] + eids
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
                userlist[int(eid)]['users'].append(up.user_id)


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
        return HttpResponseRedirect("/passage/")
    if plen == p.index_of_last_completed_entry:
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
        data["pass_num"] = p.index_of_last_completed_entry + 1
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
    entryTitle = request.POST.get("entry_title")
    responseData = {}
    try:
        e = Entry.objects.get(eid=entryNumber)
        e.title = entryTitle
        e.entry = newEntry
        e.pub_date = datetime.datetime.utcnow()
        e.save()
        responseData["success"] = True
        responseData["entry_existed"] = True
    except ObjectDoesNotExist:
        e = Entry(eid=entryNumber, entry=newEntry, pub_date=datetime.datetime.utcnow(), title=entryTitle,
                  practice=False)
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


'''
def Decrement(request):
    es_id = request.POST.get('esid')
    es = EntrySpecifics.objects.get(euuid=es_id)
    thetid = request.POST.get("tid")
    t = Tag.objects.get(tid=tid)
    responseData = {}
    try:
        theTag = Tag.objects.get(tid=thetid)
        theTag.num_votes = theTag.num_votes - 1
        theTag.upvoted = False
        theTag.save()
        responseData["success"] = True
        #responseData["num_votes"] = theTag.num_votes
        #responseData["comments"] = 'Decremented the tag!'
    except Exception:
        responseData["success"] = False
        #responseData["comments"] = 'Could not decrement!'
    return HttpResponse(json.dumps(responseData), content_type="application/json")
'''


# use checkbox to do the voting
def vote(request, es_id):
    responseData = {}
    es = EntrySpecifics.objects.get(euuid=es_id)
    tids = request.POST.getlist("tag[]")
    current_ts = TagSpecifics.objects.filter(entry_specifics=es)
    # check whether the existed upvoted tags should be decremented in this update
    for ts in current_ts:
        if ts.upvoted:
            ts_id = ts.tag.tid
            if ts_id not in tids:
                t = ts.tag
                t.num_votes -= 1
                t.save()
                ts.upvoted = False
                ts.entry_date = datetime.datetime.utcnow()
                ts.save()
    # update the checked tags
    for tid in tids:
        t = Tag.objects.get(tid=tid)
        try:
            ts = TagSpecifics.objects.get(tag=t, entry_specifics=es)
        except ObjectDoesNotExist:
            ts = TagSpecifics(entry_specifics=es, tag=t, entry_date=datetime.datetime.utcnow(),
                              upvoted=True)
            ts.save()
            t.num_votes += 1
            t.save()
        if ts.upvoted is False:
            t.num_votes += 1
            t.save()
            ts.upvoted = True
            ts.entry_date = datetime.datetime.utcnow()
            ts.save()
    responseData["success"] = True
    return HttpResponseRedirect('/entry/')
    # return HttpResponse(json.dumps(responseData), content_type="application/json")


def OutputData(request):
    return render(request, 'output.html')


def OutputUserInfo(request):
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
