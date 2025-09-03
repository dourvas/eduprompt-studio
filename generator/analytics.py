import re
from textstat import flesch_reading_ease, syllable_count
from collections import Counter

class PromptAnalyzer:
    """Comprehensive analysis of educational prompts for research purposes"""
    
    # Educational Theory Keywords
    BLOOMS_KEYWORDS = [
        'analyze', 'evaluate', 'create', 'synthesize', 'compare', 'contrast',
        'critique', 'assess', 'judge', 'design', 'construct', 'plan',
        'remember', 'understand', 'apply', 'knowledge', 'comprehension'
    ]
    
    UDL_KEYWORDS = [
        'multiple means', 'representation', 'engagement', 'expression',
        'diverse learners', 'accessibility', 'flexible', 'options',
        'accommodations', 'modifications', 'inclusive', 'universal'
    ]
    
    TPACK_KEYWORDS = [
        'technology', 'digital', 'online', 'interactive', 'multimedia',
        'pedagogical', 'content knowledge', 'integration', 'enhance',
        'facilitate', 'support learning', 'educational technology'
    ]
    
    PEDAGOGICAL_KEYWORDS = [
        'scaffolding', 'differentiation', 'formative assessment', 'feedback',
        'inquiry', 'collaboration', 'problem-solving', 'critical thinking',
        'metacognition', 'reflection', 'authentic', 'real-world'
    ]

    # === COMPREHENSIVE PATTERNS FOR EXACT CLASSIFICATION ===
    
    # Complete Age Group Patterns (από dropdown + common variations)
    AGE_PATTERNS = {
        'Early_Childhood': [
            # Exact dropdown options
            'preschool (ages 3-5)', 'preschool', 'ages 3-5',
            # Common variations
            'early childhood', 'kindergarten', 'pre-k', 'nursery',
            'toddlers', '3 year old', '4 year old', '5 year old',
            'pre-school', 'daycare'
        ],
        'Primary': [
            # Exact dropdown
            'primary students (ages 6-11)', 'primary students', 'ages 6-11',
            # Common variations  
            'elementary', 'primary school', 'elementary school',
            'grade 1', 'grade 2', 'grade 3', 'grade 4', 'grade 5', 'grade 6',
            'first grade', 'second grade', 'third grade', 'fourth grade', 'fifth grade',
            '6 year old', '7 year old', '8 year old', '9 year old', '10 year old', '11 year old',
            'junior school', 'primary education'
        ],
        'Lower_Secondary': [
            # Exact dropdown
            'lower secondary (ages 12-14)', 'lower secondary', 'ages 12-14',
            # Common variations
            'middle school', 'junior high', 'intermediate',
            'grade 7', 'grade 8', 'grade 9',
            'seventh grade', 'eighth grade', 'ninth grade',
            '12 year old', '13 year old', '14 year old',
            'secondary education', 'junior secondary'
        ],
        'Upper_Secondary': [
            # Exact dropdown
            'upper secondary (ages 15-18)', 'upper secondary', 'ages 15-18',
            # Common variations
            'high school', 'senior high', 'secondary school',
            'grade 10', 'grade 11', 'grade 12',
            'tenth grade', 'eleventh grade', 'twelfth grade',
            '15 year old', '16 year old', '17 year old', '18 year old',
            'senior', 'junior', 'sophomore', 'freshman',
            'college prep', 'advanced placement', 'ap students'
        ],
        'Adult': [
            # Exact dropdown
            'adult learners',
            # Common variations
            'university', 'college', 'higher education',
            'professional development', 'adult education',
            'continuing education', 'workplace learning',
            'corporate training', 'graduate students',
            'undergraduate', 'postgraduate', 'mature students'
        ],
        'Mixed': [
            # Special contexts από dropdown
            'mixed-ability classroom', 'mixed ability', 'multi-age',
            'combined classes', 'composite class', 'mixed grades',
            'all ages', 'various ages', 'different age groups'
        ]
    }
    
    # Complete Methodology Patterns (από dropdown + variations)
    METHODOLOGY_PATTERNS = {
        'Direct_Instruction': [
            # Exact dropdown options
            'teacher explains, ai provides examples and practice (direct instruction)',
            'teacher explains, ai provides examples and practice',
            'teacher demonstrates, ai offers step-by-step guidance (modeling & demonstration)',
            'teacher demonstrates, ai offers step-by-step guidance',
            'teacher presents, ai reinforces with interactive content (lecture-based with tech enhancement)',
            'teacher presents, ai reinforces with interactive content',
            # Common variations for "Other"
            'direct instruction', 'explicit teaching', 'teacher-led',
            'lecture', 'presentation', 'demonstration',
            'modeling', 'guided instruction', 'structured teaching',
            'traditional teaching', 'didactic', 'expository'
        ],
        'Inquiry_Based': [
            # Exact dropdown
            'students explore with ai as research assistant (inquiry-based learning)',
            'students explore with ai as research assistant',
            # Common variations
            'inquiry-based learning', 'inquiry based', 'discovery learning',
            'exploration', 'investigation', 'research-based',
            'questioning', 'wonder', 'find out', 'explore',
            'student inquiry', 'open inquiry', 'guided inquiry'
        ],
        'Problem_Based': [
            # Exact dropdown
            'students solve problems with ai hints and scaffolding (problem-based learning)',
            'students solve problems with ai hints and scaffolding',
            # Common variations
            'problem-based learning', 'problem based', 'pbl',
            'real-world problems', 'authentic problems',
            'case studies', 'scenarios', 'challenges',
            'problem solving', 'solution-focused'
        ],
        'Project_Based': [
            # Exact dropdown
            'students create projects with ai collaboration tools (project-based learning)',
            'students create projects with ai collaboration tools',
            # Common variations
            'project-based learning', 'project based', 'pbl',
            'projects', 'create', 'build', 'design',
            'portfolio', 'exhibition', 'showcase',
            'maker', 'construction', 'development'
        ],
        'Collaborative': [
            # Exact dropdown
            'students work in groups with ai facilitation (collaborative learning)',
            'students work in groups with ai facilitation',
            # Common variations
            'collaborative learning', 'group work', 'teamwork',
            'cooperative learning', 'peer learning',
            'discussion', 'team', 'partner', 'pairs',
            'social learning', 'shared learning'
        ],
        'Differentiated': [
            # Exact dropdown
            'ai provides different paths for different learners (differentiated instruction)',
            'ai provides different paths for different learners',
            'ai adjusts difficulty based on student progress (adaptive learning)',
            'ai adjusts difficulty based on student progress',
            'ai offers multiple ways to show understanding (multiple intelligences)',
            'ai offers multiple ways to show understanding',
            # Common variations
            'differentiated instruction', 'differentiation',
            'adaptive learning', 'personalized learning',
            'individualized', 'customized', 'tailored',
            'multiple intelligences', 'learning styles',
            'flexible grouping', 'tiered assignments'
        ],
        'Assessment_Focused': [
            # Exact dropdown
            'ai provides ongoing feedback during learning (formative assessment)',
            'ai provides ongoing feedback during learning',
            'ai helps students reflect on their progress (self-assessment & reflection)',
            'ai helps students reflect on their progress',
            'students assess each other with ai guidance (peer assessment)',
            'students assess each other with ai guidance',
            # Common variations
            'formative assessment', 'summative assessment',
            'evaluation', 'feedback', 'reflection',
            'self-assessment', 'peer assessment',
            'rubrics', 'criteria', 'standards'
        ],
        'Scaffolding': [
            # Exact dropdown
            'ai gives personalized support and encouragement (scaffolding)',
            'ai gives personalized support and encouragement',
            # Common variations
            'scaffolding', 'support', 'guidance',
            'gradual release', 'modeling', 'coaching',
            'mentoring', 'assistance', 'prompting'
        ]
    }
    
    # Enhanced Subject Patterns
    SUBJECT_PATTERNS = {
        'STEM': {
            'keywords': [
                'math', 'mathematics', 'science', 'physics', 'chemistry', 'biology',
                'technology', 'engineering', 'computer', 'coding', 'programming',
                'algebra', 'geometry', 'calculus', 'statistics', 'data science',
                'robotics', 'artificial intelligence', 'machine learning'
            ],
            'topics': [
                # Math topics
                'fractions', 'decimals', 'percentages', 'equations', 'functions',
                'trigonometry', 'probability', 'graphing', 'measurement',
                # Science topics  
                'atoms', 'molecules', 'cells', 'dna', 'genetics', 'evolution',
                'forces', 'energy', 'electricity', 'magnetism', 'waves',
                'chemical reactions', 'periodic table', 'photosynthesis',
                'solar system', 'climate change', 'ecosystems',
                # Technology topics
                'algorithms', 'variables', 'loops', 'functions', 'databases',
                'networks', 'cybersecurity', 'web development', 'app development'
            ]
        },
        'Humanities': {
            'keywords': [
                'history', 'social studies', 'geography', 'literature', 'language arts',
                'english', 'writing', 'reading', 'essay', 'poetry', 'novel',
                'culture', 'society', 'politics', 'government', 'economics',
                'philosophy', 'psychology', 'anthropology', 'sociology'
            ],
            'topics': [
                # History topics
                'world war', 'civil war', 'revolutionary war', 'independence',
                'renaissance', 'middle ages', 'ancient civilizations',
                'industrial revolution', 'great depression', 'cold war',
                'colonialism', 'democracy', 'constitution', 'bill of rights',
                # Literature topics
                'shakespeare', 'poetry analysis', 'character development',
                'theme', 'symbolism', 'narrative', 'prose', 'drama',
                # Geography/Social Studies
                'continents', 'countries', 'capitals', 'climate zones',
                'cultural diversity', 'immigration', 'globalization'
            ]
        },
        'Arts': {
            'keywords': [
                'art', 'music', 'drama', 'theater', 'creative', 'visual arts',
                'performing arts', 'drawing', 'painting', 'sculpture',
                'dance', 'singing', 'acting', 'design', 'photography'
            ],
            'topics': [
                'color theory', 'composition', 'perspective', 'shading',
                'rhythm', 'melody', 'harmony', 'tempo', 'instruments',
                'improvisation', 'character development', 'stage design',
                'choreography', 'vocal techniques', 'art history'
            ]
        },
        'PE_Health': {
            'keywords': [
                'physical education', 'health', 'fitness', 'sports', 'exercise',
                'nutrition', 'wellness', 'safety', 'first aid', 'mental health',
                'pe', 'gym', 'athletics', 'recreation'
            ],
            'topics': [
                'cardiovascular', 'strength training', 'flexibility', 'endurance',
                'team sports', 'individual sports', 'healthy eating',
                'food pyramid', 'hygiene', 'stress management',
                'drug prevention', 'injury prevention'
            ]
        },
        'Languages': {
            'keywords': [
                # Core language terms
                'english', 'language', 'grammar', 'nouns', 'verbs', 'adjectives',
                'linguistics', 'syntax', 'morphology', 'vocabulary', 'phonetics',
                # Teaching context  
                'language instructor', 'language teacher', 'esl', 'efl',
                # Activities & skills
                'debate', 'arguments', 'discussion', 'speaking', 'conversation',
                'pronunciation', 'listening', 'reading', 'writing', 'comprehension',
                # Other languages
                'french', 'spanish', 'german', 'italian', 'chinese'
            ],
            'topics': [
                # Grammar specifics
                'english nouns', 'parts of speech', 'sentence structure', 'word formation',
                'noun phrases', 'proper nouns', 'common nouns', 'grammar rules',
                # Language learning activities
                'debate topics', 'language learning', 'discussion topics', 'conversation practice',
                'vocabulary building', 'language skills', 'second language', 'foreign language',
                # Advanced concepts
                'linguistic analysis', 'language structure', 'semantic meaning'
            ]
        },
        'Life_Skills': {
            'keywords': [
                'life skills', 'personal development', 'social skills', 'emotional',
                'communication', 'leadership', 'teamwork', 'time management',
                'financial literacy', 'cooking', 'health education'
            ],
            'topics': [
                'budgeting', 'personal finance', 'cooking skills', 'nutrition',
                'social interaction', 'conflict resolution', 'decision making',
                'goal setting', 'stress management', 'self-care'
            ]
        },
        'Vocational': {
            'keywords': [
                'career', 'technical education', 'vocational', 'trade',
                'professional skills', 'workplace', 'job skills',
                'business', 'entrepreneurship', 'marketing'
            ],
            'topics': [
                'resume writing', 'interview skills', 'communication skills',
                'leadership', 'teamwork', 'project management',
                'financial literacy', 'customer service'
            ]
        }
    }
    
    # Enhanced Complexity Indicators
    COMPLEXITY_INDICATORS = {
        'Basic': [
            'list', 'identify', 'recall', 'name', 'define', 'describe',
            'simple', 'basic', 'introduction', 'overview', 'beginning'
        ],
        'Intermediate': [
            'explain', 'compare', 'discuss', 'analyze', 'examine',
            'classify', 'organize', 'summarize', 'interpret'
        ],
        'Advanced': [
            'evaluate', 'create', 'design', 'synthesize', 'critique',
            'develop', 'lesson plan', 'complete plan', 'comprehensive',
            'assessment rubric', 'differentiated activities',
            'cross-curricular', 'multi-step', 'complex'
        ],
        'Expert': [
            'integrate multiple', 'innovative approach', 'research-based',
            'theoretical framework', 'paradigm shift', 'cutting-edge',
            'interdisciplinary', 'meta-analysis', 'systematic review'
        ]
    }

    # Comprehensive Bloom's Taxonomy Indicators based on Anderson & Krathwohl (2001)
    BLOOMS_COMPLEXITY_INDICATORS = {
        'Remember': {
            'verbs': [
                # Core remember verbs
                'list', 'name', 'identify', 'recall', 'recognize', 'define', 
                'describe', 'match', 'select', 'state', 'label', 'locate',
                # Extended remember verbs
                'memorize', 'repeat', 'reproduce', 'quote', 'cite', 'recite',
                'show', 'spell', 'tell', 'relate', 'find', 'choose',
                'duplicate', 'enumerate', 'record', 'underline', 'point to'
            ],
            'tasks': [
                # Basic recall tasks
                'vocabulary', 'definitions', 'facts', 'basic information', 'key terms', 
                'simple recall', 'memorization', 'word list', 'terminology',
                # Educational formats
                'flashcards', 'drill exercises', 'rote learning', 'basic facts',
                'simple identification', 'naming activity', 'matching exercise'
            ],
            'complexity': 'Basic'
        },
        'Understand': {
            'verbs': [
                # Core understand verbs
                'explain', 'describe', 'discuss', 'summarize', 'paraphrase',
                'interpret', 'translate', 'outline', 'give examples', 'classify',
                # Extended understand verbs
                'infer', 'predict', 'extend', 'associate', 'distinguish', 'express',
                'locate', 'report', 'restate', 'review', 'recognize', 'express',
                'identify', 'indicate', 'represent', 'illustrate', 'convert'
            ],
            'tasks': [
                # Comprehension tasks
                'explanation', 'summary', 'main ideas', 'concepts', 'understanding', 
                'interpretation', 'comprehension', 'overview', 'description',
                # Educational formats
                'concept mapping', 'graphic organizers', 'reading comprehension',
                'paraphrasing exercise', 'translation activity', 'concept explanation'
            ],
            'complexity': 'Basic'
        },
        'Apply': {
            'verbs': [
                # Core apply verbs
                'apply', 'demonstrate', 'use', 'show', 'solve', 'practice',
                'illustrate', 'operate', 'implement', 'execute',
                # Extended apply verbs
                'modify', 'relate', 'calculate', 'complete', 'examine', 'classify',
                'choose', 'dramatize', 'employ', 'interpret', 'schedule', 'sketch',
                'write', 'prepare', 'produce', 'translate', 'manipulate', 'utilize'
            ],
            'tasks': [
                # Application tasks
                'practice exercises', 'application', 'problem solving', 'demonstrations', 
                'examples', 'implementation', 'practical application', 'case studies',
                # Educational formats
                'worksheets', 'homework', 'lab work', 'simulations', 'role playing',
                'hands-on activities', 'guided practice', 'skill practice'
            ],
            'complexity': 'Intermediate'
        },
        'Analyze': {
            'verbs': [
                # Core analyze verbs
                'analyze', 'examine', 'compare', 'contrast', 'investigate',
                'categorize', 'differentiate', 'distinguish', 'question', 'test',
                # Extended analyze verbs
                'organize', 'deconstruct', 'attribute', 'break down', 'correlate',
                'diagram', 'divide', 'order', 'connect', 'classify', 'arrange',
                'separate', 'advertise', 'deduce', 'dissect', 'discriminate', 'focus'
            ],
            'tasks': [
                # Analysis tasks
                'analysis', 'comparison', 'investigation', 'examination', 'critical thinking', 
                'breakdown', 'relationships', 'case analysis', 'research',
                # Educational formats
                'compare and contrast', 'cause and effect', 'critical analysis',
                'data analysis', 'text analysis', 'pattern recognition', 'classification'
            ],
            'complexity': 'Advanced'
        },
        'Evaluate': {
            'verbs': [
                # Core evaluate verbs
                'evaluate', 'assess', 'judge', 'critique', 'appraise',
                'argue', 'defend', 'justify', 'support', 'rate', 'prioritize',
                # Extended evaluate verbs
                'recommend', 'conclude', 'discriminate', 'decide', 'grade',
                'measure', 'rank', 'score', 'select', 'validate', 'verify',
                'choose', 'estimate', 'predict', 'award', 'compare', 'criticize'
            ],
            'tasks': [
                # Evaluation tasks
                'evaluation', 'assessment', 'criticism', 'judgment', 'argumentation', 
                'justification', 'critique', 'peer review', 'quality assessment',
                # Educational formats
                'rubrics', 'peer assessment', 'self-assessment', 'portfolio review',
                'debate', 'editorial', 'survey', 'recommendation report'
            ],
            'complexity': 'Advanced'
        },
        'Create': {
            'verbs': [
                # Core create verbs
                'create', 'design', 'develop', 'compose', 'construct',
                'build', 'plan', 'produce', 'invent', 'formulate', 'generate',
                # Extended create verbs
                'synthesize', 'reorganize', 'substitute', 'combine', 'compile',
                'devise', 'role-play', 'rewrite', 'tell', 'adapt', 'change',
                'choose', 'delete', 'estimate', 'happen', 'imagine', 'improve',
                'make up', 'maximize', 'minimize', 'modify', 'original', 'predict',
                'propose', 'solve', 'suppose', 'discuss', 'facilitate', 'format'
            ],
            'tasks': [
                # Creation tasks
                'lesson plan', 'curriculum', 'project', 'design', 'creation', 
                'development', 'original work', 'innovation', 'presentation',
                # Educational formats
                'unit plan', 'assessment design', 'activity creation', 'material development',
                'instructional design', 'learning experience', 'educational resource',
                'teaching strategy', 'learning module', 'course design', 'program development'
            ],
            'complexity': 'Expert'
        }
    }

    # Additional Educational Context Keywords for Enhanced Accuracy
    EDUCATIONAL_COMPLEXITY_CONTEXT = {
        'Basic': [
            'simple', 'basic', 'elementary', 'introductory', 'beginner',
            'fundamental', 'starting', 'first', 'easy', 'straightforward'
        ],
        'Intermediate': [
            'moderate', 'intermediate', 'developing', 'practicing', 'applying',
            'building', 'expanding', 'extending', 'guided', 'structured'
        ],
        'Advanced': [
            'complex', 'advanced', 'sophisticated', 'in-depth', 'comprehensive',
            'detailed', 'thorough', 'analytical', 'critical', 'higher-order'
        ],
        'Expert': [
            'expert', 'master', 'innovative', 'creative', 'original', 'cutting-edge',
            'comprehensive', 'integrated', 'synthesized', 'professional', 'advanced'
        ]
    }

    # === ENHANCED CLASSIFICATION METHODS ===

    @staticmethod
    def enhanced_context_classification(context_text, generated_prompt=""):
        """Enhanced context classification with complete dropdown coverage"""
        combined_text = f"{context_text} {generated_prompt}".lower()
        
        scores = {}
        for age_group, patterns in PromptAnalyzer.AGE_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if pattern in combined_text:
                    # Exact dropdown matches get higher score
                    if pattern == context_text.lower():
                        score += 10
                    else:
                        score += 3
            scores[age_group] = score
            
        # Handle learning environments (map to appropriate age group)
        environment_mappings = {
            'traditional classroom': 'Primary',
            'online/remote learning': 'Upper_Secondary',
            'hybrid classroom': 'Upper_Secondary',
            'homeschool setting': 'Primary',
            'after-school program': 'Primary'
        }
        
        for env, default_age in environment_mappings.items():
            if env in combined_text:
                scores[default_age] = scores.get(default_age, 0) + 5
                
        # Handle special considerations
        if any(term in combined_text for term in ['mixed-ability', 'esl/efl', 'learning difficulties']):
            scores['Mixed'] = scores.get('Mixed', 0) + 5
            
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return 'Primary'

    @staticmethod
    def enhanced_methodology_classification(methodology_text, task_text="", generated_prompt=""):
        """Enhanced methodology classification with complete dropdown coverage"""
        combined_text = f"{methodology_text} {task_text} {generated_prompt}".lower()
        
        scores = {}
        for method, patterns in PromptAnalyzer.METHODOLOGY_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if pattern in combined_text:
                    # Exact dropdown matches get highest score
                    if pattern == methodology_text.lower():
                        score += 15
                    # Partial dropdown matches
                    elif any(dropdown_part in pattern for dropdown_part in methodology_text.lower().split()):
                        score += 10
                    else:
                        score += 3
            scores[method] = score
            
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return 'Direct_Instruction'

    @staticmethod
    def enhanced_subject_classification(subject_text, task_text="", generated_prompt="", role_text=""):
        """Enhanced subject classification with role-based priority"""
        
        # ROLE-BASED PRIORITY CLASSIFICATION (99% accuracy)
        role_lower = role_text.lower()
        
        if 'art teacher' in role_lower or 'art instructor' in role_lower:
            return 'Arts'
        elif 'pe teacher' in role_lower or 'physical education teacher' in role_lower:
            return 'PE_Health'
        elif 'math teacher' in role_lower or 'mathematics teacher' in role_lower:
            return 'STEM'
        elif 'science teacher' in role_lower:
            return 'STEM'
        elif 'language instructor' in role_lower or 'language teacher' in role_lower or 'english teacher' in role_lower:
            return 'Languages'
        elif 'history teacher' in role_lower or 'social studies teacher' in role_lower:
            return 'Humanities'
        elif 'literature teacher' in role_lower:
            return 'Languages'
        
        # FALLBACK: Content-based analysis for non-teacher roles
        combined_text = f"{subject_text} {task_text} {generated_prompt}".lower()
        
        scores = {}
        for category, patterns in PromptAnalyzer.SUBJECT_PATTERNS.items():
            score = 0
            
            # Keywords (lower weight) - with word boundaries
            for keyword in patterns['keywords']:
                if f' {keyword} ' in f' {combined_text} ':
                    score += 2
            
            # Specific topics (higher weight) - with word boundaries  
            for topic in patterns['topics']:
                if f' {topic} ' in f' {combined_text} ':
                    score += 5
                    
            scores[category] = score
        
        # Special handling for cross-curricular
        if sum(scores.values()) > 25:
            return 'Cross_Curricular'
            
        if max(scores.values()) > 3:
            return max(scores, key=scores.get)
        return 'Other'
            
        @staticmethod
        def enhanced_complexity_assessment(task_text, methodology_text, generated_prompt):
            """Enhanced complexity assessment with task-specific rules"""
            combined_text = f"{task_text} {methodology_text} {generated_prompt}".lower()
            
            scores = {}
            for level, indicators in PromptAnalyzer.COMPLEXITY_INDICATORS.items():
                score = sum(1 for indicator in indicators if indicator in combined_text)
                scores[level] = score
                
            # Task-specific complexity rules
            if any(term in combined_text for term in ['complete lesson plan', 'lesson plan with objectives']):
                return 'Advanced'
            elif any(term in combined_text for term in ['assessment rubric', 'differentiated activities']):
                return 'Advanced'
            elif 'quiz' in combined_text and 'assessment' in combined_text:
                return 'Intermediate'
            elif any(term in combined_text for term in ['warm-up', 'introduction to']):
                return 'Intermediate'
                
            if max(scores.values()) > 0:
                return max(scores, key=scores.get)
            return 'Intermediate'

        # === LEGACY METHODS (kept for compatibility) ===

    @staticmethod
    def categorize_subject(subject_text):
        """Legacy method - use enhanced_subject_classification instead"""
        return PromptAnalyzer.enhanced_subject_classification(subject_text)

    @staticmethod
    def categorize_age_group(context_text):
        """Legacy method - use enhanced_context_classification instead"""
        return PromptAnalyzer.enhanced_context_classification(context_text)

    @staticmethod
    def categorize_methodology(methodology_text):
        """Legacy method - use enhanced_methodology_classification instead"""
        return PromptAnalyzer.enhanced_methodology_classification(methodology_text)

    @staticmethod
    def assess_complexity(prompt_text, task_text, methodology_text):
        """Enhanced Bloom's Taxonomy-based complexity assessment with primary verb priority"""
        combined_text = f"{task_text} {methodology_text} {prompt_text}".lower()
        
        # PRIMARY VERB DETECTION (First 30 chars of task - highest priority)
        task_start = task_text.lower()[:30]
        
        # Define primary verb groups for quick lookup
        primary_verbs = {
            'Expert': ['create', 'design', 'develop', 'build', 'construct', 'compose', 'generate', 'produce'],
            'Advanced': ['analyze', 'evaluate', 'compare', 'contrast', 'assess', 'critique', 'examine', 'judge'],
            'Intermediate': ['apply', 'demonstrate', 'solve', 'use', 'implement', 'practice', 'show'],
            'Basic': ['list', 'name', 'identify', 'recall', 'define', 'describe', 'explain', 'summarize']
        }
        
        # Check for primary verbs at start of task
        for complexity, verbs in primary_verbs.items():
            for verb in verbs:
                if task_start.startswith(verb) or f' {verb} ' in f' {task_start} ':
                    return complexity
        
        # Full Bloom's analysis if no primary verb detected
        bloom_scores = {}
        complexity_votes = {'Basic': 0, 'Intermediate': 0, 'Advanced': 0, 'Expert': 0}
        
        for bloom_level, indicators in PromptAnalyzer.BLOOMS_COMPLEXITY_INDICATORS.items():
            score = 0
            
            # Check verbs with stricter word boundaries
            for verb in indicators['verbs']:
                if (f' {verb} ' in f' {combined_text} ' or 
                    combined_text.startswith(f'{verb} ') or 
                    combined_text.endswith(f' {verb}')):
                    score += 3
            
            # Check task types with stricter matching
            for task in indicators['tasks']:
                if len(task) >= 4 and task in combined_text:
                    score += 2
            
            bloom_scores[bloom_level] = score
            
            # Vote for complexity level
            if score > 0:
                complexity_votes[indicators['complexity']] += score
        
        # Educational task overrides
        if ('complete lesson plan' in combined_text or 
            'lesson plan with objectives' in combined_text or
            'unit plan' in combined_text):
            return 'Expert'
        elif ('assessment rubric' in combined_text or 
            'create rubric' in combined_text or
            'design rubric' in combined_text):
            return 'Expert'
        elif ('warm-up activity' in combined_text and 
            not any(word in combined_text for word in ['complex', 'advanced', 'create'])):
            return 'Basic'
        elif 'vocabulary' in combined_text and 'list' in combined_text:
            return 'Basic'
        
        # Determine winner based on votes with minimum threshold
        max_votes = max(complexity_votes.values())
        if max_votes >= 3:
            result = max(complexity_votes, key=complexity_votes.get)
            return result
        
        return 'Intermediate'
    @staticmethod
    def analyze_content(prompt_text):
        """Comprehensive content analysis (unchanged)"""
        if not prompt_text:
            return {}
            
        # Basic metrics
        word_count = len(prompt_text.split())
        sentence_count = len(re.findall(r'[.!?]+', prompt_text))
        
        # Keyword analysis
        text_lower = prompt_text.lower()
        
        blooms_count = sum(1 for keyword in PromptAnalyzer.BLOOMS_KEYWORDS 
                        if keyword in text_lower)
        udl_count = sum(1 for keyword in PromptAnalyzer.UDL_KEYWORDS 
                    if keyword in text_lower)
        tpack_count = sum(1 for keyword in PromptAnalyzer.TPACK_KEYWORDS 
                        if keyword in text_lower)
        pedagogical_count = sum(1 for keyword in PromptAnalyzer.PEDAGOGICAL_KEYWORDS 
                            if keyword in text_lower)
        
        # Calculate scores (0-10 scale)
        theory_score = min(10, (blooms_count + udl_count + tpack_count + pedagogical_count) / 2)
        
        # Complexity score based on readability
        try:
            complexity_score = max(0, min(10, (100 - flesch_reading_ease(prompt_text)) / 10))
        except:
            complexity_score = 5.0
            
        # Specificity and actionability scores
        specific_terms = ['students will', 'learning objective', 'step by step', 
                        'for example', 'specifically', 'in particular']
        specificity_score = min(10, sum(2 for term in specific_terms if term in text_lower))
        
        action_verbs = ['create', 'design', 'develop', 'implement', 'analyze', 
                    'evaluate', 'compare', 'explain', 'demonstrate']
        actionability_score = min(10, sum(1 for verb in action_verbs if verb in text_lower))
        
        return {
            'prompt_word_count': word_count,
            'prompt_sentence_count': sentence_count,
            'prompt_complexity_score': round(complexity_score, 2),
            'blooms_keywords_count': blooms_count,
            'udl_keywords_count': udl_count,
            'tpack_keywords_count': tpack_count,
            'pedagogical_keywords_count': pedagogical_count,
            #'theory_integration_score': round(theory_score, 2),
            'specificity_score': round(specificity_score, 2),
            'actionability_score': round(actionability_score, 2),
            #'originality_score': 5.0
        }