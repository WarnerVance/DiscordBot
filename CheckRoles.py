import discord


# Get configured logger


def check_pledge(name):
    """
    Check if a pledge exists in the pledges.csv file
    Args:
        name (str): Name of pledge to check
    Returns:
        bool: True if pledge exists, False otherwise
    """
    with open('pledges.csv', 'r') as fil:
        pledge_names = [line.rstrip('\n') for line in fil]
        if name in pledge_names:
            return True
        else:
            return False


async def check_vp_internal_role(interaction: discord.Interaction) -> bool:
    """
    Checks if the user who triggered the interaction has the "VP Internal" role in their guild.

    :param interaction: The interaction object representing the command or event in
        Discord. This is used to access details about the user and their roles.
    :type interaction: discord.Interaction
    :return: Returns ``True`` if the user has the "VP Internal" role; otherwise, sends
        an ephemeral message to the user and returns ``False``.
    :rtype: bool
    """
    vp_role = discord.utils.get(interaction.guild.roles, name="VP Internal")
    if vp_role is None or vp_role not in interaction.user.roles:
        await interaction.response.send_message(
            "You must have the VP Internal role to use this command.",
            ephemeral=True
        )
        return False
    return True


async def check_brother_role(interaction: discord.Interaction) -> bool:
    """
    Verify if a user has the Brother role.

    Args:
        interaction (discord.Interaction): The interaction to check

    Returns:
        bool: True if user has Brother role, False otherwise
    """
    brother_role = discord.utils.get(interaction.guild.roles, name="Brother")
    if brother_role is None or brother_role not in interaction.user.roles:
        await interaction.response.send_message("You must have the Brother role to use this command.", ephemeral=True)
        return False
    return True
