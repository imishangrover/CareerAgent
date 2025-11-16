from django.urls import path
from .views import (
    CareerRoadmapView,
    UserRoadmapListView,
    UserRoadmapDetailView,
    UserRoadmapDeleteView,
    UserRoadmapRegenerateView,
    SkillGapView,
    WeeklyPlanView,
    ExplainStepView,
    MockInterviewView,)

urlpatterns = [
    path('roadmap/<path:career_name>/', CareerRoadmapView.as_view(), name='career_roadmap'),
    path("my-roadmaps/", UserRoadmapListView.as_view()),
    path("roadmap/<int:pk>/", UserRoadmapDetailView.as_view()),
    path("roadmap/<int:pk>/delete/", UserRoadmapDeleteView.as_view()),
    path("roadmap/<int:pk>/regenerate/", UserRoadmapRegenerateView.as_view()),
    path("roadmap/<int:pk>/skills-gap/", SkillGapView.as_view(), name="skills-gap"),
    path("roadmap/<int:pk>/weekly-plan/", WeeklyPlanView.as_view(), name="weekly-plan"),
    path("roadmap/<int:pk>/explain-step/", ExplainStepView.as_view(), name="explain-step"),
    path("roadmap/<int:pk>/mock-interview/", MockInterviewView.as_view(), name="mock-interview"),
]
