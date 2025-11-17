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
    MockInterviewView,
    UpdateProgressView,
    ProgressSummaryView,
    RoadmapChatView,
    SaveRoadmapVersionView,
    ApplyChatUpdateView,
    )

urlpatterns = [
    path('roadmap/<path:career_name>/', CareerRoadmapView.as_view(), name='career_roadmap'),
    path("roadmap/save-version/", SaveRoadmapVersionView.as_view(), name="roadmap-save-version"),
    path("my-roadmaps/", UserRoadmapListView.as_view()),
    path("roadmap/<int:pk>/", UserRoadmapDetailView.as_view()),
    path("roadmap/<int:pk>/delete/", UserRoadmapDeleteView.as_view()),
    path("roadmap/<int:pk>/regenerate/", UserRoadmapRegenerateView.as_view()),
    path("roadmap/<int:pk>/skills-gap/", SkillGapView.as_view(), name="skills-gap"),
    path("roadmap/<int:pk>/weekly-plan/", WeeklyPlanView.as_view(), name="weekly-plan"),
    path("roadmap/<int:pk>/explain-step/", ExplainStepView.as_view(), name="explain-step"),
    path("roadmap/<int:pk>/mock-interview/", MockInterviewView.as_view(), name="mock-interview"),
    path("roadmap/<int:pk>/update-progress/", UpdateProgressView.as_view(), name="update-progress"),
    path("roadmap/<int:pk>/progress-summary/", ProgressSummaryView.as_view(), name="progress-summary"),
    path("roadmap/<int:pk>/chat/", RoadmapChatView.as_view(), name="roadmap-chat"),
    path("roadmap/<int:pk>/chat/apply/", ApplyChatUpdateView.as_view(), name="roadmap-chat-apply"),
    
]
