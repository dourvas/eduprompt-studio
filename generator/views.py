from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
import requests
import json
import logging

from .notices import get_notice

# Application logging must never contain what the teacher typed or what Gemini
# returned. Only status codes and exception class names are logged.
logger = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent"


def index(request):
    # Nothing about the visit is stored: no session, no page-view record.
    return render(request, "generator/index.html", {
        "notice": get_notice(settings.UI_LANGUAGE),
    })

# NEW ENHANCED THEORY SELECTION SYSTEM

def suggest_optimal_theory(methodology, task, context):
    """
    Intelligent theory suggestion based on pedagogical context
    """
    methodology_lower = methodology.lower()
    task_lower = task.lower()
    context_lower = context.lower()
    
    # Methodology-based suggestions (highest priority)
    if any(keyword in methodology_lower for keyword in ['inquiry', 'explore', 'discovery', 'problem']):
        return 'constructivist'
    elif any(keyword in methodology_lower for keyword in ['collaborative', 'group', 'peer']):
        return 'social_learning'
    elif any(keyword in methodology_lower for keyword in ['technology', 'ai', 'digital']):
        return 'tpack'
    elif any(keyword in methodology_lower for keyword in ['differentiated', 'adaptive', 'personalized']):
        return 'udl'
    elif any(keyword in methodology_lower for keyword in ['scaffolding', 'support', 'guidance']):
        return 'scaffolding'
    
    # Task-based suggestions (medium priority)
    elif any(keyword in task_lower for keyword in ['critical thinking', 'questions', 'analysis']):
        return 'blooms'
    elif any(keyword in task_lower for keyword in ['assessment', 'quiz', 'rubric']):
        return 'blooms'
    elif any(keyword in task_lower for keyword in ['lesson plan', 'curriculum']):
        return 'blooms'
    elif any(keyword in task_lower for keyword in ['differentiated', 'multiple intelligences']):
        return 'differentiation'
    
    # Context-based suggestions (lower priority)
    elif any(keyword in context_lower for keyword in ['mixed-ability', 'special needs', 'learning difficulties']):
        return 'udl'
    
    # Default fallback
    return 'blooms'

def generate_blooms_enhancement(form_data):
    """Generate Bloom's Taxonomy specific enhancement"""
    task = form_data.get("task", "").lower()
    
    if any(keyword in task for keyword in ["critical thinking", "questions", "analysis"]):
        return "Structure questions to progress from analysis (break down concepts) to evaluation (judge quality/value) to creation (generate new ideas), following Bloom's cognitive taxonomy levels"
    elif any(keyword in task for keyword in ["practice", "exercises", "activities"]):
        return "Design activities that span remember (recall facts) → understand (explain concepts) → apply (use knowledge) → analyze (examine relationships), progressing through Bloom's taxonomy"
    elif any(keyword in task for keyword in ["assessment", "quiz", "rubric"]):
        return "Include assessment items covering multiple cognitive levels: remembering key facts, understanding main concepts, applying knowledge to new situations, and analyzing complex scenarios (Bloom's taxonomy)"
    elif any(keyword in task for keyword in ["lesson plan", "introduction"]):
        return "Structure the lesson to progress through cognitive levels from foundational knowledge (remember/understand) to application and higher-order thinking (analyze/evaluate/create), following Bloom's taxonomy"
    else:
        return "Incorporate cognitive progression from basic recall to higher-order thinking skills, following Bloom's taxonomy levels"

def generate_udl_enhancement(form_data):
    """Generate UDL specific enhancement"""
    context = form_data.get("context", "").lower()
    
    if any(keyword in context for keyword in ["mixed-ability", "learning difficulties", "special needs"]):
        return "Provide multiple means of representation (visual, auditory, tactile), multiple means of engagement (choice, relevance, challenge levels), and multiple means of expression (verbal, written, demonstration) to support diverse learners (UDL principles)"
    elif any(keyword in context for keyword in ["esl", "efl"]):
        return "Include visual supports, simplified language options, and multiple ways to demonstrate understanding to accommodate language learners (UDL principles)"
    else:
        return "Design with flexibility in content presentation, student engagement methods, and expression formats to accommodate diverse learning needs (UDL principles)"

# Replace the generate_tpack_enhancement function in views.py

