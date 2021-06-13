from django.contrib import admin
# <HINT> Import any new Models here
from .models import Course, Lesson, Instructor, Learner, Choice, Question


# <HINT> Register QuestionInline and ChoiceInline classes here

class ChoiceInline(admin.StackedInline):
    model: Choice
    question = ['question']
    is_correct = ['is_correct']
    actions = ['enable_selected', 'disable_selected']

    def enable_selected(self):
        self.is_correct = True

    def disable_selected(self):
        self.is_correct = False


class QuestionInline(admin.StackedInline):
    model: Question
    lesson = ['lesson']
    extra = 3


class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 5


# Register your models here.
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ('name', 'pub_date')
    list_filter = ['pub_date']
    search_fields = ['name', 'description']


class LessonAdmin(admin.ModelAdmin):
    list_display = ['title']


# <HINT> Register Question and Choice models here
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
