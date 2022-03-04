from discord import DMChannel


class CheckMsg(object):
    def __init__(self, ctx=None, authid=None) -> None:
        """
        Class runs a check and returns a boolean based on the author id.
        :param ctx: Context of message
        :param authid: Authors id number
        """
        self.ctx = ctx
        self.authid = authid

    def dm_check(self, _msg=None) -> bool:
        """
        Run a check to see if the message is not from the bot
        :param _msg: Passed message
        :return:
        """
        if isinstance(self.ctx.channel, DMChannel):
            return self.non_bot(_msg) and self.auth_msg(_msg)

    @staticmethod
    def non_bot(_msg=None) -> bool:
        """
        Determine if the message is not from the bot.
        :param _msg: Message in question
        :return:
        """
        return len(_msg.content) != 0 and not _msg.author.bot

    def auth_msg(self, _msg=None) -> bool:
        """
        Determine if the message is owned by the owner
        :param _msg: Message in question
        :return:
        """
        return _msg.author.id == self.authid

    @staticmethod
    def force_bot(_msg) -> bool:
        """
        Forces the bot to be the message author. ;)
        :return:
        """
        return True