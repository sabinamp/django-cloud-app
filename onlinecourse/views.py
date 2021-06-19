from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission, Lesson
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
from collections import OrderedDict
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# <HINT> A example method to collect the selected choices from the exam form from the request object
def extract_answers(request):
    submitted_choices = []
    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]  # print("{}: {}".format(choice_id, request.POST.getlist(choice_id)))
            choice_id = int(value)
            submitted_choices.append(choice_id)
    return submitted_choices


# <HINT> Create a submit view to create an exam submission record for a course enrollment,
# you may implement it based on following logic:
# Get user and course object, then get the associated enrollment object created when the user enrolled the course
# Create a submission object referring to the enrollment
# Collect the selected choices from exam form
# Add each selected choice object to the submission object
# Redirect to show_exam_result with the submission id
# def submit(request, course_id):

def submit(request, course_id):
    current_user = request.user
    course = get_object_or_404(Course, pk=course_id)
    if request.method == 'POST':
        enrollment = Enrollment.objects.get(user=current_user, course=course)
        submission = Submission.objects.create(enrollment=enrollment)
        submission.choices.set(extract_answers(request=request))
        submission.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:show_exam_result', args=(course.id, submission.id)))


# Python code t get difference of two lists
# Using set()
def diff(li1, li2):
    return list(set(li1) - set(li2)) + list(set(li2) - set(li1))


# <HINT> Create an exam result view to check if learner passed exam and show their question results and result for each question,
# you may implement it based on the following logic:
# Get course and submission based on their ids
# Get the selected choice ids from the submission record
# For each selected choice, check if it is a correct answer or not
# Calculate the total score
def show_exam_result(request, course_id, submission_id):
    current_user = request.user
    score = 0

    course = get_object_or_404(Course, pk=course_id)
    question_list = []
    question_list_ids = []
    for each_lesson in course.lesson_set.all():
        questions = each_lesson.question_set.all()
        question_list.extend(questions)
        for q in questions:
            question_list_ids.append(q.id)

    context = {'user': current_user, 'course': course, 'question_list': question_list, }

    submission = get_object_or_404(Submission, pk=submission_id)
    selected_choices = submission.choices.all()
    answered_questions = []

    # Order it by key-question id
    selected_ids_q = dict()
    for selected in selected_choices:
        selected_ids_q[selected.id] = selected.question.id
        answered_questions.append(selected.question)

    for each_question in answered_questions:
        choices_question = []
        for key in selected_ids_q.keys():
            if selected_ids_q[key] == each_question.id:
                choices_question.append(key)
        each_question.q_grade = compute_question_grade(each_question, set(choices_question))
        score = score + each_question.q_grade

    if len(selected_choices) == 0:
        context['error_message'] = "No answer selected."
        context['grade'] = 0.0
        return render(request, 'onlinecourse/exam_result_bootstrap.html', context)
    else:
        grade = score / len(question_list)  # represents percentage value
        not_answered_questions = diff(set(question_list), set(answered_questions))
        context = {'user': current_user, 'course': course, 'not_answered_questions': not_answered_questions,
                   'grade': grade, 'selected_choices': selected_choices}

        return render(request, 'onlinecourse/exam_result_bootstrap.html', context)


def compute_question_grade(question, selected_ids):
    all_answers = question.choice_set.filter(is_correct=True).count()
    selected_correct = question.choice_set.filter(is_correct=True, id__in=selected_ids).count()
    return (selected_correct / all_answers) * 100
