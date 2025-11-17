import json
from datetime import datetime, timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import CareerRoadmap, RoadmapReference
from .ai import generate_ai_roadmap, generate_ai_response, roadmap_chat_ai
from .scraper import scrape_roadmap



# ============================================================
# 1) MAIN: Generate Roadmap PREVIEW (NOT SAVED)
# ============================================================
class CareerRoadmapView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, career_name):
        user = request.user

        # Parse preferences
        preferences = request.GET.get("preferences", "{}")
        try:
            preferences = json.loads(preferences)
        except:
            preferences = {}

        # Check if user already saved roadmap for this career
        saved_roadmap = (
            CareerRoadmap.objects
            .filter(user=user, career_name=career_name, is_deleted=False)
            .order_by("-version")
            .first()
        )

        # Return last SAVED version
        if saved_roadmap:
            return Response({
                "roadmap": {
                    "name": career_name,
                    "steps": saved_roadmap.roadmap,
                    "progress": saved_roadmap.progress,
                    "source_url": saved_roadmap.reference.source_url if saved_roadmap.reference else None,
                    "version": saved_roadmap.version,
                    "personalized_for": str(user.id)
                },
                "saved": True,
                "source": "user_db"
            })

        # Otherwise generate preview
        reference = RoadmapReference.objects.filter(name__iexact=career_name).first()
        reference_content = reference.content if reference else None

        if not reference:
            try:
                reference_content = scrape_roadmap(career_name)
            except:
                reference_content = None

        # Generate unsaved roadmap preview
        ai_output = generate_ai_roadmap(
            user_id=user.id,
            career_name=career_name,
            reference_content=reference_content,
            preferences=preferences
        )

        steps = ai_output.get("steps", {})
        preview_progress = {step: "not_started" for step in steps.keys()}

        return Response({
            "roadmap": {
                "name": career_name,
                "steps": steps,
                "progress": preview_progress,
                "source_url": reference.source_url if reference else None,
                "preview": True,
                "version": None,
                "personalized_for": str(user.id)
            },
            "saved": False,
            "source": "preview"
        })



# ============================================================
# 2) SAVE A VERSION (Manual Save Button)
# ============================================================
class SaveRoadmapVersionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        career_name = request.data.get("career_name")
        roadmap = request.data.get("roadmap")
        preferences = request.data.get("preferences", {})

        if not career_name or not roadmap:
            return Response({"error": "Missing fields"}, status=400)

        # Fetch last version
        last = CareerRoadmap.objects.filter(
            user=user,
            career_name=career_name,
            is_deleted=False
        ).order_by("-version").first()

        version = last.version + 1 if last else 1
        progress = {step: "not_started" for step in roadmap.keys()}

        new_entry = CareerRoadmap.objects.create(
            user=user,
            career_name=career_name,
            roadmap=roadmap,
            preferences=preferences,
            reference=None,
            version=version,
            progress=progress,
            parent=last if last else None
        )

        return Response({
            "message": "Roadmap saved successfully",
            "version": version,
            "roadmap_id": new_entry.id
        })



# ============================================================
# 3) CHAT WITH AI (Preview Update Only — NO SAVE)
# ============================================================
class RoadmapChatView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        user_message = request.data.get("message")

        roadmap_obj = get_object_or_404(
            CareerRoadmap, pk=pk, user=request.user, is_deleted=False
        )

        ai_response = roadmap_chat_ai(
            user_message=user_message,
            roadmap=roadmap_obj.roadmap,
            preferences=roadmap_obj.preferences
        )

        updated = ai_response.get("updated_roadmap")

        # If AI edited roadmap, return candidate roadmap (NOT SAVED)
        if updated:
            return Response({
                "message": ai_response.get("message"),
                "updated": True,
                "candidate_roadmap": updated,
                "pending_save": True
            })

        # Normal chat response
        return Response({
            "message": ai_response.get("message"),
            "updated": False,
            "pending_save": False
        })



# ============================================================
# 4) APPLY CHAT CHANGES (Save or Overwrite or Discard)
# ============================================================
class ApplyChatUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        roadmap = get_object_or_404(
            CareerRoadmap,
            pk=pk,
            user=request.user,
            is_deleted=False
        )

        new_steps = request.data.get("candidate_roadmap")
        save_mode = request.data.get("save_mode")  # new_version | overwrite | discard

        if save_mode not in ["new_version", "overwrite", "discard"]:
            return Response({"error": "Invalid save_mode"}, status=400)

        if save_mode == "discard":
            return Response({"message": "Changes discarded", "saved": False})

        new_progress = {step: "not_started" for step in new_steps.keys()}

        # Save as NEW version
        if save_mode == "new_version":
            new_version = roadmap.version + 1

            new_entry = CareerRoadmap.objects.create(
                user=request.user,
                career_name=roadmap.career_name,
                roadmap=new_steps,
                preferences=roadmap.preferences,
                reference=roadmap.reference,
                version=new_version,
                progress=new_progress,
                parent=roadmap
            )

            return Response({
                "message": "New version created",
                "saved": True,
                "new_version": new_version,
                "roadmap": new_steps
            })

        # OVERWRITE existing roadmap version
        if save_mode == "overwrite":
            roadmap.roadmap = new_steps
            roadmap.progress = new_progress
            roadmap.save()

            return Response({
                "message": "Roadmap overwritten",
                "saved": True,
                "version": roadmap.version,
                "roadmap": new_steps
            })



