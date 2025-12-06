# Updated views.py - Replace the existing functions

from django.shortcuts import render
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db.models import Count, Avg, Q  # Προσθέστε το Avg αν δεν υπάρχει
import requests
import json
import time
import logging
from .models import UserSession, PromptGeneration, PageView, TemplateUsage
from .analytics import PromptAnalyzer
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone

# Setup logging
logger = logging.getLogger(__name__)

def index(request):
    # Ensure session exists
    if not request.session.session_key:
        request.session.create()
   
    session_id = request.session.session_key
    session, created = UserSession.objects.get_or_create(
        session_id=session_id,
        defaults={'referrer': request.META.get('HTTP_REFERER', '')}
    )
   
    if not created:
        session.pages_visited += 1
        session.save()
   
    PageView.objects.create(session=session, path=request.path)
   
    # Pass ENABLE_SURVEYS to template
    context = {
        'settings': settings
    }
   
    return render(request, "generator/index.html", context)  

# NEW ENHANCED THEORY SELECTION SYSTEM

def suggest_optimal_theory(methodology, task, context):
    """
    Intelligent theory suggestion based on pedagogical context
    """
    methodology_lower = methodology.lower()
    task_lower = task.lower()
    context_lower = context.lower()
    
    # Methodology-based suggestions (highest priority)
    if any(keyword in methodology_lower for keyword in ['διερευνητική', 'εξερεύνηση', 'ανακάλυψη', 'πρόβλημα']):
        return 'constructivist'
    elif any(keyword in methodology_lower for keyword in ['συνεργατική', 'ομάδα', 'ομαδική', 'συνεργασία']):
        return 'social_learning'
    elif any(keyword in methodology_lower for keyword in ['τεχνολογία', 'ψηφιακή', 'ai']):
        return 'tpack'
    elif any(keyword in methodology_lower for keyword in ['διαφοροποιημένη', 'προσαρμοστική', 'εξατομικευμένη']):
        return 'udl'
    elif any(keyword in methodology_lower for keyword in ['υποστήριξη', 'καθοδήγηση', 'scaffolding']):
        return 'scaffolding'
    
    # Task-based suggestions (medium priority)
    elif any(keyword in task_lower for keyword in ['κριτική σκέψη', 'ερωτήσεις', 'ανάλυση']):
        return 'blooms'
    elif any(keyword in task_lower for keyword in ['αξιολόγηση', 'κουίζ', 'ρουμπρίκα']):
        return 'blooms'
    elif any(keyword in task_lower for keyword in ['σχέδιο μαθήματος', 'πλάνο μαθήματος', 'αναλυτικό πρόγραμμα']):
        return 'blooms'
    elif any(keyword in task_lower for keyword in ['διαφοροποιημένη', 'πολλαπλές νοημοσύνες']):
        return 'differentiation'
    
    # Context-based suggestions (lower priority)
    elif any(keyword in context_lower for keyword in ['μικτό επίπεδο', 'ειδικές ανάγκες', 'μαθησιακές δυσκολίες']):
        return 'udl'
    
    # Default fallback
    return 'blooms'

