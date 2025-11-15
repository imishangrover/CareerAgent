from django.urls import path
from .views import (CareerRoadmapView,
                    UserRoadmapListView,
                    UserRoadmapDetailView,
                    UserRoadmapDeleteView,
                    UserRoadmapRegenerateView,)

urlpatterns = [
    path('roadmap/<path:career_name>/', CareerRoadmapView.as_view(), name='career_roadmap'),
    path("my-roadmaps/", UserRoadmapListView.as_view()),
    path("roadmap/<int:pk>/", UserRoadmapDetailView.as_view()),
    path("roadmap/<int:pk>/delete/", UserRoadmapDeleteView.as_view()),
    path("roadmap/<int:pk>/regenerate/", UserRoadmapRegenerateView.as_view()),
]
