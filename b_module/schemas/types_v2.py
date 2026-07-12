from __future__ import annotations

from typing import List, Literal, TypedDict, Optional


RouteType = Literal["uniform_exam", "free_layout_homework"]
CoordinateBase = Literal["page_image", "preprocessed_image"]
BBoxSource = Literal["ocr", "estimated", "rendered"]
SourceMode = Literal["ocr", "text_extract", "image_marker"]
DecisionSource = Literal["rule", "llm", "human", "rule_fallback"]


class FileTask(TypedDict, total=False):
    file_id: str
    submission_id: str
    origin_name: str
    ext: str
    mime_type: str
    storage_path: str
    file_size: int
    page_count: int
    source_type: str
    parse_mode: str
    task_status: str
    created_at: str
    error_message: str


class NormalizedPage(TypedDict, total=False):
    file_id: str
    page_no: int
    page_image_path: str
    preprocessed_image_path: str
    original_width: int
    original_height: int
    processed_width: int
    processed_height: int
    dpi: int
    coordinate_base: CoordinateBase
    transform_matrix: Optional[list[list[float]]]
    rotation_degree: float
    has_perspective_fix: bool
    preprocess_steps: List[str]


class OCRBlockBase(TypedDict):
    block_id: str
    bbox: List[float]
    bbox_source: BBoxSource
    source_mode: SourceMode
    text: str
    confidence: float
    reading_order: int
    is_low_confidence: bool


class OCRBlock(OCRBlockBase, total=False):
    line_index: int
    block_type: str
    image_id: str
    image_path: str
    parent_block_id: str


class OCRPageResultBase(TypedDict):
    file_id: str
    page_no: int
    image_path: str
    width: int
    height: int
    dpi: int
    coordinate_base: CoordinateBase
    ocr_engine: str
    blocks: List[OCRBlock]


class OCRPageResult(OCRPageResultBase, total=False):
    overall_confidence: float


class RouteDecisionBase(TypedDict):
    file_id: str
    route_type: RouteType
    reason: str


class RouteDecision(RouteDecisionBase, total=False):
    template_id: Optional[str]


class QuestionCandidateBase(TypedDict):
    question_no: str
    page_no: int
    block_ids: List[str]
    text: str
    split_confidence: float
    needs_review: bool


class QuestionCandidate(QuestionCandidateBase, total=False):
    file_id: str
    route_type: RouteType
    paragraph_ids: List[str]
    paragraph_role: str
    start_block_id: str
    end_block_id: str
    start_anchor_bbox: List[float]
    end_anchor_bbox: List[float]
    page_height: int
    page_width: int
    heading_confidence: float
    heading_source: str
    issue_flags: List[str]
    risk_flags: List[str]
    decision_source: DecisionSource
    semantic_confidence: float
    semantic_reason: str
    question_id: str
    section_no: Optional[str]
    section_label: Optional[str]
    section_context: str
    section_context_block_ids: List[str]


class MergedQuestionBase(TypedDict):
    merge_group_id: str
    question_no: str
    from_pages: List[int]
    merged_text: str
    merge_confidence: float
    needs_review: bool


class MergedQuestion(MergedQuestionBase, total=False):
    file_id: str
    route_type: RouteType
    source_candidate_indexes: List[int]
    merge_evidence: List[str]
    issue_flags: List[str]
    decision_source: DecisionSource
    semantic_confidence: float
    semantic_reason: str
    question_id: str
    section_no: Optional[str]
    section_label: Optional[str]
    section_context: str
    section_context_block_ids: List[str]


class ReviewResultBase(TypedDict):
    review_id: str
    file_id: str
    question_no: str
    before_text: str
    after_text: str
    operator_id: str
    review_time: str


class ReviewResult(ReviewResultBase, total=False):
    merge_group_id: str
    review_reason: str


class QuestionLevelResultBase(TypedDict):
    question_no: str
    route_type: RouteType
    page_nos: List[int]
    ocr_text: str
    final_text: str
    confidence: float
    needs_review: bool


class QuestionLevelResult(QuestionLevelResultBase, total=False):
    corrected_text: str
    merge_group_id: str
    file_id: str
    decision_source: DecisionSource
    semantic_confidence: float
    semantic_reason: str
    risk_flags: List[str]
    question_id: str
    section_no: Optional[str]
    section_label: Optional[str]
    section_context: str
    section_context_block_ids: List[str]
