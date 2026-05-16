"""
Thought-Retriever: Don't Just Retrieve Raw Data, Retrieve Thoughts

A universal thought memory system for LLM-based agents.
Based on the paper by UIUC, MIT & CMU (TMLR 2026).
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="thought-retriever",
    version="1.0.0",
    description="Self-evolving long-term memory for LLM agents via thought retrieval",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Thought-Retriever Contributors",
    url="https://github.com/mhx0628/thought-retriever",
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*"]),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
    ],
    install_requires=[
        "numpy>=1.21.0",
    ],
    extras_require={
        "full": [
            "sentence-transformers>=2.2.0",
            "scikit-learn>=1.0.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "sentence-transformers>=2.2.0",
        ],
    },
    python_requires=">=3.8",
    keywords="llm, rag, memory, agent, retrieval-augmented, thought-retriever",
    project_urls={
        "Paper": "https://arxiv.org/abs/2604.12231",
        "GitHub": "https://github.com/mhx0628/thought-retriever",
        "Gitee": "https://gitee.com/ma-hongxing-1/thought-retriever",
        "HuggingFace": "https://huggingface.co/spaces/star0628/thought-retriever",
    },
)