from django.contrib import admin
from .models import Slots,AnswerSheet,CandidateScore
# Register your models here.
admin.site.register(Slots)
admin.site.register(AnswerSheet)
admin.site.register(CandidateScore)