def generate_blooms_enhancement(form_data):
    """Generate Bloom's Taxonomy specific enhancement"""
    task = form_data.get("task", "").lower()
    
    if any(keyword in task for keyword in ["κριτική σκέψη", "ερωτήσεις", "ανάλυση"]):
        return "Δόμησε τις ερωτήσεις ώστε να προχωρούν από ανάλυση (ανάλυση εννοιών) σε αξιολόγηση (κρίση ποιότητας/αξίας) σε δημιουργία (παραγωγή νέων ιδεών), ακολουθώντας τα γνωστικά επίπεδα της Ταξινομίας Bloom"
    elif any(keyword in task for keyword in ["άσκηση", "ασκήσεις", "δραστηριότητες"]):
        return "Σχεδίασε δραστηριότητες που καλύπτουν: θυμάμαι (ανάκληση γεγονότων) → κατανοώ (εξήγηση εννοιών) → εφαρμόζω (χρήση γνώσης) → αναλύω (εξέταση σχέσεων), προοδευτικά μέσα από την Ταξινομία Bloom"
    elif any(keyword in task for keyword in ["αξιολόγηση", "κουίζ", "ρουμπρίκα"]):
        return "Συμπεριέλαβε στοιχεία αξιολόγησης που καλύπτουν πολλαπλά γνωστικά επίπεδα: απομνημόνευση βασικών γεγονότων, κατανόηση κύριων εννοιών, εφαρμογή γνώσης σε νέες καταστάσεις, και ανάλυση σύνθετων σεναρίων (Ταξινομία Bloom)"
    elif any(keyword in task for keyword in ["σχέδιο μαθήματος", "πλάνο μαθήματος", "εισαγωγή"]):
        return "Δόμησε το μάθημα ώστε να προχωρά μέσα από γνωστικά επίπεδα από θεμελιώδη γνώση (θυμάμαι/κατανοώ) σε εφαρμογή και σκέψη υψηλότερης τάξης (αναλύω/αξιολογώ/δημιουργώ), ακολουθώντας την Ταξινομία Bloom"
    else:
        return "Ενσωμάτωσε γνωστική πρόοδο από βασική ανάκληση σε δεξιότητες σκέψης υψηλότερης τάξης, ακολουθώντας τα επίπεδα της Ταξινομίας Bloom"

def generate_udl_enhancement(form_data):
    """Generate UDL specific enhancement"""
    context = form_data.get("context", "").lower()
    
    if any(keyword in context for keyword in ["μικτό επίπεδο", "μαθησιακές δυσκολίες", "ειδικές ανάγκες"]):
        return "Παρέχε πολλαπλά μέσα αναπαράστασης (οπτικά, ακουστικά, απτικά), πολλαπλά μέσα αφοσίωσης (επιλογή, συνάφεια, επίπεδα πρόκλησης), και πολλαπλά μέσα έκφρασης (προφορικά, γραπτά, επίδειξη) για να υποστηρίξεις διαφορετικούς μαθητές (αρχές UDL)"
    elif any(keyword in context for keyword in ["δεύτερη γλώσσα", "ξένη γλώσσα"]):
        return "Συμπεριέλαβε οπτικές υποστηρίξεις, απλοποιημένες γλωσσικές επιλογές, και πολλαπλούς τρόπους επίδειξης κατανόησης για να φιλοξενήσεις μαθητές γλώσσας (αρχές UDL)"
    else:
        return "Σχεδίασε με ευελιξία στην παρουσίαση περιεχομένου, στις μεθόδους αφοσίωσης μαθητών, και στις μορφές έκφρασης για να φιλοξενήσεις διαφορετικές μαθησιακές ανάγκες (αρχές UDL)"

