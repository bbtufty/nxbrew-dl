from discordwebhook import Discord


def discord_push(
    url,
    embeds,
):
    """Post a message to Discord

    Args:
        url (str): Discord URL
        embeds (list): List of dictionaries of embeds
    """

    discord = Discord(url=url)
    discord.post(
        embeds=embeds,
    )

    return True
