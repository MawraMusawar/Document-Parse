"""Strict Pydantic models for structured resume representation."""

from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class PersonalInfo(BaseModel):
    """Personal contact information extracted from the resume."""

    full_name: str = Field(..., description="Candidate's full legal or professional name")
    email: Optional[EmailStr] = Field(None, description="Validated email address of the candidate")
    phone: Optional[str] = Field(None, description="Contact telephone or mobile number")
    location: Optional[str] = Field(None, description="Candidate's current location (e.g., City, State, Country)")
    linkedin_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    github_url: Optional[str] = Field(None, description="GitHub profile URL")
    portfolio_url: Optional[str] = Field(None, description="Personal website or portfolio URL")


class EducationItem(BaseModel):
    """Individual academic degree or institutional qualification."""

    institution: str = Field(..., description="Name of the university, college, or school")
    degree: str = Field(..., description="Degree obtained or pursued (e.g., Bachelor of Science, Master of Arts)")
    field_of_study: Optional[str] = Field(None, description="Academic major or department (e.g., Computer Science)")
    start_year: Optional[int] = Field(None, description="Starting calendar year of education (e.g., 2018)")
    end_year: Optional[int] = Field(None, description="Graduation calendar year (e.g., 2022)")
    grade_or_gpa: Optional[str] = Field(None, description="Achieved GPA, percentage, or honors distinction")


class ExperienceItem(BaseModel):
    """Professional work experience entry."""

    company: str = Field(..., description="Company, organization, or employer name")
    role: str = Field(..., description="Job title or designation")
    location: Optional[str] = Field(None, description="Job location or Remote")
    start_date: Optional[str] = Field(None, description="Start date (e.g., 'Jan 2022' or '2022')")
    end_date: Optional[str] = Field(None, description="End date (e.g., 'Present' or 'Dec 2023')")
    is_current: bool = Field(default=False, description="True if candidate currently holds this position")
    responsibilities: List[str] = Field(
        default_factory=list,
        description="Key responsibilities, achievements, and impact statements",
    )
    technologies: List[str] = Field(
        default_factory=list,
        description="List of tools, programming languages, and frameworks used in this role",
    )


class SkillSet(BaseModel):
    """Categorized professional competencies and skills."""

    technical_skills: List[str] = Field(
        default_factory=list,
        description="Core programming languages, frameworks, libraries, and databases",
    )
    soft_skills: List[str] = Field(
        default_factory=list,
        description="Interpersonal and management skills (e.g., Leadership, Problem Solving)",
    )
    tools_and_platforms: List[str] = Field(
        default_factory=list,
        description="Development and collaboration platforms (e.g., Git, Docker, AWS, Jira)",
    )
    languages: List[str] = Field(
        default_factory=list,
        description="Natural languages spoken by the candidate",
    )


class CertificationItem(BaseModel):
    """Professional license or credential."""

    title: str = Field(..., description="Name of the certification or credential")
    issuer: str = Field(..., description="Issuing organization or authority (e.g., AWS, Microsoft, Coursera)")
    year: Optional[int] = Field(None, description="Calendar year when credential was earned")


class ParsedResume(BaseModel):
    """Root model representing the entire structured resume document."""

    summary: Optional[str] = Field(
        None,
        description="Executive summary or professional bio extracted or synthesized from the resume",
    )
    personal_info: PersonalInfo = Field(..., description="Candidate contact details")
    total_years_experience: Optional[float] = Field(
        None,
        ge=0,
        description="Estimated total professional experience in years",
    )
    skills: SkillSet = Field(default_factory=SkillSet, description="Categorized skillset")
    work_experience: List[ExperienceItem] = Field(
        default_factory=list,
        description="Chronological work history",
    )
    education: List[EducationItem] = Field(
        default_factory=list,
        description="Academic qualifications",
    )
    certifications: List[CertificationItem] = Field(
        default_factory=list,
        description="Professional certifications and credentials",
    )
