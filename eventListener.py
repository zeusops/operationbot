import importlib
from datetime import datetime, timedelta
from typing import Optional

from discord import Game, Member, Message, RawReactionActionEvent, Reaction
from discord.ext.commands import Cog

import config as cfg
from errors import EventNotFound, RoleNotFound
import messageFunctions as msgFnc
from event import Event
from eventDatabase import EventDatabase
from operationbot import OperationBot
from role import Role


class EventListener(Cog):

    def __init__(self, bot: OperationBot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        print("Waiting until ready")
        await self.bot.wait_until_ready()
        self.bot.fetch_data()
        commandchannel = self.bot.commandchannel
        await commandchannel.send("Connected")
        print("Ready, importing")
        await commandchannel.send("Importing events")
        # await EventDatabase.fromJson(self.bot)
        await self.bot.import_database()
        await commandchannel.send("syncing")
        await msgFnc.syncMessages(EventDatabase.events, self.bot)
        await commandchannel.send("synced")
        EventDatabase.toJson()
        # TODO: add conditional message creation
        # if debug:
        #   create messages
        # else:
        #   detect existing messages
        msg = "{} events imported".format(len(EventDatabase.events))
        print(msg)
        await commandchannel.send(msg)
        await self.bot.change_presence(activity=Game(name=cfg.GAME, type=2))
        print('Logged in as', self.bot.user.name, self.bot.user.id)

    @Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.member == self.bot.user or \
                payload.channel_id != self.bot.eventchannel.id:
            # Bot's own reaction, or reaction outside of the event channel
            return

        if payload.emoji.name in cfg.EXTRA_EMOJIS:
            return

        # Remove the reaction
        message = await self.bot.eventchannel.fetch_message(payload.message_id)
        user = payload.member
        await message.remove_reaction(payload.emoji, user)

        # Get event from database with message ID
        try:
            event: Event = EventDatabase.getEventByMessage(message.id)
        except EventNotFound as e:
            print(e)
            await self.bot.logchannel.send(
                "NOTE: reaction to a non-existent event. "
                "msg: {} role: {} user: {} ({}#{})"
                .format(message.id, payload.emoji,
                        user.display_name,
                        user.name, user.discriminator))
            return

        # Get emoji string
        if payload.emoji.is_custom_emoji():
            emoji = payload.emoji
        else:
            emoji = payload.emoji.name

        # Find signup of user
        signup: Optional[Role] = event.findSignupRole(user.id)

        # Get role with the emoji
        try:
            role = event.findRoleWithEmoji(emoji)
        except RoleNotFound as e:
            raise RoleNotFound("{} in event {} by user {}#{}"
                               .format(str(e), event, user.name,
                                       user.discriminator))
        if role.name == "ZEUS":
            # somebody with Nitro added the ZEUS reaction by hand
            return

        late_signoff = False

        """
        if user is not signed up and the role is     free, sign up
        if user is not signed up and the role is not free, do nothing
        if user is     signed up and they select    the same role, sign off
        if user is     signed up and they select a different role, do nothing
        """
        if signup is None:
            message_action = msignup(event, role, user)
        else:
            message_action = signoff_or_change(event, role, user, signup, emoji)
        
        await msgFnc.updateMessageEmbed(message, event)
        EventDatabase.toJson()
        if message_action is None:
            return

        late_signoff = calculate_signoff_delta(event, role)

        if late_signoff is not None and not event.sideop:
            message = "{}: User {} ({}#{}) signed off from {} role {} " \
                       "{} before the operation." \
                        .format(self.bot.signoff_notify_user.mention,
                                user.display_name,
                                user.name,
                                user.discriminator,
                                event,
                                role.emoji,
                                late_signoff)
        else:
            message = "{}: event: {} role: {} user: {} ({}#{})" \
                        .format(message_action, event, emoji,
                                user.display_name,
                                user.name,
                                user.discriminator)
        await self.bot.logchannel.send(message)


    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author == self.bot.user:
            return
        if message.guild is None:
            owner = self.bot.owner
            await owner.send("DM: [{}]: {}".format(
                message.author, message.content))


def setup(bot: OperationBot):
    importlib.reload(cfg)
    bot.add_cog(EventListener(bot))

#KOSI START REFRACTORING (needs improvements with naming xD)
def msignup(given_event : Event,  given_role : Role, given_user):
        if given_role.userID is None:
            given_event.signup(given_role, given_user)
            return "Signup"
        else:
            return None
        
def signoff_or_change(given_event : Event,  given_role : Role, given_user, given_signup: Optional[Role], given_emoji):
    given_event.undoSignup(given_user)
    if given_signup.emoji == given_emoji:
        return "Signoff"
    else:
        changed = msignup(given_event, given_role, given_user)
        if changed is not None:
            return "Change"
        else:
            return None

def calculate_signoff_delta(given_event : Event, given_role : Role):
    if given_role.name in cfg.SIGNOFF_NOTIFY_ROLES[given_event.platoon_size]:
        time_delta = given_event.date - datetime.today()
        days = time_delta.days
        hours = time_delta.seconds // (60 * 60)
        mins = (time_delta.seconds - hours * 60 * 60) // 60
        if days > 0:
            timeframe = "{} days".format(days)
        else
            timeframe = "{}h{}min".format(hours, mins)
        if time_delta > timedelta(days=0):
            if time_delta < cfg.SIGNOFF_NOTIFY_TIME:
                return timeframe
    return None  
#KOSI END