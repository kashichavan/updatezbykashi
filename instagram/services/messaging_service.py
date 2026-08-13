class MessagingService:
    @staticmethod
    def format_dm_message(template, username="", first_name="", comment="", reel="", link=""):
        """Format DM variables."""
        if not template:
            template = "Hey {{username}}! Thanks for commenting. Here is your link: {{link}}"
        
        msg = template
        msg = msg.replace("{{username}}", username).replace("{username}", username)
        msg = msg.replace("{{first_name}}", first_name or username).replace("{first_name}", first_name or username)
        msg = msg.replace("{{comment}}", comment).replace("{comment}", comment)
        msg = msg.replace("{{reel}}", reel).replace("{reel}", reel)
        msg = msg.replace("{{link}}", link).replace("{link}", link)
        return msg
