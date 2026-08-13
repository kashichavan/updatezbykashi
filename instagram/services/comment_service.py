import random

class CommentService:
    @staticmethod
    def format_reply_message(template, username=""):
        """Format dynamic variables into public comment reply."""
        if not template:
            return ""
        return template.replace("{username}", username).replace("{{username}}", username)

    @staticmethod
    def select_reply_variation(variations, username=""):
        """Pick a random variation to prevent duplicate spam flags."""
        if not variations:
            return "Sent you a DM 📩"
        if isinstance(variations, str):
            variations = [v.strip() for v in variations.split("\n") if v.strip()]
        selected = random.choice(variations)
        return CommentService.format_reply_message(selected, username)
