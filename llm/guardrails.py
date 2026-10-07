from pydantic import BaseModel, Field

from utils.validators import suspicious

NO_ANSWER = "The information is not available in the uploaded documents."
LOW_RELEVANCE = "I could not find sufficiently relevant information in the uploaded documents to answer this question reliably."


class EvidenceClaim(BaseModel):
    statement: str = Field(description="One factual sentence supported entirely by the cited excerpt.")
    source_label: str = Field(description="Exact supplied source label, such as S1.")
    supporting_quote: str = Field(description="An exact, verbatim excerpt from this source supporting the sentence.")


class GroundedAnswer(BaseModel):
    answerable: bool
    claims: list[EvidenceClaim] = Field(default_factory=list, max_length=12)


def safe_context(chunks, max_chars):
    """Second defense: discard flagged passages and bound the document context."""
    kept, used = [], 0
    for chunk in chunks:
        if suspicious(chunk.text):
            continue
        if used + len(chunk.text) > max_chars:
            continue
        used += len(chunk.text)
        kept.append(chunk.model_copy(update={"label": f"S{len(kept) + 1}"}))
    return kept


def validate_answer(answer: GroundedAnswer, chunks):
    """Reject the WHOLE answer on invalid citation/quote. Entailment remains a model risk."""
    if not answer.answerable or not answer.claims:
        return NO_ANSWER, []
    by_label = {chunk.label: chunk for chunk in chunks}
    lines, cited = [], []
    for claim in answer.claims:
        source = by_label.get(claim.source_label)
        quote = " ".join(claim.supporting_quote.split())
        if (source is None or len(quote) < 12 or not claim.statement.strip()
                or suspicious(claim.statement) or suspicious(quote)
                or quote not in " ".join(source.text.split())):
            return NO_ANSWER, []
        # Display source identity from trusted metadata, never model-generated filenames/pages.
        lines.append(f"{claim.statement.strip()} [{source.label}]")
        if source not in cited:
            cited.append(source)
    return "\n\n".join(lines), cited
