import json
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import CareerRoadmap, RoadmapReference
from .ai import generate_ai_roadmap, generate_ai_response
from .scraper import scrape_roadmap


# ---------------------------------------
#  MAIN: Generate Roadmap for Career
# ---------------------------------------
class CareerRoadmapView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, career_name):
        user = request.user

        # Parse preferences from query param
        preferences = request.GET.get("preferences", "{}")
        try:
            preferences = json.loads(preferences)
        except:
            preferences = {}

        # 1️⃣ Return existing roadmap for this career (latest version)
        roadmap_obj = (
            CareerRoadmap.objects
            .filter(user=user, career_name=career_name, is_deleted=False)
            .order_by("-version")
            .first()
        )

        if roadmap_obj:
            return Response({
                "roadmap": {
                    "name": career_name,
                    "steps": roadmap_obj.roadmap,
                    "source_url": roadmap_obj.reference.source_url if roadmap_obj.reference else None,
                    "personalized_for": str(user.id),
                    "version": roadmap_obj.version,
                },
                "source": "user_db"
            })

        # 2️⃣ Check for reference roadmap in DB
        reference = RoadmapReference.objects.filter(name__iexact=career_name).first()
        reference_content = None

        # Auto-refresh reference every 30 days
        if reference:
            if not reference.auto_refresh_at or reference.auto_refresh_at < datetime.utcnow():
                try:
                    updated = scrape_roadmap(career_name)
                    reference.content = updated
                    reference.auto_refresh_at = datetime.utcnow() + timedelta(days=30)
                    reference.save()
                except Exception:
                    pass

            reference_content = reference.content

        # 3️⃣ If no reference, scrape roadmap.sh
        if not reference:
            try:
                reference_content = scrape_roadmap(career_name)
            except:
                reference_content = None

        # 4️⃣ Generate AI-based roadmap
        ai_output = generate_ai_roadmap(
            user_id=user.id,
            career_name=career_name,
            reference_content=reference_content,
            preferences=preferences
        )

        steps = ai_output.get("steps", {})

        # 5️⃣ Save as version 1
        roadmap_obj = CareerRoadmap.objects.create(
            user=user,
            career_name=career_name,
            roadmap=steps,
            preferences=preferences,
            reference=reference,
            version=1
        )

        return Response({
            "roadmap": {
                "name": career_name,
                "steps": steps,
                "source_url": reference.source_url if reference else None,
                "personalized_for": str(user.id),
                "version": 1
            },
            "source": "ai_generated"
        })


# ---------------------------------------
#  LIST USER ROADMAPS (with filters)
# ---------------------------------------
class UserRoadmapListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        career_filter = request.GET.get("career")
        tag_filter = request.GET.get("tag")

        qs = CareerRoadmap.objects.filter(user=user, is_deleted=False).order_by("-created_at")

        if career_filter:
            qs = qs.filter(career_name__icontains=career_filter)

        if tag_filter:
            qs = qs.filter(tags__contains=[tag_filter])

        data = [{
            "id": r.id,
            "career_name": r.career_name,
            "preferences": r.preferences,
            "version": r.version,
            "created_at": r.created_at,
        } for r in qs]

        return Response({"roadmaps": data})


# ---------------------------------------
#  VIEW SINGLE ROADMAP
# ---------------------------------------
class UserRoadmapDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        roadmap = get_object_or_404(
            CareerRoadmap, pk=pk, user=request.user, is_deleted=False
        )

        return Response({
            "id": roadmap.id,
            "career_name": roadmap.career_name,
            "roadmap": roadmap.roadmap,
            "preferences": roadmap.preferences,
            "version": roadmap.version,
            "reference": roadmap.reference.content if roadmap.reference else None,
            "source_url": roadmap.reference.source_url if roadmap.reference else None,
            "created_at": roadmap.created_at,
            "updated_at": roadmap.updated_at,
        })


# ---------------------------------------
#  SOFT DELETE ROADMAP
# ---------------------------------------
class UserRoadmapDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        roadmap = get_object_or_404(
            CareerRoadmap, pk=pk, user=request.user, is_deleted=False
        )
        roadmap.is_deleted = True
        roadmap.save()

        return Response({"message": "Roadmap deleted (soft delete)"})


# ---------------------------------------
#  REGENERATE ROADMAP = VERSIONING
# ---------------------------------------
class UserRoadmapRegenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        old = get_object_or_404(
            CareerRoadmap, pk=pk, user=request.user, is_deleted=False
        )

        new_preferences = request.data.get("preferences", {})
        reference_content = old.reference.content if old.reference else None
        career_name = old.career_name

        # generate new version
        new_data = generate_ai_roadmap(
            user_id=request.user.id,
            career_name=career_name,
            reference_content=reference_content,
            preferences=new_preferences
        )

        new_steps = new_data.get("steps", {})

        new_version = old.version + 1

        new_roadmap = CareerRoadmap.objects.create(
            user=request.user,
            career_name=career_name,
            roadmap=new_steps,
            preferences=new_preferences,
            reference=old.reference,
            version=new_version,
            parent=old,
        )

        return Response({
            "message": "New version created",
            "version": new_version,
            "steps": new_steps
        })


# ---------------------------------------
#  SKILL GAP ANALYSIS
# ---------------------------------------
class SkillGapView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        roadmap = get_object_or_404(CareerRoadmap, pk=pk, user=request.user)

        prompt = f"""
        Given the roadmap steps:
        {json.dumps(roadmap.roadmap)}

        And the user's preferences (skills they know):
        {json.dumps(roadmap.preferences)}

        Return a skill gap analysis in JSON:
        {{
            "missing_skills": [],
            "priority_skills": [],
            "suggestions": ""
        }}
        """

        return Response(generate_ai_response(prompt))


# ---------------------------------------
#  WEEKLY LEARNING PLAN
# ---------------------------------------
class WeeklyPlanView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        roadmap = get_object_or_404(CareerRoadmap, pk=pk, user=request.user)

        prompt = f"""
        Convert this roadmap:
        {json.dumps(roadmap.roadmap)}

        Into a 6-week learning plan.

        Return JSON:
        {{
            "week_1": [],
            "week_2": [],
            "week_3": [],
            "week_4": [],
            "week_5": [],
            "week_6": []
        }}
        """

        return Response(generate_ai_response(prompt))


# ---------------------------------------
#  STEP EXPLAINER
# ---------------------------------------
class ExplainStepView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        step = request.data.get("step")
        roadmap = get_object_or_404(CareerRoadmap, pk=pk, user=request.user)

        if step not in roadmap.roadmap:
            return Response({"error": "Invalid step"}, status=400)

        step_text = roadmap.roadmap.get(step)

        prompt = f"""
        Explain this step in detail:
        {step}: {step_text}

        Include examples, resources, and use-cases.

        Return JSON:
        {{
            "explanation": "",
            "resources": [],
            "examples": []
        }}
        """

        return Response(generate_ai_response(prompt))


# ---------------------------------------
#  MOCK INTERVIEW QUESTIONS
# ---------------------------------------
class MockInterviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        roadmap = get_object_or_404(CareerRoadmap, pk=pk, user=request.user)

        prompt = f"""
        Generate 10 mock interview questions for:
        {roadmap.career_name}

        Return JSON:
        {{
            "questions": []
        }}
        """

        return Response(generate_ai_response(prompt))
