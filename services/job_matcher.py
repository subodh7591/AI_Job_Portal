
import json
import re

from datetime import datetime
from functools import lru_cache

import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_MODEL = "all-MiniLM-L6-v2"


# ============================================================
# 1. LOAD SEMANTIC MODEL
# ============================================================

@lru_cache(maxsize=2)
def load_semantic_model(model_name=DEFAULT_MODEL):

    try:

        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(model_name)

    except ImportError:

        raise ImportError(
            "Sentence Transformers is not installed. "
            "Run: pip install sentence-transformers numpy"
        )

    except Exception as error:

        raise RuntimeError(
            f"Could not load the semantic matching model: {error}"
        )


# ============================================================
# 2. NORMALISE TEXT
# ============================================================

def normalise_text(value):

    if not value:
        return ""

    value = str(value).lower()

    value = re.sub(
        r"[^a-z0-9+#.\s]",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# ============================================================
# 3. CONVERT VALUES INTO LISTS
# ============================================================

def convert_to_list(value):

    if not value:
        return []

    if isinstance(value, (list, tuple, set)):

        return [
            str(item).strip()
            for item in value
            if item and str(item).strip()
        ]

    if isinstance(value, str):

        value = value.strip()

        if not value:
            return []

        try:

            decoded = json.loads(value)

            if isinstance(decoded, list):
                return convert_to_list(decoded)

        except (json.JSONDecodeError, TypeError):
            pass

        return [
            item.strip()
            for item in re.split(r"[,;\n]", value)
            if item.strip()
        ]

    return [str(value).strip()]


# ============================================================
# 4. EXTRACT CANDIDATE INFORMATION
# ============================================================

def extract_candidate_information(parsed_resume):

    if isinstance(parsed_resume, str):

        try:
            parsed_resume = json.loads(parsed_resume)

        except json.JSONDecodeError:

            raise ValueError(
                "The parsed resume contains invalid JSON."
            )

    if not isinstance(parsed_resume, dict):

        raise ValueError(
            "Invalid candidate resume information."
        )

    professional_summary = parsed_resume.get(
        "professional_summary", ""
    )

    education = parsed_resume.get("education", [])

    experience = parsed_resume.get("experience", [])

    skills = convert_to_list(
        parsed_resume.get("skills", [])
    )

    certifications = convert_to_list(
        parsed_resume.get("certifications", [])
    )

    languages = convert_to_list(
        parsed_resume.get("languages", [])
    )

    # Extract education information.
    education_text = []

    for item in education:

        if isinstance(item, dict):

            education_text.extend([
                item.get("qualification", ""),
                item.get("institution", ""),
                item.get("year", ""),
                item.get("details", "")
            ])

        else:

            education_text.append(str(item))

    # Extract work experience.
    experience_text = []

    for item in experience:

        if isinstance(item, dict):

            experience_text.extend([
                item.get("job_title", ""),
                item.get("company", ""),
                item.get("duration", "")
            ])

            responsibilities = convert_to_list(
                item.get("responsibilities", [])
            )

            experience_text.extend(responsibilities)

        else:

            experience_text.append(str(item))

    # Construct candidate text.
    candidate_sections = [

        professional_summary,

        " ".join(skills),

        " ".join(education_text),

        " ".join(experience_text),

        " ".join(certifications),

        " ".join(languages)

    ]

    candidate_text = " ".join(
        str(section)
        for section in candidate_sections
        if section
    )

    return {

        "skills": skills,

        "education": education_text,

        "experience": experience_text,

        "professional_summary": professional_summary,

        "certifications": certifications,

        "languages": languages,

        "candidate_text": normalise_text(candidate_text)

    }


# ============================================================
# 5. EXTRACT JOB INFORMATION
# ============================================================

def extract_job_information(job):

    required_skills = convert_to_list(
        getattr(job, "required_skills", None)
    )

    preferred_skills = convert_to_list(
        getattr(job, "preferred_skills", None)
    )

    job_title = getattr(job, "title", "") or ""

    description = getattr(job, "description", "") or ""

    qualifications = getattr(job, "qualifications", "") or ""

    experience_level = getattr(
        job,
        "experience_level",
        ""
    ) or ""

    job_sections = [

        job_title,

        description,

        qualifications,

        experience_level,

        " ".join(required_skills),

        " ".join(preferred_skills)

    ]

    job_text = " ".join(
        str(section)
        for section in job_sections
        if section
    )

    return {

        "job_id": job.id,

        "job_title": job_title,

        "required_skills": required_skills,

        "preferred_skills": preferred_skills,

        "description": description,

        "qualifications": qualifications,

        "experience_level": experience_level,

        "job_text": normalise_text(job_text)

    }


# ============================================================
# 6. GENERATE AND STORE JOB EMBEDDINGS
# ============================================================

def generate_job_embedding(
    job,
    model_name=DEFAULT_MODEL
):

    job_information = extract_job_information(job)

    job_text = job_information["job_text"]

    if not job_text:

        raise ValueError(
            f"Job {job.id} does not contain enough information "
            "to generate an embedding."
        )

    model = load_semantic_model(model_name)

    embedding = model.encode(

        job_text,

        convert_to_numpy=True,

        normalize_embeddings=True

    )

    return embedding.astype(float).tolist()


def prepare_job_embedding(
    job,
    model_name=DEFAULT_MODEL
):

    """
    Generate an embedding and assign it to the Job object.

    The calling route is responsible for committing
    the database transaction.
    """

    embedding = generate_job_embedding(
        job,
        model_name
    )

    job.job_embedding = embedding

    job.embedding_model = model_name

    job.embedding_generated_at = datetime.utcnow()

    return embedding


# ============================================================
# 7. READ A STORED JOB EMBEDDING
# ============================================================

def get_stored_job_embedding(job):

    embedding = getattr(
        job,
        "job_embedding",
        None
    )

    if not embedding:
        return None

    # Support both JSON lists and JSON strings.
    if isinstance(embedding, str):

        try:
            embedding = json.loads(embedding)

        except json.JSONDecodeError:
            return None

    try:

        embedding = np.asarray(
            embedding,
            dtype=np.float32
        )

        if embedding.ndim != 1:
            return None

        if embedding.size == 0:
            return None

        if not np.all(np.isfinite(embedding)):
            return None

        return embedding

    except (TypeError, ValueError):

        return None


# ============================================================
# 8. GENERATE CANDIDATE EMBEDDING
# ============================================================

def generate_candidate_embedding(
    candidate_text,
    model_name=DEFAULT_MODEL
):

    if not candidate_text:
        return None

    model = load_semantic_model(model_name)

    embedding = model.encode(

        candidate_text,

        convert_to_numpy=True,

        normalize_embeddings=True

    )

    return np.asarray(
        embedding,
        dtype=np.float32
    )


# ============================================================
# 9. CALCULATE COSINE SIMILARITY
# ============================================================

def cosine_similarity_percentage(
    candidate_embedding,
    job_embedding
):

    if candidate_embedding is None or job_embedding is None:
        return 0.0

    if candidate_embedding.shape != job_embedding.shape:
        return 0.0

    similarity = float(
        np.dot(
            candidate_embedding,
            job_embedding
        )
    )

    # Convert cosine similarity into a non-negative
    # percentage score for presentation.
    #
    # Negative cosine similarities are treated as zero.
    # A similarity of 1.0 becomes 100%.

    score = max(0.0, min(1.0, similarity)) * 100

    return round(score, 2)


# ============================================================
# 10. IDENTIFY MATCHED AND MISSING SKILLS
# ============================================================

def compare_skills(
    candidate_skills,
    job_skills,
    candidate_text
):

    matched_skills = []

    missing_skills = []

    candidate_skill_values = {

        normalise_text(skill)

        for skill in candidate_skills

    }

    for skill in job_skills:

        normalised_skill = normalise_text(skill)

        if not normalised_skill:
            continue

        is_matched = (
            normalised_skill in candidate_skill_values
        )

        if not is_matched:

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(normalised_skill)
                + r"(?![a-z0-9])"
            )

            is_matched = bool(
                re.search(pattern, candidate_text)
            )

        if is_matched:
            matched_skills.append(skill)

        else:
            missing_skills.append(skill)

    return {

        "matched_skills": matched_skills,

        "missing_skills": missing_skills

    }


