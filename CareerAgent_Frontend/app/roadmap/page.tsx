"use client";

import { useEffect, useState } from "react";
import axios from "axios";

import { Card, CardContent } from "@/components/ui/card";
import RoadmapTimeline from "@/components/roadmap-timeline";
import { CheckCircle, Clock, Target } from "lucide-react";

interface RoadmapPhase {
  id: string;
  phase: string;
  duration: string;
  title: string;
  description: string;
  skills: string[];
  status: "completed" | "current" | "upcoming";
}

export default function RoadmapPage() {
  const [roadmapPhases, setRoadmapPhases] = useState<RoadmapPhase[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRoadmap = async () => {
      try {
        const token = localStorage.getItem("access_token") || ""; // <-- your token
        const name = localStorage.getItem("career_path") || "vue";
        const res = await axios.get(
          `http://127.0.0.1:8000/api/career/roadmap/${name}`,
          {
            headers: {
              Authorization: `Bearer ${token}`, // <-- added
            },
          }
        );
        console.log("Roadmap response:", res.data);

        const steps = res.data.roadmap.steps;

        const parsedPhases: RoadmapPhase[] = Object.entries(steps).map(
          ([stepName, stepData], index) => {
            let json: any = {};

            try {
              // clean markdown code fences if present
              let cleaned = String(stepData)
                .replace(/```json/g, "")
                .replace(/```/g, "")
                .trim();

              json = JSON.parse(cleaned); // try parsing JSON
            } catch (e) {
              // ❗ If not JSON — treat as plain text step
              json = {
                name: stepName,
                description: String(stepData),
                skills: [],
              };
            }

            return {
              id: `phase-${index + 1}`,
              phase: stepName,
              duration: `Step ${index + 1}`,
              title: json.name || stepName,
              description: json.description || "",
              skills: json.skills || [],
              status: index === 0 ? "current" : "upcoming",
            };
          }
        );

        setRoadmapPhases(parsedPhases);
      } catch (err) {
        console.error("Error fetching roadmap:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchRoadmap();
  }, []);

  const stats = [
    {
      icon: Target,
      label: "Total Duration",
      value: `${roadmapPhases.length} Steps`,
    },
    { icon: CheckCircle, label: "Phases", value: roadmapPhases.length },
    {
      icon: Clock,
      label: "Current Phase",
      value: roadmapPhases[0]?.title || "Loading...",
    },
  ];

  if (loading) {
    return (
      <div className="text-center py-20 text-lg text-muted-foreground">
        Loading roadmap...
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-linear-to-br from-background via-background to-secondary px-4 py-12">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-5xl md:text-6xl font-bold text-foreground mb-4">
            Your Career Roadmap
          </h1>
          <p className="text-xl text-muted-foreground">
            A structured path to mastering your chosen field
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-4 mb-12">
          {stats.map((stat) => {
            const Icon = stat.icon;
            return (
              <Card key={stat.label}>
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-4">
                    <div className="bg-primary/10 p-3 rounded-lg">
                      <Icon className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">
                        {stat.label}
                      </p>
                      <p className="text-2xl font-bold text-foreground">
                        {stat.value}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="space-y-6">
          {roadmapPhases.map((phase, index) => (
            <RoadmapTimeline key={phase.id} phase={phase} index={index} />
          ))}
        </div>
      </div>
    </main>
  );
}
