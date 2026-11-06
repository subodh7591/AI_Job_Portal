
from urllib.parse import quote_plus


# Curated learning resources for commonly required skills.
# Resources are grouped by skill to avoid recommending
# unrelated learning materials.

RESOURCE_CATALOG = {

    "python": [
        {
            "title": "Python Official Tutorial",
            "provider": "Python",
            "url": "https://docs.python.org/3/tutorial/",
            "type": "Documentation",
            "description": "Learn Python fundamentals, data structures, functions and modules."
        },
        {
            "title": "Scientific Computing with Python",
            "provider": "freeCodeCamp",
            "url": "https://www.freecodecamp.org/learn/scientific-computing-with-python/",
            "type": "Course",
            "description": "Practise Python programming through practical exercises and projects."
        }
    ],

    "java": [
        {
            "title": "Java Tutorials",
            "provider": "Oracle",
            "url": "https://docs.oracle.com/javase/tutorial/",
            "type": "Documentation",
            "description": "Learn Java programming concepts and object-oriented development."
        },
        {
            "title": "Java Programming",
            "provider": "MOOC.fi",
            "url": "https://java-programming.mooc.fi/",
            "type": "Course",
            "description": "Practise Java through structured programming exercises."
        }
    ],

    "javascript": [
        {
            "title": "JavaScript Guide",
            "provider": "MDN",
            "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide",
            "type": "Documentation",
            "description": "Understand JavaScript syntax, functions, objects and modern language features."
        },
        {
            "title": "JavaScript Algorithms and Data Structures",
            "provider": "freeCodeCamp",
            "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures-v8/",
            "type": "Course",
            "description": "Develop practical JavaScript and problem-solving skills."
        }
    ],

    "html": [
        {
            "title": "HTML Learning Guide",
            "provider": "MDN",
            "url": "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Structuring_content",
            "type": "Documentation",
            "description": "Learn how to structure web pages using HTML."
        }
    ],

    "css": [
        {
            "title": "CSS Learning Guide",
            "provider": "MDN",
            "url": "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics",
            "type": "Documentation",
            "description": "Learn CSS styling, layouts and responsive design."
        },
        {
            "title": "Learn CSS",
            "provider": "freeCodeCamp",
            "url": "https://www.freecodecamp.org/learn/",
            "type": "Course",
            "description": "Practise styling web pages and building responsive interfaces."
        }
    ],

    "react": [
        {
            "title": "React Official Documentation",
            "provider": "React",
            "url": "https://react.dev/learn",
            "type": "Documentation",
            "description": "Learn React components, props, state and hooks."
        }
    ],

    "flask": [
        {
            "title": "Flask Official Documentation",
            "provider": "Pallets Projects",
            "url": "https://flask.palletsprojects.com/en/stable/",
            "type": "Documentation",
            "description": "Learn Flask routing, templates, request handling and application development."
        }
    ],

    "django": [
        {
            "title": "Django Official Tutorial",
            "provider": "Django",
            "url": "https://docs.djangoproject.com/en/stable/intro/tutorial01/",
            "type": "Documentation",
            "description": "Build web applications using Django."
        }
    ],

    "sql": [
        {
            "title": "SQL Tutorial",
            "provider": "SQLBolt",
            "url": "https://sqlbolt.com/",
            "type": "Interactive Course",
            "description": "Practise SQL queries, joins and database operations."
        },
        {
            "title": "PostgreSQL Tutorial",
            "provider": "PostgreSQL",
            "url": "https://www.postgresql.org/docs/current/tutorial.html",
            "type": "Documentation",
            "description": "Learn relational database concepts and SQL using PostgreSQL."
        }
    ],

    "postgresql": [
        {
            "title": "PostgreSQL Official Tutorial",
            "provider": "PostgreSQL",
            "url": "https://www.postgresql.org/docs/current/tutorial.html",
            "type": "Documentation",
            "description": "Learn relational database operations and PostgreSQL."
        }
    ],

    "machine learning": [
        {
            "title": "Machine Learning Specialization",
            "provider": "DeepLearning.AI and Stanford",
            "url": "https://www.coursera.org/specializations/machine-learning-introduction",
            "type": "Course",
            "description": "Study supervised learning, unsupervised learning and machine learning fundamentals."
        },
        {
            "title": "Scikit-learn User Guide",
            "provider": "Scikit-learn",
            "url": "https://scikit-learn.org/stable/user_guide.html",
            "type": "Documentation",
            "description": "Learn practical machine learning algorithms and model evaluation."
        }
    ],

    "deep learning": [
        {
            "title": "Deep Learning Specialization",
            "provider": "DeepLearning.AI",
            "url": "https://www.coursera.org/specializations/deep-learning",
            "type": "Course",
            "description": "Study neural networks, deep learning architectures and model optimisation."
        },
        {
            "title": "PyTorch Tutorials",
            "provider": "PyTorch",
            "url": "https://pytorch.org/tutorials/",
            "type": "Documentation",
            "description": "Learn to build and train deep learning models."
        }
    ],

    "data analysis": [
        {
            "title": "Data Analysis with Python",
            "provider": "freeCodeCamp",
            "url": "https://www.freecodecamp.org/learn/data-analysis-with-python/",
            "type": "Course",
            "description": "Learn data analysis using Python, Pandas and NumPy."
        }
    ],

    "pandas": [
        {
            "title": "Pandas Getting Started Tutorials",
            "provider": "Pandas",
            "url": "https://pandas.pydata.org/docs/getting_started/intro_tutorials/",
            "type": "Documentation",
            "description": "Learn data manipulation, cleaning and analysis."
        }
    ],

    "numpy": [
        {
            "title": "NumPy Learning Resources",
            "provider": "NumPy",
            "url": "https://numpy.org/learn/",
            "type": "Documentation",
            "description": "Learn numerical computing and array operations in Python."
        }
    ],

    "git": [
        {
            "title": "Git Book",
            "provider": "Git",
            "url": "https://git-scm.com/book/en/v2",
            "type": "Documentation",
            "description": "Learn version control, branching and collaboration using Git."
        }
    ],

    "github": [
        {
            "title": "GitHub Skills",
            "provider": "GitHub",
            "url": "https://skills.github.com/",
            "type": "Interactive Course",
            "description": "Practise repositories, collaboration and GitHub workflows."
        }
    ],

    "docker": [
        {
            "title": "Docker Getting Started",
            "provider": "Docker",
            "url": "https://docs.docker.com/get-started/",
            "type": "Documentation",
            "description": "Learn containers, images and application deployment."
        }
    ],

    "aws": [
        {
            "title": "AWS Skill Builder",
            "provider": "Amazon Web Services",
            "url": "https://skillbuilder.aws/",
            "type": "Learning Platform",
            "description": "Explore cloud computing and AWS services."
        }
    ],

    "cybersecurity": [
        {
            "title": "Introduction to Cybersecurity",
            "provider": "Cisco Networking Academy",
            "url": "https://www.netacad.com/courses/introduction-to-cybersecurity",
            "type": "Course",
            "description": "Learn cybersecurity fundamentals, threats and security principles."
        }
    ],

    "excel": [
        {
            "title": "Excel Training",
            "provider": "Microsoft",
            "url": "https://support.microsoft.com/en-us/excel",
            "type": "Documentation",
            "description": "Learn spreadsheet operations, formulas and data analysis."
        }
    ]
}


