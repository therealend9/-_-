# Exam Review Product Team Work Plan

## 1. Scope

This phase covers the university ideological-political final-exam workflow:

- Question paper: recognize free-layout questions and return `questions[]`.
- Blank answer sheet: generate, review, publish, and bind a fixed template.
- Completed student answer sheet: align pages, crop fixed regions, detect blank areas, recognize handwriting, and return `answers[]`.
- Organize materials by `question_id` and hand them to the grading module.

The grading module owner remains unchanged. This recognition module does not process standalone answer-key files, objective questions, scoring rules, or anti-cheating decisions.

## 2. Product Requirements

- Support batch exam-file processing.
- Split and organize content by the questions in the exam paper.
- Provide two frontend views for each grading task: an exam-paper view and an AI-grading-suggestion view.
- Allow the user to click a question and switch between those two views.
- The grading owner controls the suggestion content, student-answer labels, and abnormal-detection indicators.

## 3. Person 1: Grading Module Owner

### Development

- Keep ownership of grading rules, scoring, annotations, suggestions, and grading status.
- Define the grading input contract using `exam_id`, `question_id`, `question_text`, `answer_text`, `is_blank`, confidence, review flags, image references, student-answer labels, and abnormal-detection fields already implemented locally.
- Adapt the grading module to consume recognition output by `question_id`.
- Maintain the existing grading status and local student-answer/abnormal-detection implementation.
- Implement question-detail data for the frontend's exam-paper view and AI-suggestion view.
- Preserve manual score and annotation changes after refresh or re-entry.

### Testing

- Verify that the same `question_id` always enters the same grading item.
- Verify blank and low-confidence answers enter manual review.
- Verify duplicate submissions do not create duplicate grading records.
- Verify existing student-answer labels and abnormal-detection fields remain available after refresh and batch processing.
- Provide unit tests, contract tests, and mock grading data containing the existing student-answer labels and abnormal-detection fields.

### Deliverables

- Grading input/output API document.
- `question_id` adapter.
- Existing grading status and question-detail APIs.
- Unit, contract, and regression tests.

### Ownership Boundary

Do not modify OCR, template detection, page alignment, or frontend layout code.

## 4. Person 2: Recognition Backend Owner

### Development

- Maintain free-layout `question_paper` recognition.
- Maintain blank answer-sheet template creation, manual review, publishing, and exam binding.
- Maintain completed `answer_sheet` recognition: alignment, fixed-region cropping, blank detection, handwriting OCR, and multi-region merging.
- Guarantee that the question paper, template regions, student answers, and grading records use the same `question_id`.
- Maintain `exam-document.v1`, API documentation, error codes, and review fields.
- Provide an adapter for the grading input contract without implementing scoring.

### Testing

- Blank answer sheet generates a draft and accepts manually adjusted regions.
- Reject missing exams, unpublished templates, missing versions, mismatched question IDs, and invalid template changes.
- Question paper returns question text, number, page, confidence, and review flags.
- Student answer sheet returns `answers[]`, including blank areas and handwriting areas.
- Cover multi-page files, multiple regions for one question, rotation, page offset, blank areas, low confidence, OCR failure, and alignment failure.
- Keep input files, templates, crops, JSON output, and expected results as regression artifacts.
- Verify unsupported `answer_key` requests are rejected.

### Deliverables

- Running recognition API and CLI entrypoint.
- JSON Schema, API document, and error-code document.
- Test samples and expected outputs for all three scenarios.
- Unit, API, and regression test reports.

### Ownership Boundary

Do not implement grading, answer comparison, or grading suggestions.

## 5. Person 3: Frontend and Integration Owner

### Development

- Exam list: show exam name, status, template name, and template version.
- Exam creation and question-paper import: upload, show recognized questions, confidence, page numbers, and manual-review flags.
- Blank-template editor: show pages and candidate regions; support move, resize, delete, add, question-ID selection, save, publish, bind, and confirmation dialogs.
- Student-answer import: batch-select files, select an exam, show per-file processing status, retry failures, and enter manual review.
- Question workspace: provide two pages or tabs for each question:
  - Exam-paper view: show the original question and relevant exam-paper context.
  - AI-grading-suggestion view: display the grading result and suggestion fields returned by the grading module.
