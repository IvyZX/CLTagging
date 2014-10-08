from django.db import models
from django.contrib.auth.models import User

import datetime
from django.utils import timezone
import uuid


class UUIDField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 64)
        kwargs['blank'] = True
        models.CharField.__init__(self, *args, **kwargs)

    def pre_save(self, model_instance, add):
        if add:
            value = str(uuid.uuid4())
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super(models.CharField, self).pre_save(model_instance, add)


# The signup/login verification for user
# Also records whether the user is an expert / in nominal group
class UserProfile(models.Model):
    user = models.OneToOneField(User)
    date_created = models.DateTimeField(blank=True)
    designated_entries = models.CommaSeparatedIntegerField(max_length=50, blank=True)
    index_of_last_completed_entry = models.IntegerField(blank=True)
    is_expert = models.BooleanField(default=True)
    is_nominal = models.BooleanField(default=True)

    def as_json(self):
        return dict(user=self.user, date_created=self.date_created, designated_entries=self.designated_entries,
                    i=self.index_of_last_completed_entry, is_expert=self.is_expert, is_nominal=self.is_nominal)

    def __unicode__(self):
        return str(self.user.username)


# The generalized entry for all users
class Entry(models.Model):
    eid = models.IntegerField()
    entry = models.CharField(max_length=5000)
    pub_date = models.DateTimeField()
    practice = models.BooleanField(default=False)
    def __unicode__(self):
        return str(self.eid)


# The class that has specifics for any given Entry class
class EntrySpecifics(models.Model):
    entry = models.ForeignKey(Entry)
    date_time = models.DateTimeField()
    user = models.ForeignKey(User)
    euuid = UUIDField(primary_key=True, editable=False)

    def __unicode__(self):
        return self.euuid


# The tags stored back, one for every tag
class Tag(models.Model):
    tid = UUIDField(primary_key=True, editable=False)
    tag = models.CharField(max_length=100)
    num_votes = models.IntegerField()
    entry = models.ForeignKey(Entry)

    def as_json(self):
        return dict(entry=self.entry, tag=self.tag, num_votes=self.num_votes, tid=self.tid)

    def __unicode__(self):
        return self.tag

# The tags entered by users, one for every entry_specifics
# They represent all actions about tags that this user did on this entry
class TagSpecifics(models.Model):
    tsid = UUIDField(primary_key=True, editable=False)
    tag = models.ForeignKey(Tag)
    entry_specifics = models.ForeignKey(EntrySpecifics)
    entry_date = models.DateTimeField()
    upvoted = models.BooleanField(default=True)
    def as_json(self):
        return dict(entry_specifics=self.entry_specifics, tag=self.tag, entry_date=self.entry_date, tsid=self.tid,
                    upvoted = self.upvoted)
    def __unicode__(self):
        return self.tag.tag


