"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"

export default function CareerPage() {
  const router = useRouter()
  const [careerInput, setCareerInput] = useState("")
  const [loading, setLoading] = useState(false)

  const handleContinue = async () => {
    if (!careerInput.trim()) return

    setLoading(true)
    try {
      // TODO: Save career selection to database
      // const response = await fetch("/api/career/select", {
      //   method: "POST",
      //   headers: { "Content-Type": "application/json" },
      //   body: JSON.stringify({ careerPath: careerInput }),
      // })

      setTimeout(() => {
        router.push("/roadmap")
      }, 500)
    } catch (error) {
      console.error("Error selecting career:", error)
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-background px-4 py-12 flex flex-col items-center justify-center">
      <div className="max-w-2xl w-full">
        <div className="text-center mb-12">
          <h1 className="text-5xl md:text-6xl font-bold text-foreground mb-4">What's Your Dream Career?</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Tell us about the career path you'd like to pursue, and we'll create a personalized roadmap to get you
            there.
          </p>
        </div>

        <div className="space-y-6">
          <div>
            <label htmlFor="career" className="block text-lg font-semibold text-foreground mb-3">
              Career Path
            </label>
            <input
              id="career"
              type="text"
              placeholder="e.g., Software Engineer, Product Manager, Data Scientist..."
              value={careerInput}
              onChange={(e) => {setCareerInput(e.target.value); localStorage.setItem("career_path", e.target.value)}}
              onKeyDown={(e) => {
                if (e.key === "Enter" && careerInput.trim()) {
                  handleContinue()
                }
              }}
              className="w-full px-6 py-4 bg-card border border-border rounded-lg text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent text-lg"
            />
          </div>

          <div className="flex justify-center pt-4">
            <Button
              size="lg"
              onClick={handleContinue}
              disabled={!careerInput.trim() || loading}
              className="text-lg px-8 flex items-center gap-2"
            >
              {loading ? "Creating Your Roadmap..." : "Continue to Roadmap"}
              {!loading && <ArrowRight className="w-5 h-5" />}
            </Button>
          </div>
        </div>
      </div>
    </main>
  )
}
