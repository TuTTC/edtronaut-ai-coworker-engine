"""
Mock LLM for prototype demonstration.
Generates contextual, persona-appropriate responses using template matching
and keyword-based routing. Designed to feel realistic without needing API keys.
"""

from __future__ import annotations

import random
from typing import Any


class MockLLM:
    """
    Template-based mock LLM that generates persona-specific responses.
    Adapts to emotional state, director hints, and user message content.
    """

    def __init__(self):
        self._responses = self._build_response_bank()

    def generate(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        user_message: str,
        persona_id: str = "CEO",
        emotional_state: dict[str, float] | None = None,
        director_hint: str | None = None,
        tool_results: str | None = None,
    ) -> str:
        """Generate a contextual response."""
        emotional_state = emotional_state or {"trust": 0.5, "patience": 0.7, "engagement": 0.6}

        # Classify the message to pick a response category
        category = self._classify(user_message, persona_id)

        # Get candidate responses
        persona_responses = self._responses.get(persona_id, self._responses["CEO"])
        candidates = persona_responses.get(category, persona_responses.get("default", []))
        if not candidates:
            candidates = persona_responses.get("default", ["Let's continue our discussion."])

        response = random.choice(candidates)

        # Apply emotional modifiers
        trust = emotional_state.get("trust", 0.5)
        patience = emotional_state.get("patience", 0.7)

        if trust < 0.3:
            response = self._apply_low_trust(response, persona_id)
        elif trust > 0.7:
            response = self._apply_high_trust(response, persona_id)

        if patience < 0.4:
            response = self._apply_low_patience(response, persona_id)

        # Incorporate director hint
        if director_hint:
            response = self._apply_hint(response, director_hint)

        # Incorporate tool results
        if tool_results:
            response += f"\n\nBased on our internal data: {tool_results[:300]}"

        return response

    # ── Classification ──────────────────────────────────────────────────

    def _classify(self, message: str, persona_id: str) -> str:
        msg = message.lower()
        keyword_map = {
            "CEO": {
                "greeting": ["hello", "hi ", "good morning", "good afternoon", "nice to meet"],
                "mission": ["mission", "purpose", "why", "vision of the group", "what drives"],
                "dna": ["dna", "identity", "culture", "values", "group dna"],
                "autonomy": ["autonomy", "independence", "brand autonomy", "control", "federat"],
                "competency": ["competency", "competencies", "framework", "skills", "capabilities"],
                "board": ["board", "stakeholder", "presentation", "slides", "pack", "ceo pack"],
                "mobility": ["mobility", "talent", "cross-brand", "movement", "transfer"],
                "problem": ["problem", "challenge", "statement", "tension", "issue"],
                "lazy": ["tell me about gucci", "what does gucci do", "what is gucci", "explain everything", "i don't know anything"],
            },
            "CHRO": {
                "greeting": ["hello", "hi ", "good morning", "nice to meet"],
                "framework": ["framework", "competency", "4 themes", "four themes", "vision entrepreneurship"],
                "levels": ["level", "associate", "mid-level", "mid level", "senior", "behavior indicator"],
                "use_cases": ["recruitment", "appraisal", "development", "mobility assessment", "use case"],
                "matrix": ["matrix", "csv", "table", "map", "grid"],
                "turnover": ["turnover", "retention", "leaving", "attrition", "people leaving"],
                "passion": ["passion", "craft", "quality", "heritage", "brand love"],
                "trust_theme": ["trust", "integrity", "transparency", "empower"],
                "vision_theme": ["vision", "strategic", "anticipat", "foresight"],
                "entrepreneurship": ["entrepreneur", "innovation", "risk", "business acumen"],
            },
            "EB Regional Manager": {
                "greeting": ["hello", "hi ", "good morning", "nice to meet"],
                "rollout": ["rollout", "roll out", "deploy", "implement", "launch", "cascade", "pilot"],
                "training": ["train", "trainer", "workshop", "certification", "facilitat"],
                "challenges": ["challenge", "resistance", "pushback", "obstacle", "barrier", "concern"],
                "kpis": ["kpi", "metric", "measure", "indicator", "track", "report", "dashboard"],
                "regions": ["region", "country", "france", "italy", "germany", "nordic", "europe", "eastern"],
                "change": ["change management", "adoption", "buy-in", "communication", "messaging"],
                "gdpr": ["gdpr", "privacy", "data protection", "compliance", "regulation"],
                "budget": ["budget", "cost", "resource", "invest"],
            },
        }

        for category, keywords in keyword_map.get(persona_id, {}).items():
            if any(kw in msg for kw in keywords):
                return category
        return "default"

    # ── Emotional modifiers ─────────────────────────────────────────────

    def _apply_low_trust(self, response: str, persona_id: str) -> str:
        prefixes = {
            "CEO": "I'll be direct with you — ",
            "CHRO": "I want to be candid — ",
            "EB Regional Manager": "Let me be straightforward — ",
        }
        return prefixes.get(persona_id, "") + response

    def _apply_high_trust(self, response: str, persona_id: str) -> str:
        prefixes = {
            "CEO": "I appreciate your thoroughness. ",
            "CHRO": "Great thinking — I can see you're connecting the dots. ",
            "EB Regional Manager": "Good — you're asking the right questions. ",
        }
        return prefixes.get(persona_id, "") + response

    def _apply_low_patience(self, response: str, persona_id: str) -> str:
        suffixes = {
            "CEO": " I have limited time — let's focus on what matters most.",
            "CHRO": " Let's make sure we're being efficient with our time here.",
            "EB Regional Manager": " We need to move this forward — what's your next concrete step?",
        }
        return response + suffixes.get(persona_id, "")

    def _apply_hint(self, response: str, hint: str) -> str:
        # Director hint is woven into the response naturally
        if len(response) > 100:
            # Insert transition before the last sentence
            sentences = response.rsplit(". ", 1)
            if len(sentences) == 2:
                return f"{sentences[0]}. {hint} {sentences[1]}"
        return response + f" {hint}"

    # ── Response Bank ───────────────────────────────────────────────────

    def _build_response_bank(self) -> dict[str, dict[str, list[str]]]:
        return {
            "CEO": {
                "greeting": [
                    "Welcome. I've set aside time for this — I understand you're leading our new leadership initiative. Let's make it count. What's your opening thesis?",
                    "Good to meet you. The board has been asking about our leadership strategy, so your timing is important. What have you prepared?",
                ],
                "mission": [
                    "Our mission is clear: be the most admired luxury group in the world. But 'most admired' isn't just about products — it's about the people who create them. Each of our 9 brands has a distinct soul. Your job is to find the connective tissue — the shared DNA — without homogenizing what makes each brand extraordinary.",
                    "The mission has always been about nurturing creative excellence. We don't run a holding company that squeezes margins — we steward brands. That distinction matters for how you think about leadership development.",
                ],
                "dna": [
                    "Group DNA is what a Gucci Group leader looks like regardless of brand. It's Vision, Entrepreneurship, Passion, Trust. But here's the nuance: a Gucci brand director expresses 'Vision' differently from a Boucheron director. Your framework must capture that — shared language, brand-specific expression.",
                    "Think of Group DNA as the operating system — every brand runs on it, but each has its own applications. If you try to standardize the applications, you'll kill what makes each brand worth billions. Focus on the shared operating principles.",
                ],
                "autonomy": [
                    "Brand autonomy isn't negotiable — it's what makes each brand worth billions. Our creative directors must feel empowered, not constrained by Group-imposed frameworks. Your challenge is designing something they'll choose to adopt because it helps them, not because HQ mandated it.",
                    "We operate a federated model by design. Group provides platforms — HR, Finance, Tech — but we do NOT dictate creative or commercial direction. Any leadership system you build must respect this. 'Support, not impose' isn't just a phrase; it's our operating philosophy.",
                ],
                "competency": [
                    "The CHRO has been developing the competency framework — Vision, Entrepreneurship, Passion, Trust. I support it conceptually, but I need you to make it real. How does each competency manifest differently at Balenciaga versus Brioni? If you can't answer that, the framework is just an HR exercise.",
                    "Competencies without context are meaningless. I've seen too many companies create beautiful matrices that gather dust. Make sure yours is tied to real business decisions — who do we promote, who do we move across brands, who do we invest in?",
                ],
                "board": [
                    "The CEO pack needs to tell a story, not just present data. Start with the tension — autonomy vs. Group needs — then show how your framework resolves it. The board thinks in outcomes: talent mobility, internal promotion rates, retention of our best people. Connect every slide to one of those.",
                    "I need 10 slides that I can present in 15 minutes with confidence. Slide 1: the problem. Slide 10: the investment ask. Everything in between should build an irresistible logic chain. Don't bury the lead — the mobility gap from 2.3% to 8% target is your headline.",
                ],
                "mobility": [
                    "Our cross-brand mobility sits at 2.3%. Comparable luxury groups are at 8%. That gap isn't just an HR metric — it means we're losing high-potential leaders who see no career path beyond their current brand. Some join competitors. That's talent leaking from the Group, and we can't afford it.",
                    "Mobility is the ultimate test of your framework. If a senior leader at Saint Laurent can be objectively assessed against Gucci Group DNA criteria, and if there's a structured onboarding that helps them absorb the new brand's specific DNA, then we've solved the puzzle.",
                ],
                "problem": [
                    "Good — you've identified the right tension. The problem statement needs to quantify the pain: mobility at 2.3%, turnover concentrated in mid-level leaders with 3-7 years tenure, and fragmented assessment processes across brands. Make it data-driven, make it urgent, but also make it clear that the solution must preserve brand autonomy.",
                    "A strong problem statement captures three things: what we're losing (talent, continuity), why we're losing it (fragmentation, limited paths), and what we gain by solving it (stronger pipeline, higher mobility, better retention). Don't make it an accusation — make it an opportunity statement.",
                ],
                "lazy": [
                    "I have to be direct — as our new OD Director, I expected you to arrive with a thorough understanding of our Group. The information about our brands and mission is in your onboarding materials. I have 15 minutes before my next meeting. Come back with a specific question about our leadership challenges, and we'll have a productive conversation.",
                    "That's a very broad question for someone in your role. Our 9 brands are well-documented. I'd rather spend our time on how you plan to solve the leadership mobility gap than on introductions. What specific aspect of the Group do you need my perspective on?",
                ],
                "default": [
                    "That's relevant, but let me push you to think bigger. How does this connect to our strategic priorities — specifically the talent mobility target and the Group DNA framework? Everything you build should ladder up to those.",
                    "I hear you. Let me share my perspective: in this Group, the best ideas come from people who understand both the Group's DNA and their specific brand's soul. How are you planning to capture both in your approach?",
                    "Interesting point. Let me challenge you though — have you tested this thinking with the CHRO? She owns the competency framework, and I want to make sure your approach aligns with the structured thinking she's been doing on the 4 themes.",
                ],
            },
            "CHRO": {
                "greeting": [
                    "Welcome to the team! I'm glad we're finally getting dedicated leadership for this initiative. I've been developing the competency framework for a while now, and I'm eager to hear your approach. What's your starting hypothesis?",
                    "Hello — I've been looking forward to this conversation. The competency framework is close to my heart because I've seen the impact when it's done well. Where would you like to start?",
                ],
                "framework": [
                    "The framework has 4 themes — let me walk you through the thinking. Vision is about strategic foresight; Entrepreneurship is the owner mindset; Passion connects to craft and brand love; Trust is the relational foundation. These aren't arbitrary — they came from analyzing what makes our best leaders successful across brands. The question for you is: how do you operationalize them?",
                    "Vision, Entrepreneurship, Passion, Trust — these are the 4 pillars we've identified. Each has 3 levels: Associate, Mid, and Senior. But the levels aren't just about seniority — they represent a developmental journey. A Senior leader doesn't just 'do more' of what an Associate does; they operate at a fundamentally different level of complexity. How would you design behavior indicators that capture that progression?",
                ],
                "levels": [
                    "The 3-level structure — Associate, Mid, Senior — is deliberate. At the Associate level, we're looking at individual contributor excellence. At Mid, it's about team leadership and cross-functional impact. At Senior, it's about shaping organizational direction. The behavior indicators should feel like a natural journey, not a watered-down version of the senior level. Let me give you an example: for 'Entrepreneurship,' an Associate 'proposes improvements' while a Senior 'drives business model innovation.' See the qualitative shift?",
                    "I want to challenge you on your level design. A common mistake is making the Associate level a 'lite' version of Senior. That's not how development works. Each level should capture a genuinely different mode of operating. How does 'Vision' look different for someone managing a store team versus someone setting the brand's 5-year strategy?",
                ],
                "use_cases": [
                    "The framework has 4 primary use cases: recruitment criteria for competency-based interviews, performance appraisal mapping, individual development planning, and inter-brand mobility assessment. Each use case requires a different lens on the same competencies. For recruitment, you're predicting potential. For appraisal, you're measuring current performance. For mobility, you're assessing adaptability. How would you tailor the framework for each?",
                    "Let me push you further — use cases aren't just about where the framework is applied. They're about who uses it and how. An HR manager using it for recruitment needs a 30-minute interview guide. A leader using it for self-development needs a reflective tool. A mobility committee needs an assessment scorecard. One framework, multiple formats. How are you thinking about that?",
                ],
                "matrix": [
                    "The competency matrix should have 4 themes across the top, 3 levels down the side, and each cell should contain 3-4 clear behavior indicators. The key test: can a manager read a cell and immediately recognize the behavior in one of their team members? If it's too abstract, it won't work in practice. Let me know when you have a draft and I'll calibrate it with you.",
                    "For the matrix, I'd suggest starting with 'Entrepreneurship' — it's the theme where we see the most confusion between levels. If you can nail the progression from 'proposes improvements' (Associate) to 'launches initiatives' (Mid) to 'drives business model innovation' (Senior), the other themes will follow a similar logic.",
                ],
                "turnover": [
                    "I'm deeply concerned about our turnover numbers. We're at 12.8% voluntary turnover, up from 10.2% three years ago. The sharpest increase is in mid-level leaders with 3-7 years tenure — exactly the people we need in our pipeline. The exit interview data says 32% cite 'limited career progression' and 24% cite 'lack of cross-brand opportunities.' The competency framework, when combined with clear mobility pathways, directly addresses both issues.",
                    "Turnover is the canary in the coal mine. When experienced leaders leave, they take institutional brand knowledge that takes years to rebuild. The framework gives us a way to show people a career path that spans beyond one brand — but only if it's implemented credibly, not as another HR initiative-du-jour.",
                ],
                "passion": [
                    "Passion is perhaps the most unique competency in our framework — it's what separates luxury from premium. At the Associate level, it manifests as genuine enthusiasm and attention to detail. At Mid, it's about inspiring others and protecting brand standards under commercial pressure. At Senior, it's about being a cultural ambassador. The behavior indicators must capture the emotional and experiential aspects, not just the cognitive ones.",
                ],
                "trust_theme": [
                    "Trust is the foundation that enables everything else. In a high-autonomy organization like ours, trust isn't just nice-to-have — it's architectural. At Associate level, it's about consistency and open communication. At Mid, it becomes about creating psychological safety and empowering others. At Senior, it's about modeling transparency at the organizational level and building governance structures. How would you assess Trust in a 360° context?",
                ],
                "vision_theme": [
                    "Vision at the Senior level isn't just 'having a vision' — it's about shaping the brand's long-term direction while staying connected to Group strategy. What does strategic foresight look like for a brand director at Gucci versus at Bottega Veneta? The context matters enormously. A Vision indicator at Gucci might emphasize trend-setting, while at Brioni it might emphasize heritage evolution.",
                ],
                "entrepreneurship": [
                    "Entrepreneurship is where we see the most variation across brands. At a fast-growing brand like Balenciaga, 'calculated risk-taking' is part of daily operations. At Brioni, with its tailoring heritage, 'entrepreneurship' manifests more as process innovation and client experience evolution. Your indicators should leave room for both expressions.",
                ],
                "default": [
                    "That's a good starting point. Let me ask you something — how does this connect to the 4 competency themes? I want to make sure we're building from the framework, not around it.",
                    "I appreciate your thinking. Let me offer a framework perspective: every initiative we launch should map back to at least one of the 4 themes. Otherwise, it risks being disconnected from how we develop and assess leaders.",
                    "Interesting approach. Let me reframe that through the competency lens — which theme does this primarily develop? And how would you measure the impact at each level (Associate, Mid, Senior)?",
                ],
            },
            "EB Regional Manager": {
                "greeting": [
                    "Good to connect. I've been expecting this conversation — we need a solid plan before we start rolling anything out in Europe. I have a lot of ground-level reality to share. Where would you like to start?",
                    "Welcome aboard. I'll cut to the chase — Europe is complicated. 15 countries, multiple languages, different labor laws, and varying levels of HR capability. Let's talk specifics.",
                ],
                "rollout": [
                    "For the rollout, I strongly recommend a phased approach. Wave 1: Italy, France, UK — they have the strongest HR teams and highest readiness. Wave 2: Germany, Switzerland, Spain — medium readiness but some regulatory hurdles. Wave 3: Nordics and Eastern Europe — they need the most pre-work. Trying to launch everywhere at once would be a recipe for failure.",
                    "A phased rollout is non-negotiable from my perspective. I've seen what happens when Group initiatives try to go Big Bang in Europe — you get compliance in the big markets and chaos everywhere else. Start with 3 anchor countries, build success stories, then use those as proof points for the next wave.",
                ],
                "training": [
                    "Trainers are our biggest bottleneck. We currently have 12 qualified trainers across Europe, and for Wave 1 alone we need at least 25. The trainer profile isn't simple: bilingual, brand knowledge across at least 2 brands, coaching certification, and 2+ years facilitating leadership workshops. The certification program is a 2-day intensive plus 1 day shadowing. We'll need to partner with external coaches for the first wave while we build internal capacity.",
                    "The train-the-trainer model is the right approach, but let me be realistic — in the Nordics and Eastern Europe, we'll need at least a full 2-day certification workshop before local HR can facilitate. Some of these teams have never run a competency-based workshop. We can't just send slides and expect them to deliver.",
                ],
                "challenges": [
                    "Honest answer? It's mixed. In France and Italy, we have strong HR leads who've been doing informal competency assessments already — they'll adapt quickly. But in the Nordics and Eastern Europe, the teams are smaller and focused purely on operational HR. They'll need extensive pre-work. And I'll flag something: three brand managers in Germany have already pushed back, saying this feels like 'HQ imposing a one-size-fits-all approach.' You'll need a change management story that addresses that head-on.",
                    "The biggest challenge isn't logistics — it's perception. If local teams see this as 'another headquarters initiative,' it's dead on arrival. We need to co-create with them, not deploy to them. In Germany, the works council must approve any new assessment framework. In France, GDPR applies to 360° feedback data. In Italy, the concept of formal coaching is still relatively new in corporate settings. Each market has its own reality.",
                ],
                "kpis": [
                    "For KPIs, you need both leading and lagging indicators. Leading: workshop participation rate (target >90%), trainer certification completion, manager awareness survey score. Lagging: cross-brand mobility rate (the big one — 2.3% to 8%), leadership pipeline strength, high-potential retention rate. I'd also add a 'sentiment tracker' — a quarterly pulse on how people feel about the framework. If sentiment drops, we need to adjust before the numbers reflect it.",
                    "I'd structure the measurement in two tiers. Tier 1 is operational: are we hitting participation targets, are trainers certified, is the platform working? Tier 2 is strategic: mobility rates, internal promotion, retention. Tier 1 gives you early warning signals. Tier 2 tells you if the program is actually moving the needle. Don't wait for Tier 2 data to make course corrections.",
                ],
                "regions": [
                    "Let me give you the quick snapshot. Italy and France: high readiness, strong HR, but regulatory complexity (GDPR, works councils). UK: medium-high readiness, good coaching culture, but post-Brexit mobility complexities. Germany: medium readiness, pushback risk, works council approval needed. Switzerland: multi-lingual challenge but high quality expectations. Nordics: low-medium readiness, small teams, need pre-certification. Eastern Europe: low readiness, operational HR only, need the most support.",
                    "Each market is different, and I can't stress this enough. What works in Milan will NOT work in Stockholm. The cultural attitudes toward feedback, hierarchy, and 'corporate frameworks' vary enormously. Your rollout plan needs to be locally adapted — same framework, different delivery.",
                ],
                "change": [
                    "Change management is where most Group initiatives fail in Europe. My recommendation: co-create local examples with brand managers in each country. When a German brand manager sees an example featuring their brand instead of a generic Gucci Group one, the resistance drops significantly. Also, find your local champions — HR leads who believe in this and can evangelize to their peers.",
                    "For messaging, avoid the phrase 'Group-mandated.' Instead, position it as 'a tool that helps your brand develop leaders more effectively.' The frame matters enormously. In my experience, the moment people feel imposed upon, they compliance-check rather than genuinely adopt.",
                ],
                "gdpr": [
                    "GDPR is a real constraint, especially for the 360° feedback component. In France specifically, you need a data processing impact assessment before collecting any feedback data. All responses must be stored in EU-based servers, anonymity must be technically guaranteed (not just promised), and participants must have right to access and deletion. I recommend involving our data privacy team before the platform goes live.",
                ],
                "budget": [
                    "Budget is tight. We can't pilot all countries simultaneously. My recommendation: invest heavily in Wave 1 (Italy, France, UK) to build a proof of concept, then use the data to justify the budget for Waves 2 and 3. External coaching partners will be needed for Wave 1 — that's about 40% of the trainer budget. By Wave 3, we should have enough internal trainers to reduce external costs.",
                ],
                "default": [
                    "That's relevant. Let me share what I'm seeing on the ground in Europe — the appetite for this is there, but the execution details will make or break it. What specific aspect of the regional rollout would you like to dive into?",
                    "Good question. From my perspective running communications across 15 European markets, I'd say the key is adaptation without dilution — keep the framework consistent but make the delivery locally relevant. What's your thinking on that?",
                    "Let me give you some practical context. In my experience, the gap between how HQ designs initiatives and how they land in regional offices is where value gets lost. How are you planning to bridge that gap?",
                ],
            },
        }