def generate_tpack_enhancement(form_data):
    """Generate TPACK specific enhancement - more specific and actionable"""
    task = form_data.get("task", "").lower()
    methodology = form_data.get("methodology", "").lower()
    subject = form_data.get("subject", "").lower()
    
    if any(keyword in task for keyword in ["lesson plan", "curriculum", "complete plan"]):
        return "Explicitly specify: (1) which AI tools/features will be used, (2) how they support specific learning objectives, (3) what pedagogical role technology plays in fraction instruction, and (4) how digital tools enhance content understanding rather than replace teaching (TPACK framework)"
    
    elif any(keyword in task for keyword in ["assessment", "quiz", "rubric"]):
        return "Detail how AI-enhanced assessment tools will measure fraction understanding, specify the pedagogical rationale for using technology in evaluation, and explain how digital assessment connects to fraction learning goals (TPACK framework)"
    
    elif any(keyword in task for keyword in ["practice", "exercises", "activities"]):
        return "Describe specific AI-powered practice tools, explain how technology personalizes fraction practice, detail the pedagogical benefits of digital exercises, and specify how AI feedback supports fraction skill development (TPACK framework)"
    
    elif any(keyword in methodology for keyword in ["ai", "technology", "digital"]):
        return "Clearly define the AI's pedagogical role, specify how technology enhances fraction instruction methods, explain the connection between digital tools and mathematical content mastery, and justify technology choices with educational theory (TPACK framework)"
    
    else:
        return "Include specific details about: how technology supports fraction learning goals, what pedagogical purpose AI serves, and how digital tools enhance rather than replace effective math teaching practices (TPACK framework)"
def generate_constructivist_enhancement(form_data):
    """Generate Constructivist Learning enhancement"""
    methodology = form_data.get("methodology", "").lower()
    
    if any(keyword in methodology for keyword in ["inquiry", "discovery", "explore"]):
        return "Support active knowledge construction through guided discovery, encouraging learners to build understanding through hands-on exploration and meaningful connections to prior knowledge"
    elif any(keyword in methodology for keyword in ["problem", "real-world"]):
        return "Facilitate learning through authentic problem-solving experiences where students construct knowledge by connecting new information to existing understanding and real-world contexts"
    else:
        return "Encourage active knowledge construction through hands-on experiences, reflection, and connection-making rather than passive information reception"

def generate_social_learning_enhancement(form_data):
    """Generate Social Learning Theory enhancement"""
    methodology = form_data.get("methodology", "").lower()
    
    if any(keyword in methodology for keyword in ["collaborative", "group", "peer"]):
        return "Leverage peer interaction and collaborative learning opportunities where students learn through observation, discussion, and shared knowledge construction in social contexts"
    elif any(keyword in methodology for keyword in ["discussion", "teamwork"]):
        return "Create structured opportunities for social learning through peer modeling, collaborative problem-solving, and shared reflection on learning processes"
    else:
        return "Incorporate peer interaction and social learning opportunities to enhance understanding through shared knowledge construction"

def generate_scaffolding_enhancement(form_data):
    """Generate Scaffolding enhancement"""
    context = form_data.get("context", "").lower()
    task = form_data.get("task", "").lower()
    
    if any(keyword in context for keyword in ["ages 3-5", "preschool"]):
        return "Provide extensive scaffolding with concrete examples, hands-on materials, and step-by-step guidance, gradually reducing support as children develop independence"
    elif any(keyword in context for keyword in ["ages 6-11", "primary"]):
        return "Include scaffolding supports such as graphic organizers, worked examples, and guided practice, with clear steps toward independent application"
    elif any(keyword in task for keyword in ["complex", "advanced"]):
        return "Break down complex tasks into manageable steps with temporary supports, modeling, and guided practice before expecting independent performance"
    else:
        return "Provide appropriate scaffolding supports that can be gradually removed as learners develop competence and confidence"

def generate_differentiation_enhancement(form_data):
    """Generate Differentiated Instruction enhancement"""
    task = form_data.get("task", "").lower()
    
    if any(keyword in task for keyword in ["differentiated", "multiple intelligences"]):
        return "Address diverse learning preferences through varied content presentation, process options, and product choices, allowing multiple pathways to demonstrate understanding"
    elif any(keyword in task for keyword in ["adaptive", "personalized"]):
        return "Provide flexible learning options that adapt to individual student needs, interests, and readiness levels through varied instructional approaches"
    else:
        return "Include differentiation strategies that address diverse learning styles, abilities, and interests through multiple instructional approaches"

# Replace the add_selected_theory_enhancement function in views.py

def add_selected_theory_enhancement(prompt, form_data, selected_theory):
    """
    Enhanced theory selection system - applies only the selected theory
    by modifying the Instructions section instead of appending at the end.
    """
    
    # Extract form data
    task = form_data.get("task", "")
    context = form_data.get("context", "")
    methodology = form_data.get("methodology", "")
    
    # If no theory selected, auto-suggest the most relevant one
    if not selected_theory:
        selected_theory = suggest_optimal_theory(methodology, task, context)
    
    # Theory enhancement mappings
    theory_enhancements = {
        'blooms': generate_blooms_enhancement(form_data),
        'udl': generate_udl_enhancement(form_data),
        'tpack': generate_tpack_enhancement(form_data),
        'constructivist': generate_constructivist_enhancement(form_data),
        'social_learning': generate_social_learning_enhancement(form_data),
        'scaffolding': generate_scaffolding_enhancement(form_data),
        'differentiation': generate_differentiation_enhancement(form_data)
    }
    
    # Apply the selected theory enhancement by modifying the Instructions
    if selected_theory in theory_enhancements:
        enhancement = theory_enhancements[selected_theory]
        if enhancement:
            # Find the Instructions section and add enhancement as instruction #7
            instructions_start = prompt.find("Instructions:")
            if instructions_start != -1:
                # Find the end of instruction 6
                instruction_6_end = prompt.find("6. Keep it professional and focused on the educational task")
                if instruction_6_end != -1:
                    instruction_6_end = prompt.find("\n", instruction_6_end) + 1
                    
                    # Insert the enhancement as instruction #7
                    enhancement_instruction = f"7. IMPORTANT: {enhancement}\n"
                    
                    prompt = (prompt[:instruction_6_end] + 
                            enhancement_instruction + 
                            prompt[instruction_6_end:])
            else:
                # Fallback: if no Instructions section found, append normally
                prompt += f"\n\nEducational Enhancement: {enhancement}"
    
    return prompt, selected_theory