# ============================================================
# 5) LIST ALL USER ROADMAPS
# ============================================================
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
            "progress": r.progress,
        } for r in qs]

        return Response({"roadmaps": data})



# ============================================================
# 6) VIEW A SINGLE ROADMAP VERSION
# ============================================================
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
            "progress": roadmap.progress,
            "reference": roadmap.reference.content if roadmap.reference else None,
            "source_url": roadmap.reference.source_url if roadmap.reference else None,
            "created_at": roadmap.created_at,
            "updated_at": roadmap.updated_at,
        })



# ============================================================
# 7) SOFT DELETE A ROADMAP VERSION
# ============================================================
class UserRoadmapDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        roadmap = get_object_or_404(
            CareerRoadmap, pk=pk, user=request.user, is_deleted=False
        )
        roadmap.is_deleted = True
        roadmap.save()

        return Response({"message": "Roadmap deleted (soft delete)"})



# ============================================================
# 8) REGENERATE NEW VERSION COMPLETELY
# ============================================================
class UserRoadmapRegenerateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        old = get_object_or_404(
            CareerRoadmap, pk=pk, user=request.user, is_deleted=False
        )

        new_preferences = request.data.get("preferences", {})
        reference_content = old.reference.content if old.reference else None
        career_name = old.career_name

        new_data = generate_ai_roadmap(
            user_id=request.user.id,
            career_name=career_name,
            reference_content=reference_content,
            preferences=new_preferences
        )

        new_steps = new_data.get("steps", {})
        new_progress = {step: "not_started" for step in new_steps.keys()}

        new_version = old.version + 1

        new_entry = CareerRoadmap.objects.create(
            user=request.user,
            career_name=career_name,
            roadmap=new_steps,
            preferences=new_preferences,
            reference=old.reference,
            version=new_version,
            progress=new_progress,
            parent=old,
        )

        return Response({
            "message": "New version created",
            "version": new_version,
            "steps": new_steps,
            "progress": new_progress
        })



# ============================================================
# 9) UPDATE PROGRESS
# ============================================================
class UpdateProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        roadmap = get_object_or_404(
            CareerRoadmap, pk=pk, user=request.user, is_deleted=False
        )

        step = request.data.get("step")
        status = request.data.get("status")

        if step not in roadmap.roadmap:
            return Response({"error": "Invalid step"}, status=400)

        if status not in ["not_started", "in_progress", "completed", "skipped"]:
            return Response({"error": "Invalid status"}, status=400)

        roadmap.progress[step] = status
        roadmap.save()

        return Response({
            "message": "Progress updated",
            "progress": roadmap.progress
        })



# ============================================================
# 10) PROGRESS SUMMARY
# ============================================================
class ProgressSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        roadmap = get_object_or_404(
            CareerRoadmap, pk=pk, user=request.user, is_deleted=False
        )

        progress = roadmap.progress
        total = len(progress)

        completed = sum(1 for s in progress.values() if s == "completed")
        in_progress = sum(1 for s in progress.values() if s == "in_progress")
        skipped = sum(1 for s in progress.values() if s == "skipped")
        not_started = total - completed - in_progress - skipped

        percent = round((completed / total * 100), 2) if total > 0 else 0

        return Response({
            "total_steps": total,
            "completed": completed,
            "in_progress": in_progress,
            "skipped": skipped,
            "not_started": not_started,
            "completion_percentage": percent,
            "progress": progress
        })



# ============================================================
# 11) SKILL GAP ANALYSIS
# ============================================================
class SkillGapView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        roadmap = get_object_or_404(CareerRoadmap, pk=pk, user=request.user)

        prompt = f"""
        Given this roadmap:
        {json.dumps(roadmap.roadmap)}

        And user skills (preferences):
        {json.dumps(roadmap.preferences)}

        Return JSON:
        {{
            "missing_skills": [],
            "priority_skills": [],
            "suggestions": ""
        }}
        """

        return Response(generate_ai_response(prompt))



# ============================================================
# 12) WEEKLY PLAN GENERATION
# ============================================================
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



# ============================================================
# 13) STEP EXPLAINER
# ============================================================
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

        Provide examples, resources.
        JSON only:
        {{
            "explanation": "",
            "resources": [],
            "examples": []
        }}
        """

        return Response(generate_ai_response(prompt))



# ============================================================
# 14) MOCK INTERVIEW QUESTIONS
# ============================================================
class MockInterviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        roadmap = get_object_or_404(CareerRoadmap, pk=pk, user=request.user)

        prompt = f"""
        Generate 10 mock interview questions for:
        {roadmap.career_name}

        JSON:
        {{
            "questions": []
        }}
        """

        return Response(generate_ai_response(prompt))
