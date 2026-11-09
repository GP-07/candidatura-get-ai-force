import re
import string
import unicodedata

from check_offer.models import QuoteStatus


def check_quote(quote, cv_text, generic_words):
    """Check whether a quote is acceptable evidence from the CV.

    The comparison ignores case, accents, repeated whitespace and line breaks,
    and it does not use an LLM.

    Special cases:
    - A missing or whitespace-only quote returns EMPTY.
    - A single generic word returns GENERIC_WORD, even if it is in the CV. This
      is checked before searching, so "desarrollo." is reported as generic even
      when the CV does not contain it with that period.
    - The generic word rule applies only to single-word quotes. A quote of two
      or more words is never rejected as generic.
    - The quote must match whole words: "Java" does not match "JavaScript".
      Quotes ending in symbols, such as "C++", are supported.

    Returns the QuoteStatus that describes the result.
    """
    normalized_quote = _normalize(quote or "")
    if not normalized_quote:
        return QuoteStatus.EMPTY

    if _is_single_generic_word(normalized_quote, generic_words):
        return QuoteStatus.GENERIC_WORD

    pattern = rf"(?<!\w){re.escape(normalized_quote)}(?!\w)"
    if re.search(pattern, _normalize(cv_text)):
        return QuoteStatus.VALID
    return QuoteStatus.NOT_FOUND


def _normalize(text):
    """Return a form of the text that is suitable for comparison.

    It applies Unicode NFKD normalization (Normalization Form Compatibility
    Decomposition), which does two things:
    - Compatibility: replaces presentation variants with their plain characters.
      For example, the PDF ligature "ﬁ" becomes the letters "f" and "i".
    - Decomposition: splits an accented character into its base letter and a
      separate combining mark. For example, "í" becomes "i" plus an accent.

    It then removes the combining marks, applies case folding and collapses all
    whitespace, including line breaks, into single spaces.

    Special case: removing combining marks also turns "ñ" into "n", so "año"
    and "ano" compare as equal.
    """
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return " ".join(without_accents.casefold().split())


def _is_single_generic_word(normalized_quote, generic_words):
    """Return whether an already normalized quote is one generic word.

    Special cases:
    - Any quote that contains a space is not a single word, so it returns False.
    - Surrounding punctuation is ignored, so "desarrollo." counts as "desarrollo".
    - The generic words are normalized too, so their case and accents do not
      affect the result.
    """
    if " " in normalized_quote:
        return False
    word = normalized_quote.strip(string.punctuation)
    return word in {_normalize(generic_word) for generic_word in generic_words}