# ============================================================
# 11. CALCULATE KEYWORD MATCH SCORE
# ============================================================

def calculate_keyword_score(
    candidate_information,
    job_information
):

    candidate_skills = candidate_information["skills"]

    candidate_text = candidate_information["candidate_text"]

    required_skills = job_information["required_skills"]

    preferred_skills = job_information["preferred_skills"]

    required_result = compare_skills(
        candidate_skills,
        required_skills,
        candidate_text
    )

    preferred_result = compare_skills(
        candidate_skills,
        preferred_skills,
        candidate_text
    )

    matched_required = required_result["matched_skills"]

    missing_required = required_result["missing_skills"]

    matched_preferred = preferred_result["matched_skills"]

    if required_skills:

        required_score = (
            len(matched_required) / len(required_skills)
        ) * 100

    else:

        required_score = None

    if preferred_skills:

        preferred_score = (
            len(matched_preferred) / len(preferred_skills)
        ) * 100

    else:

        preferred_score = None

    if required_score is not None and preferred_score is not None:

        keyword_score = (
            required_score * 0.80
            +
            preferred_score * 0.20
        )

    elif required_score is not None:

        keyword_score = required_score

    elif preferred_score is not None:

        keyword_score = preferred_score

    else:

        keyword_score = None

    return {

        "keyword_score": (
            round(keyword_score, 2)
            if keyword_score is not None
            else None
        ),

        "matched_skills": matched_required,

        "missing_skills": missing_required,

        "matched_preferred_skills": matched_preferred,

        "required_skill_score": (
            round(required_score, 2)
            if required_score is not None
            else None
        ),

        "preferred_skill_score": (
            round(preferred_score, 2)
            if preferred_score is not None
            else None
        )

    }


