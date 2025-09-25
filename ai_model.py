from cerebras.cloud.sdk import Cerebras
import json
import os
from dotenv import load_dotenv

load_dotenv()

class AIModel:
    def call_model(self, system_prompt, message, output_mode = "json", api_key_val = "API_KEY", filename=None, model="qwen-3-coder-480b", output_size=150000):
        api_key = os.getenv(api_key_val)
        if not api_key:
            raise ValueError("API_KEY environment variable not set")
        client = Cerebras(api_key=api_key)
        stream = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": message
                }    
            ],
            model=model,
            stream=True,
            max_completion_tokens=output_size,
            temperature=0.7,
            top_p=0.8
            )
        collected_chunks = []
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                collected_chunks.append(content)
                #print(content, end="")


        if output_mode.lower() == "json":
            full_output = "".join(collected_chunks)
            parsed_output = json.loads(full_output)
            output_data = {
                "output": parsed_output 
            }
            
            with open(filename, "w", encoding="utf-8") as json_file:
                json.dump(output_data, json_file, ensure_ascii=False, indent=4)
        
        else:
            return "".join(collected_chunks)

            
                        


#call_model = AIModel()
# call_model.call_model(system_prompt="""You are a JSON converter.
# I will give you a block of text listing SJSU courses and their community college equivalents.

# Convert it into a JSON array where:

# - Each top-level element is:
#   {
#     "subject": "<subject area>",
#     "courses": [
#       {
#         "sjsu_course": "<uppercase course code only>", 
#         "equivalents": [ "<marker+course1>", "<course2>", ... ]
#       },
#       ...
#     ]
#   }

# Rules:
# - For each SJSU course, only output the code (example: "ANTH 011") in `sjsu_course`.
# - If multiple equivalents joined by “OR”:
#   - Make the first element `"||<first course>"`, then the next `"Second course"`, etc.
# - If multiple equivalents joined by “AND”:
#   - Make the first element `"&&<first course>"`, then the next `"Second course"`, etc.
# - If there is “No Current Equivalent” use `[ "None" ]` for `equivalents`.
# - Output only valid JSON.

# Example input: 
# ANTH 011 Cultural Anthropology → ANTH 102 Introduction to Cultural Anthropology OR SOC 101 Intro to Sociology  
# ART 013 Three-Dimensional Design Concepts → ART 150 3-D Design Basics AND ART 160 Sculpture I  

# Example output:
# [
#   {
#     "subject": "Anthropology",
#     "courses": [
#       {
#         "sjsu_course": "ANTH 011",
#         "equivalents": ["||ANTH 102", "SOC 101"]
#       }
#     ]
#   },
#   {
#     "subject": "Art and Art History",
#     "courses": [
#       {
#         "sjsu_course": "ART 013",
#         "equivalents": ["&&ART 150", "ART 160"]
#       }
#     ]
#   }
# ]



