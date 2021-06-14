from django.contrib import admin, messages
# <HINT> Import any new Models here
from .models import Course, Lesson, Instructor, Learner, Choice, Question

from django.utils.translation import ngettext


# <HINT> Register QuestionInline and ChoiceInline classes here

class ChoiceAdmin(admin.ModelAdmin):
    model: Choice
    question = ['question']
    actions = ['mark_as_true']
    correct = ['is_correct']
    display = ['id', 'question', 'is_correct']
    list_display = ['id', 'question', 'is_correct']

    def mark_as_true(modeladmin, request, queryset):
        updated = queryset.update(is_correct=True)


class QuestionAdmin(admin.ModelAdmin):
    lesson = ['lesson']
    list_display = ['id', 'q_text']


class ChoiceInline(admin.StackedInline):
    model: Choice
    extra = 3


class QuestionInline(admin.StackedInline):
    inlines = [ChoiceInline]
    model: Question
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


admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(Instructor)
admin.site.register(Learner)