# ============================================================
# 12. CALCULATE SEMANTIC SCORE FOR TWO TEXTS
# ============================================================

def calculate_semantic_score(
    candidate_text,
    job_text,
    model_name=DEFAULT_MODEL
):

    if not candidate_text or not job_text:
        return 0.0

    model = load_semantic_model(model_name)

    embeddings = model.encode(

        [
            candidate_text,
            job_text
        ],

        convert_to_numpy=True,

        normalize_embeddings=True

    )

    return cosine_similarity_percentage(
        embeddings[0],
        embeddings[1]
    )


# ============================================================
# 13. MATCH ONE JOB AGAINST A RESUME
# ============================================================

def match_single_job(
    parsed_resume,
    job,
    model_name=DEFAULT_MODEL
):

    candidate_information = extract_candidate_information(
        parsed_resume
    )

    job_information = extract_job_information(job)

    keyword_results = calculate_keyword_score(
        candidate_information,
        job_information
    )

    # Use the stored job embedding where available.
    job_embedding = get_stored_job_embedding(job)

    # Generate one only if it has not been stored yet.
    if (
        job_embedding is None
        or getattr(job, "embedding_model", None) != model_name
    ):

        job_embedding = np.asarray(
            generate_job_embedding(job, model_name),
            dtype=np.float32
        )

    candidate_embedding = generate_candidate_embedding(
        candidate_information["candidate_text"],
        model_name
    )

    semantic_score = cosine_similarity_percentage(
        candidate_embedding,
        job_embedding
    )

    return {

        "job_id": job_information["job_id"],

        "job_title": job_information["job_title"],

        "keyword_score": keyword_results["keyword_score"],

        "semantic_score": semantic_score,

        "matched_skills": keyword_results["matched_skills"],

        "missing_skills": keyword_results["missing_skills"],

        "matched_preferred_skills": (
            keyword_results["matched_preferred_skills"]
        ),

        "required_skill_score": (
            keyword_results["required_skill_score"]
        ),

        "preferred_skill_score": (
            keyword_results["preferred_skill_score"]
        )

    }


# ============================================================
# 14. MATCH ALL AVAILABLE JOBS
# ============================================================

