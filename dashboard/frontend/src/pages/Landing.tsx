import Hero from "../components/landing/Hero";
import HowItWorks from "../components/landing/HowItWorks";
import LandingFooter from "../components/landing/LandingFooter";
import LandingNav from "../components/landing/LandingNav";
import NotificationBar from "../components/landing/NotificationBar";
import TeamSection from "../components/landing/TeamSection";
import { useReveal } from "../hooks/useReveal";

export default function Landing() {
  useReveal();
  return (
    <div className="flex min-h-screen flex-col bg-cream font-instrument text-ink">
      <NotificationBar />
      <LandingNav />
      <Hero />
      <HowItWorks />
      <TeamSection />
      <LandingFooter />
    </div>
  );
}
