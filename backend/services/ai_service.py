"""
AI pipeline service for ticket categorization, draft responses, and assignment.

Uses Anthropic Claude. Falls back to rule-based heuristics if no API key is configured.
All AI requests go through the centralized call_ai() function.
Prompt YAML files define model, temperature, max_tokens alongside the system prompt.
"""

import json
import re
from config import get_settings
from prompts import load_prompt


# Category keywords for fallback heuristic
CATEGORY_KEYWORDS = {
    "refund_request": ["refund", "remboursement", "rückerstattung", "geld zurück", "money back", "reimburse"],
    "subscription_cancellation": ["cancel", "kündigen", "kündigung", "annuler", "résiliation", "abo kündigen", "abonnement"],
    "subscription_info": ["subscription", "abonnement", "abo", "plan", "pricing", "preis"],
    "billing_invoice": ["invoice", "rechnung", "facture", "billing", "payment", "zahlung"],
    "flashcard_issues": ["flashcard", "karteikarte", "lernkarte", "lerndeck", "deck", "karten"],
    "quiz_issues": ["quiz", "test", "prüfung", "exam question"],
    "podcast_issues": ["podcast", "audio"],
    "summary_issues": ["summary", "zusammenfassung", "résumé", "export"],
    "mindmap_issues": ["mindmap", "mind map"],
    "mock_exam_issues": ["mock exam", "probeprüfung", "probe"],
    "content_upload": ["upload", "hochladen", "import", "pdf", "document", "dokument"],
    "technical_errors": ["error", "fehler", "bug", "crash", "laden", "loading", "funktioniert nicht", "doesn't work", "ne marche pas"],
    "account_issues": ["account", "konto", "login", "password", "passwort", "einloggen", "anmelden"],
    "language_issues": ["language", "sprache", "langue", "translation", "übersetzung"],
    "general_how_to": ["how to", "wie kann", "comment faire", "how do i"],
    "data_loss": ["lost", "verloren", "disappeared", "verschwunden", "deleted", "gelöscht"],
    "misunderstanding": ["what is", "was ist", "qu'est-ce que"],
    "garbage": [],
}

LANGUAGE_INDICATORS = {
    "de": ["ich", "und", "die", "das", "ist", "habe", "mein", "kann", "nicht", "ein", "mir", "bitte", "guten"],
    "fr": ["je", "est", "les", "une", "mon", "pas", "que", "pour", "dans", "bonjour", "merci", "vous"],
    "nl": ["ik", "het", "een", "van", "niet", "dat", "heb", "mijn", "maar"],
    "it": ["sono", "mio", "non", "che", "una", "per", "questo", "buongiorno"],
    "en": ["the", "is", "my", "have", "can", "please", "would", "hello", "thanks"],
}

# Team member routing rules
ASSIGNMENT_RULES = {
    "refund_request": "billing",
    "subscription_cancellation": "billing",
    "subscription_info": "billing",
    "billing_invoice": "billing",
    "technical_errors": "engineering",
    "data_loss": "engineering",
    "flashcard_issues": "support",
    "quiz_issues": "support",
    "content_upload": "support",
    "account_issues": "support",
}