def generate_tpack_enhancement(form_data):
    """Generate TPACK specific enhancement - more specific and actionable"""
    task = form_data.get("task", "").lower()
    methodology = form_data.get("methodology", "").lower()
    subject = form_data.get("subject", "").lower()
    
    if any(keyword in task for keyword in ["σχέδιο μαθήματος", "πλάνο μαθήματος", "αναλυτικό πρόγραμμα", "πλήρες πλάνο"]):
        return "Καθόρισε ρητά: (1) ποια εργαλεία/χαρακτηριστικά AI θα χρησιμοποιηθούν, (2) πώς υποστηρίζουν συγκεκριμένους μαθησιακούς στόχους, (3) ποιος παιδαγωγικός ρόλος παίζει η τεχνολογία στη διδασκαλία, και (4) πώς τα ψηφιακά εργαλεία ενισχύουν την κατανόηση περιεχομένου αντί να αντικαθιστούν τη διδασκαλία (πλαίσιο TPACK)"
    
    elif any(keyword in task for keyword in ["αξιολόγηση", "κουίζ", "ρουμπρίκα"]):
        return "Λεπτομέρησε πώς τα εργαλεία αξιολόγησης που ενισχύονται με AI θα μετρήσουν την κατανόηση, καθόρισε την παιδαγωγική αιτιολογία για τη χρήση τεχνολογίας στην αξιολόγηση, και εξήγησε πώς η ψηφιακή αξιολόγηση συνδέεται με τους μαθησιακούς στόχους (πλαίσιο TPACK)"
    
    elif any(keyword in task for keyword in ["άσκηση", "ασκήσεις", "δραστηριότητες"]):
        return "Περίγραψε συγκεκριμένα εργαλεία εξάσκησης που τροφοδοτούνται από AI, εξήγησε πώς η τεχνολογία εξατομικεύει την εξάσκηση, λεπτομέρησε τα παιδαγωγικά οφέλη των ψηφιακών ασκήσεων, και καθόρισε πώς η ανατροφοδότηση AI υποστηρίζει την ανάπτυξη δεξιοτήτων (πλαίσιο TPACK)"
    
    elif any(keyword in methodology for keyword in ["ai", "τεχνολογία", "ψηφιακή"]):
        return "Καθόρισε σαφώς τον παιδαγωγικό ρόλο του AI, προσδιόρισε πώς η τεχνολογία ενισχύει τις μεθόδους διδασκαλίας, εξήγησε τη σύνδεση μεταξύ ψηφιακών εργαλείων και κυριαρχίας περιεχομένου, και δικαιολόγησε τις τεχνολογικές επιλογές με εκπαιδευτική θεωρία (πλαίσιο TPACK)"
    
    else:
        return "Συμπεριέλαβε συγκεκριμένες λεπτομέρειες για το: πώς η τεχνολογία υποστηρίζει τους μαθησιακούς στόχους, ποιος παιδαγωγικός σκοπός εξυπηρετεί το AI, και πώς τα ψηφιακά εργαλεία ενισχύουν αντί να αντικαθιστούν αποτελεσματικές διδακτικές πρακτικές (πλαίσιο TPACK)"

def generate_constructivist_enhancement(form_data):
    """Generate Constructivist Learning enhancement"""
    methodology = form_data.get("methodology", "").lower()
    
    if any(keyword in methodology for keyword in ["διερευνητική", "ανακάλυψη", "εξερεύνηση"]):
        return "Υποστήριξε την ενεργή κατασκευή γνώσης μέσω καθοδηγούμενης ανακάλυψης, ενθαρρύνοντας τους μαθητές να χτίσουν κατανόηση μέσω πρακτικής εξερεύνησης και ουσιαστικών συνδέσεων με προηγούμενη γνώση"
    elif any(keyword in methodology for keyword in ["πρόβλημα", "πραγματικός κόσμος", "πραγματικές καταστάσεις"]):
        return "Διευκόλυνε τη μάθηση μέσω αυθεντικών εμπειριών επίλυσης προβλημάτων όπου οι μαθητές κατασκευάζουν γνώση συνδέοντας νέες πληροφορίες με υπάρχουσα κατανόηση και πραγματικά πλαίσια"
    else:
        return "Ενθάρρυνε την ενεργή κατασκευή γνώσης μέσω πρακτικών εμπειριών, στοχασμού, και δημιουργίας συνδέσεων αντί για παθητική λήψη πληροφοριών"

