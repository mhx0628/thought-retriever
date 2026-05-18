# Changelog

All notable changes to Thought-Retriever will be documented in this file.

## [2.0.0] - 2025-05-19

### Added
- 🇨🇳 **Chinese Embedding Engine**: jieba tokenization + TF-IDF embedder (`_JiebaTfidfEmbedder`)
  - Auto-detected as priority backend after sentence-transformers
  - 3-5x better semantic similarity for Chinese text vs character n-gram TF-IDF
  - Fully offline, no model download required
  - Vocabulary caching for consistent embedding dimensions

- 🇨🇳 **Chinese Prompt Templates**: `thought_confidence_prompt_zh()` and `answer_generation_prompt_zh()`
  - Auto language detection based on Chinese character ratio
  - Configurable via `ThoughtConfig(language="zh")`

- 🧹 **Smart Message Filtering**: `should_generate_thought()` utility
  - Skip short/meaningless messages (e.g., "嗯", "好", "ok")
  - 7 regex patterns for filtering noise

- 🧹 **Thought Content Cleaning**: Auto-remove LLM output labels
  - Clean `[知识点]：`, `[提炼的知识点]` etc. from thought content

- 📊 **Language Configuration**: `ThoughtConfig.language` and `ThoughtConfig.thought_prompt_lang`
  - `auto`: Auto-detect based on Chinese character ratio
  - `zh`: Force Chinese prompts
  - `en`: Force English prompts

- 🔧 **Public API Extensions**:
  - `ThoughtStore.clear_knowledge()` public method
  - Export `ThoughtStore`, `EmbeddingEngine`, `generate_id`, `timestamp_now`, `chunk_text` from package

- 🛡 **Robust Response Parsing**: Enhanced `_parse_thought_response()`
  - Support Chinese "是/否/有效/无效" in addition to "1/0"
  - Fallback: treat multi-line content as valid if ≥5 chars

### Changed
- **Embedding Backend Priority**: sentence-transformers → jieba_tfidf → tfidf → hash
- **JiebaTfidfEmbedder**: Vocabulary and IDF cached after first encode, reused in subsequent calls
- **setup.py**: Added `jieba>=0.42.1` to core dependencies
- **Minimum Python version**: 3.8 (unchanged)

### Fixed
- Fixed embedding dimension inconsistency when jieba_tfidf rebuilds vocabulary each call
- Fixed `_parse_thought_response` failing on Chinese LLM output formats
- Fixed `ThoughtMemory.clear()` directly accessing private `_knowledge` attribute

## [1.0.0] - 2025-05-15

### Added
- Initial release based on TMLR 2026 paper
- 5-step pipeline: Retrieval → Answer → Thought → Merge → Update
- Dual filtering: confidence (ci) + redundancy (si)
- 3-tier embedding fallback: sentence-transformers → TF-IDF → hash
- JSON file persistence
- Trae AI IDE Skill integration
