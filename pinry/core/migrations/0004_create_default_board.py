# -*- coding: utf-8 -*-
from django.conf import settings

from guardian.core import ObjectPermissionChecker
from guardian.models import UserObjectPermission
from south.db import db
from south.v2 import DataMigration

from pinry.users.models import User


def south_assign_perm(perm, identity, obj):
    """
    A custom assign_perm implementation for South

    django-guardian doesn't work well with South (isinstance(user_obj, User)
    assumption is broken) so we have to fiddle with the database directly.

    """
    user = User.objects.get(pk=identity.pk)

    UserObjectPermission.objects.assign_perm(perm, user, obj)


def south_remove_perm(perm, identity, obj):
    """
    A custom remove_perm implementation for South

    django-guardian doesn't work well with South (isinstance(user_obj, User)
    assumption is broken) so we have to fiddle with the database directly.

    """
    user = User.objects.get(pk=identity.pk)

    UserObjectPermission.objects.remove_perm(perm, user, obj)


def south_get_perms(identity, obj):
    """
    A custom get_perms implementation for South

    django-guardian doesn't work well with South (isinstance(user_obj, User)
    assumption is broken) so we have to fiddle with the database directly.

    """
    identity = User.objects.get(pk=identity.pk)
    check = ObjectPermissionChecker(identity)
    return check.get_perms(obj)


class Migration(DataMigration):
    def forwards(self, orm):
        """Create a default board, assign pins to it and set permissions."""
        if db.dry_run:
            return
        board = orm['core.board'].objects.create(name='Default board')
        # Get users who are not site-wide admins and not anonymous
        anonymous_id = settings.ANONYMOUS_USER_ID
        users = orm['auth.user'].objects.filter(is_superuser=False,
                                                pk__gt=anonymous_id)
        for user in users:
            board.members.add(user)
            south_assign_perm('view_board', user, board)
        orm['core.pin'].objects.update(board=board)

    def backwards(self, orm):
        """
        Clean up data related to boards.

        Remove all pin<->board mappings, user permissions, board membership
        relationship.
        """
        if db.dry_run:
            return
        boards = orm['core.board'].objects.all()
        for board in boards:
            users = board.members.filter(is_superuser=False)
            for user in users:
                # Make sure that we don't leave any dangling permissions
                perms = south_get_perms(user, board)
                for perm in perms:
                    south_remove_perm(perm, user, board)
            board.members.clear()
            board.delete()
        orm['core.pin'].objects.update(board=None)

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.board': {
            'Meta': {'object_name': 'Board'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.User']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'settings': ('pinry.core.models.JSONField', [], {'default': '{}'})
        },
        u'core.pin': {
            'Meta': {'object_name': 'Pin'},
            'board': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pins'", 'null': 'True', 'to': u"orm['core.Board']"}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'pin'", 'to': u"orm['django_images.Image']"}),
            'origin': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'submitter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'})
        },
        u'django_images.image': {
            'Meta': {'object_name': 'Image'},
            'height': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '255'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
        },
        u'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        u'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_tagged_items'", 'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_items'", 'to': u"orm['taggit.Tag']"})
        }
    }

    complete_apps = ['core']
    symmetrical = True
