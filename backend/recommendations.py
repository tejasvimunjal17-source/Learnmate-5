"""
backend/recommendations.py
-----------------------------
Curated, hand-picked course & certification recommendations, keyed by
career domain, drawn exclusively from official learning platforms
(IBM SkillsBuild, IBM Training, Coursera, edX, Cisco Skills for All,
Google Cloud Skills Boost, Microsoft Learn, Kaggle Learn, freeCodeCamp,
Harvard CS50, DeepLearning.AI, Hugging Face, DataCamp, Codecademy, and
highly-rated Udemy tracks).

This is static reference data (no network calls, so it always renders
instantly) rather than something the LLM invents — every link points at a
real, official course/certification landing page so recommendations stay
trustworthy even when watsonx.ai is offline.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Course:
    name: str
    provider: str
    duration: str
    difficulty: str
    pricing: str  # "Free" | "Paid" | "Free (Paid Certificate)"
    link: str


@dataclass(frozen=True)
class Certification:
    name: str
    provider: str
    difficulty: str
    exam_cost: str
    link: str


COURSES: dict[str, list[Course]] = {
    "Data Science": [
        Course("Data Science Foundations", "IBM SkillsBuild", "4 weeks", "Beginner", "Free", "https://skillsbuild.org"),
        Course("IBM Data Science Professional Certificate", "Coursera", "3-6 months", "Beginner", "Paid (Free to audit)", "https://www.coursera.org/professional-certificates/ibm-data-science"),
        Course("Python for Data Science", "freeCodeCamp", "6-8 hrs", "Beginner", "Free", "https://www.freecodecamp.org/learn/data-analysis-with-python/"),
        Course("Intro to Machine Learning", "Kaggle Learn", "3 hrs", "Beginner", "Free", "https://www.kaggle.com/learn/intro-to-machine-learning"),
        Course("CS50's Introduction to Data Science", "Harvard (edX)", "10 weeks", "Intermediate", "Free (Paid Certificate)", "https://cs50.harvard.edu/college/"),
    ],
    "Web Development": [
        Course("CS50's Web Programming with Python and JavaScript", "Harvard (edX)", "12 weeks", "Intermediate", "Free (Paid Certificate)", "https://cs50.harvard.edu/web/"),
        Course("Responsive Web Design", "freeCodeCamp", "300 hrs", "Beginner", "Free", "https://www.freecodecamp.org/learn/responsive-web-design/"),
        Course("Full-Stack Web Development", "Codecademy", "6 months", "Beginner", "Paid", "https://www.codecademy.com/learn/paths/full-stack-engineer-career-path"),
        Course("Meta Front-End Developer Professional Certificate", "Coursera", "7 months", "Beginner", "Paid (Free to audit)", "https://www.coursera.org/professional-certificates/meta-front-end-developer"),
    ],
    "Cloud Computing": [
        Course("IBM Cloud Essentials", "IBM SkillsBuild", "2 weeks", "Beginner", "Free", "https://skillsbuild.org"),
        Course("Google Cloud Digital Leader Training", "Google Cloud Skills Boost", "8 hrs", "Beginner", "Free", "https://www.cloudskillsboost.google/"),
        Course("Microsoft Azure Fundamentals (AZ-900)", "Microsoft Learn", "10 hrs", "Beginner", "Free", "https://learn.microsoft.com/en-us/training/paths/az-900-describe-cloud-concepts/"),
        Course("IBM Cloud Professional Certificate", "Coursera", "4 months", "Intermediate", "Paid (Free to audit)", "https://www.coursera.org/professional-certificates/ibm-cloud"),
    ],
    "Artificial Intelligence": [
        Course("AI For Everyone", "DeepLearning.AI (Coursera)", "6 hrs", "Beginner", "Paid (Free to audit)", "https://www.coursera.org/learn/ai-for-everyone"),
        Course("Machine Learning Specialization", "DeepLearning.AI (Coursera)", "3 months", "Intermediate", "Paid (Free to audit)", "https://www.coursera.org/specializations/machine-learning-introduction"),
        Course("Hugging Face NLP Course", "Hugging Face", "Self-paced", "Intermediate", "Free", "https://huggingface.co/learn/nlp-course"),
        Course("IBM AI Fundamentals", "IBM SkillsBuild", "3 weeks", "Beginner", "Free", "https://skillsbuild.org"),
    ],
    "Cybersecurity": [
        Course("Introduction to Cybersecurity", "Cisco Skills for All", "6 hrs", "Beginner", "Free", "https://skillsforall.com/course/introduction-to-cybersecurity"),
        Course("Google Cybersecurity Professional Certificate", "Coursera", "6 months", "Beginner", "Paid (Free to audit)", "https://www.coursera.org/professional-certificates/google-cybersecurity"),
        Course("IBM Cybersecurity Fundamentals", "IBM SkillsBuild", "4 weeks", "Beginner", "Free", "https://skillsbuild.org"),
    ],
    "DevOps": [
        Course("Introduction to DevOps", "IBM SkillsBuild", "3 weeks", "Beginner", "Free", "https://skillsbuild.org"),
        Course("DevOps on AWS", "Coursera", "4 months", "Intermediate", "Paid (Free to audit)", "https://www.coursera.org/specializations/aws-devops"),
        Course("Kubernetes and Cloud Native Associate", "Microsoft Learn", "8 hrs", "Intermediate", "Free", "https://learn.microsoft.com/en-us/training/"),
    ],
    "Mobile Development": [
        Course("Meta Android Developer Professional Certificate", "Coursera", "8 months", "Beginner", "Paid (Free to audit)", "https://www.coursera.org/professional-certificates/meta-android-developer"),
        Course("Flutter & Dart Bootcamp", "Udemy", "60 hrs", "Beginner", "Paid", "https://www.udemy.com/topic/flutter/"),
        Course("Introduction to iOS Development (Swift)", "Codecademy", "25 hrs", "Beginner", "Paid", "https://www.codecademy.com/learn/learn-swift"),
    ],
    "Product Management": [
        Course("Google Project Management Professional Certificate", "Coursera", "6 months", "Beginner", "Paid (Free to audit)", "https://www.coursera.org/professional-certificates/google-project-management"),
        Course("Digital Product Management", "edX", "5 weeks", "Beginner", "Free (Paid Certificate)", "https://www.edx.org/"),
    ],
    "UI/UX Design": [
        Course("Google UX Design Professional Certificate", "Coursera", "6 months", "Beginner", "Paid (Free to audit)", "https://www.coursera.org/professional-certificates/google-ux-design"),
        Course("Figma Essentials Training", "Codecademy", "8 hrs", "Beginner", "Paid", "https://www.codecademy.com/"),
    ],
    "Business Analytics": [
        Course("Google Data Analytics Professional Certificate", "Coursera", "6 months", "Beginner", "Paid (Free to audit)", "https://www.coursera.org/professional-certificates/google-data-analytics"),
        Course("Power BI Fundamentals", "Microsoft Learn", "6 hrs", "Beginner", "Free", "https://learn.microsoft.com/en-us/training/powerplatform/power-bi"),
        Course("SQL for Data Analysis", "DataCamp", "4 hrs", "Beginner", "Paid (Free intro)", "https://www.datacamp.com/"),
    ],
}

CERTIFICATIONS: dict[str, list[Certification]] = {
    "Data Science": [
        Certification("IBM Data Science Professional Certificate", "IBM", "Beginner", "Free (audit) / Paid for certificate", "https://www.coursera.org/professional-certificates/ibm-data-science"),
        Certification("TensorFlow Developer Certificate", "TensorFlow", "Intermediate", "$100 USD", "https://www.tensorflow.org/certificate"),
        Certification("Databricks Certified Data Analyst Associate", "Databricks", "Intermediate", "$200 USD", "https://www.databricks.com/learn/certification"),
    ],
    "Web Development": [
        Certification("Meta Front-End Developer Certificate", "Meta", "Beginner", "Paid (subscription)", "https://www.coursera.org/professional-certificates/meta-front-end-developer"),
        Certification("responsive Web Design Certification", "freeCodeCamp", "Beginner", "Free", "https://www.freecodecamp.org/learn/responsive-web-design/"),
        Certification("GitHub Foundations Certification", "GitHub", "Beginner", "$99 USD", "https://resources.github.com/learn/certifications/"),
    ],
    "Cloud Computing": [
        Certification("IBM Certified Technical Advocate - Cloud", "IBM", "Beginner", "$200 USD", "https://www.ibm.com/training/certification"),
        Certification("AWS Certified Cloud Practitioner", "AWS", "Beginner", "$100 USD", "https://aws.amazon.com/certification/certified-cloud-practitioner/"),
        Certification("Microsoft Certified: Azure Fundamentals (AZ-900)", "Microsoft", "Beginner", "$99 USD", "https://learn.microsoft.com/en-us/credentials/certifications/azure-fundamentals/"),
        Certification("Google Cloud Digital Leader", "Google Cloud", "Beginner", "$99 USD", "https://cloud.google.com/learn/certification/cloud-digital-leader"),
    ],
    "Artificial Intelligence": [
        Certification("IBM AI Engineering Professional Certificate", "IBM", "Intermediate", "Free (audit) / Paid for certificate", "https://www.coursera.org/professional-certificates/ai-engineer"),
        Certification("NVIDIA Deep Learning Institute Certificate", "NVIDIA", "Intermediate", "Varies by course", "https://www.nvidia.com/en-us/training/"),
        Certification("Microsoft Certified: Azure AI Fundamentals (AI-900)", "Microsoft", "Beginner", "$99 USD", "https://learn.microsoft.com/en-us/credentials/certifications/azure-ai-fundamentals/"),
    ],
    "Cybersecurity": [
        Certification("IBM Cybersecurity Analyst Professional Certificate", "IBM", "Beginner", "Free (audit) / Paid for certificate", "https://www.coursera.org/professional-certificates/ibm-cybersecurity-analyst"),
        Certification("CompTIA Security+", "CompTIA", "Beginner", "~$392 USD", "https://www.comptia.org/certifications/security"),
        Certification("Cisco Certified Support Technician (CCST) Cybersecurity", "Cisco", "Beginner", "$125 USD", "https://www.cisco.com/site/us/en/learn/training-certifications/certifications/ccst/index.html"),
    ],
    "DevOps": [
        Certification("IBM DevOps and Software Engineering Certificate", "IBM", "Intermediate", "Free (audit) / Paid for certificate", "https://www.coursera.org/professional-certificates/devops-and-software-engineering"),
        Certification("Docker Certified Associate", "Docker", "Intermediate", "$195 USD", "https://www.docker.com/certification/"),
        Certification("Certified Kubernetes Administrator (CKA)", "Linux Foundation", "Advanced", "$395 USD", "https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/"),
    ],
    "Mobile Development": [
        Certification("Meta Android Developer Certificate", "Meta", "Beginner", "Paid (subscription)", "https://www.coursera.org/professional-certificates/meta-android-developer"),
        Certification("Associate Android Developer", "Google", "Intermediate", "Varies", "https://developer.android.com/"),
    ],
    "Product Management": [
        Certification("Google Project Management Certificate", "Google", "Beginner", "Paid (subscription)", "https://www.coursera.org/professional-certificates/google-project-management"),
        Certification("Certified Scrum Product Owner (CSPO)", "Scrum Alliance", "Beginner", "~$450-1000 USD", "https://www.scrumalliance.org/get-certified/product-owner-track/certified-scrum-product-owner"),
    ],
    "UI/UX Design": [
        Certification("Google UX Design Certificate", "Google", "Beginner", "Paid (subscription)", "https://www.coursera.org/professional-certificates/google-ux-design"),
    ],
    "Business Analytics": [
        Certification("Google Data Analytics Certificate", "Google", "Beginner", "Paid (subscription)", "https://www.coursera.org/professional-certificates/google-data-analytics"),
        Certification("Microsoft Certified: Power BI Data Analyst Associate (PL-300)", "Microsoft", "Intermediate", "$165 USD", "https://learn.microsoft.com/en-us/credentials/certifications/power-bi-data-analyst-associate/"),
        Certification("Oracle Analytics Certified Professional", "Oracle", "Intermediate", "$245 USD", "https://education.oracle.com/"),
    ],
}

_FALLBACK_COURSES = [
    Course("IBM SkillsBuild Career Catalog", "IBM SkillsBuild", "Self-paced", "All Levels", "Free", "https://skillsbuild.org"),
    Course("edX Explore Courses", "edX", "Self-paced", "All Levels", "Free (Paid Certificate)", "https://www.edx.org/"),
]

_FALLBACK_CERTS = [
    Certification("IBM Professional Certificates Catalog", "IBM", "All Levels", "Varies", "https://www.ibm.com/training/certification"),
]


def get_courses_for_domain(domain: str) -> list[Course]:
    return COURSES.get(domain, _FALLBACK_COURSES)


def get_certifications_for_domain(domain: str) -> list[Certification]:
    return CERTIFICATIONS.get(domain, _FALLBACK_CERTS)
