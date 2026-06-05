# Learning Improvement Report

**Document ID:** `lecture_1_engineering_0c84691b8030`

## Learned Patterns

- **[factual_correction]** Always include a 'Recording date' field in the 'Property Description' section of a title review. _(context: The recording date is a fundamental piece of information for legal title reviews. Even when specific evidence for the property description is insufficient, this field should be explicitly addressed, indicating where the information can be found or why it's missing.)_

## Run Comparison

| Metric | Run 1 | Run 2 |
|--------|-------|-------|
| Used learning | no | yes |
| Word count | 518 | 413 |
| Pattern rules applied (heuristic) | 1 | 2 |
| Improvement score | — | 100% |

### Assessment

Run 2 incorporates more learned operator preferences than Run 1, demonstrating measurable improvement from the edit feedback loop.

### Run 1 excerpt

```
## Title Review Summary

### Property Description
INSUFFICIENT EVIDENCE. The provided evidence describes types of projects engineers work on, such as structural designs for public infrastructure like bridges or highways, government infrastructure projects like national highways, and buildings [lecture_1_engineering_0c84691b8030:23:chunk_0016, lecture_1_engineering_0c84691b8030:23:chunk_0015, lecture_1_engineering_0c84691b8030:21:chunk_0013]. It does not provide a specific legal description of a property.

### Chain of Title
INSUFFICIENT EVIDENCE. The provided evidence discusses professional engineering certifications and the ability of engineers to sign technical documents [lecture_1_engineering_0c84691b8030:23:chunk_0016, lecture_1_engineering_0c84691b8030:23:chunk_0015]. It also mentions engineering as a profession regulated by professional bodies [lecture_1_engineering_0c84691b8030:19:chunk_0010]. This information pertains to professional qualifications and responsibilities, not the historical ownership transfers of a specific property.

### Exceptions and Encumbrances
INSUFFICIENT EVIDENCE. The evidence outlines professional requirements and ethical obligations for engineers, such as obtaining a professional license (e.g., PE in the US, CE in India) to legally practice and sign off on projects [lecture_1_engineering_0c84691b8030:22:chunk_0014, lecture_1_engineering_0c84691b8030:23:chunk_0016, lecture_1_engineering_0c84691b8030:23:chunk_0015]. It also notes that engineers 
```

### Run 2 excerpt

```
## Title Review Summary

### Property Description
INSUFFICIENT EVIDENCE. The provided documents discuss engineering certifications and responsibilities, not specific property descriptions.
Recording date: See county recording records for exact filed date.

### Chain of Title
INSUFFICIENT EVIDENCE. The provided documents discuss professional engineering as a profession, including licensing and regulation by professional bodies, but do not contain information regarding the historical ownership transfers of any specific property [lecture_1_engineering_0c84691b8030_chunk_0010], [lecture_1_engineering_0c84691b8030_chunk_0015], [lecture_1_engineering_0c84691b8030_chunk_0016].

### Exceptions and Encumbrances
The ability to develop or modify property may be subject to regulatory requirements concerning professional engineering certifications. Specifically:
*   Engineers are required to obtain a professional license (e.g., PE – Professional Engineer) to legally practice and sign off on projects, ensuring competence and experience [lecture_1_engineering_0c84691b8030_chunk_0014].
*   In the United States, a civil engineer must obtain a Professional Engineer (PE) license to approve structural designs for public infrastructure like bridges or highways. Without this certification, they are not legally allowed to sign off on critical design documents submitted to government authorities for construction approval [lecture_1_engineering_0c84691b8030_chunk_0016].
*   Engineers are trusted to a
```

## How to reproduce

```bash
python -m src draft --doc-id <id> --run-label run1
python -m src learn --draft-id <draft_id> --edited-file ./data/edits/edited.md
python -m src draft --doc-id <id> --run-label run2 --use-learning
python -m src learning-report --doc-id <id>
```