def generate_social_learning_enhancement(form_data):
    """Generate Social Learning Theory enhancement"""
    methodology = form_data.get("methodology", "").lower()
    
    if any(keyword in methodology for keyword in ["συνεργατική", "ομάδα", "ομαδική", "συνεργασία"]):
        return "Αξιοποίησε την αλληλεπίδραση μεταξύ συνομηλίκων και τις ευκαιρίες συνεργατικής μάθησης όπου οι μαθητές μαθαίνουν μέσω παρατήρησης, συζήτησης, και κοινής κατασκευής γνώσης σε κοινωνικά πλαίσια"
    elif any(keyword in methodology for keyword in ["συζήτηση", "ομαδική εργασία"]):
        return "Δημιούργησε δομημένες ευκαιρίες για κοινωνική μάθηση μέσω μοντελοποίησης από συνομηλίκους, συνεργατικής επίλυσης προβλημάτων, και κοινού στοχασμού για τις μαθησιακές διαδικασίες"
    else:
        return "Ενσωμάτωσε αλληλεπίδραση με συνομηλίκους και ευκαιρίες κοινωνικής μάθησης για να ενισχύσεις την κατανόηση μέσω κοινής κατασκευής γνώσης"

def generate_scaffolding_enhancement(form_data):
    """Generate Scaffolding enhancement"""
    context = form_data.get("context", "").lower()
    task = form_data.get("task", "").lower()
    
    if any(keyword in context for keyword in ["3-5", "νηπιαγωγείο", "προσχολική"]):
        return "Παρέχε εκτενή υποστήριξη με συγκεκριμένα παραδείγματα, πρακτικά υλικά, και βήμα-προς-βήμα καθοδήγηση, μειώνοντας σταδιακά την υποστήριξη καθώς τα παιδιά αναπτύσσουν αυτονομία"
    elif any(keyword in context for keyword in ["6-11", "δημοτικό", "πρωτοβάθμια"]):
        return "Συμπεριέλαβε υποστηρίξεις όπως γραφικούς οργανωτές, επεξεργασμένα παραδείγματα, και καθοδηγούμενη εξάσκηση, με σαφή βήματα προς ανεξάρτητη εφαρμογή"
    elif any(keyword in task for keyword in ["σύνθετη", "προχωρημένη", "δύσκολη"]):
        return "Διαίρεσε σύνθετες εργασίες σε διαχειρίσιμα βήματα με προσωρινές υποστηρίξεις, μοντελοποίηση, και καθοδηγούμενη εξάσκηση πριν αναμένεις ανεξάρτητη επίδοση"
    else:
        return "Παρέχε κατάλληλες υποστηρίξεις που μπορούν να αφαιρεθούν σταδιακά καθώς οι μαθητές αναπτύσσουν ικανότητα και αυτοπεποίθηση"

def generate_differentiation_enhancement(form_data):
    """Generate Differentiated Instruction enhancement"""
    task = form_data.get("task", "").lower()
    
    if any(keyword in task for keyword in ["διαφοροποιημένη", "πολλαπλές νοημοσύνες"]):
        return "Απευθύνσου σε διαφορετικές μαθησιακές προτιμήσεις μέσω ποικίλης παρουσίασης περιεχομένου, επιλογών διαδικασίας, και επιλογών προϊόντος, επιτρέποντας πολλαπλές διαδρομές για επίδειξη κατανόησης"
    elif any(keyword in task for keyword in ["προσαρμοστική", "εξατομικευμένη"]):
        return "Παρέχε ευέλικτες μαθησιακές επιλογές που προσαρμόζονται στις ατομικές ανάγκες, ενδιαφέροντα, και επίπεδα ετοιμότητας των μαθητών μέσω ποικίλων διδακτικών προσεγγίσεων"
    else:
        return "Συμπεριέλαβε στρατηγικές διαφοροποίησης που απευθύνονται σε διαφορετικά μαθησιακά στυλ, ικανότητες, και ενδιαφέροντα μέσω πολλαπλών διδακτικών προσεγγίσεων"
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
            instructions_start = prompt.find("Οδηγίες:")  # ← ΑΛΛΑΓΗ: Ελληνικά
            if instructions_start != -1:
                # Find the end of instruction 6
                instruction_6_end = prompt.find("6. Κράτησέ την επαγγελματική και εστιασμένη στην εκπαιδευτική εργασία")  # ← ΑΛΛΑΓΗ
                if instruction_6_end != -1:
                    instruction_6_end = prompt.find("\n", instruction_6_end) + 1
                    
                    # Insert the enhancement as instruction #7
                    enhancement_instruction = f"7. ΣΗΜΑΝΤΙΚΟ: {enhancement}\n"  # ← ΑΛΛΑΓΗ: Ελληνικά
                    
                    prompt = (prompt[:instruction_6_end] + 
                            enhancement_instruction + 
                            prompt[instruction_6_end:])
            else:
                # Fallback: if no Instructions section found, append normally
                prompt += f"\n\nΕκπαιδευτική Ενίσχυση: {enhancement}"  # ← ΑΛΛΑΓΗ: Ελληνικά
    
    return prompt, selected_theory

