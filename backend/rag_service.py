# backend/rag_service.py
import re
import os
import httpx
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from schemes_data import SCHEMES_DATA
from schemas import Citation, ChatResponse

class SchemeRAGService:
    def __init__(self):
        self.schemes = SCHEMES_DATA
        self.corpus_docs: List[Dict[str, Any]] = []
        self.corpus_texts: List[str] = []
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            stop_words=None,
            max_features=5000
        )
        self._build_index()

    def _build_index(self):
        """Index scheme metadata, descriptions, benefits, and eligibility rules."""
        docs = []
        texts = []
        for s in self.schemes:
            # English document
            en_text = f"{s['title_en']} {s['ministry']} {s['category']} {s['brief_en']} {s['description_en']} " \
                      f"{' '.join(s['benefits_en'])} {s['eligibility_summary_en']} {' '.join(s['documents_required_en'])} " \
                      f"{' '.join(s['application_steps_en'])} {' '.join(s['tags'])}"
            docs.append({"scheme": s, "lang": "en", "text": en_text})
            texts.append(en_text)

            # Hindi document
            hi_text = f"{s['title_hi']} {s['title_en']} {s['category']} {s['brief_hi']} {s['description_hi']} " \
                      f"{' '.join(s['benefits_hi'])} {s['eligibility_summary_hi']} {' '.join(s['documents_required_hi'])} " \
                      f"{' '.join(s['application_steps_hi'])} {' '.join(s['tags'])}"
            docs.append({"scheme": s, "lang": "hi", "text": hi_text})
            texts.append(hi_text)

            # Marathi document
            mr_text = f"{s['title_mr']} {s['title_en']} {s['category']} {s['brief_mr']} {s['description_mr']} " \
                      f"{' '.join(s['benefits_mr'])} {s['eligibility_summary_mr']} {' '.join(s['documents_required_mr'])} " \
                      f"{' '.join(s['application_steps_mr'])} {' '.join(s['tags'])}"
            docs.append({"scheme": s, "lang": "mr", "text": mr_text})
            texts.append(mr_text)

        self.corpus_docs = docs
        self.corpus_texts = texts
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus_texts)

    def retrieve(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Retrieve most relevant schemes using vector cosine similarity."""
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        
        # Rank by score
        ranked_indices = similarities.argsort()[::-1]
        
        seen_scheme_ids = set()
        retrieved_results = []
        
        for idx in ranked_indices:
            score = float(similarities[idx])
            doc = self.corpus_docs[idx]
            scheme_id = doc["scheme"]["id"]
            
            if scheme_id not in seen_scheme_ids and (score > 0.05 or len(retrieved_results) < 2):
                seen_scheme_ids.add(scheme_id)
                retrieved_results.append({
                    "scheme": doc["scheme"],
                    "score": round(score, 4),
                    "matched_lang": doc["lang"]
                })
            
            if len(retrieved_results) >= top_k:
                break
                
        return retrieved_results

    @staticmethod
    def _sanitize_query(query: str) -> str:
        """Sanitize query against excessive length and malformed input."""
        if not query:
            return ""
        cleaned = " ".join(query.strip().split())
        return cleaned[:500]

    async def answer_query(
        self,
        query: str,
        language: str = "en",
        api_key: Optional[str] = None,
        llm_provider: Optional[str] = "gemini",
        user_context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """Execute RAG pipeline: Retrieve relevant scheme context, then generate grounded response."""
        query = self._sanitize_query(query)
        retrieved = self.retrieve(query, top_k=4)
        
        citations: List[Citation] = []
        referenced_schemes = []
        
        for r in retrieved:
            s = r["scheme"]
            title = s.get(f"title_{language}") or s["title_en"]
            citations.append(Citation(
                scheme_id=s["id"],
                title=title,
                official_portal_url=s["official_portal_url"],
                relevance_score=r["score"]
            ))
            referenced_schemes.append({
                "id": s["id"],
                "title": title,
                "category": s["category"],
                "brief": s.get(f"brief_{language}") or s["brief_en"],
                "portal": s["official_portal_url"],
                "helpline": s.get("helpline_number")
            })

        # Check if external LLM API key is provided
        effective_api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        if effective_api_key and (llm_provider in ["gemini", "openai"]):
            try:
                answer = await self._call_external_llm(
                    query=query,
                    language=language,
                    retrieved=retrieved,
                    api_key=effective_api_key,
                    provider=llm_provider,
                    user_context=user_context
                )
                followups = self._generate_followups(retrieved, language)
                return ChatResponse(
                    query=query,
                    language=language,
                    answer=answer,
                    citations=citations,
                    suggested_followups=followups,
                    referenced_schemes=referenced_schemes
                )
            except Exception as e:
                # Fallback to local grounded RAG generator if external call fails
                print(f"[RAG fallback] External LLM error: {e}. Falling back to internal engine.")

        # Grounded Internal RAG Generator (Offline-capable & High Accuracy)
        answer = self._synthesize_grounded_answer(query, retrieved, language, user_context)
        followups = self._generate_followups(retrieved, language)

        return ChatResponse(
            query=query,
            language=language,
            answer=answer,
            citations=citations,
            suggested_followups=followups,
            referenced_schemes=referenced_schemes
        )

    def _synthesize_grounded_answer(
        self,
        query: str,
        retrieved: List[Dict[str, Any]],
        language: str,
        user_context: Optional[Dict[str, Any]]
    ) -> str:
        """Synthesize a structured, accurate, hallucination-free response from retrieved knowledge."""
        if not retrieved:
            if language == "hi":
                return "मुझे आपके प्रश्न से संबंधित कोई विशिष्ट सरकारी योजना नहीं मिली। कृपया अपने प्रश्न में अपनी आयु, पेशा (जैसे किसान, छात्र) या श्रेणी का उल्लेख करें।"
            elif language == "mr":
                return "मला तुमच्या प्रश्नाशी संबंधित कोणतीही विशिष्ट शासकीय योजना आढळली नाही. कृपया तुमच्या प्रश्नात तुमचे वय, व्यवसाय (उदा. शेतकरी, विद्यार्थी) किंवा प्रवर्गाचा उल्लेख करा."
            else:
                return "I could not find an exact matching government scheme for your query. Please provide more context such as your age, occupation (e.g., student, farmer, artisan), or category."

        primary = retrieved[0]["scheme"]
        title = primary.get(f"title_{language}") or primary["title_en"]
        brief = primary.get(f"brief_{language}") or primary["brief_en"]
        eligibility = primary.get(f"eligibility_summary_{language}") or primary["eligibility_summary_en"]
        benefits = primary.get(f"benefits_{language}") or primary["benefits_en"]
        steps = primary.get(f"application_steps_{language}") or primary["application_steps_en"]
        docs = primary.get(f"documents_required_{language}") or primary["documents_required_en"]
        portal = primary["official_portal_url"]
        helpline = primary.get("helpline_number", "N/A")

        if language == "hi":
            response_parts = [
                f"### मुख्य योजना: {title}",
                f"{brief}\n",
                "**प्रमुख लाभ एवं विशेषताएं:**",
                "\n".join([f"- {b}" for b in benefits[:3]]),
                f"\n**पात्रता शर्तें:**\n{eligibility}",
                "\n**आवेदन कैसे करें:**",
                f"- आधिकारिक पोर्टल: [{portal}]({portal})",
                f"- आवेदन का माध्यम: {primary.get('application_mode', 'ऑनलाइन')}",
                f"- हेल्पलाइन नंबर: {helpline}",
                f"- पहला कदम: {steps[0] if steps else 'आधिकारिक पोर्टल पर जाएं'}",
                f"\n**आवश्यक दस्तावेज:** {', '.join(docs[:4])}."
            ]
            if len(retrieved) > 1:
                other_titles = [r["scheme"].get(f"title_hi") or r["scheme"]["title_en"] for r in retrieved[1:3]]
                response_parts.append(f"\n*अन्य संबंधित योजनाएं जिन पर आप विचार कर सकते हैं:* {', '.join(other_titles)}")

        elif language == "mr":
            response_parts = [
                f"### प्रमुख योजना: {title}",
                f"{brief}\n",
                "**मुख्य लाभ आणि वैशिष्ट्ये:**",
                "\n".join([f"- {b}" for b in benefits[:3]]),
                f"\n**पात्रतेचे निकष:**\n{eligibility}",
                "\n**अर्ज कसा करावा:**",
                f"- अधिकृत संकेतस्थळ: [{portal}]({portal})",
                f"- अर्ज पद्धती: {primary.get('application_mode', 'ऑनलाइन')}",
                f"- हेल्पलाईन क्रमांक: {helpline}",
                f"- पहिली पायरी: {steps[0] if steps else 'अधिकृत पोर्टलवर नोंदणी करा'}",
                f"\n**आवश्यक कागदपत्रे:** {', '.join(docs[:4])}."
            ]
            if len(retrieved) > 1:
                other_titles = [r["scheme"].get(f"title_mr") or r["scheme"]["title_en"] for r in retrieved[1:3]]
                response_parts.append(f"\n*इतर संबंधित योजना ज्यांचा आपण विचार करू शकता:* {', '.join(other_titles)}")

        else:
            response_parts = [
                f"### Primary Recommendation: {title}",
                f"{brief}\n",
                "**Key Benefits & Highlights:**",
                "\n".join([f"- {b}" for b in benefits[:3]]),
                f"\n**Eligibility Criteria:**\n{eligibility}",
                "\n**How to Apply:**",
                f"- Official Portal: [{portal}]({portal})",
                f"- Application Mode: {primary.get('application_mode', 'Online')}",
                f"- Helpline: {helpline}",
                f"- First Step: {steps[0] if steps else 'Visit official website'}",
                f"\n**Essential Documents:** {', '.join(docs[:4])}."
            ]
            if len(retrieved) > 1:
                other_titles = [r["scheme"]["title_en"] for r in retrieved[1:3]]
                response_parts.append(f"\n*Other related schemes you may explore:* {', '.join(other_titles)}")

        return "\n".join(response_parts)

    def _generate_followups(self, retrieved: List[Dict[str, Any]], language: str) -> List[str]:
        if not retrieved:
            return [
                "What schemes are available for farmers?",
                "Which scholarship can I get as a college student?",
                "Are there loans for small businesses?"
            ]
        s = retrieved[0]["scheme"]
        title = s.get(f"title_{language}") or s["title_en"]
        
        if language == "hi":
            return [
                f"{title} के लिए कौन से दस्तावेज चाहिए?",
                f"{title} में ऑनलाइन आवेदन करने की अंतिम तिथि क्या है?",
                "क्या इस योजना के लिए आय प्रमाण पत्र अनिवार्य है?"
            ]
        elif language == "mr":
            return [
                f"{title} साठी कोणती कागदपत्रे लागतात?",
                f"{title} चा अर्ज ऑनलाईन कसा करावा?",
                "या योजनेसाठी उत्पन्नाचा दाखला आवश्यक आहे का?"
            ]
        else:
            return [
                f"What are the mandatory documents for {s['title_en']}?",
                f"How do I check application status for {s['title_en']}?",
                "Is an income certificate required for this scheme?"
            ]

    async def _call_external_llm(
        self,
        query: str,
        language: str,
        retrieved: List[Dict[str, Any]],
        api_key: str,
        provider: str,
        user_context: Optional[Dict[str, Any]]
    ) -> str:
        """Call external LLM API (Google Gemini or OpenAI) with retrieved context."""
        context_blocks = []
        for r in retrieved:
            s = r["scheme"]
            context_blocks.append(
                f"Scheme: {s['title_en']} ({s.get('title_hi')})\n"
                f"Ministry: {s['ministry']}\n"
                f"Benefits: {'; '.join(s['benefits_en'])}\n"
                f"Eligibility: {s['eligibility_summary_en']}\n"
                f"Portal: {s['official_portal_url']}\n"
                f"Helpline: {s.get('helpline_number')}\n"
            )
        context_str = "\n---\n".join(context_blocks)

        prompt = f"""You are BharatScheme AI, an official and helpful assistant for Indian Government schemes.
Answer the user's question accurately in language: {language} (use English, Hindi, or Marathi based on the parameter).
Use ONLY the verified scheme context below. If you don't know, state it clearly. Do not invent scheme names or benefits.
Always cite the official portal and helpline number where available.

User Context: {user_context or 'None'}
User Question: {query}

Verified Scheme Knowledge Base:
{context_str}
"""

        if provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, json=payload)
                data = res.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            # OpenAI compatible
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(url, headers=headers, json=payload)
                data = res.json()
                return data["choices"][0]["message"]["content"]

rag_service = SchemeRAGService()
