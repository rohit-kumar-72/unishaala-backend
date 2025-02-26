from django.db import models
from .choices import DEPARTMENT_CHOICE,SHIFT_CHOICE
from django.contrib.auth.models import User

# Create your models here.
class Slots(models.Model):
    department=models.CharField(max_length=100,choices=DEPARTMENT_CHOICE)
    shift=models.CharField(max_length=20,choices=SHIFT_CHOICE,null=True,blank=True)
    date=models.DateTimeField(null=True,blank=True)
    passing_marks_general = models.FloatField(null=True, blank=True)  
    department_topper_marks = models.FloatField(null=True, blank=True)
    status=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.department}-{self.status}'


class AnswerSheet(models.Model):
    question_Id=models.PositiveBigIntegerField()
    question_no=models.PositiveIntegerField(null=True,blank=True)
    answer=models.CharField(max_length=500)
    q_type=models.CharField(max_length=20)
    mark=models.FloatField()
    slot=models.ForeignKey(Slots,on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.question_no}-{self.question_Id}-{self.slot}'
    

class CandidateScore(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # One user, one score
    slot = models.ForeignKey(Slots, on_delete=models.CASCADE)
    marks_obtained = models.FloatField()
    normalized_marks = models.FloatField(null=True, blank=True)
    gate_score = models.FloatField(null=True, blank=True)
    sheet_url = models.CharField(max_length=500, null=True, blank=True)
    rank=models.CharField(max_length=20, null=True, blank=True)
    normalized_rank=models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} - {self.marks_obtained}'