# Now convert the following text:
# """,message="""African American Studies
# AFAM 002A African Americans and the Development of America's History and Government		No Current Equivalent
# AFAM 002B African Americans and the Development of America's History and Government		No Current Equivalent
# AFAM 022 The Humanities in African-American Culture		No Current Equivalent
# AFAM 040 African Origins		No Current Equivalent
# Anthropology
# ANTH 011 Cultural Anthropology		ANTH 102 Introduction to Cultural Anthropology
# ANTH 012 Introduction to Human Evolution		ANTH 101 Introduction to Biological Anthropology
# ANTH 013 Archaeology		ANTH 140 Introduction to Archaeology
# ANTH 025 Human Lifecourse in Context		No Current Equivalent
# Art and Art History
# ART 012 Two-Dimensional Design and Color Concepts		No Current Equivalent
# ART 013 Three-Dimensional Design Concepts		ART 150 3-D Design Basics
# ART 014 Color		No Current Equivalent
# ART 024 Drawing I		ART 110 Drawing
# ART 025 Expressive Drawing		No Current Equivalent
# ART 026 Drawing II		No Current Equivalent
# ART 039 Multicultural Arts for Children		No Current Equivalent
# ART 046 Introduction to Ceramics		ART 135 Beginning Wheel-Thrown Ceramics
# ART 047 Introduction to Metalsmithing		No Current Equivalent
# ART 061 Beginning Painting		ART 113 Painting I
# ART 068 Beginning Sculpture: Object & Concept		No Current Equivalent
# ART 074 Introduction to Digital Media		No Current Equivalent
# ART 075 Introduction to Digital Video Art		No Current Equivalent
# ARTH 011 Modern Art History		No Current Equivalent
# ARTH 070A Art History, Prehistoric to Medieval		ART 101 History of Art, Prehistoric to Gothic
# ARTH 070B Art History, Renaissance to Modern		ART 102 History of Art, Renaissance to Modern
# ARTH 070C Arts of Asia		ART 106 History of Art: Asia
# ARTH 072 Design in Society		No Current Equivalent
# PHOT 040 Beginning Photography		No Current Equivalent
# Aviation
# AVIA 001 Introduction to the Aviation Industry		No Current Equivalent
# AVIA 002 Private Pilot Ground		No Current Equivalent
# AVIA 031 Aircraft Theory and Design		No Current Equivalent
# AVIA 042 Aircraft Systems		No Current Equivalent
# AVIA 043 Propulsion Theory		No Current Equivalent
# AVIA 062 Instrument Pilot Ground		No Current Equivalent
# AVIA 068 Avionics and Airborne Communication		No Current Equivalent
# AVIA 073 Air Traffic Control		No Current Equivalent
# AVIA 091 Aircraft Turbine Engines		No Current Equivalent
# Biological Sciences
# BIOL 010 The Living World		No Current Equivalent
# BIOL 020 Ecological Biology		No Current Equivalent
# BIOL 021 Human Biology		No Current Equivalent
# BIOL 030 Principles of Biology I		BIOL 110 General Molecular Cell Biology
# BIOL 031 Principles of Biology II		BIOL 120 General Organismal, Ecological and Evolutionary Biology
# BIOL 055 Biostatistics		MATH 115 Statistics
# BIOL 065 Human Anatomy		No Current Equivalent
# BIOL 065O Human Anatomy		BIOL 201 General Human Anatomy
# BIOL 066 Human Physiology		BIOL 202 General Human Physiology
# MICR 020 General Bacteriology		No Current Equivalent
# Business
# BUS1 020 Financial Accounting		ACCT 201 Financial Accounting
# BUS1 020N Survey of Accounting		No Current Equivalent
# BUS1 021 Managerial Accounting		ACCT 205 Managerial Accounting
# BUS2 090 Business Statistics		MATH 115 Statistics
#    OR
# MATH 115H Statistics Honors
# BUS3 010 Discovering Business		BUS 101 Introduction to Business
# BUS3 080 Legal Environment of Business		BUS 201 Business Law
# BUS4 091L Computer Tools for Business		CA 221 Computer Concepts and Applications in Business
# BUS4 092 Introduction to Business Programming		No Current Equivalent
# Chemistry
# CHEM 001A General Chemistry		CHEM 110 General Chemistry
# CHEM 001B General Chemistry		CHEM 120 General Chemistry
# CHEM 008 Organic Chemistry		No Current Equivalent
# CHEM 009 Organic Chemistry Lab		No Current Equivalent
# CHEM 030A Introductory Chemistry		CHEM 101 Introductory Chemistry
# CHEM 030B Introductory Chemistry		CHEM 102 Intro Chemistry (Organic & Biochemistry)
# CHEM 55 and 55L Quantitative Analysis and Lab sequence		No Current Equivalent
# CHEM 112A, 112B and 113A Organic Chemistry & Lab		CHEM 210 Organic Chemistry
#    AND
# CHEM 220 Organic Chemistry
# CONTENT CREDIT ONLY (CHEM 210 & CHEM 220 must be completed at same school)
# Chemistry for Nursing Equivalent Transfer Course		No Current Equivalent
# Chicano and Chicana Studies
# CCS 001 Introduction to Chicana and Chicano Studies		No Current Equivalent
# CCS 025 The Changing Majority: Power and Ethnicity in America		No Current Equivalent
# CCS 030 Race and Ethnicity in Public Space		No Current Equivalent
# Communication Studies
# COMM 010 Communication and Human Relationships		No Current Equivalent
# COMM 020 Public Speaking		COMM 101 Introduction to Public Speaking
#    OR
# COMM 101H Introduction to Public Speaking Honors
# COMM 040 Argumentation and Advocacy		No Current Equivalent
# COMM 041 Critical Decision Making		No Current Equivalent
# COMM 045 Media and Culture		No Current Equivalent
# COMM 074 Fundamentals of Intercultural Communication		No Current Equivalent
# Comparative Religious Studies
# RELS 070 Gods, Guns, Gurus, Grails-World Religion		No Current Equivalent
# RELS 090 Bible History and Literature		No Current Equivalent
# RELS 099 Death, Dying and Religions		No Current Equivalent
# Computer Science
# CS 022A Python for Everyone		No Current Equivalent
# CS 022B Python Programming for Data Analysis		No Current Equivalent
# CS 046A Introduction to Programming		CS 121 Programming and Algorithms in Java
#    AND
# CS 131 Data Structures in Java
# (CS 121 & CS 131 must be completed at same school)
# CS 046B Introduction to Data Structures		CS 121 Programming and Algorithms in Java
#    AND
# CS 131 Data Structures in Java
# (CS 121 & CS 131 must be completed at same school)
# CS 047 Introduction to Computer Systems		CS 140 Assembly Language and Computer Architecture
# CS 049C Programming in C		No Current Equivalent
# CS 049J Programming in Java		No Current Equivalent
# Design
# ANI 010 Light and Optics		No Current Equivalent
# ANI 011 Illustration Fundamentals I		ART 110 Drawing
# ANI 013 Drawing for Animation/Illustration I		ART 216 Life Drawing
# ANI 021 Color Principles for Screen Arts		No Current Equivalent
# ANI 031 2D Animation I		No Current Equivalent
# ANI 041 Introduction to 3D Modeling		No Current Equivalent
# ANI 061 Introduction to 3D Animation		No Current Equivalent
# ANI 071 Visual Principles		No Current Equivalent
# DSGD 063 Fundamental Graphic Visualization		No Current Equivalent
# DSGD 083 Digital Applications: Basics		No Current Equivalent
# DSGD 099 Introduction to Typography		No Current Equivalent
# DSIT 005 Introduction of Interior Design and Architecture		No Current Equivalent
# DSIT 010 Sketching, Drawing + Modeling		No Current Equivalent
# DSIT 029 Design Process		No Current Equivalent
# DSIT 033 Architectural Presentation		No Current Equivalent
# DSIT 034 Interior Architecture Foundation Studio		No Current Equivalent
# DSIT 083 Visual Communication I		No Current Equivalent
# Economics
# ECON 001A Principles of Economics: Macroeconomics		ECON 101 Principles of Macroeconomics
#    OR
# ECON 101H Principles of Macroeconomics Honors
# ECON 001B Principles of Economics: Microeconomics		ECON 102 Principles of Microeconomics
#    OR
# ECON 102H Principles of Microeconomics Honors
# ECON 003 Economic Statistics		MATH 115 Statistics
#    OR
# MATH 115H Statistics Honors
# Education
# CHAD 060 Child Development		CFE 102 The Developing Child - Child Growth and Development
# CHAD 070 Lifespan Development in the 21st Century		PSY 236 Developmental Psychology
# CHAD 080 Quantitative Analysis in Developmental Science		MATH 115 Statistics
#    OR
# MATH 115H Statistics Honors
# EDSE 014A American Sign Language I		No Current Equivalent
# EDSE 014B American Sign Language II		No Current Equivalent
# Engineering
# AE 020 Computer-Aided Design for Aerospace Engineers		ENGR 140 Engineering 3D Graphics
# AE 030 Computer Programming for Aerospace Engineers		ENGR 125 Programming and Problem-Solving in MATLAB
# CE 008 Plane Surveying		No Current Equivalent
# CE 020 Engineering Graphics, CAD and Programming		No Current Equivalent
# CE 095 Theory and Application of Statics		ENGR 210 Statics
# CE 099 Introductory Statics		ENGR 210 Statics
# CMPE 030 Programming Concepts and Methodology		CS 120 Programming and Algorithms in C/C++
#    OR
# CS 121 Programming and Algorithms in Java
#    AND
# CS 131 Data Structures in Java
# (CS 121 & CS 131 must be completed at same school)
# CMPE 050 Object-Oriented Concepts and Methodology		CS 131 Data Structures in Java
# EE 030 Introduction to Programming Micro-Controllers for Electrical Engineering		CS 120 Programming and Algorithms in C/C++
#    OR
# CS 121 Programming and Algorithms in Java
# EE 097 Introductory Electrical Engineering Laboratory		No Current Equivalent
# EE 098 Introduction to Circuit Analysis		ENGR 230 Circuit Analysis
# ENGR 010 Introduction to Engineering		ENGR 110 Introduction to Engineering
# (No GE Credit given)
# MATE 025 Introduction to Materials		ENGR 130 Materials Science
# ME 020 Design and Graphics		ENGR 140 Engineering 3D Graphics
# ME 030 Computer Applications		ENGR 125 Programming and Problem-Solving in MATLAB
# ME 041 Machine Shop Safety		No Current Equivalent
# English and Comparative Literature
# ENGL 001A First Year Writing		ENGL 101 College Reading and Composition
#    OR
# ENGL 101H College Composition Honors
# ENGL 001B Argument and Analysis		No Current Equivalent
# ENGL 002 Critical Thinking and Writing		ENGL 102 Critical Thinking and Literature
#    OR
# ENGL 102H Critical Thinking and Literature Honors
#    OR
# ENGL 103 Critical Thinking and Research
#    OR
# ENGL 103H Critical Thinking and Research Honors
#    OR
# PHIL 201 Critical Thinking
# ENGL 010 Great Works of Literature		ENGL 102 Critical Thinking and Literature
# ENGL 022 Fantasy and Science Fiction		No Current Equivalent
# ENGL 040 Contemporary World Fiction		No Current Equivalent
# ENGL 050 Beginnings to the "American" Experiment		ENGL 225 English Literature (800-1750)
# ENGL 060 Literatures of the Atlantic World, 1680-1860		No Current Equivalent
# ENGL 070 Emerging Modernisms and Beyond		No Current Equivalent
# ENGL 071 Creative Writing		No Current Equivalent
# ENGL 078 Introduction to Shakespeare's Drama		No Current Equivalent
# Environmental Studies
# ENVS 001 Introduction to Environmental Issues		BIOL 104 Environmental Biology
#    OR
# BIOL 104H Environmental Biology Honors
# ENVS 010 Life on a Changing Planet		No Current Equivalent
# Film and Theatre
# RTVF 010 The Art of Film		No Current Equivalent
# RTVF 020 Introduction to Audio for Film & Television		No Current Equivalent
# RTVF 030 Introduction to Film & Television Production		FTV 244 Production and Post-Production of the Short Film
# RTVF 031 Film and Television Aesthetics		No Current Equivalent
# RTVF 080 Introduction to Media		No Current Equivalent
# RTVF 082 Introduction to Film History		No Current Equivalent
# TA 005 Acting		THA 110 Fundamentals of Acting
# TA 010 Theatre Appreciation		THA 101 Introduction to Theatre
#    OR
# THA 101H Introduction to Theatre Honors
# TA 011 Script Analysis		THA 225 Script Analysis
# TA 017 Intermediate Acting		THA 125 Intermediate Acting Workshop
# TA 048 Voice & Movement for the Actor		No Current Equivalent
# TA 051A Scenery and Props for the Performing Arts		THA 102 Introduction to Stagecraft
# TA 051B Costume for the Performing Arts		THA 104 Introduction to Stage Costume
# TA 051C Lighting & Sound for the Performing Arts		No Current Equivalent
# TA 064 Make-up for Performing Arts		THA 133 Makeup for the Stage
# Geography
# GEOG 001 Physical Geography		GEOG 101 Physical Geography: Earth's Surface Landscapes
# GEOG 010 Cultural Geography		GEOG 105 Cultural Geography
# GEOG 012 World Regional Geography		GEOG 110 World Regional Geography
# Geology
# GEOL 001 General Geology		GEOL 101 Physical Geology
#    AND
# GEOL 101L Physical Geology Lab
#    OR
# GEOL 101H Physical Geology Honors
#    AND
# GEOL 101L Physical Geology Lab
# (Must complete courses at same school)
# GEOL 002 Geology for Engineers		No Current Equivalent
# GEOL 003 Planet Earth		No Current Equivalent
# GEOL 004L Earth Systems Lab		GEOL 101L Physical Geology Lab
# (if not used for GEOL 1)
# GEOL 007 Earth, Time and Life		GEOL 102 Historical Geology
#    AND
# GEOL 102L Historical Geology Lab
# (GEOL 102 & GEOL 102L must be completed at same school)
# GEOL 028 Geology Outdoors		No Current Equivalent
# Global Studies
# GLST 001A Introduction to Global Studies		No Current Equivalent
# History
# HIST 001A World History to 1500		HIST 104 Intro to World Civilizations from Human Beginnings until 1500
# HIST 001B World History from 1500		HIST 105 Intro to World Civilizations from 1500 Until Present
# HIST 010A Western Civilization		HIST 101 Western Civilization, Ancient-1750
# HIST 010B Western Civilization		HIST 102 Western Civilization, 1750-Present
# HIST 020A History of the American People		HIST 107 U S History 1607-1877
#    OR
# HIST 107H U.S. History from 1607-1877 Honors
# HIST 020B History of the American People		HIST 108 U S History from 1865
#    OR
# HIST 108H U.S. History from 1865 Honors
# Hospitality Management
# HSPM 001 Travel to Learn, Learn to Travel		No Current Equivalent
# HSPM 011 Restaurant Entrepreneurship		No Current Equivalent
# HSPM 012 Data Analytics in Restaurant Operations		No Current Equivalent
# HSPM 020 Sanitation and Environmental Issues in the Hospitality Industry		No Current Equivalent
# Hospitality Major Elective/s Equivalent Transfer Course/s		No Current Equivalent
# Journalism and Mass Communications
# ADV 091 Introduction to Advertising		No Current Equivalent
# JOUR 061 Writing for Print, Electronic and Online Media		JOUR 121 Beginning Journalism
# JOUR 095 Beginning Digital News Photography		No Current Equivalent
# MCOM 063 New Media		No Current Equivalent
# MCOM 070 Visual Communication for Modern Media		No Current Equivalent
# MCOM 072 Mass Communication and Society		COMM 105 Introduction to Mass Communication
# PR 099 Introduction to Public Relations		No Current Equivalent
# Justice Studies
# FS 011 Survey of Forensic Science		AJ 208 Introduction to Forensic Science
# JS 010 Introduction to Justice Studies		AJ 101 Intro to the Administration of Justice
# JS 012 Introduction to Legal Studies		No Current Equivalent
# JS 015 Introductory Statistics in Justice Studies		MATH 115 Statistics
#    OR
# MATH 115H Statistics Honors
# JS 025 Introduction to Human Rights and Justice		No Current Equivalent
# Kinesiology
# KIN 001 Adapted Physical Activities		KINF 100 Adaptive Physical Education
# KIN 002A Beginning Swimming		KINF 190 Beginning Swimming for Non-swimmers
# KIN 002B Intermediate Swimming		KINF 192 Intermediate Swimming
# KIN 002C Advanced Swimming		No Current Equivalent
# KIN 003 Water Polo		No Current Equivalent
# KIN 008 Skin and SCUBA Diving		No Current Equivalent
# KIN 009A Beginning Sailing		No Current Equivalent
# KIN 011A Beginning Rowing		No Current Equivalent
# KIN 014A Beginning Volleyball		KINF 180 Beginning Volleyball
# KIN 014B Intermediate Volleyball		KINF 190 Beginning Swimming for Non-swimmers
# KIN 014C Advanced Volleyball		KINF 280 Advanced Volleyball
# KIN 015A Beginning Basketball		No Current Equivalent
# KIN 015B Intermediate Basketball		No Current Equivalent
# KIN 019A Beginning Soccer		KINF 150 Beginning Soccer
# KIN 019B Intermediate Soccer		KINF 151 Intermediate Soccer
# KIN 020A Beginning Badminton		No Current Equivalent
# KIN 020B Intermediate Badminton		No Current Equivalent
# KIN 020C Advanced Badminton		No Current Equivalent
# KIN 021A Beginning Tennis		KINF 160 Beginning Tennis
# KIN 021B Intermediate Tennis		KINF 161 Intermediate Tennis
# KIN 023A Beginning Archery		No Current Equivalent
# KIN 023B Intermediate Archery		No Current Equivalent
# KIN 024A Beginning Bowling		No Current Equivalent
# KIN 024B Intermediate Bowling		No Current Equivalent
# KIN 025A Beginning Golf		KINF 140 Beginning Golf
# KIN 025B Intermediate Golf		No Current Equivalent
# KIN 027A Beginning Table Tennis		No Current Equivalent
# KIN 027B Intermediate Table Tennis		No Current Equivalent
# KIN 028A Beginning Gymnastics		No Current Equivalent
# KIN 029 Cardio Kickboxing		No Current Equivalent
# KIN 030 Pilates		No Current Equivalent
# KIN 031 Body Sculpting		No Current Equivalent
# KIN 032 Aerobics		No Current Equivalent
# KIN 034 Step Training		No Current Equivalent
# KIN 035A Beginning Weight Training		KINF 107 Beginning Weight Lifting
# KIN 035B Intermediate Weight Training		KINF 108 Intermediate Weight Lifting
# KIN 037 Fitness Walking		No Current Equivalent
# KIN 038 Beginning Jogging		No Current Equivalent
# KIN 040A Topics in Modern Dance I		No Current Equivalent
# KIN 041A Topics in Ballet I		No Current Equivalent
# KIN 042A Topics in Jazz Dance I		No Current Equivalent
# KIN 045A Beginning Lindy Hop and Night Club Swing		No Current Equivalent
# KIN 046A Beginning Social Dance		No Current Equivalent
# KIN 047A Beginning West Coast Swing		No Current Equivalent
# KIN 048A Beginning Latin Dance		No Current Equivalent
# KIN 049A Topics in Tap Dance I		No Current Equivalent
# KIN 050 Tai Chi (Non-Combative)		No Current Equivalent
# KIN 051A Beginning Aikido		No Current Equivalent
# KIN 051B Intermediate Aikido		No Current Equivalent
# KIN 052A Beginning Judo		No Current Equivalent
# KIN 052B Intermediate Judo		No Current Equivalent
# KIN 052C Competitive Judo		No Current Equivalent
# KIN 053A Beginning Karate		No Current Equivalent
# KIN 053B Intermediate Karate		No Current Equivalent
# KIN 054A Beginning Tae Kwon Do		No Current Equivalent
# KIN 055A Beginning Self-Defense		No Current Equivalent
# KIN 061A Beginning Hatha Yoga		KINF 144 Hatha Yoga
# KIN 061B Intermediate Hatha Yoga		KINF 244 Intermediate/Advanced Hatha Yoga
# KIN 063A Beginning Hiking and Backpacking		No Current Equivalent
# KIN 069 Stress Management: A Multidisciplinary Perspective		No Current Equivalent
# KIN 070 Introduction to Kinesiology		KINT 100 Introduction to Kinesiology
# (Will not satisfy PE activity requirement)
# Linguistics and Language Development
# LING 020 Nature of Language		No Current Equivalent
# Mathematics
# MATH 012 Number Systems		No Current Equivalent
# MATH 018A College Algebra		MATH 128 College Algebra for Liberal Arts
# MATH 018B Trigonometry		No Current Equivalent
# MATH 019 Precalculus		MATH 140 Precalculus
# MATH 030 Calculus I		MATH 150 Calculus and Analytic Geometry
#    OR
# MATH 150H Calculus & Analytic Geometry Honors
# MATH 031 Calculus II		MATH 160 Calculus and Analytic Geometry
# MATH 032 Calculus III		MATH 250 Calculus and Analytic Geometry
# MATH 033A Ordinary Differential Equations for SCI & ENGR		MATH 230 Introduction to Ordinary Differential Equations
# MATH 033LA Differential Equations and Linear Algebra		MATH 220 Linear Algebra
#    AND
# MATH 230 Introduction to Ordinary Differential Equations
# (MATH 220 & MATH 230 must be completed at same school)
# MATH 039 Linear Algebra I		MATH 220 Linear Algebra
# MATH 042 Discrete Mathematics		CS 150 Discrete Structures
# MATH 050 Scientific Computing I		No Current Equivalent
# MATH 070 Mathematics for Business		MATH 124 Finite Math
# MATH 071 Calculus for Business and Aviation		No Current Equivalent
# Meteorology
# METR 010 Weather and Climate		GEOG 102 Physical Geography: Earth's Weather and Climate
# METR 012 Global Warming: Science and Solutions		No Current Equivalent
# METR 050 Scientific Computing I		No Current Equivalent
# METR 051 Scientific Computing II		No Current Equivalent
# METR 061 Meteorology and Climate Science II		No Current Equivalent
# Music and Dance
# DANC 010 Dance Appreciation		No Current Equivalent
# DANC 040A Topics in Modern Dance I		No Current Equivalent
# DANC 042A Topics in Jazz Dance I		No Current Equivalent
# DANC 043 Dance Improvisation		No Current Equivalent
# DANC 048A Beginning Latin Dance		No Current Equivalent
# DANC 049A Topics in Tap Dance I		No Current Equivalent
# DANC 051A Dance Production		No Current Equivalent
# DANC 051B Topics in Dance Crewing		No Current Equivalent
# DANC 053 World Dance		No Current Equivalent
# DANC 054 Topics in Dance Technique II		No Current Equivalent
# DANC 075 Rhythm and Dynamics in Dance		No Current Equivalent
# MUSC 001A Music Theory IA		MUS 151 Music Theory II
#    OR
# MUS 120 Music Theory I
# Subject to Completion of Theory Placement Exam
# MUSC 001B Musicianship IB		MUS 153A Musicianship I
# Subject to Completion of Theory Placement Exam
# MUSC 002A Music Theory IIA		MUS 151 Music Theory II
# Subject to Completion of Theory Placement Exam
# MUSC 002B Musicianship IIB		MUS 153B Musicianship II
# Subject to Completion of Theory Placement Exam
# MUSC 003A Music Theory IIIA		MUS 251A Music Theory III
# Subject to Completion of Theory Placement Exam
# MUSC 003B Musicianship IIIB		MUS 253A Musicianship III
# Subject to Completion of Theory Placement Exam
# MUSC 004A Music Theory IVA		MUS 251B Music Theory IV
# Subject to Completion of Theory Placement Exam
# MUSC 004B Musicianship IVB		MUS 253B Musicianship IV
# Subject to Completion of Theory Placement Exam
# MUSC 006 Jazz Theory		No Current Equivalent
# MUSC 009 Music Fundamentals		MUS 111 Fundamentals of Music
# MUSC 010A Music Appreciation		MUS 101 Music Appreciation
# MUSC 010B Introduction to Music		No Current Equivalent
# MUSC 012 Medieval and Renaissance Music		No Current Equivalent
# MUSC 013 Music Technology		No Current Equivalent
# MUSC 019 Music in World Cultures		No Current Equivalent
# MUSC 025A Piano Proficiency I		No Current Equivalent
# MUSC 025B Piano Proficiency II		No Current Equivalent
# MUSC 025C Piano Proficiency III		No Current Equivalent
# MUSC 026A Voice Fundamentals		No Current Equivalent
# MUSC 027A Fundamentals of Jazz Keyboard I		No Current Equivalent
# MUSC 027B Fundamentals of Jazz Keyboard II		No Current Equivalent
# MUSC 028 Guitar Fundamentals		No Current Equivalent
# MUSC 030 Piano		No Current Equivalent
# MUSC 033 Voice		No Current Equivalent
# MUSC 034 Strings		No Current Equivalent
# MUSC 035 Woodwinds		No Current Equivalent
# MUSC 036 Brass		No Current Equivalent
# MUSC 037 Percussion		No Current Equivalent
# MUSC 039A Jazz: Improvisation, Composition or Arranging 1		No Current Equivalent
# MUSC 040A Jazz Improvisation - I		No Current Equivalent
# MUSC 050A ENS: Concert Choir		MUS 181 Master Chorale
#    OR
# MUS 185 Concert Choir
# MUSC 051 ENS: University Chorales		No Current Equivalent
# MUSC 052 ENS: Opera Theater		No Current Equivalent
# MUSC 053 ENS: University Symphony Orchestra		MUS 166 Orchestra
#    OR
# MUS 167 Orchestra B
#    OR
# MUS 266 Orchestra C
# MUSC 054 ENS: Symphonic Band		MUS 160 Symphonic Band
#    OR
# MUS 260 Concert Band
# MUSC 055 ENS: Wind Ensemble		No Current Equivalent
# MUSC 057 ENS: Jazz Orchestra		MUSC 273 Jazz Ensemble A (Advanced)
#    OR
# MUSC 274 Advanced Jazz Ensemble
# MUSC 059 ENS: Afro-Latin Jazz Ensemble		No Current Equivalent
# MUSC 060A ENS: Choraliers		No Current Equivalent
# MUSC 060C ENS: Chamber Music		No Current Equivalent
# MUSC 060D ENS: Collegium Musicum		No Current Equivalent
# MUSC 060E ENS: Jazz Singers		No Current Equivalent
# MUSC 060F ENS: Small Jazz Ensembles		No Current Equivalent
# MUSC 060H ENS: Percussion Ensemble		No Current Equivalent
# MUSC 060I ENS: Jazz Ensemble		MUSC 173 Jazz Ensemble B (Beginning)
# MUSC 060J ENS: String Ensemble		No Current Equivalent
# MUSC 060K ENS: Brass Ensemble		No Current Equivalent
# MUSC 060L ENS: Woodwind Ensemble		No Current Equivalent
# MUSC 060M ENS: Saxophone Ensemble		No Current Equivalent
# Nutrition and Food Science
# NUFS 008 Nutrition for the Health Professions		NF 100 Nutrition
# NUFS 009 Introduction to Human Nutrition		No Current Equivalent
# NUFS 012 Cost Control in Hospitality		No Current Equivalent
# NUFS 020 Sanitation and Environmental Issues in the Hospitality Industry		No Current Equivalent
# NUFS 021 Culinary Principles and Practice		NF 103 Principles of Food Preparation
# NUFS 022 Catering and Beverage Management		No Current Equivalent
# NUFS 025 Internship in Foodservice Management		No Current Equivalent
# Philosophy
# PHIL 009 Mathematics and Logic for General Education		No Current Equivalent
# PHIL 010 Introduction to Philosophy		PHIL 106 Introduction to Philosophy
# PHIL 057 Logic and Critical Reasoning		PHIL 110 Introduction to Logic
# PHIL 061 Moral Issues		PHIL 105 Ethics: Moral Issues in Contemporary Society
#    OR
# PHIL 105H Ethics: Moral Issues in Society Honors
# PHIL 066 Introduction to Aesthetics		No Current Equivalent
# PHIL 070A Ancient Philosophy		No Current Equivalent
# PHIL 070B Early Modern Philosophy		No Current Equivalent
# Physics
# PHYS 001 Elementary Physics		No Current Equivalent
# PHYS 002A Fundamentals of Physics		PHYS 101 Introductory Physics
# PHYS 002B Fundamentals of Physics		PHYS 102 Introductory Physics
# PHYS 050 General Physics I: Mechanics		PHYS 110 General Physics
# PHYS 051 General Physics II: Electricity and Magnetism		PHYS 120 General Physics
# PHYS 052 General Physics III: Waves, Light, Heat		PHYS 211 General Physics
# Political Science
# POLS 001 American Government		POLS 101 American Political Institutions
#    OR
# POLS 101H American Political Institutions
# POLS 002 Introduction to Comparative Politics		POLS 103 Comparative Government
# POLS 003 Introduction to Political Thought		POLS 200 Introduction to Polticial Theory
# POLS 004 Introduction to International Relations		POLS 201 Contemporary International Relations
# Psychology and Statistics
# PSYC 001 Introduction to Psychology		PSY 101 General Psychology
#    OR
# PSY 101H General Psychology Honors
# PSYC 018 Introduction to Research Methods		PSY 200 Intro to Research Methods in Psychology
# PSYC 030 Introductory Psychobiology		PSY 201 Introduction to Physiological Psychology
# STAT 095 Elementary Statistics		MATH 115 Statistics
#    OR
# MATH 115H Statistics Honors
# Public Health & Recreation
# PH 001 Understanding Your Health		HE 101 Health Education
# PH 015 Human Life Span		PSY 236 Developmental Psychology
# PH 067 Introductory Health Statistics		MATH 115 Statistics
#    OR
# MATH 115H Statistics Honors
# PH 099 Introduction To Public Health		No Current Equivalent
# RECL 090 Foundations of Recreation Parks & Tourism		No Current Equivalent
# RECL 097 Event Planning		No Current Equivalent
# Social Work
# SCWK 010 Introduction to Social Welfare and Social Work		No Current Equivalent
# Sociology
# SOCI 001 Introduction to Sociology		SOC 101 Introduction to Sociology
#    OR
# SOC 101H Introduction to Sociology - Honors
# SOCI 015 Statistical Applications in the Social Sciences		MATH 115 Statistics
#    OR
# MATH 115H Statistics Honors
#    OR
# MATH 116 Introduction to Statistics Using R
# SOCI 080 Social Problems		SOC 112 American Social Issues: Problems and Challenges
# Technology
# TECH 020A Computer-Aided-Graphics		ENGR 140 Engineering 3D Graphics
# TECH 025 Introduction to Materials Technology		No Current Equivalent
# TECH 030 Introduction to Python Programming		No Current Equivalent
# TECH 031 Quality Assurance and Control		No Current Equivalent
# TECH 041 Machine Shop Safety		No Current Equivalent
# TECH 045 Sustainable Facilities Design & Planning		No Current Equivalent
# TECH 046 Machine Operation and Management		No Current Equivalent
# TECH 060 Introduction to Electronics		No Current Equivalent
# TECH 062 Analog Circuits		No Current Equivalent
# TECH 063 Analog and Digital Circuits		No Current Equivalent
# TECH 065 Introduction to Networks		No Current Equivalent
# TECH 066 Network Administration		No Current Equivalent
# TECH 067 Introduction to Internet of Things		No Current Equivalent
# TECH 068 Internet of Things Systems		No Current Equivalent
# University Studies
# UNVS 015 Statway: Statistics-Concepts & Methods		No Current Equivalent
# World Languages and Literatures
# CHIN 001A Elementary Chinese		No Current Equivalent
# CHIN 001B Elementary Chinese		No Current Equivalent
# CHIN 025A Intermediate Chinese		No Current Equivalent
# CHIN 025B Intermediate Chinese		No Current Equivalent
# FREN 001A Elementary French		FREN 101 Elementary French 1
# FREN 001B Elementary French		FREN 102 Elementary French 2
# FREN 025A, 025B, and 025C Intermediate French		FREN 201 Intermediate French 1
#    AND
# FREN 202 Intermediate French 2
# CAN FREN SEQ B (FREN 201 & FREN 202 must be completed at the same school)
# GERM 001A Elementary German		GER 101 Elementary German 1
# GERM 001B Elementary German		GER 102 Elementary German 2
# GERM 025A Intermediate German		GER 201 Intermediate German 1
# GERM 025B Intermediate German		GER 202 Intermediate German 2
# HEBR 001A Elementary Hebrew		No Current Equivalent
# HEBR 001B Elementary Hebrew		No Current Equivalent
# HEBR 015A Intermediate Hebrew		No Current Equivalent
# HEBR 015B Intermediate Hebrew		No Current Equivalent
# ITAL 001A Elementary Italian		No Current Equivalent
# ITAL 001B Elementary Italian		No Current Equivalent
# JPN 001A Elementary Japanese		No Current Equivalent
# JPN 001B Elementary Japanese		No Current Equivalent
# JPN 025A Intermediate Japanese		No Current Equivalent
# JPN 025B Intermediate Japanese		No Current Equivalent
# PORT 001A Elementary Portuguese I		No Current Equivalent
# PORT 001B Elementary Portuguese II		No Current Equivalent
# SPAN 001A Elementary Spanish		SPAN 101 Elementary Spanish 1
# SPAN 001B Elementary Spanish		SPAN 102 Elementary Spanish 2
# SPAN 003 Special Topics in Practical Spanish		No Current Equivalent
# SPAN 004A Basic Spanish I		No Current Equivalent
# SPAN 004B Basic Spanish II		No Current Equivalent
# SPAN 020A Spanish for Heritage Speakers I		SPAN 110SS Spanish for Heritage Speakers I
# SPAN 020B Spanish for Heritage Speakers II		SPAN 210SS Spanish for Heritage Speakers II
# SPAN 025A Intermediate Spanish		SPAN 201 Intermediate Spanish 1
# SPAN 025B Intermediate Spanish		SPAN 202 Intermediate Spanish 2
# VIET 001A Elementary Vietnamese		No Current Equivalent
# VIET 001B Elementary Vietnamese		No Current Equivalent""")