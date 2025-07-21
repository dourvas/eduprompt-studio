from django.shortcuts import render
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests
import json
import time
import logging

# Setup logging
logger = logging.getLogger(__name__)

def index(request):
    return render(request, "generator/index.html")

def add_theoretical_enhancement(prompt, form_data):
    """Add TPACK, UDL, and Bloom's enhancements to the prompt"""
    enhancements = []
    
    task = form_data.get("task", "").lower()
    context = form_data.get("context", "").lower()
    methodology = form_data.get("methodology", "").lower()
    subject = form_data.get("subject", "").lower()
    
    # BLOOM'S TAXONOMY - Apply to ALL cognitive tasks
    if any(keyword in task for keyword in ["critical thinking", "questions", "analysis"]):
        enhancements.append("incorporating questions that progress from analysis to evaluation and creation levels (Bloom's taxonomy)")
    elif any(keyword in task for keyword in ["practice", "exercises", "activities"]):
        enhancements.append("including activities spanning remember, understand, and apply cognitive levels, progressing to higher-order thinking (Bloom's taxonomy)")
    elif any(keyword in task for keyword in ["assessment", "quiz", "rubric"]):
        enhancements.append("covering multiple cognitive levels from basic recall to higher-order thinking and creation (Bloom's taxonomy)")
    elif any(keyword in task for keyword in ["lesson plan", "introduction"]):
        enhancements.append("structuring content to progress through cognitive levels from foundational to advanced thinking (Bloom's taxonomy)")
    
    # UDL PRINCIPLES - Apply when learner diversity is present
    if any(keyword in context for keyword in ["mixed-ability", "learning difficulties", "special needs", "esl", "efl", "gifted", "diverse"]):
        enhancements.append("providing multiple means of representation, engagement, and expression to accommodate diverse learners (UDL principles)")
    
    # TPACK INTEGRATION - Apply to ALL technology-enhanced tasks
    if any(keyword in task for keyword in ["technology-enhanced", "ai", "digital", "gamified"]):
        enhancements.append("seamlessly integrating technology with pedagogical approaches and content knowledge (TPACK framework)")
    
    # CONSTRUCTIVIST LEARNING - Apply to discovery-based approaches
    if any(keyword in methodology for keyword in ["inquiry", "problem", "discovery", "explore", "create projects"]):
        enhancements.append("supporting active knowledge construction through scaffolded discovery and meaningful learning experiences")
    
    # SOCIAL LEARNING THEORY - Apply to collaborative approaches
    if any(keyword in methodology for keyword in ["collaborative", "group", "peer", "discussion"]):
        enhancements.append("leveraging peer interaction and social learning to enhance understanding through shared knowledge construction")
    
    # AGE-APPROPRIATE SCAFFOLDING - Specific to developmental stages
    if any(keyword in context for keyword in ["preschool", "ages 3-5", "early childhood"]):
        enhancements.append("incorporating hands-on, sensory-based learning experiences appropriate for early childhood development")
    elif any(keyword in context for keyword in ["primary", "elementary", "ages 6-11"]):
        enhancements.append("using concrete-to-abstract learning progression with visual and manipulative supports")
    elif any(keyword in context for keyword in ["middle school", "lower secondary", "ages 12-14"]):
        enhancements.append("bridging concrete and abstract thinking with scaffolded reasoning support")
    elif any(keyword in context for keyword in ["high school", "upper secondary", "ages 15-18"]):
        enhancements.append("supporting abstract reasoning and critical thinking development appropriate for adolescent learners")
    elif any(keyword in context for keyword in ["adult learners", "adult"]):
        enhancements.append("incorporating self-directed learning principles and real-world application for adult learners")
    
    # DIFFERENTIATION - Apply when multiple learning paths needed
    if any(keyword in task for keyword in ["differentiated", "multiple intelligences", "adapt", "extension"]):
        enhancements.append("addressing diverse learning styles, abilities, and interests through varied instructional approaches")
    
    # FORMATIVE ASSESSMENT - Apply to feedback-focused approaches
    if any(keyword in methodology for keyword in ["formative assessment", "feedback", "reflection"]):
        enhancements.append("including embedded assessment opportunities for continuous feedback and learning adjustment")
    
    # SUBJECT-SPECIFIC ENHANCEMENTS
    if "math" in subject:
        enhancements.append("connecting mathematical concepts to real-world applications and building conceptual understanding alongside procedural skills")
    elif any(keyword in subject for keyword in ["science", "biology", "chemistry", "physics"]):
        enhancements.append("emphasizing scientific inquiry, evidence-based reasoning, and connections between theory and practical application")
    elif any(keyword in subject for keyword in ["language", "literature", "writing", "reading"]):
        enhancements.append("developing both language skills and critical literacy through authentic communication and textual analysis")
    elif any(keyword in subject for keyword in ["history", "social studies"]):
        enhancements.append("promoting historical thinking skills and connections between past and present through primary source analysis")
    
    if enhancements:
        prompt += f"\n\nEducational Enhancement Requirements:\nEnsure the output incorporates: {'; '.join(enhancements)}."
    
    return prompt

def generate_prompt(request):
    if request.method == "POST":
        start_time = time.time()
        
        try:
            data = json.loads(request.body)
            prompt = data.get("prompt", "default prompt")
            
            # Get enhancement preference (default to enhanced)
            enhancement_type = data.get("enhancement", "enhanced")
            
            # Detect request type
            is_theory_request = 'educational theory expert' in prompt.lower()
            is_improvement_request = 'prompt engineering expert' in prompt.lower()
            
        except Exception as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        api_key = settings.GEMINI_API_KEY
        
        # Use flash model for faster response
        url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=" + api_key

        # For special requests, modify the prompt directly
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
            # Apply theoretical enhancement for regular prompts if requested
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
                prompt = add_theoretical_enhancement(prompt, form_data)

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

        logger.info(f"📤 Sending request to Gemini at {time.time() - start_time:.2f}s")
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                timeout=30,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'AI-Prompt-Generator/1.0'
                }
            )
            
            api_time = time.time() - start_time
            logger.info(f"📨 Got response from Gemini in {api_time:.2f}s")
            
            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.status_code} - {response.text}")
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
            logger.error(f"Network error: {e}")
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
                    # Test if it's valid JSON
                    json.loads(text_response)
                except json.JSONDecodeError:
                    # Create appropriate fallback based on request type
                    if is_improvement_request:
                        fallback_response = {
                            "prompt_improvements": text_response[:300] + "..." if len(text_response) > 300 else text_response
                        }
                    else:
                        fallback_response = {
                            "theory_explanation": text_response[:300] + "..." if len(text_response) > 300 else text_response,
                            "teaching_tip": "Remember to adapt this approach based on your students' individual needs."
                        }
                    text_response = json.dumps(fallback_response)
            
            total_time = time.time() - start_time
            logger.info(f"✅ Total processing time: {total_time:.2f}s")
            
        except (KeyError, IndexError) as e:
            logger.error(f"Response parsing error: {e}")
            logger.error(f"Full response: {response.text}")
            text_response = "Sorry, no prompt was generated. Please try again."
        except Exception as e:
            logger.error(f"Unexpected parsing error: {e}")
            text_response = "Sorry, an unexpected error occurred."

        return JsonResponse({"response": text_response})
    
    else:
        return JsonResponse({"error": "Only POST requests are allowed."}, status=400)

def help_page(request):
    return render(request, "generator/help.html")