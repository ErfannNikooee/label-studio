# Generated by Django 3.2.23 on 2024-01-10 09:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import groups.mixins


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=500, verbose_name='group name')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('contact_info', models.EmailField(blank=True, max_length=254, null=True, verbose_name='contact info')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_groups', to=settings.AUTH_USER_MODEL, verbose_name='created_by')),
            ],
            options={
                'ordering': ['pk'],
            },
            bases=(groups.mixins.GroupMixin, models.Model),
        ),
        migrations.CreateModel(
            name='GroupMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('admin', models.BooleanField()),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('deleted_at', models.DateTimeField(blank=True, db_index=True, default=None, help_text='Timestamp indicating when the group member was marked as deleted.  If NULL, the member is not considered deleted.', null=True, verbose_name='deleted at')),
                ('group', models.ForeignKey(help_text='Group ID', on_delete=django.db.models.deletion.CASCADE, to='groups.group')),
                ('user', models.ForeignKey(help_text='User ID', on_delete=django.db.models.deletion.CASCADE, related_name='gm_through', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['pk'],
            },
            bases=(groups.mixins.GroupMemberMixin, models.Model),
        ),
        migrations.AddField(
            model_name='group',
            name='users',
            field=models.ManyToManyField(related_name='members', through='groups.GroupMember', to=settings.AUTH_USER_MODEL),
        ),
    ]