def match_jobs(
    parsed_resume,
    jobs,
    method="semantic",
    model_name=DEFAULT_MODEL,
    top_n=None
):

    if method not in {"keyword", "semantic"}:

        raise ValueError(
            "Method must be either 'keyword' or 'semantic'."
        )

    candidate_information = extract_candidate_information(
        parsed_resume
    )

    candidate_text = candidate_information["candidate_text"]

    results = []

    # --------------------------------------------------------
    # KEYWORD MATCHING
    # --------------------------------------------------------

    if method == "keyword":

        for job in jobs:

            job_information = extract_job_information(job)

            keyword_results = calculate_keyword_score(
                candidate_information,
                job_information
            )

            score = keyword_results["keyword_score"]

            if score is None:
                score = 0.0

            results.append({

                "job": job,

                "job_id": job_information["job_id"],

                "job_title": job_information["job_title"],

                "match_score": round(score, 2),

                "method": method,

                "keyword_score": keyword_results["keyword_score"],

                "semantic_score": None,

                "matched_skills": keyword_results["matched_skills"],

                "missing_skills": keyword_results["missing_skills"],

                "matched_preferred_skills": (
                    keyword_results["matched_preferred_skills"]
                )

            })

    # --------------------------------------------------------
    # SEMANTIC MATCHING
    # --------------------------------------------------------

    else:

        if not candidate_text:

            raise ValueError(
                "The candidate resume does not contain enough "
                "information for semantic matching."
            )

        model = load_semantic_model(model_name)

        # Encode the candidate only once.
        candidate_embedding = generate_candidate_embedding(
            candidate_text,
            model_name
        )

        valid_jobs = []

        job_embeddings = []

        job_information_list = []

        keyword_results_list = []

        for job in jobs:

            # Only use jobs with a stored embedding
            # generated by the currently selected model.
            if (
                getattr(job, "embedding_model", None)
                != model_name
            ):
                continue

            job_embedding = get_stored_job_embedding(job)

            if job_embedding is None:
                continue

            # Check that the embedding dimensions match.
            if (
                job_embedding.shape
                != candidate_embedding.shape
            ):
                continue

            job_information = extract_job_information(job)

            keyword_results = calculate_keyword_score(
                candidate_information,
                job_information
            )

            valid_jobs.append(job)

            job_embeddings.append(job_embedding)

            job_information_list.append(job_information)

            keyword_results_list.append(keyword_results)

        # Calculate similarities in one vectorised operation.
        if job_embeddings:

            embedding_matrix = np.vstack(job_embeddings)

            similarity_scores = np.dot(
                embedding_matrix,
                candidate_embedding
            )

            # Convert cosine similarities to percentages.
            similarity_scores = np.clip(
                similarity_scores,
                0.0,
                1.0
            ) * 100

            for index, job in enumerate(valid_jobs):

                job_information = job_information_list[index]

                keyword_results = keyword_results_list[index]

                score = round(
                    float(similarity_scores[index]),
                    2
                )

                results.append({

                    "job": job,

                    "job_id": job_information["job_id"],

                    "job_title": job_information["job_title"],

                    "match_score": score,

                    "method": method,

                    "keyword_score": keyword_results["keyword_score"],

                    "semantic_score": score,

                    "matched_skills": (
                        keyword_results["matched_skills"]
                    ),

                    "missing_skills": (
                        keyword_results["missing_skills"]
                    ),

                    "matched_preferred_skills": (
                        keyword_results["matched_preferred_skills"]
                    )

                })

    # --------------------------------------------------------
    # SORT RESULTS
    # --------------------------------------------------------

    results.sort(

        key=lambda item: item["match_score"],

        reverse=True

    )

    if top_n is not None:

        results = results[:top_n]

    return results



# ============================================================
# 15. GENERATE AI JOB SKILL GAP REPORT
# ============================================================

def calculate_skill_gap(parsed_resume, job):
    """
    Generate a skill gap report by comparing a candidate's
    stored resume information with a job's requirements.

    This function does not call Gemini or generate embeddings.
    It uses the structured resume JSON and job information
    already stored in the database.
    """

    # Extract candidate information from the parsed resume.
    candidate_information = extract_candidate_information(
        parsed_resume
    )

    # Extract job requirements.
    job_information = extract_job_information(job)

    candidate_skills = candidate_information["skills"]
    candidate_text = candidate_information["candidate_text"]

    required_skills = job_information["required_skills"]
    preferred_skills = job_information["preferred_skills"]

    # Compare candidate skills against required skills.
    required_result = compare_skills(
        candidate_skills,
        required_skills,
        candidate_text
    )

    # Compare candidate skills against preferred skills.
    preferred_result = compare_skills(
        candidate_skills,
        preferred_skills,
        candidate_text
    )

    matched_required = required_result["matched_skills"]
    missing_required = required_result["missing_skills"]

    matched_preferred = preferred_result["matched_skills"]
    missing_preferred = preferred_result["missing_skills"]

    # Calculate required skill coverage.
    if required_skills:
        required_skill_score = round(
            (len(matched_required) / len(required_skills)) * 100,
            2
        )
    else:
        required_skill_score = None

    # Calculate preferred skill coverage.
    if preferred_skills:
        preferred_skill_score = round(
            (len(matched_preferred) / len(preferred_skills)) * 100,
            2
        )
    else:
        preferred_skill_score = None

    # Return the complete skill gap report.
    return {
        "job_id": job_information["job_id"],
        "job_title": job_information["job_title"],

        "candidate_skills": candidate_skills,

        "required_skills": required_skills,
        "preferred_skills": preferred_skills,

        "matched_required_skills": matched_required,
        "missing_required_skills": missing_required,

        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,

        "required_skill_score": required_skill_score,
        "preferred_skill_score": preferred_skill_score,

        "total_required_skills": len(required_skills),
        "total_preferred_skills": len(preferred_skills),

        "matched_required_count": len(matched_required),
        "missing_required_count": len(missing_required),

        "matched_preferred_count": len(matched_preferred),
        "missing_preferred_count": len(missing_preferred)
    }