# UPDATED MAIN GENERATE FUNCTION

def generate_prompt(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            prompt = data.get("prompt", "default prompt")
            
            # Get enhancement preference and selected theory
            enhancement_type = data.get("enhancement", "enhanced")
            selected_theory = data.get("theory_enhancement", "")  # NEW: Get selected theory
            
            # Detect request type
            is_theory_request = 'educational theory expert' in prompt.lower()
            is_improvement_request = 'prompt engineering expert' in prompt.lower()
            
        except Exception as e:
            logger.error("JSON decode error (%s)", type(e).__name__)
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        api_key = settings.GEMINI_API_KEY
        
        # Model selection - use gemini-2.5-flash for all requests
        url = GEMINI_URL
        
        # Handle special requests
        if is_theory_request or is_improvement_request:
            if is_improvement_request:
                prompt = """You are a prompt engineering expert. Respond with ONLY valid JSON in this exact format:
{"prompt_improvements": "Your 3 numbered suggestions here..."}

Please provide exactly 3 specific improvements the user could add to their prompt to make it more effective.

Focus on the most impactful improvements like: duration/timing, output format, specificity, differentiation, assessment criteria, etc.

Do not include ```json, markdown, or any other formatting. Just pure JSON.

""" + prompt
            else:
                prompt = """You are an educational psychology expert. Respond with ONLY valid JSON in this exact format:
{"theory_explanation": "Your explanation here", "teaching_tip": "Your tip here"}

Do not include ```json, markdown, or any other formatting. Just pure JSON.

""" + prompt
        else:
            # Apply NEW ENHANCED theoretical enhancement for regular prompts
            if enhancement_type == "enhanced":
                # Extract form data for enhancement
                form_data = {
                    "role": data.get("role", ""),
                    "task": data.get("task", ""),
                    "context": data.get("context", ""),
                    "methodology": data.get("methodology", ""),
                    "subject": data.get("subject", ""),
                    "tone": data.get("tone", "")
                }
                
                # Use NEW enhancement system
                # Use NEW enhancement system
                prompt, _applied_theory = add_selected_theory_enhancement(prompt, form_data, selected_theory)
                

        # [Rest of the API call logic remains the same]
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 2000,
                "stopSequences": []
            }
        }

        
        try:
            response = requests.post(
                url, 
                json=payload, 
                timeout=30,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'AI-Prompt-Generator/1.0',
                    'x-goog-api-key': api_key,
                }
            )
            
            
            if response.status_code != 200:
                logger.error("Gemini API error: status %s", response.status_code)
                return JsonResponse({
                    "error": f"API Error: {response.status_code}",
                    "response": "Sorry, there was an error generating your prompt. Please try again."
                }, status=500)
            
        except requests.exceptions.Timeout:
            logger.error("Gemini API timeout")
            return JsonResponse({
                "error": "Request timeout", 
                "response": "The request took too long. Please try again with a shorter prompt."
            }, status=408)
        except requests.exceptions.RequestException as e:
            logger.error("Network error (%s)", type(e).__name__)
            return JsonResponse({
                "error": "Network error",
                "response": "Network error occurred. Please check your connection and try again."
            }, status=500)

        try:
            result = response.json()
            text_response = result["candidates"][0]["content"]["parts"][0]["text"]
            
            # Handle special requests - ensure JSON format
            if is_theory_request or is_improvement_request:
                try:
                    json.loads(text_response)
                except json.JSONDecodeError:
                    if is_improvement_request:
                        fallback_response = {
                            "prompt_improvements": text_response
                        }
                    else:
                        fallback_response = {
                            "theory_explanation": text_response,
                            "teaching_tip": "Remember to adapt this approach based on your students' individual needs."
                        }
                    text_response = json.dumps(fallback_response)
            
            
        except (KeyError, IndexError) as e:
            logger.error("Response parsing error (%s)", type(e).__name__)
            text_response = "Sorry, no prompt was generated. Please try again."
        except Exception as e:
            logger.error("Unexpected parsing error (%s)", type(e).__name__)
            text_response = "Sorry, an unexpected error occurred."

        return JsonResponse({"response": text_response})
    
    else:
        return JsonResponse({"error": "Only POST requests are allowed."}, status=400)

def help_page(request):
    return render(request, "generator/help.html")
