"""
Single source of the in-app data-handling notice shown next to the prompt form.

Keys are UI language codes. A value of None means "not translated yet"; the
English text is then shown instead (see get_notice).
"""

NOTICES = {
    'en': (
        "This tool is a separate application used inside PROODOS. "
        "Do not enter personal data of students or colleagues. "
        "What you type is sent to Google Gemini to generate the prompt. "
        "This tool does not store what you type."
    ),
    'el': None,
}


def get_notice(language):
    """Return the notice for a language code, falling back to English."""
    return NOTICES.get(language) or NOTICES['en']