# UPDATED MAIN GENERATE FUNCTION

def generate_prompt(request):
    if request.method == "POST":
        start_time = time.time()
        
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
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        api_key = settings.GEMINI_API_KEY
        
        # Model selection based on request type
        if is_improvement_request:
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key=" + api_key
        else:
            url = "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=" + api_key
        
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
                #print(f"DEBUG: selected_theory = {selected_theory}")
                #print(f"DEBUG: enhancement_type = {enhancement_type}")
                prompt, applied_theory = add_selected_theory_enhancement(prompt, form_data, selected_theory)
                #print(f"DEBUG: applied_theory = {applied_theory}")
                #print(f"DEBUG: enhanced prompt length = {len(prompt)}")
                
                # Log which theory was applied for research purposes
                logger.info(f"Applied theory: {applied_theory} (user selected: {selected_theory})")

        # [Rest of the API call logic remains the same]
        #print(f"DEBUG: Final prompt being sent to Gemini:")
        #print(f"DEBUG: {prompt}")
        #print("="*80)
        
        # Detect large prompts (improvements applied)
        is_large_prompt = len(prompt) > 3000 or is_improvement_request
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
                "maxOutputTokens": 8192 if is_large_prompt else 4096,
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
            logger.info(f"📄 Response status: {response.status_code}")
            logger.info(f"📏 Response length: {len(response.text)} chars")
            
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
            
            total_time = time.time() - start_time
            logger.info(f"✅ Total processing time: {total_time:.2f}s")
            
        except (KeyError, IndexError) as e:
            logger.error(f"Response parsing error: {e}")
            logger.error(f"Full response: {response.text}")
            text_response = "Sorry, no prompt was generated. Please try again."
        except Exception as e:
            logger.error(f"Unexpected parsing error: {e}")
            text_response = "Sorry, an unexpected error occurred."

        # Enhanced analytics tracking
        session_id = request.session.session_key or request.session.create()
        session, created = UserSession.objects.get_or_create(session_id=session_id)
        
        # Update template usage if template was used
        template_used = data.get("template", "")
        if template_used:
            template_obj, created = TemplateUsage.objects.get_or_create(template_name=template_used)
            template_obj.usage_count += 1
            template_obj.save()
        
        # Auto-analysis of educational data
        subject_category = PromptAnalyzer.enhanced_subject_classification(
            data.get("subject", ""),
            data.get("task", ""),
            data.get("role", ""), 
            text_response
        )
        age_group_category = PromptAnalyzer.categorize_age_group(data.get("context", ""))
        methodology_category = PromptAnalyzer.categorize_methodology(data.get("methodology", ""))
        complexity_level = PromptAnalyzer.assess_complexity(
            text_response, 
            data.get("task", ""), 
            data.get("methodology", "")
        )
        
        # Content analysis
        content_analysis = PromptAnalyzer.analyze_content(text_response)
        
        # Determine the final applied theory for analytics
        if enhancement_type == "enhanced" and not (is_theory_request or is_improvement_request):
            final_applied_theory = applied_theory
            theory_was_auto_suggested = not bool(selected_theory)
        else:
            final_applied_theory = None
            theory_was_auto_suggested = False
        
        # Create comprehensive prompt generation record with NEW THEORY TRACKING
        PromptGeneration.objects.create(
            session=session,
            template_used=template_used,
            role=data.get("role", ""),
            subject=data.get("subject", ""),
            task=data.get("task", ""),
            context=data.get("context", ""),
            methodology=data.get("methodology", ""),
            tone=data.get("tone", ""),
            enhancement_mode=enhancement_type,
            success=True,
            response_time_seconds=time.time() - start_time,
            generated_prompt=text_response,
            
            # Auto-analyzed categories
            subject_category=subject_category,
            age_group_category=age_group_category,
            methodology_category=methodology_category,
            complexity_level=complexity_level,
            
            # NEW: Theory selection tracking (will need to add these fields to model)
            selected_theory=final_applied_theory,
            theory_auto_suggested=theory_was_auto_suggested,
            
            # Content analysis results
            **content_analysis
        )
        
        return JsonResponse({"response": text_response})
    
    else:
        return JsonResponse({"error": "Only POST requests are allowed."}, status=400)