def normalise_skill(skill):
    """
    Standardise skill names for resource lookup.
    """

    if not skill:
        return ""

    return " ".join(str(skill).strip().lower().split())


def get_learning_resources(missing_skills, max_resources_per_skill=3):
    """
    Generate learning resource recommendations for missing skills.

    Known skills receive curated resources.
    Unknown skills receive a search link so that the application
    can still recommend learning materials.

    Returns a list of dictionaries.
    """

    recommendations = []

    if not missing_skills:
        return recommendations

    processed_skills = set()

    for skill in missing_skills:

        normalised_skill = normalise_skill(skill)

        if not normalised_skill:
            continue

        if normalised_skill in processed_skills:
            continue

        processed_skills.add(normalised_skill)

        resources = RESOURCE_CATALOG.get(normalised_skill, [])

        if resources:

            selected_resources = resources[:max_resources_per_skill]

        else:

            search_url = (
                "https://www.google.com/search?q="
                + quote_plus(
                    f"{normalised_skill} free online course tutorial"
                )
            )

            selected_resources = [
                {
                    "title": f"Learn {skill}",
                    "provider": "Learning resource search",
                    "url": search_url,
                    "type": "Search",
                    "description": (
                        f"Find online courses, tutorials and documentation "
                        f"to develop your {skill} skills."
                    )
                }
            ]

        recommendations.append({
            "skill": skill,
            "resources": selected_resources
        })

    return recommendations
