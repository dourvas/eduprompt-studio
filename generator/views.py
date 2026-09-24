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
        
        # Model selection based on request type
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
