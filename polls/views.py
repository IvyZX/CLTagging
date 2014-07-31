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


def LoginPage(request):
    # Like before, obtain the context for the user's request.
    context = RequestContext(request)

    # If the request is a HTTP POST, try to pull out the relevant information.
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        username = request.POST['username']
        password = request.POST['password']

        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

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
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details: {0}, {1}".format(username, password)
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

    # If it's a HTTP POST, we're interested in processing form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we make use of both UserForm and UserProfileForm.
        user_form = UserForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid():

            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method.
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()

            # # Now sort out the UserProfile instance.
            # # Since we need to set the user attribute ourselves, we set commit=False.
            # # This delays saving the model until we're ready to avoid integrity problems.
            # profile = profile_form.save(commit=False)

            # randomly select two entries
            designated_entries = random.sample([e.eid for e in Entry.objects.all()], 5)

            profile = UserProfile(user=user,
                                  date_created=datetime.datetime.utcnow(),
                                  designated_entries=designated_entries,  # ",".join(designated_entries),
                                  index_of_last_completed_entry=0,
                                  is_expert=user_form.cleaned_data["expert"],
                                  is_nominal=user_form.cleaned_data["nominal"])

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the template registration was successful.
            registered = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()

    # Render the template depending on the context.
    return render_to_response(
        'register.html',
        {'user_form': user_form, 'registered': registered}, context)


@login_required
def EntryPage(request):
    data = {}
    context = RequestContext(request)

    p = UserProfile.objects.get(user=request.user)
    rand_entries = list(literal_eval(p.designated_entries))
    plen = len(rand_entries)

    if plen == p.index_of_last_completed_entry:
        # the user has completed his survey
        return HttpResponse("Thank you, your survey is complete.")
    else:
        e_id = rand_entries[p.index_of_last_completed_entry]
        e = Entry.objects.get(eid=e_id)

        try:
            es = EntrySpecifics.objects.get(entry=e, user=request.user)
        except ObjectDoesNotExist:
            es = EntrySpecifics(entry=e, date_time=datetime.datetime.utcnow(), user=request.user)
            es.save()

        data["entry_id"] = e.eid
        data["es_id"] = es.euuid
        data["pass_num"] = p.index_of_last_completed_entry + 1
        data["entry"] = e.entry

        # delete tags that has zero num_votes (i.e. no one have actually voted on it)
        # this will also delete the tagspecifics object
        for t in Tag.objects.filter(num_votes=0):
            t.delete()
        data["tag_specifics"] = TagSpecifics.objects.filter(entry_specifics=es)

        # load the available tags for this entry
        # load all tags of this entry if the user is in social group
        if p.is_nominal == False:
            data["tags"] = Tag.objects.filter(entry=e)
        # only load tags created by the user if the user is in nominal group
        else:
            tags = []
            for ts in data["tag_specifics"]:
                tags.append(ts.tag)
            data["tags"] = tags

        # load a record that checks the tag that had been added by the user
        for tag in data["tags"]:
            try:
                ts = TagSpecifics.objects.get(tag=tag, entry_specifics=es)
                tag.upvoted = ts.upvoted
            except ObjectDoesNotExist:
                tag.upvoted = False

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
        e = Entry(eid=entryNumber, entry=newEntry, pub_date=datetime.datetime.utcnow())
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

'''
def vote(request, es_id):
    tid = request.POST.get("id")
    up = request.POST.get("up")
    down = request.POST.get("down")
    responseData = {}
    #print (up,down)
    es = EntrySpecifics.objects.get(euuid=es_id)
    t = Tag.objects.get(tid=tid)
    ts = TagSpecifics.objects.get(tag=t)
    # when voted up; create new tag_specifics if not created before
    if (up == 'true'):
        if ts is None:
            ts = TagSpecifics(entry_specifics=es, tag=t, entry_date=datetime.datetime.utcnow(),
                              upvoted=False, entry=es.entry)
        if (ts.upvoted == False):
            t.num_votes += 1
            t.upvoted = True
            t.save()
    # when voted down; only works when ts is created before and it has upvoted = true
    else:
        if (ts != None & ts.upvoted == True):
            t.num_votes -= 1
            t.upvoted = True
            t.save()
    responseData["success"] = True
    return HttpResponse(json.dumps(responseData), content_type="application/json")
'''

def Increment(request):
    t = request.POST.get("tid")
    responseData = {}
    try:
        myTag = Tag.objects.get(tid=t)
        myTag.num_votes = myTag.num_votes + 1
        myTag.save()
        responseData["success"] = True
        responseData["num_votes"] = myTag.num_votes
        responseData["comments"] = 'Incremented the tag!'
    except Exception:
        responseData["success"] = False
        responseData["comments"] = 'Could not increment!'
    return HttpResponse(json.dumps(responseData), content_type="application/json")


def Decrement(request):
    thetid = request.POST.get("tid")
    responseData = {}
    try:
        theTag = Tag.objects.get(tid=thetid)
        theTag.num_votes = theTag.num_votes - 1
        theTag.save()
        responseData["success"] = True
        responseData["num_votes"] = theTag.num_votes
        responseData["comments"] = 'Decremented the tag!'
    except Exception:
        responseData["success"] = False
        responseData["comments"] = 'Could not decrement!'
    return HttpResponse(json.dumps(responseData), content_type="application/json")


def viewTag(request):
    thetid = request.POST.get("tid")
    theTag = Tag.objects.get(tid=thetid)
    return theTag.tag