def _parse_json_response(text: str) -> dict:
    """Parse JSON from AI response, handling markdown fences and plain text."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    stripped = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    stripped = re.sub(r"\n?```\s*$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Try to extract first JSON object from the text
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("No valid JSON found in AI response", text, 0)


def detect_language(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for lang, words in LANGUAGE_INDICATORS.items():
        scores[lang] = sum(1 for w in words if f" {w} " in f" {text_lower} ")
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "en"


async def call_ai(
    prompt_name: str,
    user_message: str,
    format_vars: dict | None = None,
) -> str:
    """Centralized AI request handler.

    Loads the prompt YAML (which includes model, temperature, max_tokens,
    and system message), formats the system prompt with optional variables,
    and sends the request to the Anthropic API.

    Args:
        prompt_name: Name of the prompt YAML file (without .yaml extension).
        user_message: The user message content to send.
        format_vars: Optional dict of variables to format into the system prompt.

    Returns:
        The raw text response from the AI model.
    """
    import anthropic

    settings = get_settings()
    prompt = load_prompt(prompt_name)

    model = prompt.get("model", "claude-sonnet-4-20250514")
    temperature = prompt.get("temperature", 0)
    max_tokens = prompt.get("max_tokens", 1024)
    system_msg = prompt["system"]

    if format_vars:
        system_msg = system_msg.format(**format_vars)

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    result = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_msg,
        messages=[{"role": "user", "content": user_message}],
    )

    return result.content[0].text


def categorize_heuristic(text: str) -> tuple[str, float]:
    text_lower = text.lower()
    best_category = "other"
    best_score = 0
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            best_category = category
    confidence = min(0.3 + best_score * 0.15, 0.8) if best_score > 0 else 0.1
    return best_category, confidence


def extract_source(text: str) -> str:
    if text.startswith("MOBILE:"):
        return "mobile"
    elif text.startswith("WEB:"):
        return "webapp"
    return "email"


async def categorize_ticket(body: str) -> dict:
    """Categorize a ticket using AI (LangChain/Claude) or fallback heuristics."""
    settings = get_settings()
    language = detect_language(body)

    if settings.anthropic_api_key:
        try:
            return await _categorize_with_ai(body, language, settings)
        except Exception as e:
            print(f"AI categorization failed, falling back to heuristics: {e}")

    # Fallback: heuristic-based categorization
    category, confidence = categorize_heuristic(body)
    suggested_role = ASSIGNMENT_RULES.get(category, "support")

    return {
        "category": category,
        "confidence": confidence,
        "summary": body[:200] + "..." if len(body) > 200 else body,
        "suggested_assignee_role": suggested_role,
        "language": language,
        "translated_body": None,
    }


async def draft_response(
    body: str, category: str, language: str, enrichment_context: str | None = None
) -> dict:
    """Draft a response using AI or return a template."""
    settings = get_settings()

    if settings.anthropic_api_key:
        try:
            return await _draft_with_ai(body, category, language, settings, enrichment_context)
        except Exception as e:
            print(f"AI draft failed, falling back to template: {e}")

    # Fallback: template-based response
    return _template_response(category, language)


async def _categorize_with_ai(body: str, language: str, settings) -> dict:
    categories = ", ".join(CATEGORY_KEYWORDS.keys())
    text = await call_ai(
        prompt_name="categorize",
        user_message=f"Ticket (detected language: {language}):\n{body}",
        format_vars={"categories": categories},
    )
    parsed = _parse_json_response(text)
    parsed["language"] = language
    return parsed


async def _draft_with_ai(
    body: str, category: str, language: str, settings, enrichment_context: str | None = None
) -> dict:
    user_message = f"Category: {category}\nTicket:\n{body}"
    if enrichment_context:
        user_message += f"\n\n--- Internal Context (from Sentry, PostHog, database) ---\n{enrichment_context}"

    text = await call_ai(
        prompt_name="draft",
        user_message=user_message,
        format_vars={"language": language},
    )
    return _parse_json_response(text)


async def translate_to_english(body: str, language: str) -> dict:
    """Translate ticket body to English using AI or return None."""
    settings = get_settings()

    if language == "en":
        return {"translated_body": body, "source_language": "en"}

    if settings.anthropic_api_key:
        try:
            return await _translate_with_ai(body, language, settings)
        except Exception as e:
            print(f"AI translation failed, falling back to heuristic: {e}")

    return {"translated_body": None, "source_language": language}


async def _translate_with_ai(body: str, language: str, settings) -> dict:
    translated = await call_ai(
        prompt_name="translate",
        user_message=body,
    )
    return {"translated_body": translated, "source_language": language}


def _template_response(category: str, language: str) -> dict:
    templates = {
        "refund_request": {
            "en": "Thank you for reaching out. We understand your concern regarding the refund. We've escalated this to our billing team who will review your case and get back to you within 24-48 hours.\n\nBest regards,\nStudyflash Support Team",
            "de": "Vielen Dank für Ihre Nachricht. Wir verstehen Ihr Anliegen bezüglich der Rückerstattung. Wir haben dies an unser Abrechnungsteam weitergeleitet, das Ihren Fall prüfen und sich innerhalb von 24-48 Stunden bei Ihnen melden wird.\n\nMit freundlichen Grüßen,\nStudyflash Support Team",
            "fr": "Merci de nous avoir contactés. Nous comprenons votre préoccupation concernant le remboursement. Nous avons transmis votre demande à notre équipe de facturation qui examinera votre cas et vous répondra dans les 24 à 48 heures.\n\nCordialement,\nStudyflash Support Team",
        },
        "subscription_cancellation": {
            "en": "Thank you for contacting us about your subscription. We're sorry to see you go. We'll process your cancellation request and confirm via email.\n\nBest regards,\nStudyflash Support Team",
            "de": "Vielen Dank für Ihre Nachricht bezüglich Ihres Abonnements. Es tut uns leid, dass Sie gehen möchten. Wir werden Ihre Kündigungsanfrage bearbeiten und per E-Mail bestätigen.\n\nMit freundlichen Grüßen,\nStudyflash Support Team",
            "fr": "Merci de nous avoir contactés au sujet de votre abonnement. Nous sommes désolés de vous voir partir. Nous traiterons votre demande d'annulation et confirmerons par e-mail.\n\nCordialement,\nStudyflash Support Team",
        },
    }

    default = {
        "en": "Thank you for reaching out to Studyflash Support. We've received your message and will review it shortly. A team member will get back to you soon.\n\nBest regards,\nStudyflash Support Team",
        "de": "Vielen Dank für Ihre Nachricht an den Studyflash Support. Wir haben Ihre Nachricht erhalten und werden sie in Kürze prüfen. Ein Teammitglied wird sich bald bei Ihnen melden.\n\nMit freundlichen Grüßen,\nStudyflash Support Team",
        "fr": "Merci d'avoir contacté le support Studyflash. Nous avons bien reçu votre message et nous l'examinerons sous peu. Un membre de l'équipe vous répondra bientôt.\n\nCordialement,\nStudyflash Support Team",
    }

    category_templates = templates.get(category, default)
    draft = category_templates.get(language, category_templates.get("en", default["en"]))

    return {"draft_response": draft, "confidence": 0.5}