- Pass through and display the student-answer labels and abnormal-detection indicators already provided by the grading module; do not recreate their logic in the frontend.
- Add loading, empty, success, failed, low-confidence, template-not-bound, and dependency-error states.
- Integrate with the grading APIs without duplicating grading rules.

### Testing

- Run the complete flow: create exam, import question paper, create and publish template, import student answer sheet, and enter grading workspace.
- Verify exam names are shown instead of raw IDs.
- Reopen a reviewed template and verify region positions, question IDs, and versions are preserved.
- Verify frontend never uses array index, printed number, or `question_no` as the cross-module key.
- Verify one failed batch file does not block other files.
- Verify the exam-paper view and AI-suggestion view never mix different questions.
- Verify suggestion text, student-answer labels, and abnormal-detection indicators are displayed from the grading API without frontend reinterpretation.
- Test desktop layout and essential narrow-screen behavior.
- Run frontend tests with mock APIs and one end-to-end test with real samples.

### Deliverables

- Exam management, question import, template review, student answer import, and grading-workspace pages.
- API client and unified error handling.
- Component, page-flow, and end-to-end test reports.
- Integration issue list and user operation guide.

### Ownership Boundary

Do not change grading rules or bypass backend template, version, and question-ID validation.

## 6. Code Ownership

| Area | Owner | Collaboration |
|---|---|---|
| Grading code and grading APIs | Person 1 | Person 2 provides input adapter; Person 3 consumes APIs |
| OCR, segmentation, template, alignment, registry | Person 2 | Person 3 provides frontend needs; Person 1 confirms grading contract |
| Recognition API and Schema | Person 2 | Persons 1 and 3 review contract |
| Frontend application | Person 3 | Persons 1 and 2 review workflows |
| Test samples and end-to-end outputs | Person 2 | Person 3 runs UI tests; Person 1 runs grading regression |

Each shared file has one owner. Other members submit changes through issues or separate branches instead of overwriting the owner’s work.

## 7. Shared Contract

The only cross-module key is:

```text
questions[].question_id == answers[].question_id == grading_record.question_id
```

Minimum student-answer item:

```json
{
  "exam_id": "mayuan_1516",
  "submission_id": "student_001",
  "question_id": "2.1",
  "question_no": "2.1",
  "answer_text": "student answer text",
  "is_blank": false,
  "confidence": 0.83,
  "needs_review": false,
  "risk_flags": []
}
```

The frontend and grading module must not depend on recognition-module intermediate data.

## 8. Milestones

### M1: Contract Freeze

- Person 1 provides grading input/output fields and mock data.
- Person 2 confirms API, Schema, errors, and sample outputs.
- Person 3 creates page routes and mock data adapters.

Acceptance: all three members confirm field meanings and `question_id` rules.

### M2: Parallel Development

- Person 1 completes existing grading status handling and question details.
- Person 2 completes the three recognition scenarios and backend tests.
- Person 3 completes the frontend page skeleton and mock workflow.

Acceptance: frontend runs with mocks; backend runs the three scenarios from CLI/API.

### M3: Integration

- Person 3 connects the real recognition API.
- Person 1 connects recognition results to grading.
- Person 2 fixes contract, status, and error issues found during integration.

Acceptance: one real sample completes the path from question paper to grading workspace.

### M4: Joint Acceptance

Test normal flow, blank card, completed card, low confidence, unbound template, mismatched IDs, partial batch failure, duplicate submission, refresh recovery, and manual review.

Acceptance: no blocking defects; all risky results can enter manual review; JSON and grading input pass contract validation.

## 9. Pre-Integration Checklist

- [ ] Person 1 delivered grading contract and mock data.
- [ ] Person 2 delivered API address, Schema, samples, and expected outputs.
- [ ] Person 3 completed page skeleton and mock integration.
- [ ] Exam-name, template-name, and version display rules are confirmed.
- [ ] The two frontend views are confirmed as "试卷" and "AI 批改建议".
- [ ] The grading owner confirms the existing suggestion, student-answer label, and abnormal-detection fields that the frontend must display.
- [ ] Real test samples are stored and脱敏 requirements are confirmed.
