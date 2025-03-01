# Generated by Django 5.1.5 on 2025-02-07 15:37

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Slots',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(choices=[('CE', 'CE'), ('ME', 'ME'), ('CSIT', 'CSIT'), ('ECE', 'ECE'), ('EE', 'EE'), ('CHE', 'CHE'), ('DSAI', 'DSAI')], max_length=100)),
                ('shift', models.CharField(choices=[('FORENOON', 'FORENOON'), ('AFTERNOON', 'AFTERNOON')], max_length=20)),
                ('date', models.DateTimeField(blank=True, null=True)),
                ('status', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='AnswerSheet',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_Id', models.PositiveIntegerField()),
                ('answer', models.CharField(max_length=50)),
                ('q_type', models.CharField(max_length=20)),
                ('mark', models.FloatField()),
                ('slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='rankpredictor.slots')),
            ],
        ),
    ]