def help_page(request):
    return render(request, "generator/help.html")

@csrf_exempt
def track_copy(request):
    if request.method == "POST":
        session_id = request.session.session_key
        if session_id:
            # Find the latest prompt generation for this session
            latest_prompt = PromptGeneration.objects.filter(
                session__session_id=session_id
            ).order_by('-timestamp').first()
            
            if latest_prompt:
                latest_prompt.copied_to_clipboard = True
                latest_prompt.save()
        
        return JsonResponse({"status": "success"})
    return JsonResponse({"error": "Only POST allowed"}, status=400)

@csrf_exempt
@require_http_methods(["POST"])
def onboarding_data_collection(request):
    """
    Collect onboarding demographics data for research purposes
    
    Expected JSON payload:
    {
        "ai_experience": "none|basic|intermediate|advanced",
        "teaching_years": "0-5|6-15|16-25|25+",
        "timestamp": "ISO timestamp"
    }
    """
    if not settings.ENABLE_SURVEYS:
        return JsonResponse({
            'status': 'disabled',
            'message': 'Surveys are currently disabled'
        })
    try:
        # Parse JSON data
        data = json.loads(request.body)
        
        # Validate required fields
        ai_experience = data.get('ai_experience')
        teaching_years = data.get('teaching_years')
        
        if not ai_experience or not teaching_years:
            return JsonResponse({
                'error': 'Missing required fields',
                'required': ['ai_experience', 'teaching_years']
            }, status=400)
        
        # Server-side validation
        valid_ai_levels = ['none', 'basic', 'intermediate', 'advanced']
        valid_teaching_years = ['0-5', '6-15', '16-25', '25+']
        
        if ai_experience not in valid_ai_levels:
            return JsonResponse({
                'error': 'Invalid ai_experience value',
                'valid_values': valid_ai_levels
            }, status=400)
        
        if teaching_years not in valid_teaching_years:
            return JsonResponse({
                'error': 'Invalid teaching_years value',
                'valid_values': valid_teaching_years
            }, status=400)
        
        # Get or create session
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        try:
            session = UserSession.objects.get(session_id=session_id)
        except UserSession.DoesNotExist:
            # Create new session if doesn't exist
            session = UserSession.objects.create(
                session_id=session_id,
                referrer=request.META.get('HTTP_REFERER', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        
        # Update demographics data
        session.ai_experience = ai_experience
        session.teaching_years = teaching_years
        session.onboarding_completed = True
        session.onboarding_completion_time = timezone.now()
        session.research_consent = True  # Implied by participation
        
        # Save with validation
        try:
            session.save()
            
            # Log for research analytics
            logger.info(f"Onboarding completed - Session: {session_id[:8]}, "
                       f"AI: {ai_experience}, Teaching: {teaching_years}")
            
            # Return success with user profile
            return JsonResponse({
                'status': 'success',
                'message': 'Demographics data saved successfully',
                'user_profile': {
                    'ai_experience': ai_experience,
                    'teaching_years': teaching_years,
                    'profile_summary': session.user_profile_summary,
                    'research_category': session.research_participant_type
                }
            })
            
        except Exception as validation_error:
            logger.error(f"Onboarding validation error: {validation_error}")
            return JsonResponse({
                'error': 'Data validation failed',
                'details': str(validation_error)
            }, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON format'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Onboarding endpoint error: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': 'Please try again later'
        }, status=500)

@require_http_methods(["GET"])
def onboarding_stats(request):
    """
    Get onboarding completion statistics (for admin/research)
    """
    try:
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        # Basic stats
        total_sessions = UserSession.objects.count()
        completed_onboarding = UserSession.objects.filter(onboarding_completed=True).count()
        skipped_onboarding = UserSession.objects.filter(onboarding_skipped=True).count()
        
        # Demographics breakdown
        ai_experience_stats = UserSession.objects.filter(
            onboarding_completed=True
        ).values('ai_experience').annotate(count=Count('ai_experience'))
        
        teaching_years_stats = UserSession.objects.filter(
            onboarding_completed=True
        ).values('teaching_years').annotate(count=Count('teaching_years'))
        
        # Recent completions (last 7 days)
        week_ago = timezone.now() - timedelta(days=7)
        recent_completions = UserSession.objects.filter(
            onboarding_completion_time__gte=week_ago
        ).count()
        
        return JsonResponse({
            'total_sessions': total_sessions,
            'onboarding_stats': {
                'completed': completed_onboarding,
                'skipped': skipped_onboarding,
                'completion_rate': round((completed_onboarding / total_sessions * 100), 1) if total_sessions > 0 else 0,
                'recent_completions_7_days': recent_completions
            },
            'demographics_breakdown': {
                'ai_experience': list(ai_experience_stats),
                'teaching_years': list(teaching_years_stats)
            }
        })
    
    except Exception as e:
        logger.error(f"Onboarding stats error: {e}")
        return JsonResponse({
            'error': 'Unable to fetch statistics'
        }, status=500)

# Optional: Helper function to check if user needs onboarding
def user_needs_onboarding(request):
    """
    Check if current user needs to complete onboarding
    Can be used in templates or other views
    """
    session_id = request.session.session_key
    if not session_id:
        return True
    
    try:
        session = UserSession.objects.get(session_id=session_id)
        return not session.onboarding_completed
    except UserSession.DoesNotExist:
        return True

# You can also add this as a context processor if needed:
def onboarding_context(request):
    """
    Add onboarding status to template context
    Add to TEMPLATES['OPTIONS']['context_processors'] in settings.py
    """
    return {
        'needs_onboarding': user_needs_onboarding(request)
    }

# Optional: Statistics endpoint for training needs data
@require_http_methods(["GET"])
def training_needs_stats(request):
    """
    Get training needs statistics (for admin/research)
    """
    try:
        from django.db.models import Count
        from collections import Counter
        
        # Basic stats
        total_sessions = UserSession.objects.count()
        completed_training = UserSession.objects.filter(training_needs_completed=True).count()
        
        # Interest distribution
        all_interests = []
        for session in UserSession.objects.filter(training_needs_completed=True):
            all_interests.extend(session.training_interests)
        
        interest_counts = Counter(all_interests)
        
        # Priority analysis
        priority_1_areas = []
        priority_2_areas = []
        priority_3_areas = []
        
        for session in UserSession.objects.filter(training_needs_completed=True):
            for area, priority in session.training_priorities.items():
                if priority == 1:
                    priority_1_areas.append(area)
                elif priority == 2:
                    priority_2_areas.append(area)
                elif priority == 3:
                    priority_3_areas.append(area)
        
        # Research participation stats
        email_provided = UserSession.objects.filter(
            training_needs_completed=True,
            follow_up_email__isnull=False
        ).exclude(follow_up_email='').count()
        
        interview_interest = UserSession.objects.filter(
            training_needs_completed=True,
            research_interview_interest=True
        ).count()
        
        return JsonResponse({
            'total_sessions': total_sessions,
            'training_needs_stats': {
                'completed': completed_training,
                'completion_rate': round((completed_training / total_sessions * 100), 1) if total_sessions > 0 else 0,
            },
            'interest_distribution': dict(interest_counts.most_common()),
            'priority_analysis': {
                'first_priority': Counter(priority_1_areas).most_common(),
                'second_priority': Counter(priority_2_areas).most_common(),
                'third_priority': Counter(priority_3_areas).most_common(),
            },
            'research_participation': {
                'email_provided': email_provided,
                'interview_interest': interview_interest,
                'email_rate': round((email_provided / completed_training * 100), 1) if completed_training > 0 else 0
            }
        })
    
    except Exception as e:
        logger.error(f"Training needs stats error: {e}")
        return JsonResponse({
            'error': 'Unable to fetch statistics'
        }, status=500)


# Helper function to check if user needs training survey (optional utility)
def user_needs_training_survey(request):
    """
    Check if current user needs to see training needs survey
    """
    session_id = request.session.session_key
    if not session_id:
        return False
    
    try:
        session = UserSession.objects.get(session_id=session_id)
        return (session.onboarding_completed and 
                not session.training_needs_completed and 
                not session.training_needs_shown)
    except UserSession.DoesNotExist:
        return False

@csrf_exempt
@require_http_methods(["POST"])
def training_needs_data_collection(request):
    """
    Collect training needs survey data (Phase 2)
    
    Expected JSON payload:
    {
        "training_interests": ["area1", "area2", ...],
        "training_priorities": {"area1": 1, "area2": 2, "area3": 3},
        "training_other_needs": "text or null",
        "follow_up_email": "email or null",
        "research_interview_interest": true/false
    }
    """
    if not settings.ENABLE_SURVEYS:
        return JsonResponse({
            'status': 'disabled',
            'message': 'Surveys are currently disabled'
        })
    try:
        # Parse JSON data
        data = json.loads(request.body)
        
        # Validate required fields
        training_interests = data.get('training_interests', [])
        training_priorities = data.get('training_priorities', {})
        
        if not training_interests:
            return JsonResponse({
                'error': 'At least one training interest must be selected'
            }, status=400)
        
        # Get session
        session_id = request.session.session_key
        if not session_id:
            return JsonResponse({
                'error': 'No valid session found'
            }, status=400)
        
        try:
            session = UserSession.objects.get(session_id=session_id)
        except UserSession.DoesNotExist:
            return JsonResponse({
                'error': 'Session not found'
            }, status=404)
        
        # Update training needs data
        session.training_interests = training_interests
        session.training_priorities = training_priorities
        session.training_other_needs = data.get('training_other_needs')
        session.follow_up_email = data.get('follow_up_email')
        session.research_interview_interest = data.get('research_interview_interest', False)
        session.training_needs_completed = True
        session.training_needs_completion_time = timezone.now()
        
        # Save
        session.save()
        
        # Log for research analytics
        logger.info(f"Training needs completed - Session: {session_id[:8]}, "
                   f"Interests: {len(training_interests)}, Priorities: {len(training_priorities)}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Training needs data saved successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON format'
        }, status=400)
    
    except Exception as e:
        logger.error(f"Training needs endpoint error: {e}")
        return JsonResponse({
            'error': 'Internal server error',
            'message': 'Please try again later'
        }, status=500)
